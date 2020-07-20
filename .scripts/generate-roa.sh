#!/usr/bin/env bash
set -xeuo pipefail
IFS=$'\n\t'

export MAX_LEN_4=29
export MAX_LEN_6=64

if [ ! -d .venv ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

mkdir -p "generated"
pushed generated

.scripts/roa.py -m "$MAX_LEN_4" -M "$MAX_LEN_6" -o roa46_bird2.conf
.scripts/roa.py -m "$MAX_LEN_4" -M "$MAX_LEN_6" -4 -o roa4_bird2.conf
.scripts/roa.py -m "$MAX_LEN_4" -M "$MAX_LEN_6" -6 -o roa6_bird2.conf
.scripts/roa.py -m "$MAX_LEN_4" -M "$MAX_LEN_6" -j -o roa46.json
.scripts/roa.py -m "$MAX_LEN_4" -M "$MAX_LEN_6" -e -o neonetwork.json
.scripts/roa.py -m "$MAX_LEN_4" -M "$MAX_LEN_6" -r -o rfc8416.json
.scripts/roa.py --summary --output README.txt
