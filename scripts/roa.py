#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from ipaddress import IPv4Network, IPv6Network, ip_network
from itertools import combinations
import re

NEONET_ADDR_POOL = ('10.127.0.0/16', 'fd10:127::/32')
NEONET_ADDR_POOL = [ip_network(neo) for neo in NEONET_ADDR_POOL]
IS_NEONET = lambda net: bool([True for neo in NEONET_ADDR_POOL if net.version == neo.version and net.subnet_of(neo)])
AS_IS_NEONET = lambda asn: 4201270000 <= asn <= 4201279999
assert hasattr(IPv4Network, 'subnet_of') # needs at least python 3.7

class BashParser:
    def __init__(self):
        self.__pa = None # are we parsing bash array?
    def end(self):
        assert not self.__pa # check if array ends properly
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
            assert len(l) >= 2 # is this line key=value syntax?
            return [l[0], '='.join([repl_quotes(i) for i in l[1:]])]
bp = BashParser()

def shell2dict(shellscript):
    fc = dict()
    for line in shellscript.split('\n'):
        r = bp.parseline(line)
        if r:
            key, val = r
            fc[key.lower()] = val
    bp.end()
    return fc

cwd = Path()
assert not [d for d in ("asn", "route", "route6", "node", "entity") if not (cwd / d).is_dir()]

def str2asn(s_asn, strict=None):
    """ strict: 1 with prefix AS, other bool(x)==True without prefix AS """
    s_asn = s_asn.strip().lower()
    if strict == 1:
        assert s_asn.startswith('as')
    elif strict:
        assert int(s_asn)
    if s_asn.startswith('as'):
        s_asn = s_asn[2:]
    return int(s_asn)

def name2nichdl(name):
    r, num = re.subn(r'[^0-9A-Z]', '-', name.upper())
    _r = len(r.replace('-', ''))
    assert _r >= 3     # has at least 3 effective chars
    assert r[0] != '-' # starts with [0-9A-Z]
    assert num < _r    # not too many subs
    return r

def neoneo_get_people():
    nic_hdl_names = set()
    people = dict()
    for f in (cwd / "entity").iterdir():
        try:
            if not f.is_file():
                continue
            fc = shell2dict(f.read_text())
            present_keys = ('name', 'desc', 'contact', 'babel', 'auth')
            assert f.name
            people[f.name] = {k: fc.get(k) for k in present_keys}
            nic_hdl = name2nichdl(f.name)
            assert nic_hdl not in nic_hdl_names # nic_hdl collision
            nic_hdl_names.add(nic_hdl)
            people[f.name]['nic_hdl'] = nic_hdl
            for v in people[f.name].values():
                assert v is not None
            auth = people[f.name]['auth']
            if auth:
                method, data = auth.split(':')
                assert method in ('PGP', 'SSH')
                if method == 'PGP':
                    assert len(data) == 40 # invaild pgp fingerprint
                elif method == 'SSH':
                    assert data.startswith('ssh-') # invalid ssh pubkey
                people[f.name]['auth'] = f"{'pgp-fingerprint ' if method == 'PGP' else ''}{data.strip()}"
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
            present_keys = ('name', 'owner', 'desc', 'source')
            required_keys = ('name', 'owner', 'source')
            asn = str2asn(f.name, 1)
            asns[asn] = {k: fc.get(k) for k in present_keys}
            assert fc.get('owner') in PEOPLE
            for k in required_keys:
                assert asns[asn].get(k) # required fields missing
            as_src = asns[asn].get('source')
            assert as_src in ('NeoNetwork', 'DN42', 'INET')
            assert AS_IS_NEONET(asn) or as_src != 'NeoNetwork'
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
            asn = str2asn(fc.get('asn'), 2)
            assert asn in ASNS
            node_table[f.name] = asn
        except Exception:
            print("[!] Error while processing file", f)
            raise
    return node_table
NODE_TABLE = node2asn()

