#!/usr/bin/env python3
"""
ibis_overlay_plotter.py

Interactive IBIS plotter that supports:
- Multiple IBIS files
- Overlay plots from different files
- Corner selection (typ, min, max, or any combination)
- Table selection across files

Usage:
    python ibis_overlay_plotter.py
    
Or with initial files:
    python ibis_overlay_plotter.py --files file1.ibs file2.ibs file3.ibs
"""

import argparse
import re
import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Set
from pathlib import Path
import matplotlib.pyplot as plt

@dataclass
class TableBlock:
    """Represents a single plottable table from an IBIS file"""
    index: int
    file_id: int  # which file this came from
    file_name: str  # short filename for display
    component: Optional[str]  # component name
    section_raw: str
    section_norm: str
    model: Optional[str]
    params: Dict[str, str] = field(default_factory=dict)
    ncols: int = 0
    data: Optional[np.ndarray] = None
    source_range: Tuple[int, int] = (0, 0)
    
    def get_fixture_info(self) -> str:
        """Get concise fixture information for waveform tables"""
        if "waveform" not in self.section_norm:
            return ""
        
        # Try different case variations
        r_fix = self.params.get("R_fixture", self.params.get("r_fixture", 
                self.params.get("R_FIXTURE", "")))
        v_fix = self.params.get("V_fixture", self.params.get("v_fixture", 
                self.params.get("V_FIXTURE", "")))
        
        if r_fix and v_fix:
            # Format numbers concisely
            try:
                r_val = float(r_fix)
                v_val = float(v_fix)
                return f"R={r_val:.0f}Ω V={v_val:.2g}V"
            except:
                return f"R={r_fix} V={v_fix}"
        return ""

def normalize_section(sec: str) -> str:
    """Normalize section names to lowercase with underscores"""
    return sec.strip().lower().replace(" ", "_").replace("-", "_")

# Plottable sections
PLOTTABLE_SECTIONS = {
    "pulldown", "pullup",
    "gnd_clamp", "ground_clamp", "power_clamp",
    "rising_waveform", "falling_waveform", "waveform",
    "composite_current",
    "isso_pu", "isso_pd",
}

# Engineering multipliers
ENG = {
    'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3,
    'k': 1e3, 'K': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12
}

# Pattern for numbers with units
_NUM_WITH_UNITS = re.compile(
    r"""
    ^\s*
    (?:
        (?P<num>
            [+-]?(?:\d+(?:\.\d*)?|\.\d+)
            (?:[eE][+-]?\d+)?
        )
        (?P<si>[fpnumkKMGTP])?
        (?P<unit>[vVaAsS])?
      |
        (?P<na>NA)
    )
    \s*$
    """,
    re.VERBOSE
)

MEG_SUFFIX_RE = re.compile(r"(?i)meg$")

def parse_number(tok: str) -> float:
    """Parse IBIS numbers with units (V, A, S), SI prefixes, NA, etc."""
    t = tok.strip().replace(",", "")
    
    if t.upper() == "NA":
        return math.nan
    
    if MEG_SUFFIX_RE.search(t) and t[-1].lower() not in ("v", "a", "s"):
        base = MEG_SUFFIX_RE.sub("", t)
        return float(base) * 1e6
    
    try:
        return float(t)
    except ValueError:
        pass
    
    m = _NUM_WITH_UNITS.match(t)
    if not m:
        return float(t)
    
    if m.group("na"):
        return math.nan
    
    val = float(m.group("num"))
    si = m.group("si")
    if si:
        val *= ENG[si]
    
    return val

def is_num_like(token: str) -> bool:
    """Check if token can be parsed as a number"""
    try:
        parse_number(token)
        return True
    except Exception:
        return False

def is_numeric_row(line: str) -> bool:
    """Check if line contains only numeric data"""
    toks = line.strip().split()
    if len(toks) < 2 or len(toks) > 8:
        return False
    return all(is_num_like(t) for t in toks)

def parse_header_params(line: str) -> Dict[str, str]:
    """Parse key=value parameters from header lines"""
    params = {}
    # Handle "key=value", "key= value", and "key = value"
    tokens = line.strip().split()
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if '=' in tok:
            k, v = tok.split('=', 1)
            k = k.strip()
            v = v.strip()
            # If value is empty and next token doesn't have =, it's the value
            if not v and i + 1 < len(tokens) and '=' not in tokens[i + 1]:
                i += 1
                v = tokens[i]
            params[k] = v
        elif i + 2 < len(tokens) and tokens[i + 1] == '=':
            # Handle "key = value" with spaces around =
            k = tok
            v = tokens[i + 2]
            params[k] = v
            i += 2  # Skip the = and value
        else:
            params[tok] = "true"
        i += 1
    return params

