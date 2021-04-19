#!/usr/bin/env python3
import argparse
import json
import re
import time
from collections import defaultdict
from contextlib import redirect_stdout
from io import StringIO
from ipaddress import IPv4Network, IPv6Network, ip_network
from itertools import combinations
from pathlib import Path

import netaddr
import toml
from tabulate import tabulate

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


def name_to_nic_hdl(name):
    r, num = re.subn(r"[^0-9A-Z]", "-", name.upper())
    _r = len(r.replace("-", ""))
    assert _r >= 3  # has at least 3 effective chars
    assert r[0] != "-"  # starts with [0-9A-Z]
    assert num < _r  # not too many subs
    return r


def iter_toml_file(path: str):
    for item in Path(path).iterdir():
        if not item.is_file() or item.suffix != ".toml":
            continue
        yield item, toml.loads(item.read_text())


def load_entities():
    for item, entity in iter_toml_file("entity"):
        yield item.stem, entity


def load_asn(entities: dict):
    for item, entity in iter_toml_file("asn"):
        asn = int(item.stem.lstrip("AS"))
        entity["source"] = (
            is_neo_network_asn(asn)
            and "NeoNetwork"
            or is_dn42_asn(asn)
            and "DN42"
            or entity.get("source")
        )
        assert entity["owner"] in entities
        assert entity["source"] in ["NeoNetwork", "DN42", "Internet"]
        yield asn, entity


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
                assert not fields["supernet"] or (
                    is_neo_network(fields["supernet"])
                    and fields["supernet"].supernet_of(fields["prefix"])
                )
                yield pick(fields, ["asn", "name", "type", "prefix", "supernet"])

    entities = sorted(make_route(), key=lambda item: item["asn"])
    prefixes = [item["prefix"] for item in entities]
    for net1, net2 in combinations(
        sorted(entities, key=lambda net: net["prefix"].prefixlen), 2
    ):
        if net1["type"] == net2["type"] == "loopback":
            continue
        if not net1["prefix"].overlaps(net2["prefix"]):
            continue
        entity_from_net = lambda net: asn_table.get(net["asn"])["owner"]
        try:
            assert net1["prefix"] != net2["prefix"]
        except AssertionError:
            assert net1['asn'] != net2['asn'] and entity_from_net(net1) == entity_from_net(net2)
            continue
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

def export_dnssec_dnskey():
    dnskey_path = Path("dns") / "dnssec"
    dnskeys = list()
    for f in dnskey_path.iterdir():
        if f.name.endswith(".keys"):
            zonekey = {"zone": "", "dnskeys": list()}
            records = f.read_text().split("\n")
            records = [r.split() for r in records if r]
            for zone, _ttl, _in, _dnskey, *dnskey in records:
                int(_ttl)
                assert _in == "IN" and _dnskey == "DNSKEY"
                if not zonekey["zone"]:
                    zonekey["zone"] = zone
                else:
                    assert zonekey["zone"] == zone
                zonekey["dnskeys"].append(" ".join(dnskey))
            if zonekey["zone"]:
                dnskeys.append(zonekey)
    return dnskeys

def make_export(roa4, roa6):
    def modify_entity(entity):
        entity["nic_hdl"] = name_to_nic_hdl(entity["name"])
        return entity

    def filter_route(records, asn):
        return [
            pick(roa, ["prefix", "maxLength"], name="netname")
            for roa in records
            if roa["asn"] == asn
        ]

    entities = dict(load_entities())
    asn_list = [
        {
            "asn": asn,
            "owner": asn_info["owner"],
            "name": asn_info["name"],
            "source": asn_info["source"],
            "description": asn_info.get("description"),
            "routes": {
                "ipv4": filter_route(roa4, asn),
                "ipv6": filter_route(roa6, asn),
            },
        }
        for asn, asn_info in load_asn(entities)
    ]

    current = int(time.time())
    output = {
        "metadata": {"generated": current, "valid": current + 14 * 86400},
        "people": {
            owner: {
                "info": modify_entity(entity),
                "asns": list(filter(lambda item: item["owner"] == owner, asn_list)),
            }
            for owner, entity in entities.items()
        },
        "dnssec": export_dnssec_dnskey()
    }
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
        "route {prefix} max {maxLength} as {asn};".format_map(roa)
        for roa in (*roa4, *roa6)
    ]
    return "\n".join(["# NeoNetwork ROA tool", "", *records])


def make_summary():
    entities = dict(load_entities())
    asn_table = dict(load_asn(entities))
    node_table = node_to_asn(set(asn_table.keys()))
    stream = StringIO()
    with redirect_stdout(stream):
        print("# NeoNetwork Summary")
        print()
        print("## Entity table")
        print()
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
            tablefmt="github",
        )
        print(entity_table)
        print()
        print("## AS table")
        print()
        as_table = tabulate(
            (
                (entity["source"], "AS{}".format(asn), entity["owner"], entity["name"])
                for asn, entity in sorted(asn_table.items(), key=lambda item: item[0])
            ),
            headers=["Source", "ASN", "Owner", "Name"],
            tablefmt="github",
        )
        print(as_table)
        print()
        print("## Node table")
        print()
        node_table = tabulate(
            (
                ("AS{}".format(asn), name)
                for name, asn in sorted(node_table.items(), key=lambda item: item[1])
            ),
            headers=["ASN", "Name"],
            tablefmt="github",
        )
        print(node_table)
        print()
        print("## Peer table")
        print()
        peer_table = tabulate(
            (
                (item.stem, downstream)
                for item, entity in iter_toml_file("peer")
                for downstream in entity["to-peer"]
            ),
            headers=["Upstream", "Downstream"],
            tablefmt="github",
            colalign=("right",),
        )
        print(peer_table)
        print()
        print("## Route table")
        print()
        route_table = tabulate(
            (
                (
                    "AS{asn}".format_map(entity),
                    entity["name"],
                    entity["type"],
                    entity["prefix"] or "",
                    entity["supernet"] or "",
                )
                for entity in route_to_roa(asn_table)
            ),
            headers=["ASN", "Name", "Type", "Prefix", "Supernet"],
            tablefmt="github",
        )
        print(route_table)
        print()
        print("## Used CIDR Range")
        print()
        prefixes = netaddr.cidr_merge(
            netaddr.IPNetwork(str(entity["prefix"]))
            for entity in route_to_roa(asn_table)
        )
        print("```")
        for prefix in prefixes:
            print(prefix)
        print("```")
        IP_VRSIONS = {4, 6}
        total_ip_count = {ver: sum([prefix.num_addresses for prefix in NEO_NETWORK_POOL if prefix.version == ver]) for ver in IP_VRSIONS}
        used_ip_count = {ver: sum([ip_network(str(prefix)).num_addresses for prefix in prefixes if prefix.version == ver]) for ver in IP_VRSIONS}
        print()
        print("## Address Space Usage")
        print()
        address_space_usage_table = tabulate(
            (
                (f"IPv{ver}", f"{(t:=total_ip_count.get(ver)):.5g}", f"{(u:=used_ip_count.get(ver)):.5g}", f"{t-u:.5g}", f"{u/t*100:.2f}%", f"{(t-u)/t*100:.2f}%")
                for ver in IP_VRSIONS
            ),
            headers=["IP Version", "Total", "Used", "Free", "Percent Used", "Percent Free"],
            tablefmt="github",
            disable_numparse=True
        )
        print(address_space_usage_table)
    return stream.getvalue()


def main(args):
    entities = dict(load_entities())
    asn_table = dict(load_asn(entities))
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
