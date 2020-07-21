#!/usr/bin/env bash
# shellcheck disable=SC1091
set -euo pipefail
IFS=$'\n\t'

set -x

export MAX_LEN_4=29
export MAX_LEN_6=64

mkdir -p generated

.scripts/roa.py -m "$MAX_LEN_4" -M "$MAX_LEN_6" -o generated/roa46_bird2.conf
.scripts/roa.py -m "$MAX_LEN_4" -M "$MAX_LEN_6" -4 -o generated/roa4_bird2.conf
.scripts/roa.py -m "$MAX_LEN_4" -M "$MAX_LEN_6" -6 -o generated/roa6_bird2.conf
.scripts/roa.py -m "$MAX_LEN_4" -M "$MAX_LEN_6" -j -o generated/roa46.json
.scripts/roa.py -m "$MAX_LEN_4" -M "$MAX_LEN_6" -e -o generated/neonetwork.json
.scripts/roa.py -m "$MAX_LEN_4" -M "$MAX_LEN_6" -r -o generated/rfc8416.json
.scripts/roa.py --summary --output generated/README.txt
