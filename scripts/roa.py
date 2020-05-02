#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from ipaddress import IPv4Network, IPv6Network
from itertools import combinations


class BashParser:
    def __init__(self):
        self.__pa = None # are we parsing bash array?
    def parseline(self, line):
        repl_quotes = lambda t: t.replace('"', '').replace('\'', '')
        line = line.strip()
        if '=(' in line:
            self.__pa = (repl_quotes(line).split('=(')[0], list())
            return None
        if self.__pa:
            if line:
                if line.endswith(')'):
                    if line[:-1]:
                        self.__pa[1].append(repl_quotes(line[:-1]))
                    ret = self.__pa
                    self.__pa = None
                    return ret
                else:
                    self.__pa[1].append(repl_quotes(line))
            return None
        else:
            if not line or line.startswith('#'):
                return None
            l = line.split('=')
            assert len(l) >= 2
            return [l[0], '='.join([repl_quotes(i) for i in l[1:]])]
bp = BashParser()

def shell2dict(shellscript):
    fc = dict()
    for line in shellscript.split('\n'):
        r = bp.parseline(line)
        if r:
            key, val = r
            fc[key.lower()] = val
    return fc

cwd = Path()
assert not [d for d in ("asn", "route", "route6", "node", "entity") if not (cwd / d).is_dir()]

def str2asn(s_asn):
    s_asn = s_asn.strip().lower()
    if s_asn.startswith('as'):
        s_asn = s_asn[2:]
    return int(s_asn)


def neoneo_get_people():
    people = dict()
    for f in (cwd / "entity").iterdir():
        try:
            if not f.is_file():
                continue
            fc = shell2dict(f.read_text())
            present_keys = ('name', 'desc', 'contact', 'babel')
            assert f.name
            people[f.name] = {k: fc.get(k) for k in present_keys}
            for v in people[f.name].values():
                assert v is not None
        except Exception:
            print("[!] Error while processing file", f)
            raise
    return people
PEOPLE = neoneo_get_people()

def neonet_get_asns():
    asns = dict()
    for f in (cwd / "asn").iterdir():
        try:
            if not f.is_file():
                continue
            fc = shell2dict(f.read_text())
            present_keys = ('name', 'owner', 'desc')
            asns[str2asn(f.name)] = {k: fc.get(k) for k in present_keys}
            assert fc.get('owner') in PEOPLE
            for v in asns[str2asn(f.name)].values():
                assert v is not None
        except Exception:
            print("[!] Error while processing file", f)
            raise
    return asns
ASNS = neonet_get_asns()

def node2asn():
    node_table = dict()
    for f in (cwd / "node").iterdir():
        try:
            if not f.is_file():
                continue
            fc = shell2dict(f.read_text())
            asn = str2asn(fc.get('asn'))
            node_table[f.name] = asn
        except Exception:
            print("[!] Error while processing file", f)
            raise
    return node_table
NODE_TABLE = node2asn()

