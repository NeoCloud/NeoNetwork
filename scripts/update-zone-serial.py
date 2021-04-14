#!/usr/bin/env python3
from pathlib import Path
import subprocess
from time import time
from re import match
from os import chdir

chdir("generated")

zone_files = [
    'neonetwork',
    'db.10.127',
    'db.fd10.127',
]

serial_base = 1586876035

for zone in zone_files:
    zone = Path("dns") / zone
    assert zone.exists()
    p = subprocess.run(['git', 'diff', '--exit-code', str(zone)])
    if p.returncode == 0:
        print(f"skip {zone.name}")
    else:
        print(f"update serial {zone.name}")
        lines = zone.read_text().split("\n")
        processed = list()
        serial = int(time()) - serial_base
        assert 0 < serial <= 2**32
        serial = str(serial)
        found = False
        for line in lines:
            if not found and (m := match(r"^(\s+)([0-9]+)(\s*;\s*Serial\s*)$", line)):
                prefix, _serial, suffix = m.groups()
                print(f"{_serial=} {serial=}")
                plen = max(len(prefix) - len(serial) + len(_serial), 0)
                processed.append(f"{' '*plen}{serial}{suffix}")
                found = True
            else:
                processed.append(line)
        zone.write_text("\n".join(processed))
