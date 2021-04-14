#!/usr/bin/env bash
# shellcheck disable=SC1091
set -xeo pipefail

[ -n "$CI" ]

install() {
    sudo DEBIAN_FRONTEND=noninteractive apt \
        -o Dpkg::Options::=--force-confold \
        install -y --no-install-recommends \
        bind9-utils
}
install || { sudo apt update -qq; install; }

check() {
    PATH=/sbin:/usr/sbin:$PATH named-checkzone -i local -l 86400 $@
}

pushd dns

check 'neo'                      neonetwork
check '127.10.in-addr.arpa'      db.10.127
check '7.2.1.0.0.1.d.f.ip6.arpa' db.fd10.127

popd
