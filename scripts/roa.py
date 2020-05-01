#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from ipaddress import IPv4Network, IPv6Network
from itertools import combinations

def keyVal(line):
    l = line.split('=')
    assert len(l) > 1
    repl_quotes = lambda t: t.replace('"', '').replace('\'', '')
    return [l[0].strip(), '='.join([repl_quotes(i).strip() for i in l[1:]])]

cwd = Path()
assert not [d for d in ("asn", "route", "route6") if not (cwd / d).is_dir()]

def get_asns():
    asns = list()
    for f in (cwd / "asn").iterdir():
        try:
            if not f.is_file():
                continue
            assert f.name.lower().startswith('as')
            asns.append(int(f.name[2:]))
        except Exception:
            print("[!] Error while processing file", f)
            raise
    return asns

ASNS = get_asns()

def route2roa(dirname, is_ipv6=False):
    roa_entries = list()
    for f in (cwd / dirname).iterdir():
        try:
            if not f.is_file():
                continue
            t = f.read_text()
            lines = t.split('\n')
            fc = dict()
            for line in lines:
                l = line.strip()
                if not l or l.startswith('#'):
                    continue
                key, val = keyVal(l)
                fc[key.lower()] = val.lower()
            nettype = IPv6Network if is_ipv6 else IPv4Network
            if fc.get('type') in ('lo', 'subnet'):
                asn = int(fc.get('as'))
                assert asn in ASNS
                route = f.name.replace(',', '/')
                roa_entries.append([asn, nettype(route, strict=True)])
            elif fc.get('type').startswith('tun'):
                asn = int(fc.get('upstream').split(':')[1])
                assert asn in ASNS
                route = f.name.replace(',', '/')
                roa_entries.append([asn, nettype(route, strict=True)])
            else:
                assert fc.get('type') in ('ptp',)
        except Exception:
            print("[!] Error while processing file", f)
            raise
    roa_entries.sort(key=lambda l: l[0])
    for en1, en2 in combinations(roa_entries, 2):
        if en1[1].overlaps(en2[1]):
            print("[!] Error: found", en1[1], "overlaps", en2[1])
            raise AssertionError
    return roa_entries

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='NeoNetwork ROA tool')
    parser.add_argument('-m', '--max', type=int, default=30, help='set ipv4 max prefix length')
    parser.add_argument('-M', '--max6', type=int, default=64, help='set ipv6 max prefix length')
    parser.add_argument('-j', '--json', action='store_true', help='output json')
    parser.add_argument('-o', '--output', default='', help='write output to file')
    parser.add_argument('-4', '--ipv4', action='store_true', help='print ipv4 only')
    parser.add_argument('-6', '--ipv6', action='store_true', help='print ipv6 only')
    args = parser.parse_args()
    if args.max < 0 or args.max6 < 0 or args.max > IPv4Network(0).max_prefixlen or args.max6 > IPv6Network(0).max_prefixlen:
        parser.error('check your max prefix length')

    roa4 = roa6 = list()
    if args.ipv4:
        roa4 = route2roa('route')
    elif args.ipv6:
        roa6 = route2roa('route6', True)
    else:
        roa4 = route2roa('route')
        roa6 = route2roa('route6', True)

    roa4 = [r for r in roa4 if r[1].prefixlen <= args.max or r[1].prefixlen == IPv4Network(0).max_prefixlen]
    roa6 = [r for r in roa6 if r[1].prefixlen <= args.max6]

    for r in roa4:
        if r[1].prefixlen == IPv4Network(0).max_prefixlen:
            r.append(IPv4Network(0).max_prefixlen)
        else:
            r.append(args.max)
        r[1] = r[1].with_prefixlen
    for r in roa6:
        r.append(args.max6)
        r[1] = r[1].with_prefixlen

    output = ""
    if args.json:
        import json
        d_output = dict()
        for r in roa4:
            d_output.setdefault('ipv4', list()).append(dict(zip(['asn', 'prefix', 'max'], r)))
        for r in roa6:
            d_output.setdefault('ipv6', list()).append(dict(zip(['asn', 'prefix', 'max'], r)))
        output = json.dumps(d_output, indent=2)
    else:
        output += "# NeoNetwork ROA tool\n"
        pattern = 'route %s max %d as %d;'
        l_output = list()
        for (asn, prefix, maxlen) in roa4:
            l_output.append(pattern % (prefix, maxlen, asn))
        for (asn, prefix, maxlen) in roa6:
            l_output.append(pattern % (prefix, maxlen, asn))
        output += '\n'.join(l_output)
    if not args.output or args.output == '-':
        print(output)
    else:
        Path(args.output).write_text(output)
        print('written to', args.output)
