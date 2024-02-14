# NeoNetwork
Yet another VPN network ready for peering!  
This network is connected with [DN42](https://dn42.net)  
Git Repo. [here](https://github.com/NeoCloud/NeoNetwork)  
Pull requests are welcomed!  
Working language: `zh_* / en_*`  

## ROA

<https://roa.neocloud.tw>

## IXs

	neovax.neocloud.tw		(10.127.110.1,	ASN 4201270000)
	fsnvax.neocloud.tw		(10.127.16.240,	ASN 4201270000)
	jpn.neo.jerryxiao.cc		(10.127.8.193,	ASN 4201270006)
	s.aureus.icu			(10.127.8.185,	ASN 4201270007)

## Address Allocation

All IPv4 addresses are under the range 10.127.0.0/16  
All IPv6 addresses are under the range fd10:127::/32  
see [route](https://github.com/NeoCloud/NeoNetwork/tree/master/route)
and [route6](https://github.com/NeoCloud/NeoNetwork/tree/master/route6) for allocated subnet.

## DNS

DNS Anycast is currently on `10.127.255.54` for IPv4 and `fd10:127:53:53::` for IPv6. All domain names are under ".neo".

## Certificate Authority

Root certificate can be downloaded from [here](https://github.com/NeoCloud/NeoNetwork/blob/master/ca/neonetwork.crt). An acmev2-api is available at `https://acme.neo/acme/acme/directory`.

## Files and Directories

	nodes.dot	Connection graph
	asn/		BGP AS Number allocation
	entity/		Entitys
	route/		Network subnet allocation
	vpn/		VPN configuration examples (Tinc & WireGuard)
	dns/		Bind9 DNS zone files and example configuration