def parse_ibis_tables(path: str, file_id: int) -> List[TableBlock]:
    """Parse all plottable tables from an IBIS file"""
    file_name = Path(path).name
    
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    blocks: List[TableBlock] = []
    section_header_re = re.compile(r'^\s*\[(.+?)\]\s*(.*)$')
    current_component: Optional[str] = None
    current_model: Optional[str] = None
    idx = 0
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("|"):
            i += 1
            continue
        
        m = section_header_re.match(line)
        if m:
            sec_name = m.group(1).strip()
            tail = (m.group(2) or "").strip()
            sec_norm = normalize_section(sec_name)
            
            if sec_norm == "component":
                current_component = tail if tail else None
                i += 1
                continue
            
            if sec_norm == "model":
                current_model = tail if tail else None
                i += 1
                continue
            
            if sec_norm in PLOTTABLE_SECTIONS:
                params = {}
                if tail:
                    params.update(parse_header_params(tail))
                i += 1
                
                # Read parameter lines
                while i < len(lines):
                    peek = lines[i].strip()
                    if not peek or peek.startswith("|"):
                        i += 1
                        continue
                    if section_header_re.match(peek) or is_numeric_row(peek):
                        break
                    params.update(parse_header_params(peek))
                    i += 1
                
                # Collect numeric data
                while i < len(lines):
                    st = lines[i].strip()
                    if not st or st.startswith("|"):
                        i += 1
                        continue
                    if section_header_re.match(st):
                        break
                    if not is_numeric_row(st):
                        i += 1
                        continue
                    
                    start = i
                    rows = []
                    ncols_expected = None
                    
                    while i < len(lines) and is_numeric_row(lines[i]):
                        parts = lines[i].strip().split()
                        if ncols_expected is None:
                            ncols_expected = len(parts)
                        if len(parts) == ncols_expected:
                            rows.append(parts)
                        i += 1
                    
                    if rows:
                        arr = np.array([[parse_number(x) for x in row] for row in rows], dtype=float)
                        idx += 1
                        blocks.append(TableBlock(
                            index=idx,
                            file_id=file_id,
                            file_name=file_name,
                            component=current_component,
                            section_raw=sec_name,
                            section_norm=sec_norm,
                            model=current_model,
                            params=params.copy(),
                            ncols=arr.shape[1],
                            data=arr,
                            source_range=(start+1, i)
                        ))
                continue
        i += 1
    
    return blocks

def axis_hint(section_norm: str) -> str:
    """Determine axis type from section name"""
    if section_norm in {"pulldown", "pullup", "gnd_clamp", "ground_clamp", "power_clamp", "isso_pu", "isso_pd"}:
        return "V-I"
    if "waveform" in section_norm:
        return "T-V"
    if section_norm == "composite_current":
        return "I-T"
    return "data"

def parse_indices(text: str, max_idx: int) -> List[int]:
    """Parse comma-separated indices or ranges (e.g., '1,3-5,7')"""
    nums: List[int] = []
    parts = re.split(r'[,\s]+', text.strip())
    
    for p in parts:
        if not p:
            continue
        if '-' in p:
            lo, hi = p.split('-', 1)
            try:
                lo_i = int(lo)
                hi_i = int(hi)
                if lo_i > hi_i:
                    lo_i, hi_i = hi_i, lo_i
                for k in range(lo_i, hi_i + 1):
                    if 1 <= k <= max_idx:
                        nums.append(k)
            except ValueError:
                continue
        else:
            try:
                k = int(p)
                if 1 <= k <= max_idx:
                    nums.append(k)
            except ValueError:
                continue
    
    # De-duplicate preserving order
    seen = set()
    out = []
    for k in nums:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out

def parse_corner_spec(text: str) -> Set[str]:
    """Parse corner specification (typ, min, max, or combinations)"""
    text = text.strip().lower()
    if not text or text == "all":
        return {"typ", "min", "max"}
    
    corners = set()
    for part in text.replace(",", " ").split():
        part = part.strip()
        if part in {"typ", "t", "typical"}:
            corners.add("typ")
        elif part in {"min", "n", "minimum"}:
            corners.add("min")
        elif part in {"max", "x", "maximum"}:
            corners.add("max")
    
    return corners if corners else {"typ", "min", "max"}

