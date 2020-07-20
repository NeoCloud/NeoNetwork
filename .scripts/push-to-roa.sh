#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

if [ -z "$SSHPRIVKEY" ]; then
	echo SSHPRIVKEY is not set
	exit 1
fi

mkdir -p "$HOME/.ssh"
echo "$SSHPRIVKEY" | base64 -d >"$HOME/.ssh/id_ed25519"
chmod 0600 "$HOME/.ssh/id_ed25519"

set -x

cd generated || exit 1

git remote set-url origin git@github.com:NeoCloud/NeoNetwork-ROA.git
git config user.name "NeoCloud ROA bot"
git config user.email "support@neocloud.tw"
git add .
git commit -m "Generated at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
git push
