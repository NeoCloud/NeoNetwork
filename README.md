# NeoNetwork
A useless VPN network ready for peering!

Pull requests are welcomed!  
Telegram Group invitation link available at TXT record of `join-telegram.neocloud.tw`

## Peers:
	caasih.neocloud.tw		(10.127.0.1,	ASN 4201048576)
	router.neocloud.tw		(10.127.255.2,	ASN 4201048576)
	r2.neocloud.tw			(10.127.3.1,	ASN 4201048576)
	megumi.yukipedia.cf		(10.127.0.30)
	hk-01.nextmoe.cloud.imiku.cn	(10.127.0.58,	ASN 4200012450)
	bgp.septs.me                    (		ASN 4200055555)
	jp-03.nextmoe.cloud.imiku.cn	(10.127.4.15,	ASN 4200012450)
	ru-01.nextmoe.cloud.imiku.cn	(10.127.4.14,	ASN 4200012450)
	jpn.neo.jerryxiao.cc		(10.127.8.193,	ASN 4200066666)

## Routing Protocols
Any protocol supported by Quagga or FRRouting, recommended to use BGP.

## IP Addresses
All IPv4 addresses are under the range 10.127.0.0/16,
see routes.txt for allocated domain.

## DNS
There's a bind9 server on NeoPDP-11 (10.127.1.1), all domain names are under "neonetwork.unix".

## Connection Graph
![NeoNetwork Nodes](https://raw.githubusercontent.com/NeoChen1024/NeoNetwork/master/nodes.svg)

## Files and Directories:
	ospf-area.txt	OSPF Area Number
	bgp-asn.txt	BGP AS Number
	routes.txt	network subnet allocation
	named.conf	Bind9 DNS configuration example
	nodes.dot	connection graph
	vpn/		VPN configuration examples (Tinc & WireGuard)
	dns/		Bind9 DNS zone files
