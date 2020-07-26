#!/bin/sh
set -xe

if which dot 2>&1 >/dev/null; then
	dot -T svg nodes.dot -o nodes.svg
else
	echo 'You need to install graphviz first'
fi
