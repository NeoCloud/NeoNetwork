#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

if [ ! -n "$SSHPRIVKEY" ]; then
	echo SSHPRIVKEY is not set
	exit 1
fi

mkdir -p "$HOME/.ssh"
echo "$SSHPRIVKEY" | base64 -d >"$HOME/.ssh/id_ed25519"
chmod 0600 "$HOME/.ssh/id_ed25519"

set -x

pushd generated
git add .
git config user.name "neonet roa bot"
git config user.email "bot@github.com"
git commit -m "Generated at $(TZ='UTC' date +%Y%m%d-%H%M%S.%N)"
git push --force --quiet "git@github.com:NeoCloud/NeoNetwork-ROA.git" HEAD:master
