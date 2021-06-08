#!/usr/bin/env python3

# highly explosive

import argparse
from pathlib import Path

if __name__ == "__main__":
    parser = argparse.ArgumentParser("named-formatzone")
    parser.add_argument("file")
    args = parser.parse_args()
    zonefile = Path(args.file)
    zonelines = zonefile.read_text().split("\n")
    formatted = list()
    max_length = [0, 0, 0, 0, 0]
    in_soa = False

    def iter_lines(scan_only=True):
        soafound = None
        for rline in zonelines:
            line, *comments = rline.split(";")
            comments = ";".join(comments)
            line = line.strip()
            if "SOA" in line and soafound is None:
                soafound = True
            else:
                if "IN" in line and soafound is True:
                    soafound = False
            if soafound is False and line:
                cols = line.split()
                if len(cols) != 5:
                    cols.insert(1, "")
                print(cols)
                name, ttl, _in, rrtype, *record = cols
                record = " ".join(record)
                cols = (name, ttl, _in, rrtype, record)
                assert _in == "IN"
                if scan_only:
                    for i, entry in enumerate(cols):
                        max_length[i] = max(max_length[i], len(entry))
                else:
                    fmtlline = list()
                    for i, entry in enumerate(cols):
                        entry += " " * (max_length[i] - len(entry) + 3)
                        if entry:
                            fmtlline.append(entry)
                    fmtline = " ".join(fmtlline)
                    formatted.append(f"{fmtline} ;{comments}" if comments else fmtline)
                    formatted[-1] = formatted[-1].strip()
            else:
                if not scan_only:
                    formatted.append(rline)

    iter_lines()
    iter_lines(False)

    zonefile.write_text("\n".join(formatted))
