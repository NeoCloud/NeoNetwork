# NeoNetwork
A useless VPN network ready for peering!

Pull requests are welcome!  
Telegram Group: https://t.me/NeoNetworkVPN

## Peers:
	caasih.nerdpol.ovh		(10.127.0.1, Area 0, ASN 4201048576)
	ucbvax.nerdpol.ovh		(10.127.255.2, Area 0, ASN 4201048576)
	r2.tw.pan93412.dedyn.ioi	(10.127.3.1, Area 0)
	cuiqh.nerdpool.ovh		(10.127.0.34, Area 1)
	fiona.yukipedia.cf		(10.127.0.30, Area 2)
	hk-01.nextmoe.cloud.imiku.cn	(10.127.0.58, Area 3)  

## Routing Protocols
Any protocol supported by Quagga or FRRouting, recommended to use BGP.

## IP Addresses
All IPv4 addresses are under the range 10.127.0.0/16,
see routes.txt for allocated domain.

## DNS
There's a bind9 server on NeoPDP-11 (10.127.1.1), all domain names are under "neonetwork.unix".

# Connection Graph
![NeoNetwork Nodes](https://raw.githubusercontent.com/NeoChen1024/NeoNetwork/master/nodes.png)

# Files and Directories:
	ospf-area.txt:	OSPF Area Number
	bgp-asn.txt:	BGP AS Number
	routes.txt:	network subnet allocation
	named.conf:	Bind9 DNS configuration example
	nodes.dot:	connection graph
	tinc:		Tinc configuration example
	dns:		Bind9 DNS zone files
