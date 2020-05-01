# NeoNetwork
A useless VPN network ready for peering!  
**WARNING:** This network is not interconnected to DN42 yet  
Git Repo. [here](https://git.neocloud.tw)  
Pull requests are welcomed!  
Working language: `zh_* / en_*`  
Telegram Group invitation link available at TXT record of `join-telegram.neocloud.tw`

## IXs

	caasih.neocloud.tw		(10.127.0.1,	ASN 4201270000)
	router.neocloud.tw		(10.127.255.2,	ASN 4201270000)
	r2.neocloud.tw			(10.127.3.1,	ASN 4201270000)
	bgp.septs.me			(IX,		ASN 4201270001)
	hk-01.nextmoe.cloud.imiku.cn	(10.127.4.10,	ASN 4201270008)
	jp-03.nextmoe.cloud.imiku.cn	(10.127.4.15,	ASN 4201270008)
	ru-01.nextmoe.cloud.imiku.cn	(10.127.4.14,	ASN 4201270008)
	jpn.neo.jerryxiao.cc		(10.127.8.193,	ASN 4201270006)
	s.aureus.ga			(10.127.8.185,	ASN 4201270007)
	megumi.yukipedia.cf		(10.127.30.1,	ASN 4242421037)

## Routing Protocols

Any protocol supported by Quagga or FRRouting, recommended to use BGP.

## IP Addresses

All IPv4 addresses are under the range 10.127.0.0/16  
All IPv6 addresses are under the range fd10:127::/32  
see routes.txt for allocated domain.

## DNS

There's a bind9 server on dns.neocloud.tw (10.127.225.2), all domain names are under ".neo".

## Connection Graph

![NeoNetwork Nodes](https://raw.githubusercontent.com/NeoChen1024/NeoNetwork/master/nodes.svg)

## Files and Directories

	nodes.dot	Connection graph
	asn/		BGP AS Number allocation
	people/		Peoples
	route/		Network subnet allocation
	node/		Nodes
	vpn/		VPN configuration examples (Tinc & WireGuard)
	dns/		Bind9 DNS zone files and example configuration
