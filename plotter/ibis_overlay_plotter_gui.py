#!/usr/bin/env python3
"""
ibis_overlay_plotter_gui.py

GUI version of IBIS overlay plotter with:
- Multiple IBIS file loading via file dialog
- Table selection with checkboxes
- Corner selection (typ, min, max)
- Interactive overlay plotting
- File management

Usage:
    python ibis_overlay_plotter_gui.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Set
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

@dataclass
class TableBlock:
    """Represents a single plottable table from an IBIS file"""
    index: int
    file_id: int
    file_name: str
    component: Optional[str]
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
    """Parse IBIS numbers with units"""
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


class IBISOverlayPlotterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("IBIS Overlay Plotter")
        self.root.geometry("1200x800")
        
        # Data storage
        self.all_blocks: List[TableBlock] = []
        self.file_map: Dict[int, str] = {}
        self.loaded_files: List[str] = []
        self.table_vars: Dict[int, tk.BooleanVar] = {}
        self.model_frames: Dict[str, ttk.Frame] = {}  # Track model frames for collapse/expand
        self.model_visible: Dict[str, tk.BooleanVar] = {}  # Track visibility state
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container with paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Controls
        left_frame = ttk.Frame(main_paned, width=400)
        main_paned.add(left_frame, weight=1)
        
        # Right panel - Plot area
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        
        # === LEFT PANEL ===
        
        # File management section
        file_frame = ttk.LabelFrame(left_frame, text="File Management", padding=10)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Add Files", command=self.add_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=2)
        
        # Loaded files listbox
        files_list_frame = ttk.Frame(file_frame)
        files_list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        files_scroll = ttk.Scrollbar(files_list_frame)
        files_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.files_listbox = tk.Listbox(files_list_frame, height=4, yscrollcommand=files_scroll.set)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        files_scroll.config(command=self.files_listbox.yview)
        
        # Corner selection section
        corner_frame = ttk.LabelFrame(left_frame, text="Corner Selection", padding=10)
        corner_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.corner_typ = tk.BooleanVar(value=True)
        self.corner_min = tk.BooleanVar(value=True)
        self.corner_max = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(corner_frame, text="Typical", variable=self.corner_typ).pack(anchor=tk.W)
        ttk.Checkbutton(corner_frame, text="Minimum", variable=self.corner_min).pack(anchor=tk.W)
        ttk.Checkbutton(corner_frame, text="Maximum", variable=self.corner_max).pack(anchor=tk.W)
        
        # Filter section
        filter_frame = ttk.LabelFrame(left_frame, text="Filter Tables", padding=10)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Search:").pack(anchor=tk.W)
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add('write', lambda *args: self.apply_filter())
        ttk.Entry(filter_frame, textvariable=self.filter_var).pack(fill=tk.X, pady=(0, 5))
        
        filter_btn_frame = ttk.Frame(filter_frame)
        filter_btn_frame.pack(fill=tk.X)
        ttk.Button(filter_btn_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_btn_frame, text="Deselect All", command=self.deselect_all).pack(side=tk.LEFT, padx=2)
        
        # Table selection section
        table_frame = ttk.LabelFrame(left_frame, text="Table Selection", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollable table list
        table_canvas = tk.Canvas(table_frame, height=200)
        table_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=table_canvas.yview)
        self.table_list_frame = ttk.Frame(table_canvas)
        
        self.table_list_frame.bind(
            "<Configure>",
            lambda e: table_canvas.configure(scrollregion=table_canvas.bbox("all"))
        )
        
        table_canvas.create_window((0, 0), window=self.table_list_frame, anchor="nw")
        table_canvas.configure(yscrollcommand=table_scrollbar.set)
        
        table_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        table_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Plot button
        plot_btn_frame = ttk.Frame(left_frame)
        plot_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(plot_btn_frame, text="Plot Selected Tables", 
                  command=self.plot_selected, style="Accent.TButton").pack(fill=tk.X, pady=2)
        ttk.Button(plot_btn_frame, text="Plot in New Window", 
                  command=self.plot_selected_new_window).pack(fill=tk.X, pady=2)
        
        # === RIGHT PANEL ===
        
        # Plot area with embedded matplotlib
        plot_container = ttk.Frame(right_frame)
        plot_container.pack(fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_container)
        self.canvas.draw()
        
        # Toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, plot_container)
        toolbar.update()
        
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready. Load IBIS files to begin.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def add_files(self):
        """Open file dialog to add IBIS files"""
        file_paths = filedialog.askopenfilenames(
            title="Select IBIS Files",
            filetypes=[("IBIS Files", "*.ibs"), ("All Files", "*.*")]
        )
        
        if not file_paths:
            return
        
        for path in file_paths:
            if path not in self.loaded_files:
                self.loaded_files.append(path)
        
        self.reload_all_files()
    
    def reload_all_files(self):
        """Reload all files and update UI"""
        self.all_blocks = []
        self.file_map = {}
        global_idx = 0
        
        for file_id, path in enumerate(self.loaded_files, start=1):
            if not Path(path).exists():
                continue
            
            try:
                blocks = parse_ibis_tables(path, file_id)
                
                for b in blocks:
                    global_idx += 1
                    b.index = global_idx
                    self.all_blocks.append(b)
                
                self.file_map[file_id] = Path(path).name
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load {path}:\n{str(e)}")
        
        self.update_files_list()
        self.update_table_list()
        self.status_var.set(f"Loaded {len(self.all_blocks)} tables from {len(self.loaded_files)} file(s)")
    
    def update_files_list(self):
        """Update the files listbox"""
        self.files_listbox.delete(0, tk.END)
        for path in self.loaded_files:
            self.files_listbox.insert(tk.END, Path(path).name)
    
    def update_table_list(self):
        """Update the table selection list with collapsible model groups"""
        # Clear existing widgets
        for widget in self.table_list_frame.winfo_children():
            widget.destroy()
        
        self.table_vars.clear()
        self.model_frames.clear()
        self.model_visible.clear()
        
        filter_text = self.filter_var.get().lower()
        
        # Group tables by file -> component -> model
        from collections import defaultdict
        hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        for b in self.all_blocks:
            # Apply filter
            if filter_text:
                search_text = f"{b.file_name} {b.component or ''} {b.model or ''} {b.section_raw}".lower()
                if filter_text not in search_text:
                    continue
            
            file_key = b.file_name
            comp_key = b.component or "Unknown"
            model_key = b.model or "Unknown"
            hierarchy[file_key][comp_key][model_key].append(b)
        
        # Create collapsible structure
        for file_name in sorted(hierarchy.keys()):
            for comp_name in sorted(hierarchy[file_name].keys()):
                for model_name in sorted(hierarchy[file_name][comp_name].keys()):
                    tables = hierarchy[file_name][comp_name][model_name]
                    
                    # Create model header (collapsible)
                    model_key = f"{file_name}::{comp_name}::{model_name}"
                    visible_var = tk.BooleanVar(value=True)
                    self.model_visible[model_key] = visible_var
                    
                    header_frame = ttk.Frame(self.table_list_frame)
                    header_frame.pack(fill=tk.X, pady=(5, 0))
                    
                    # Toggle button
                    toggle_btn = ttk.Button(
                        header_frame,
                        text="▼",
                        width=3,
                        command=lambda mk=model_key: self.toggle_model_visibility(mk)
                    )
                    toggle_btn.pack(side=tk.LEFT, padx=(0, 5))
                    
                    # Model label with count
                    model_label = ttk.Label(
                        header_frame,
                        text=f"{file_name} / {comp_name} / {model_name} ({len(tables)} tables)",
                        font=("TkDefaultFont", 9, "bold")
                    )
                    model_label.pack(side=tk.LEFT)
                    
                    # Store button reference for updating arrow
                    header_frame.toggle_btn = toggle_btn
                    
                    # Tables container
                    tables_frame = ttk.Frame(self.table_list_frame)
                    tables_frame.pack(fill=tk.X, padx=(20, 0))
                    self.model_frames[model_key] = (tables_frame, header_frame)
                    
                    # Add checkboxes for each table
                    for b in tables:
                        var = tk.BooleanVar(value=False)
                        self.table_vars[b.index] = var
                        
                        fixture_str = f" ({b.get_fixture_info()})" if b.get_fixture_info() else ""
                        label_text = f"[{b.index}] {b.section_raw}{fixture_str}"
                        
                        cb = ttk.Checkbutton(tables_frame, text=label_text, variable=var)
                        cb.pack(anchor=tk.W, pady=1)
    
    def toggle_model_visibility(self, model_key: str):
        """Toggle visibility of tables under a model"""
        if model_key not in self.model_frames:
            return
        
        tables_frame, header_frame = self.model_frames[model_key]
        is_visible = self.model_visible[model_key].get()
        
        if is_visible:
            # Hide tables
            tables_frame.pack_forget()
            header_frame.toggle_btn.config(text="▶")
            self.model_visible[model_key].set(False)
        else:
            # Show tables
            tables_frame.pack(fill=tk.X, padx=(20, 0), after=header_frame)
            header_frame.toggle_btn.config(text="▼")
            self.model_visible[model_key].set(True)
    
    def apply_filter(self):
        """Apply filter and update table list"""
        self.update_table_list()
    
    def select_all(self):
        """Select all visible tables"""
        for var in self.table_vars.values():
            var.set(True)
    
    def deselect_all(self):
        """Deselect all tables"""
        for var in self.table_vars.values():
            var.set(False)
    
    def clear_all(self):
        """Clear all loaded files"""
        if messagebox.askyesno("Confirm", "Clear all loaded files?"):
            self.loaded_files.clear()
            self.all_blocks.clear()
            self.file_map.clear()
            self.table_vars.clear()
            self.update_files_list()
            self.update_table_list()
            self.ax.clear()
            self.canvas.draw()
            self.status_var.set("All files cleared.")
    
    def get_selected_corners(self) -> Set[str]:
        """Get selected corners"""
        corners = set()
        if self.corner_typ.get():
            corners.add("typ")
        if self.corner_min.get():
            corners.add("min")
        if self.corner_max.get():
            corners.add("max")
        return corners if corners else {"typ"}
    
    def get_selected_tables(self) -> List[TableBlock]:
        """Get list of selected tables"""
        selected = []
        id_to_block = {b.index: b for b in self.all_blocks}
        
        for idx, var in self.table_vars.items():
            if var.get() and idx in id_to_block:
                selected.append(id_to_block[idx])
        
        return selected
    
    def plot_selected(self):
        """Plot selected tables in embedded canvas"""
        selected = self.get_selected_tables()
        
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one table to plot.")
            return
        
        corners = self.get_selected_corners()
        
        if not corners:
            messagebox.showwarning("No Corners", "Please select at least one corner (Typ/Min/Max).")
            return
        
        try:
            self.plot_overlaid_tables(selected, corners, self.ax, self.fig)
            self.status_var.set(f"Plotted {len(selected)} table(s) with corners: {', '.join(sorted(corners))}")
        except Exception as e:
            messagebox.showerror("Plot Error", f"Failed to plot:\n{str(e)}")
    
    def plot_selected_new_window(self):
        """Plot selected tables in a new matplotlib window"""
        selected = self.get_selected_tables()
        
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one table to plot.")
            return
        
        corners = self.get_selected_corners()
        
        if not corners:
            messagebox.showwarning("No Corners", "Please select at least one corner (Typ/Min/Max).")
            return
        
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            self.plot_overlaid_tables(selected, corners, ax, fig)
            plt.show()
            self.status_var.set(f"Opened new window with {len(selected)} table(s)")
        except Exception as e:
            messagebox.showerror("Plot Error", f"Failed to plot:\n{str(e)}")
    
    def plot_overlaid_tables(self, blocks: List[TableBlock], corners: Set[str], ax, fig):
        """Plot multiple tables overlaid with corner selection"""
        ax.clear()
        
        # Group by section type
        section_type = blocks[0].section_norm
        axis_type = axis_hint(section_type)
        
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
            
            for corner in sorted(corners):
                col_idx = corner_to_col.get(corner)
                
                if col_idx and col_idx < b.ncols:
                    y = b.data[:, col_idx]
                    
                    # Build label with component, model, and fixture info
                    comp_str = f"{b.component}/" if b.component else ""
                    model_str = f"{b.model}" if b.model else "?"
                    fixture_str = f" ({b.get_fixture_info()})" if b.get_fixture_info() else ""
                    label = f"{b.file_name}: {comp_str}{model_str} {b.section_raw}{fixture_str} - {corner_labels[corner]}"
                    
                    ax.plot(x, y,
                           linestyle=line_style,
                           color=color,
                           marker=marker,
                           markersize=4,
                           markevery=max(1, len(x) // 20),
                           label=label,
                           linewidth=1.5,
                           alpha=0.8)
        
        # Set axis labels
        if axis_type == "V-I":
            ax.set_xlabel("Voltage (V)", fontsize=11)
            ax.set_ylabel("Current (A)", fontsize=11)
        elif axis_type == "T-V":
            ax.set_xlabel("Time (s)", fontsize=11)
            ax.set_ylabel("Voltage (V)", fontsize=11)
        elif axis_type == "I-T":
            ax.set_xlabel("Time (s)", fontsize=11)
            ax.set_ylabel("Current (A)", fontsize=11)
        else:
            ax.set_xlabel("X", fontsize=11)
            ax.set_ylabel("Y", fontsize=11)
        
        ax.set_title(f"Overlay: {section_type.replace('_', ' ').title()}", 
                    fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc='best', framealpha=0.9)
        
        fig.tight_layout()
        
        # If using embedded canvas, redraw
        if hasattr(self, 'canvas'):
            self.canvas.draw()


def main():
    root = tk.Tk()
    app = IBISOverlayPlotterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
