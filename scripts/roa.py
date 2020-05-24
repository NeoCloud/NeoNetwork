#!/usr/bin/env python3
import argparse
import json
import time
from collections import defaultdict
from contextlib import redirect_stdout
from io import StringIO
from ipaddress import IPv4Network, IPv6Network, ip_network
from itertools import combinations
from pathlib import Path

import toml

NEO_NETWORK_POOL = [ip_network("10.127.0.0/16"), ip_network("fd10:127::/32")]


def pick(entity: dict, fields: [str], **kwargs: dict):
    new_entity = {}
    for field in fields:
        new_entity[field] = entity.get(field)
    for old_field, new_field in kwargs.items():
        new_entity[new_field] = entity.get(old_field)
    return new_entity


def is_neo_network(address):
    return any(
        address.version == neo.version and address.subnet_of(neo)
        for neo in NEO_NETWORK_POOL
    )


def is_neo_network_asn(asn: int):
    return 4201270000 <= asn <= 4201279999


def is_dn42_asn(asn: int):
    return 4242420000 <= asn <= 4242429999


def iter_toml_file(path: str):
    for item in Path(path).iterdir():
        if not item.is_file() or item.suffix != ".toml":
            continue
        yield item, toml.loads(item.read_text())


def load_entities():
    return {item.stem: entity for item, entity in iter_toml_file("entity")}


def load_asn(entities: dict):
    def assert_entity(entity, asn):
        owner = entity.get("owner")
        source = entity.get("source")
        if is_neo_network_asn(asn):
            source = "NeoNetwork"
        elif is_dn42_asn(asn):
            source = "DN42"
        entity["source"] = source
        assert owner in entities
        assert source in ["NeoNetwork", "DN42", "Internet"]
        return entity

    mapping = {
        int(item.stem.lstrip("AS")): entity for item, entity in iter_toml_file("asn")
    }
    return {asn: assert_entity(entity, asn) for asn, entity in mapping.items()}


def node_to_asn(orignal_asn_set: set):
    node_table = dict()
    for _, entities in iter_toml_file("node"):
        mapping = {name: entity["asn"] for (name, entity) in entities.items()}
        asn_set = set(mapping.values())
        assert orignal_asn_set & asn_set == asn_set
        node_table.update(mapping)
    return node_table


def assert_peer(nodes: set):
    for item, entities in iter_toml_file("peer"):
        peers = set(entities["to-peer"])
        assert item.stem in nodes
        assert nodes & peers == peers


def route_to_roa(asn_table: dict):
    def make_route():
        for item, entity in iter_toml_file("route"):
            asn = int(item.stem.lstrip("AS"))
            for prefix, fields in entity.items():
                if fields["type"] not in ("loopback", "subnet"):
                    continue
                fields["asn"] = asn
                fields["prefix"] = ip_network(prefix, strict=True)
                supernet = fields.get("supernet")
                fields["supernet"] = (
                    ip_network(supernet, strict=True) if supernet else None
                )
                assert fields["name"]
                assert is_neo_network(fields["prefix"])
                assert not fields["supernet"] or is_neo_network(fields["supernet"])
                yield fields

    entities = (
        pick(route, ["asn", "name", "prefix", "supernet"]) for route in make_route()
    )
    entities = sorted(entities, key=lambda item: item["asn"])
    prefixes = [item["prefix"] for item in entities]
    for net1, net2 in combinations(
        sorted(entities, key=lambda net: net["prefix"].prefixlen), 2
    ):
        if not net1["prefix"].overlaps(net2["prefix"]):
            continue
        assert net1["prefix"] != net2["prefix"]
        assert net1["prefix"].supernet_of(net2["prefix"])
        s1net, s2net = (net1["supernet"], net2["supernet"])
        assert s2net  # please include supernet = <cidr> in your route
        # if net1(the bigger net) has a supernet s1net, then s1net and net1
        # will be checked or must have been checked, same for net2
        assert not s1net or s1net in prefixes  # net1.supernet is garbage
        assert s2net == net1["prefix"] or s2net in prefixes  # net2.supernet is garbage
    return entities


def prehandle_roa(asn_table: dict, args):
    roa = route_to_roa(asn_table)
    max_prefixlen = IPv4Network(0).max_prefixlen
    roa4 = filter(lambda item: isinstance(item["prefix"], IPv4Network), roa)
    roa6 = filter(lambda item: isinstance(item["prefix"], IPv6Network), roa)
    if args.ipv4:
        roa6 = []
    elif args.ipv6:
        roa4 = []
    roa4 = [
        r
        for r in roa4
        if r["prefix"].prefixlen <= args.max or r["prefix"].prefixlen == max_prefixlen
    ]
    roa6 = [r for r in roa6 if r["prefix"].prefixlen <= args.max6]
    for r in roa4:
        r["maxLength"] = args.max
        if r["prefix"].prefixlen == max_prefixlen:
            r["maxLength"] = max_prefixlen
    for r in roa6:
        r["maxLength"] = args.max6
    for r in (*roa4, *roa6):
        r["prefix"] = r["prefix"].with_prefixlen
    return roa4, roa6


