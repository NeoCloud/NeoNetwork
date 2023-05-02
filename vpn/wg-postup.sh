#!/usr/bin/env bash

IF="$1"
LOCAL_IP="$2"
PEER_IP="$3"
LOCAL_IPV6="$4"
PEER_IPV6="$5"

ip addr add "$LOCAL_IP" peer "$PEER_IP" dev "$IF"

if [ "$#" -ge 5 ]; then
	ip addr add "$LOCAL_IPV6" peer "$PEER_IPV6" dev "$IF"
fi
