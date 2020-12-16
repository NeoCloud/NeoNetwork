#!/usr/bin/env bash
# shellcheck disable=SC1091
set -eo pipefail

[ -n "$CI" ]

sudo apt update -qq
sudo DEBIAN_FRONTEND=noninteractive apt -o Dpkg::Options::=--force-confold install -y --no-install-recommends bind9-utils

alias check='PATH=/sbin:/usr/sbin:$PATH named-checkzone -i local'

pushd dns

check 'neo'                      neonetwork
check '127.10.in-addr.arpa'      db.10.127
check '7.2.1.0.0.1.d.f.ip6.arpa' db.fd10.127

popd