def plot_overlaid_tables(blocks: List[TableBlock], corners: Set[str]):
    """Plot multiple tables overlaid on the same figure with corner selection"""
    if not blocks:
        print("No tables to plot.")
        return
    
    # Group by section type for consistent axis labels
    section_type = blocks[0].section_norm
    axis_type = axis_hint(section_type)
    
    plt.figure(figsize=(10, 6))
    
    # Color cycle for different files
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    line_styles = ['-', '--', '-.', ':']
    markers = ['o', 's', '^', 'v', 'D', 'p', '*', 'h']
    
    corner_to_col = {"typ": 1, "min": 2, "max": 3}
    corner_labels = {"typ": "Typ", "min": "Min", "max": "Max"}
    
    for b_idx, b in enumerate(blocks):
        color = colors[b.file_id % len(colors)]
        line_style = line_styles[b_idx % len(line_styles)]
        marker = markers[b_idx % len(markers)]
        
        x = b.data[:, 0]
        
        # Determine which columns are available
        available_cols = b.ncols - 1  # excluding x column
        
        for corner in sorted(corners):
            col_idx = corner_to_col.get(corner)
            
            if col_idx and col_idx < b.ncols:
                y = b.data[:, col_idx]
                
                # Build label with component, model, and fixture info
                comp_str = f"{b.component}/" if b.component else ""
                model_str = f"{b.model}" if b.model else "?"
                fixture_str = f" ({b.get_fixture_info()})" if b.get_fixture_info() else ""
                label = f"{b.file_name}: {comp_str}{model_str} {b.section_raw}{fixture_str} - {corner_labels[corner]}"
                
                plt.plot(x, y, 
                        linestyle=line_style,
                        color=color,
                        marker=marker,
                        markersize=4,
                        markevery=max(1, len(x) // 20),
                        label=label,
                        linewidth=1.5,
                        alpha=0.8)
    
    # Set axis labels based on table type
    if axis_type == "V-I":
        plt.xlabel("Voltage (V)", fontsize=11)
        plt.ylabel("Current (A)", fontsize=11)
    elif axis_type == "T-V":
        plt.xlabel("Time (s)", fontsize=11)
        plt.ylabel("Voltage (V)", fontsize=11)
    elif axis_type == "I-T":
        plt.xlabel("Time (s)", fontsize=11)
        plt.ylabel("Current (A)", fontsize=11)
    else:
        plt.xlabel("X", fontsize=11)
        plt.ylabel("Y", fontsize=11)
    
    plt.title(f"Overlay: {section_type.replace('_', ' ').title()}", fontsize=13, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=8, loc='best', framealpha=0.9)
    plt.tight_layout()

def load_files(file_paths: List[str]) -> Tuple[List[TableBlock], Dict[int, str]]:
    """Load all IBIS files and return all tables with file mapping"""
    all_blocks = []
    file_map = {}
    global_idx = 0
    
    for file_id, path in enumerate(file_paths, start=1):
        if not Path(path).exists():
            print(f"Warning: File not found: {path}")
            continue
        
        print(f"Loading {path}...")
        blocks = parse_ibis_tables(path, file_id)
        
        # Renumber blocks globally
        for b in blocks:
            global_idx += 1
            b.index = global_idx
            all_blocks.append(b)
        
        file_map[file_id] = Path(path).name
        print(f"  → Found {len(blocks)} tables")
    
    return all_blocks, file_map

def print_table_list(blocks: List[TableBlock], file_map: Dict[int, str]):
    """Print formatted list of all available tables"""
    print("\n" + "="*120)
    print(f"{'ID':<5} {'File':<20} {'Component':<15} {'Model':<15} {'Section':<18} {'Fixture':<20} {'Type':<6} {'Cols':<4}")
    print("="*120)
    
    for b in blocks:
        file_short = file_map.get(b.file_id, "?")[:19]
        comp_short = (b.component or "-")[:14]
        model_short = (b.model or "-")[:14]
        section_short = b.section_raw[:17]
        fixture_info = b.get_fixture_info()[:19]
        axis = axis_hint(b.section_norm)
        
        print(f"{b.index:<5} {file_short:<20} {comp_short:<15} {model_short:<15} {section_short:<18} {fixture_info:<20} {axis:<6} {b.ncols:<4}")
    
    print("="*120)

def main():
    parser = argparse.ArgumentParser(
        description="Interactive IBIS overlay plotter with multiple files and corner selection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode - load files one by one
  python ibis_overlay_plotter.py
  
  # Load multiple files at start
  python ibis_overlay_plotter.py --files file1.ibs file2.ibs file3.ibs
  
  # Then interactively select tables and corners to overlay
        """
    )
    parser.add_argument("--files", "-f", nargs="+", help="Initial IBIS files to load")
    args = parser.parse_args()
    
    all_blocks = []
    file_map = {}
    loaded_files = []
    
    # Load initial files if provided
    if args.files:
        all_blocks, file_map = load_files(args.files)
        loaded_files = list(args.files)
    
    print("\n" + "="*100)
    print(" "*30 + "IBIS OVERLAY PLOTTER")
    print("="*100)
    
    # Main interactive loop
    while True:
        print("\n" + "-"*100)
        print("Commands:")
        print("  add <file>           - Add an IBIS file")
        print("  list                 - List all loaded tables")
        print("  plot <ids> [corners] - Plot tables (e.g., 'plot 1,3-5 typ,min')")
        print("  files                - Show loaded files")
        print("  help                 - Show this help")
        print("  quit                 - Exit")
        print("-"*100)
        
        cmd = input("\n>> ").strip()
        
        if not cmd:
            continue
        
        parts = cmd.split(maxsplit=1)
        action = parts[0].lower()
        
        if action in {"q", "quit", "exit"}:
            print("Goodbye!")
            break
        
        elif action == "help":
            print("\nDetailed Help:")
            print("  add <file>          - Load an IBIS file (can use relative or absolute paths)")
            print("  list                - Display all tables from all loaded files")
            print("  plot <ids> [corners]- Overlay selected tables")
            print("                        <ids>: comma-separated or ranges (e.g., 1,3-5,7)")
            print("                        [corners]: typ, min, max, or combinations (e.g., typ,max)")
            print("                        Default corners: all (typ, min, max)")
            print("  files               - Show which files are currently loaded")
            print("  quit                - Exit the program")
            print("\nExample sessions:")
            print("  >> add file1.ibs")
            print("  >> add file2.ibs")
            print("  >> list")
            print("  >> plot 1,5 typ        # Plot tables 1 and 5, typ corner only")
            print("  >> plot 2-4 min,max    # Plot tables 2,3,4, min and max corners")
        
        elif action == "add":
            if len(parts) < 2:
                print("Usage: add <file>")
                continue
            
            file_path = parts[1].strip()
            if not Path(file_path).exists():
                print(f"Error: File not found: {file_path}")
                continue
            
            loaded_files.append(file_path)
            all_blocks, file_map = load_files(loaded_files)
        
        elif action == "list":
            if not all_blocks:
                print("No files loaded. Use 'add <file>' to load an IBIS file.")
                continue
            
            print_table_list(all_blocks, file_map)
        
        elif action == "files":
            if not loaded_files:
                print("No files loaded.")
            else:
                print("\nLoaded files:")
                for i, f in enumerate(loaded_files, start=1):
                    print(f"  [{i}] {f}")
        
        elif action == "plot":
            if not all_blocks:
                print("No files loaded. Use 'add <file>' first.")
                continue
            
            if len(parts) < 2:
                print("Usage: plot <ids> [corners]")
                print("  <ids>: e.g., 1,3-5,7")
                print("  [corners]: typ, min, max (default: all)")
                continue
            
            # Parse arguments
            args_str = parts[1].strip()
            args_parts = args_str.split(maxsplit=1)
            
            ids_str = args_parts[0]
            corners_str = args_parts[1] if len(args_parts) > 1 else "all"
            
            # Parse indices and corners
            indices = parse_indices(ids_str, max_idx=len(all_blocks))
            if not indices:
                print(f"No valid indices parsed from '{ids_str}'")
                continue
            
            corners = parse_corner_spec(corners_str)
            
            # Get selected blocks
            id_to_block = {b.index: b for b in all_blocks}
            selected = [id_to_block[i] for i in indices if i in id_to_block]
            
            if not selected:
                print("No valid tables selected.")
                continue
            
            # Check if all selected tables are compatible for overlay
            sections = {b.section_norm for b in selected}
            if len(sections) > 1:
                print(f"Warning: Mixing different table types: {sections}")
                print("Plotting anyway, but axes may not be consistent.")
            
            print(f"\nPlotting {len(selected)} table(s) with corners: {', '.join(sorted(corners))}")
            plot_overlaid_tables(selected, corners)
            plt.show()
        
        else:
            print(f"Unknown command: '{action}'. Type 'help' for available commands.")

if __name__ == "__main__":
    main()
