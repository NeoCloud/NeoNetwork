#!/bin/sh
set -xeu

if ! which markdown 2>&1 >/dev/null; then
	echo "need markdown"
	exit
fi

(
	cat docs/header.html
	markdown README.md
	cat docs/footer.html
) >docs/index.html