def neonet_route2roa(dirname, is_ipv6=False):
    roa_entries = list()
    for f in (cwd / dirname).iterdir():
        try:
            if not f.is_file():
                continue
            fc = shell2dict(f.read_text())
            nettype = IPv6Network if is_ipv6 else IPv4Network
            get_supernet = lambda s_net: None if not s_net else nettype(s_net, strict=True)
            roa_entries_key = ("asn", "prefix", "supernet")
            if fc.get('type').lower() in ('lo', 'subnet'):
                asn = str2asn(fc.get('asn'))
                assert asn in ASNS
                route = f.name.replace(',', '/')
                supernet = get_supernet(fc.get('supernet'))
                roa_entries.append(dict(zip(roa_entries_key, [asn, nettype(route, strict=True), supernet])))
            elif fc.get('type').lower().startswith('tun'):
                assert NODE_TABLE[fc.get('downstream')] # extra check for downstream
                asn = NODE_TABLE[fc.get('upstream')]
                assert asn in ASNS
                route = f.name.replace(',', '/')
                supernet = get_supernet(fc.get('supernet'))
                roa_entries.append(dict(zip(roa_entries_key, [asn, nettype(route, strict=True), supernet])))
            else:
                assert fc.get('type').lower() in ('ptp',)
        except Exception:
            print("[!] Error while processing file", f)
            raise
    roa_entries.sort(key=lambda l: l['asn'])
    for _net1, _net2 in combinations(roa_entries, 2):
        net1, net2 = sorted([_net1, _net2], key=lambda net: net['prefix'].prefixlen)
        if net1['prefix'].overlaps(net2['prefix']):
            if net1['prefix'] != net2['prefix'] and net1['prefix'].supernet_of(net2['prefix']) \
                and net2['supernet'] == net1['prefix']:
                # This is allowed
                pass
            else:
                print("[!] Error: found", net2, "overlaps", net1)
                raise AssertionError
    return roa_entries

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='NeoNetwork ROA tool')
    parser.add_argument('-m', '--max', type=int, default=29, help='set ipv4 max prefix length')
    parser.add_argument('-M', '--max6', type=int, default=64, help='set ipv6 max prefix length')
    parser.add_argument('-j', '--json', action='store_true', help='output json')
    parser.add_argument('-o', '--output', default='', help='write output to file')
    parser.add_argument('-4', '--ipv4', action='store_true', help='print ipv4 only')
    parser.add_argument('-6', '--ipv6', action='store_true', help='print ipv6 only')
    parser.add_argument('-e', '--export', action='store_true', help='export registry to json')
    args = parser.parse_args()
    if args.max < 0 or args.max6 < 0 or args.max > IPv4Network(0).max_prefixlen or args.max6 > IPv6Network(0).max_prefixlen:
        parser.error('check your max prefix length')

    roa4 = roa6 = list()
    if args.ipv4:
        roa4 = neonet_route2roa('route')
    elif args.ipv6:
        roa6 = neonet_route2roa('route6', True)
    else:
        roa4 = neonet_route2roa('route')
        roa6 = neonet_route2roa('route6', True)

    roa4 = [r for r in roa4 if r['prefix'].prefixlen <= args.max or r['prefix'].prefixlen == IPv4Network(0).max_prefixlen]
    roa6 = [r for r in roa6 if r['prefix'].prefixlen <= args.max6]

    for r in roa4:
        if r['prefix'].prefixlen == IPv4Network(0).max_prefixlen:
            r['maxLength'] = IPv4Network(0).max_prefixlen
        else:
            r['maxLength'] = args.max
    for r in roa6:
        r['maxLength'] = args.max6
    for r in (*roa4, *roa6):
        r['prefix'] = r['prefix'].with_prefixlen


    output = ""
    VALID_KEYS = ('asn', 'prefix', 'maxLength')
    if args.export:
        import json, time
        current = int(time.time())
        # people has [asns], asn has [route]
        d_output = {"metadata": {"generated": current, "valid": current+14*86400}, "people": dict()}
        for asn, asi in ASNS.items():
            as_route4 = list()
            as_route6 = list()
            vkeys = [k for k in VALID_KEYS if k != 'asn']
            for roa, as_route in ((roa4, as_route4), (roa6, as_route6)):
                for r in roa:
                    if r['asn'] == asn:
                        as_route.append({k:v for k, v in r.items() if k in vkeys})
            owner = asi['owner']
            peopledict = d_output['people'].setdefault(owner, {"info": PEOPLE[owner], "asns": list()})
            peopledict['asns'].append({"asn": asn, "routes": {'ipv4': as_route4, 'ipv6': as_route6}})
        output = json.dumps(d_output, indent=2)
    elif args.json:
        import json, time
        current = int(time.time())
        d_output = {"metadata": {"counts": len(roa4)+len(roa6), "generated": current, "valid": current+14*86400}, "roas": list()}
        for r in (*roa4, *roa6):
            # some preprocessing
            r['asn'] = "AS%d" % r['asn']
        for r in (*roa4, *roa6):
            d_output['roas'].append({k:v for k, v in r.items() if k in VALID_KEYS})
        output = json.dumps(d_output, indent=2)
    else:
        output += "# NeoNetwork ROA tool\n"
        pattern = 'route %s max %d as %d;'
        l_output = list()
        rdict2list = lambda d: [d[k] for k in VALID_KEYS]
        for (asn, prefix, maxlen) in [rdict2list(r) for r in (*roa4, *roa6)]:
            l_output.append(pattern % (prefix, maxlen, asn))
        output += '\n'.join(l_output)
    if not args.output or args.output == '-':
        print(output)
    else:
        Path(args.output).write_text(output)
        print('written to', args.output)
