#!/usr/bin/env bash

IF="$1"
LOCAL_IP="$2"
PEER_IP="$3"
LOCAL_IPV6="$4"
PEER_IPV6="$5"

ip addr del "$LOCAL_IP" dev "$IF"
ip addr add "$LOCAL_IP" peer "$PEER_IP" dev "$IF"
ip addr del "$LOCAL_IPV6"
ip addr add "$LOCAL_IPV6" peer "$PEER_IPV6" dev "$IF"