def neonet_peercheck():
    for f in (cwd / "peer").iterdir():
        try:
            if not f.is_file():
                continue
            fc = shell2dict(f.read_text())
            desc = fc.get('desc')
            assert desc is not None
            upstream, downstream = f.name.split('~')
            assert upstream in NODE_TABLE
            assert downstream in NODE_TABLE
        except Exception:
            print("[!] Error while processing file", f)
            raise
neonet_peercheck()

def neonet_route2roa(dirname, is_ipv6=False):
    roa_entries = list()
    for f in (cwd / dirname).iterdir():
        try:
            if not f.is_file():
                continue
            fc = shell2dict(f.read_text())
            nettype = IPv6Network if is_ipv6 else IPv4Network
            get_supernet = lambda s_net: None if not s_net else nettype(s_net, strict=True)
            roa_entries_key = ("asn", "prefix", "supernet", "netname")
            if fc.get('type').lower() in ('lo', 'subnet'):
                asn = str2asn(fc.get('asn'), 2)
                assert asn in ASNS # asn not in as-dir
                route = f.name.replace(',', '/')
                net = nettype(route, strict=True)
                assert IS_NEONET(net)
                supernet = get_supernet(fc.get('supernet'))
                assert not supernet or IS_NEONET(supernet)
                netname = fc.get('name')
                assert netname
                roa_entries.append(dict(zip(roa_entries_key, [asn, net, supernet, netname])))
            else:
                raise AssertionError # unknown type
        except Exception:
            print("[!] Error while processing file", f)
            raise
    roa_entries.sort(key=lambda l: l['asn'])
    l_prefix = [_roa['prefix'] for _roa in roa_entries]
    for _net1, _net2 in combinations(roa_entries, 2):
        net1, net2 = sorted([_net1, _net2], key=lambda net: net['prefix'].prefixlen)
        if net1['prefix'].overlaps(net2['prefix']):
            try:
                assert net1['prefix'] != net2['prefix']
                assert net1['prefix'].supernet_of(net2['prefix'])
                s1net, s2net= (net1['supernet'], net2['supernet'])
                assert s2net # please include SUPERNET=<cidr> in your route
                # if net1(the bigger net) has a supernet s1net, then s1net and net1
                # will be checked or must have been checked, same for net2
                assert not s1net               or s1net in l_prefix # net1.supernet is garbage
                assert s2net == net1['prefix'] or s2net in l_prefix # net2.supernet is garbage
            except AssertionError:
                print("[!] Error: found", net1, "overlaps", net2)
                raise
    return roa_entries

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='NeoNetwork ROA tool')
    parser.add_argument('-m', '--max', type=int, default=29, help='set ipv4 max prefix length')
    parser.add_argument('-M', '--max6', type=int, default=64, help='set ipv6 max prefix length')
    parser.add_argument('-j', '--json', action='store_true', help='output json')
    parser.add_argument('-r', '--rfc8416', action='store_true', help='output rfc8416')
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
            vkeys.append('netname')
            for roa, as_route in ((roa4, as_route4), (roa6, as_route6)):
                for r in roa:
                    if r['asn'] == asn:
                        as_route.append({k:v for k, v in r.items() if k in vkeys})
            owner = asi['owner']
            peopledict = d_output['people'].setdefault(owner, {"info": PEOPLE[owner], "asns": list()})
            peopledict['asns'].append({"asn": asn, **{k:v for k, v in ASNS[asn].items() if k != 'owner'},
                                       "routes": {'ipv4': as_route4, 'ipv6': as_route6}})
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
    elif args.rfc8416:
        import json
        l_prefix = list()
        d_output = {'slurmVersion': 1, 'validationOutputFilters': {'prefixFilters': list(),
                    'bgpsecFilters': list()}, 'locallyAddedAssertions': {'bgpsecAssertions': list(),
                    'prefixAssertions': l_prefix}}
        for r in (*roa4, *roa6):
            vkeys = ["netname", "maxLength", *VALID_KEYS]
            substk = lambda k: "maxPrefixLength" if k == 'maxLength' else ("comment" if k == "netname" else k)
            l_prefix.append({substk(k):v for k, v in r.items() if k in vkeys})
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
