# NeoNetwork Recommended Setup:

### Part 0: Routing Protocols

* BGP for EGP, the use of MP-BGP is encouraged
* OSPF for IGP, there's not much reason to use anything else these days, especially with pure software-based solution

### Part 1: Intra-AS (within your own AS) WireGuard configs

* Use IPv4 Link-Local addresses in point-to-point tunnels (such that all internal routing is determined by your IGP of choice)
* Only IPv6 loopback address is required to run OSPFv3
* Actual IPv4/IPv6 address for a node should be on a loopback interface
* Remember to set src addr to node addresses

### Part 2: Inter-AS (tunnels interfacing with other AS) WireGuard configs

* Use Link-Local or Point-to-Point addresses, depending on your (or your peer's) taste
* Older versions (before 8.5.1) of FRRouting have problems interfacing with BIRD when using Link-Local addresses, choose Point-to-Point in this case
* Point-to-Point setup requires less config in FRRouting

### Part -1: (Un)Common Pitfalls

* DO NOT RUN IGP ON AN INTERFACE THAT MIGHT CONTAIN PUBLIC IP (This kickstarts route flapping, use MACVLAN to avoid it)
