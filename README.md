# NeoNetwork
A useless VPN network ready for peering!  
This network is connected with [DN42](https://dn42.net)  
Git Repo. [here](https://git.neocloud.tw)  
Pull requests are welcomed!  
Working language: `zh_* / en_*`  

## ROA

<https://roa.neocloud.tw>

## IXs

	caasih.neocloud.tw		(10.127.0.1,	ASN 4201270000)
	router.neocloud.tw		(10.127.255.2,	ASN 4201270000)
	r2.neocloud.tw			(10.127.3.1,	ASN 4201270000)
	bgp.septs.me			(IX,		ASN 4201270001)
	jpn.neo.jerryxiao.cc		(10.127.8.193,	ASN 4201270006)
	s.aureus.ga			(10.127.8.185,	ASN 4201270007)
	megumi.yukipedia.cf		(10.127.30.1,	ASN 4242421037)

## Routing Protocols

Any protocol supported by Bird, Quagga or FRRouting, BGP recommended.

## IP Addresses

All IPv4 addresses are under the range 10.127.0.0/16  
All IPv6 addresses are under the range fd10:127::/32  
see [route](https://github.com/NeoCloud/NeoNetwork/tree/master/route)
and [route6](https://github.com/NeoCloud/NeoNetwork/tree/master/route6) for allocated subnet.

## DNS

DNS Anycast is currently on `10.127.255.54` for IPv4 and `fd10:127:53:53::` for IPv6. All domain names are under ".neo".

## Connection Graph

![NeoNetwork Nodes](https://raw.githubusercontent.com/NeoCloud/NeoNetwork/master/nodes.svg)

## Files and Directories

	nodes.dot	Connection graph
	asn/		BGP AS Number allocation
	entity/		Entitys
	route/		Network subnet allocation
	node/		Nodes
	peer/		Peering status
	vpn/		VPN configuration examples (Tinc & WireGuard)
	dns/		Bind9 DNS zone files and example configuration
