#!/bin/sh

set -xe

if which dot 2>&1 > /dev/null ; then
	dot -T png nodes.dot -o nodes.png
else
	echo 'You need to install graphviz first'
fi

if [ "$1" != 'noopt' ]; then
	if which optipng 2>&1 > /dev/null ; then
		optipng -o7 -zm9 -v nodes.png
	else
		echo 'optipng is not present, not optimizing compression'
	fi
fi
