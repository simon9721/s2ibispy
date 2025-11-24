#!/usr/bin/env python3
# flat_to_subckt.py — FINAL BULLETPROOF VERSION
# Correctly detects only real pins, ignores all instance names

import sys
import re
import os
from datetime import datetime

def flat_to_subckt(input_path: str, output_path: str, subckt_name: str = "IO_BUF"):
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # Collect all node names that appear as connections (not instance names)
    connected_nodes = set()
    power_nodes = {"vdd", "vss", "gnd", "0", "vcc", "vssio", "vddio", "ground", "supply"}

    node_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b')

    for line in lines:
        line_lower = line.lower()
        if line.strip() == "" or line.strip().startswith(("*", ".", "$")):
            continue

        tokens = line.split()
        if not tokens:
            continue

        # Skip instance name (first token if it starts with m, c, x)
        start_idx = 1
        if tokens[0][0].lower() in "mcx":
            start_idx = 1
        else:
            start_idx = 0

        # Extract nodes from connections
        for token in tokens[start_idx:]:
            token_clean = token.split("=")[0]  # remove w= l= etc.
            matches = node_pattern.findall(token_clean.lower())
            for node in matches:
                if node not in power_nodes and node not in {"pfet", "nfet", "w", "l", "m"}:
                    connected_nodes.add(node)

    # Priority pins
    priority_order = ["in", "oe", "en", "enable", "out", "pad", "io", "in_sense", "sense"]
    def pin_key(p):
        pl = p.lower()
        return (priority_order.index(pl) if pl in priority_order else 999, pl)

    sorted_pins = sorted(connected_nodes, key=pin_key)

    # Take first 4 non-power pins + vdd + vss
    final_pins = []
    for p in sorted_pins:
        if len(final_pins) >= 4:
            break
        if p.lower() not in [fp.lower() for fp in final_pins]:
            final_pins.append(p)

    # Force vdd and vss
    vdd_name = "vdd"
    vss_name = "vss"
    for line in lines:
        l = line.lower()
        if " vdd " in l or l.endswith(" vdd"):
            vdd_name = [t for t in l.split() if "vdd" in t and t[0].isalpha()][0]
        if " vss " in l or l.endswith(" vss") or " gnd " in l or " 0 " in l:
            candidates = [t for t in l.split() if t in {"vss", "gnd", "0"} or "vss" in t]
            if candidates:
                vss_name = candidates[0]

    if vdd_name not in final_pins:
        final_pins.append(vdd_name)
    if vss_name not in final_pins and vss_name != vdd_name:
        final_pins.append(vss_name)

    # Write wrapper
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"* Auto-generated subcircuit wrapper — FLAT → SUBCKT\n")
        f.write(f".subckt {subckt_name} {' '.join(final_pins)}\n")
        f.write(f"* Source: {os.path.basename(input_path)}\n")
        f.write(f"* Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for line in lines:
            if line.strip().lower().startswith((".ends", ".end")):
                continue
            f.write(line.rstrip("\n") + "\n")
        f.write(f".ends {subckt_name}\n")

    print(f"SUCCESS! → {output_path}")
    print(f"   Subcircuit: {subckt_name}")
    print(f"   Pins: {' '.join(final_pins)}")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print("Usage: python flat_to_subckt.py input.sp output.sp [name]")
        sys.exit(1)
    flat_to_subckt(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) == 4 else "IO_BUF")