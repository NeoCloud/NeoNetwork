#!/usr/bin/env python3
import subprocess
from os import chdir
from pathlib import Path
from re import match
from time import time

zone_files = [
    "neonetwork",
    "db.10.127",
    "db.fd10.127",
]

serial_base = 1586876035
new_serial = int(time()) - serial_base


def update_serial_to(zone: Path, serial: int = 0) -> int:
    lines = zone.read_text().split("\n")
    processed = list()
    assert 0 <= serial <= 2 ** 32
    found = False
    old_serial = None
    for line in lines:
        if not found and (m := match(r"^(\s+)([0-9]+)(\s*;\s*Serial\s*)$", line)):
            prefix, old_serial, suffix = m.groups()
            old_serial = int(old_serial)
            print(f"{old_serial=} {serial=}")
            plen = max(len(prefix) - len(str(serial)) + len(str(old_serial)), 0)
            processed.append(f"{' '*plen}{serial}{suffix}")
            found = True
        else:
            processed.append(line)
    if serial:
        zone.write_text("\n".join(processed))
    return old_serial


for zone in zone_files:
    gen_zone = Path("generated") / "dns" / zone
    repo_zone = Path("dns") / zone
    assert gen_zone.exists()
    assert repo_zone.exists()
    old_serial = update_serial_to(gen_zone)
    update_serial_to(repo_zone, old_serial)
    gen_zone.write_text(repo_zone.read_text())
    p = subprocess.run(
        ["git", "diff", "--exit-code", gen_zone.name], cwd=gen_zone.parent
    )
    if p.returncode == 0:
        print(f"skip {repo_zone.name}")
    else:
        print(f"update serial {repo_zone.name}")
        update_serial_to(repo_zone, new_serial)
