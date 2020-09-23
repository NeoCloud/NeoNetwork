#!/usr/bin/env python3

import ipaddress

ZONE = '.127.10.in-addr.arpa'
def truncate(rev: str) -> str:
    assert rev.endswith(ZONE)
    rev = rev[:-len(ZONE)]
    return rev

def gen_reverse_pointers(network: str, ns: list) -> list:
    buf = list()
    net = ipaddress.IPv4Network(network, strict=True)
    assert net.prefixlen > 24
    netrev = truncate(net.reverse_pointer)
    for _ns in ns:
        buf.append(f"{netrev:<10s} IN NS    {_ns}")

    for addr in net:
        cnamefr = truncate(addr.reverse_pointer)
        cnameto = f"{int.from_bytes(addr.packed, byteorder='big', signed=False) & 0xff}.{netrev}"
        buf.append(f"{cnamefr:<10s} IN CNAME {cnameto}")
    return buf

if __name__ == "__main__":
    print("\n".join(gen_reverse_pointers('10.127.8.64/26', ['ns1.jerry.neo.'])))