def make_export(roa4, roa6):
    entities = load_entities()
    asn_table = load_asn(entities)
    current = int(time.time())
    output = {
        "metadata": {"generated": current, "valid": current + 14 * 86400},
        "people": {
            owner: {"info": entity, "asns": []} for owner, entity in entities.items()
        },
    }
    for asn, asn_info in asn_table.items():
        owner = asn_info["owner"]
        asn_item = {
            "asn": asn,
            "name": asn_info["name"],
            "source": asn_info["source"],
            "routes": {
                "ipv4": [
                    pick(roa, ["prefix", "maxLength"])
                    for roa in roa4
                    if roa["asn"] == asn
                ],
                "ipv6": [
                    pick(roa, ["prefix", "maxLength"])
                    for roa in roa6
                    if roa["asn"] == asn
                ],
            },
        }
        output["people"][owner]["asns"].append(asn_item)
    return json.dumps(output, indent=2)


def make_json(roa4, roa6):
    current = int(time.time())
    output = {
        "metadata": {
            "counts": len(roa4) + len(roa6),
            "generated": current,
            "valid": current + 14 * 86400,
        },
        "roas": [
            {"asn": "AS%d" % roa["asn"], **pick(roa, ["prefix", "maxLength"])}
            for roa in (*roa4, *roa6)
        ],
    }
    return json.dumps(output, indent=2)


def make_rfc8416(roa4, roa6):
    output = {
        "slurmVersion": 1,
        "validationOutputFilters": {"prefixFilters": [], "bgpsecFilters": []},
        "locallyAddedAssertions": {
            "bgpsecAssertions": [],
            "prefixAssertions": [
                pick(
                    roa, ["asn", "prefix"], maxLength="maxPrefixLength", name="comment",
                )
                for roa in (*roa4, *roa6)
            ],
        },
    }
    return json.dumps(output, indent=2)


def make_roa_records(roa4, roa6):
    records = [
        "route {asn} max {prefix} as {maxLength};".format_map(roa)
        for roa in (*roa4, *roa6)
    ]
    return "\n".join(["# NeoNetwork ROA tool", "", *records])


def make_summary():
    from tabulate import tabulate

    entities = load_entities()
    asn_table = load_asn(entities)
    node_table = node_to_asn(set(asn_table.keys()))
    stream = StringIO()
    with redirect_stdout(stream):
        print("Entity table:")
        entity_table = tabulate(
            (
                (
                    entity["name"],
                    entity.get("contact", {}).get("email"),
                    entity.get("contact", {}).get("telegram"),
                )
                for entity in entities.values()
            ),
            headers=["Name", "Email", "Telegram"],
            tablefmt="presto",
        )
        print(entity_table)
        print()
        print("AS table:")
        as_table = tabulate(
            (
                (entity["source"], "AS{}".format(asn), entity["owner"], entity["name"])
                for asn, entity in sorted(asn_table.items(), key=lambda item: item[0])
            ),
            headers=["Source", "ASN", "Owner", "Name"],
            tablefmt="presto",
        )
        print(as_table)
        print()
        print("Node table:")
        node_table = tabulate(
            (
                ("AS{}".format(asn), name)
                for name, asn in sorted(node_table.items(), key=lambda item: item[1])
            ),
            headers=["ASN", "Name"],
            tablefmt="presto",
        )
        print(node_table)
        print()
        print("Peer table:")
        peer_table = tabulate(
            (
                (item.stem, downstream)
                for item, entity in iter_toml_file("peer")
                for downstream in entity["to-peer"]
            ),
            headers=["Upstream", "Downstream"],
            tablefmt="presto",
            colalign=("right",),
        )
        print(peer_table)
        print()
        print("Route table:")
        route_table = tabulate(
            (
                (
                    "AS{asn}".format_map(entity),
                    entity["name"],
                    entity["prefix"] or "",
                    entity["supernet"] or "",
                )
                for entity in route_to_roa(asn_table)
            ),
            headers=["ASN", "Name", "Prefix", "Supernet"],
            tablefmt="presto",
        )
        print(route_table)
    return stream.getvalue()


def main(args):
    entities = load_entities()
    asn_table = load_asn(entities)
    node_table = node_to_asn(set(asn_table.keys()))
    assert_peer(set(node_table.keys()))
    roa4, roa6 = prehandle_roa(asn_table, args)
    if args.export:
        return make_export(roa4, roa6)
    elif args.json:
        return make_json(roa4, roa6)
    elif args.rfc8416:
        return make_rfc8416(roa4, roa6)
    elif args.summary:
        return make_summary()
    else:
        return make_roa_records(roa4, roa6)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NeoNetwork ROA tool")
    parser.add_argument(
        "-m", "--max", type=int, default=29, help="set ipv4 max prefix length"
    )
    parser.add_argument(
        "-M", "--max6", type=int, default=64, help="set ipv6 max prefix length"
    )
    parser.add_argument("-j", "--json", action="store_true", help="output json")
    parser.add_argument("-r", "--rfc8416", action="store_true", help="output rfc8416")
    parser.add_argument("-s", "--summary", action="store_true", help="output summary")
    parser.add_argument("-o", "--output", default="", help="write output to file")
    parser.add_argument("-4", "--ipv4", action="store_true", help="print ipv4 only")
    parser.add_argument("-6", "--ipv6", action="store_true", help="print ipv6 only")
    parser.add_argument(
        "-e", "--export", action="store_true", help="export registry to json"
    )
    args = parser.parse_args()
    if (
        args.max < 0
        or args.max6 < 0
        or args.max > IPv4Network(0).max_prefixlen
        or args.max6 > IPv6Network(0).max_prefixlen
    ):
        parser.error("check your max prefix length")
    output = main(args)
    if not args.output or args.output == "-":
        print(output)
    elif output:
        Path(args.output).write_text(output)
        print("written to", args.output)
