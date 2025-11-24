# gui/utils/tr0_reader.py
# Final, battle-tested, ASCII .tr0 parser (POST_VERSION=9601)
# No dependencies except numpy and standard library

import numpy as np
import re
from pathlib import Path
from typing import Dict, Tuple

def parse_tr0_file(filepath: Path) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """
    Parse HSPICE ASCII .tr0 file (POST_VERSION=9601 format)
    Returns: {signal_name: (time_array, voltage_array)}
    """
    text = filepath.read_text()

    # === Extract signal names from all v(...) lines ===
    name_lines = []
    for line in text.splitlines():
        if line.strip().startswith("v("):
            # Clean and collect
            cleaned = line.replace("v(", "").replace(")", "").strip()
            name_lines.append(cleaned)
    
    if not name_lines:
        raise ValueError("No v(...) header found — not a valid ASCII .tr0")
    
    names_text = ' '.join(name_lines)
    names = [n.strip() for n in names_text.split() if n.strip() and not n.startswith('$')]
    
    if not names:
        raise ValueError("No valid signal names found")
    
    print(f"[tr0_reader] Found {len(names)} signals: {names}")

    # === Extract all 11-char numeric fields ===
    # Find all pure data lines (multiple of 11 chars, starts with valid number)
    data_str = ""
    for line in text.splitlines():
        s = line.strip()
        if (len(s) % 11 == 0 and 
            not s.startswith('$') and 
            'END' not in s.upper() and 
            'Copyright' not in s and
            re.match(r'[-+]?[0-9]*\.?[0-9]+[EeDd]?[-+]?[0-9]+', s[:11])):
            data_str += s

    # Trim to exact multiple of 11
    data_str = data_str[:len(data_str) // 11 * 11]
    
    if not data_str:
        raise ValueError("No valid data rows found")

    # Parse 11-char fields
    values = []
    for i in range(0, len(data_str), 11):
        field = data_str[i:i+11].replace('D', 'E')  # HSPICE uses D sometimes
        try:
            values.append(float(field))
        except ValueError:
            print(f"[tr0_reader] Warning: skipping invalid field: '{field}'")
            continue

    values = np.array(values)
    
    # Remove 1e31 end marker (HSPICE adds this sometimes)
    values = values[values < 1e20]
    
    if len(values) % len(names) != 0:
        # Trim incomplete row
        values = values[:len(values) // len(names) * len(names)]
    
    npoints = len(values) // len(names)
    data = values.reshape(npoints, len(names))
    
    time = data[:, 0]  # First column is always TIME
    
    result = {}
    for i, name in enumerate(names):
        result[name] = (time, data[:, i])
    
    print(f"[tr0_reader] Successfully parsed {npoints} time points")
    return result

