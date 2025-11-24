# gui/utils/tr0_reader.py
# FINAL — 100% IDENTICAL TO test_tr0_reader.py — PERFECT signal/data matching

import re
import numpy as np
from pathlib import Path
from typing import Dict, Tuple


def parse_tr0_file(filepath: Path) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """
    Parse HSPICE ASCII .tr0 file — EXACTLY like your working test_tr0_reader.py
    Column 0 = TIME
    Columns 1-14 = signals (in fixed order)
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # === PHASE 1: Extract pure 11-char numeric data lines ===
    data_lines = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith('$') or 'END' in s.upper() or 'Copyright' in s:
            continue
        if len(s) % 11 == 0:
            if re.match(r'[-+]?[0-9]*\.?[0-9]+[EeDd]?[-+]?[0-9]+', s[:11]):
                data_lines.append(s)

    if not data_lines:
        raise ValueError("No valid data found in the file!")

    # === PHASE 2: Parse exactly like test script ===
    data_str = ''.join(data_lines)
    data_str = data_str[:len(data_str) // 11 * 11]

    values = []
    for i in range(0, len(data_str), 11):
        field = data_str[i:i+11].replace('D', 'E')
        try:
            values.append(float(field))
        except ValueError:
            print(f"Warning: Could not parse field: '{field}' → skipping rest")
            break

    values = np.array(values)

    # Trim incomplete row
    if len(values) % 15 != 0:
        values = values[:len(values) // 15 * 15]

    data = values.reshape(-1, 15)

    # Remove end marker
    data = data[data[:, 0] < 1e20]

    print(f"Successfully loaded {len(data)} time points")

    # === PHASE 3: CORRECT SIGNAL MAPPING (matches test_tr0_reader.py EXACTLY) ===
    time = data[:, 0]  # Column 0 = TIME

    signal_names = [
        "in_spice", "in_ibis",
        "out1spice", "out1ibis",
        "out2spice", "out2ibis",
        "out3spice", "out3ibis",
        "end1spice", "end1ibis",
        "end2spice", "end2ibis",
        "end3spice", "end3ibis"
    ]

    result = {}
    for i, name in enumerate(signal_names):
        result[name] = (time.copy(), data[:, i + 1].copy())  # ← +1 offset!

    return result