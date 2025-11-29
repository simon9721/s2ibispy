# gui/tabs/main_entry_tab.py
"""
Main Entry Tab - Merged Input/Config + YAML Editor + Simulation Controls
Provides unified interface for loading files, editing config, and running simulations
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime
import threading
import sys

# Import business logic
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from gui.utils.yaml_editor_model import YamlModel, ValidationError
from gui.utils.yaml_editor_config import UI_SCHEMA, COLORS, FONTS
from gui.utils.s2i_to_yaml import convert_s2i_to_yaml
from legacy.parser import S2IParser
from s2ibispy.cli import main as run_conversion

try:
    from gui.utils.parse_netlist import parse_netlist
    NETLIST_PARSER_AVAILABLE = True
except ImportError:
    NETLIST_PARSER_AVAILABLE = False
    parse_netlist = None


class Tooltip:
    """Tooltip widget that appears on hover."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tw or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tw = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background=COLORS["tooltip_bg"],
                         relief="solid", borderwidth=1, font=FONTS["tooltip"],
                         padx=5, pady=3)
        label.pack()

    def hide(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None


class MainEntryTab:
    """Unified entry tab combining file loading, configuration, and simulation controls."""
    
    def __init__(self, notebook, gui):
        self.gui = gui
        self.frame = ttk.Frame(notebook)
        
        # File and config state
        self.input_file = ""
        self.outdir = ""
        self.ibischk_path = ""
        self.input_type = tk.StringVar(value="yaml")
        
        # YAML model
        self.yaml_model = YamlModel()
        self.current_yaml_file = None
        self.yaml_modified = False
        
        # Widget registries
        self.entries = {}
        self.global_entries = {}
        self.models_tree = None
        self.pins_tree = None
        
        # Simulation control
        self.simulation_thread = None
        self.simulation_running = False
        
        # Build UI
        self.build_ui()
        
        # Set defaults
        self._set_defaults()

    def build_ui(self):
        """Build the complete UI layout."""
        # Main container with scrollbar
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        canvas = tk.Canvas(self.frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        self.content = ttk.Frame(canvas, padding=15)
        
        self.content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Build form sections
        row = 0
        row = self._build_file_input_section(self.content, row)
        row += 1
        
        ttk.Separator(self.content, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=15)
        row += 1
        
        row = self._build_config_section(self.content, row)
        row += 1
        
        ttk.Separator(self.content, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=15)
        row += 1
        
        row = self._build_simulation_options(self.content, row)
        row += 1
        
        ttk.Separator(self.content, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=15)
        row += 1
        
        row = self._build_models_section(self.content, row)
        row += 1
        
        row = self._build_pins_section(self.content, row)
        row += 1
        
        ttk.Separator(self.content, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=20)
        row += 1
        
        row = self._build_simulation_controls(self.content, row)

    def _build_file_input_section(self, parent, start_row):
        """Build file input section."""
        row = start_row
        
        ttk.Label(parent, text="📁 Input File", font=("", 14, "bold")).grid(
            row=row, column=0, columnspan=4, pady=(0, 15), sticky="w"
        )
        row += 1
        
        # Input type selector
        input_type_frame = ttk.Frame(parent)
        input_type_frame.grid(row=row, column=0, columnspan=4, sticky="w", pady=8)
        ttk.Label(input_type_frame, text="Input Type:", font=("", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(input_type_frame, text="YAML Config", variable=self.input_type, 
                       value="yaml", command=self.on_input_type_changed).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(input_type_frame, text="Legacy .s2i", variable=self.input_type, 
                       value="s2i", command=self.on_input_type_changed).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Input file selector
        self.input_label = ttk.Label(parent, text="Input File:", font=("", 10, "bold"))
        self.input_label.grid(row=row, column=0, sticky="w", padx=5, pady=8)
        self.input_entry = ttk.Entry(parent, width=70)
        self.input_entry.grid(row=row, column=1, columnspan=2, padx=8, pady=8, sticky="ew")
        ttk.Button(parent, text="Browse", command=self.load_input_file).grid(row=row, column=3, padx=5, pady=8)
        row += 1
        
        # Output directory
        ttk.Label(parent, text="Output Directory:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.outdir_entry = ttk.Entry(parent, width=70)
        self.outdir_entry.grid(row=row, column=1, columnspan=2, padx=8, pady=5, sticky="ew")
        ttk.Button(parent, text="Browse", command=self.browse_outdir).grid(row=row, column=3, padx=5, pady=5)
        row += 1
        
        # ibischk path
        ttk.Label(parent, text="ibischk7 Path (optional):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.ibischk_entry = ttk.Entry(parent, width=70)
        self.ibischk_entry.grid(row=row, column=1, columnspan=2, padx=8, pady=5, sticky="ew")
        ttk.Button(parent, text="Browse", command=self.browse_ibischk).grid(row=row, column=3, padx=5, pady=5)
        row += 1
        
        # Quick action buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=10)
        ttk.Button(btn_frame, text="New YAML", command=self.new_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save YAML", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save As", command=self.save_as).pack(side=tk.LEFT, padx=5)
        if NETLIST_PARSER_AVAILABLE:
            ttk.Button(btn_frame, text="Parse SPICE", command=self.open_spice).pack(side=tk.LEFT, padx=5)
        row += 1
        
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_columnconfigure(2, weight=1)
        
        return row

    def _build_config_section(self, parent, start_row):
        """Build configuration fields section."""
        row = start_row
        
        ttk.Label(parent, text="⚙️ General Configuration", font=("", 14, "bold")).grid(
            row=row, column=0, columnspan=4, pady=(0, 15), sticky="w"
        )
        row += 1
        
        schema = UI_SCHEMA.get("general_settings", {})
        fields = schema.get("fields", [])
        
        col = 0
        for field_info in fields:
            # Skip iterate and cleanup - they're in simulation options
            key = field_info[1]
            if key in ["iterate", "cleanup"]:
                continue
            
            if col >= 2:
                row += 1
                col = 0
            
            label_text = field_info[0]
            tip = field_info[2] if len(field_info) > 2 else ""
            required = field_info[3] if len(field_info) > 3 else False
            widget_type = field_info[4] if len(field_info) > 4 else "entry"
            widget_options = field_info[5] if len(field_info) > 5 else None
            
            label_display = label_text + (" *" if required else "") + ":"
            lbl = ttk.Label(parent, text=label_display)
            lbl.grid(row=row, column=col*2, sticky="w", padx=(5, 10))
            if tip:
                Tooltip(lbl, tip)
            
            # Create appropriate widget based on type
            if widget_type == "dropdown":
                var = tk.StringVar()
                widget = ttk.Combobox(parent, textvariable=var, width=28, state="readonly")
                widget['values'] = widget_options
                widget.grid(row=row, column=col*2+1, sticky="ew", padx=(0, 15))
                self.entries[key] = widget
                self.entries[f"{key}_var"] = var
            elif widget_type == "checkbox":
                var = tk.StringVar(value=widget_options[1] if widget_options else "0")
                widget = ttk.Checkbutton(parent, variable=var)
                widget.grid(row=row, column=col*2+1, sticky="w", padx=(0, 15))
                self.entries[key] = widget
                self.entries[f"{key}_var"] = var
            else:
                widget = ttk.Entry(parent, width=30)
                widget.grid(row=row, column=col*2+1, sticky="ew", padx=(0, 15))
                self.entries[key] = widget
            
            col += 1
        
        if col > 0:
            row += 1
        
        # Component section
        row += 1
        ttk.Label(parent, text="Component Info", font=("", 11, "bold")).grid(
            row=row, column=0, columnspan=4, pady=(10, 10), sticky="w"
        )
        row += 1
        
        comp_schema = UI_SCHEMA.get("component", {})
        comp_fields = comp_schema.get("fields", [])
        
        for field_info in comp_fields:
            label_text = field_info[0]
            key = field_info[1]
            tip = field_info[2] if len(field_info) > 2 else ""
            
            ttk.Label(parent, text=label_text + ":").grid(row=row, column=0, sticky="w", padx=5, pady=5)
            if tip:
                Tooltip(ttk.Label(parent, text="ⓘ"), tip)
            
            entry = ttk.Entry(parent, width=50)
            entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=8, pady=5)
            self.entries[key] = entry
            
            if key == "spiceFile":
                ttk.Button(parent, text="Browse", command=lambda: self._browse_spice_file()).grid(
                    row=row, column=3, padx=5, pady=5
                )
            
            row += 1
        
        # Global defaults section
        row += 1
        ttk.Label(parent, text="Global Defaults", font=("", 11, "bold")).grid(
            row=row, column=0, columnspan=4, pady=(10, 10), sticky="w"
        )
        row += 1
        
        global_schema = UI_SCHEMA.get("global_defaults", {})
        groups = global_schema.get("groups", [])
        
        for group_name, group_fields in groups:
            # Group label
            ttk.Label(parent, text=group_name, font=("", 10, "bold")).grid(
                row=row, column=0, columnspan=4, pady=(8, 5), sticky="w", padx=5
            )
            row += 1
            
            # Fields in this group
            col = 0
            for field_info in group_fields:
                if col >= 3:
                    row += 1
                    col = 0
                
                label_text = field_info[0]
                key = field_info[1]
                tip = field_info[2] if len(field_info) > 2 else ""
                
                # Use col*2 for label, col*2+1 for entry to prevent overlap
                ttk.Label(parent, text=label_text + ":").grid(row=row, column=col*2, sticky="e", padx=(10, 5), pady=3)
                if tip:
                    Tooltip(ttk.Label(parent, text="ⓘ"), tip)
                
                entry = ttk.Entry(parent, width=15)
                entry.grid(row=row, column=col*2+1, sticky="w", padx=(0, 15), pady=3)
                self.global_entries[key] = entry
                
                col += 1
            
            if col > 0:
                row += 1
        
        return row

    def _build_simulation_options(self, parent, start_row):
        """Build simulation options section."""
        row = start_row
        
        ttk.Label(parent, text="🔧 Simulation Options", font=("", 14, "bold")).grid(
            row=row, column=0, columnspan=4, pady=(0, 15), sticky="w"
        )
        row += 1
        
        opts = ttk.Frame(parent)
        opts.grid(row=row, column=0, columnspan=4, sticky="ew", pady=5)
        
        self.spice_type_var = tk.StringVar(value="hspice")
        ttk.Label(opts, text="SPICE Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Combobox(opts, textvariable=self.spice_type_var, values=["hspice", "spectre", "eldo"], 
                     state="readonly", width=12).grid(row=0, column=1, sticky="w", padx=10)
        
        self.iterate_var = tk.BooleanVar(value=False)
        self.cleanup_var = tk.BooleanVar(value=True)
        self.verbose_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(opts, text="Reuse existing SPICE data (--iterate)", 
                       variable=self.iterate_var).grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=3)
        ttk.Checkbutton(opts, text="Cleanup intermediate files", 
                       variable=self.cleanup_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=3)
        ttk.Checkbutton(opts, text="Verbose logging", 
                       variable=self.verbose_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=3)
        
        row += 1
        return row

    def _build_models_section(self, parent, start_row):
        """Build Models treeview section."""
        row = start_row
        
        ttk.Label(parent, text="📊 Models", font=("", 14, "bold")).grid(
            row=row, column=0, columnspan=4, pady=(10, 10), sticky="w"
        )
        row += 1
        
        schema = UI_SCHEMA["models"]
        tree = ttk.Treeview(parent, columns=schema["columns"], show="headings", height=8)
        for c in tree["columns"]:
            tree.heading(c, text=c)
            tree.column(c, width=220, anchor="center")
        tree.grid(row=row, column=0, columnspan=4, sticky="ew", pady=10)
        self.models_tree = tree
        tree.bind("<Double-1>", self.edit_cell)
        row += 1
        
        # Buttons
        btns = ttk.Frame(parent)
        btns.grid(row=row, column=0, columnspan=4, pady=8)
        ttk.Button(btns, text="➕ Add Model", command=self.add_model).pack(side=tk.LEFT, padx=10)
        ttk.Button(btns, text="✏️ Edit Model", command=self.edit_model).pack(side=tk.LEFT, padx=10)
        ttk.Button(btns, text="🗑️ Delete Selected", 
                  command=lambda: [self.models_tree.delete(i) for i in self.models_tree.selection()]).pack(side=tk.LEFT, padx=10)
        
        row += 1
        return row

    def _build_pins_section(self, parent, start_row):
        """Build Pins treeview section."""
        row = start_row
        
        ttk.Label(parent, text="📌 Pins", font=("", 14, "bold")).grid(
            row=row, column=0, columnspan=4, pady=(10, 10), sticky="w"
        )
        row += 1
        
        schema = UI_SCHEMA["pins"]
        tree = ttk.Treeview(parent, columns=schema["columns"], show="headings", height=6)
        for c in tree["columns"]:
            tree.heading(c, text=c)
            tree.column(c, width=180, anchor="center")
        tree.grid(row=row, column=0, columnspan=4, sticky="ew", pady=10)
        self.pins_tree = tree
        tree.bind("<Double-1>", self.edit_cell)
        row += 1
        
        # Buttons
        btns = ttk.Frame(parent)
        btns.grid(row=row, column=0, columnspan=4, pady=10)
        ttk.Button(btns, text="➕ Add Pin", 
                  command=lambda: self.pins_tree.insert("", "end", values=("A1", "sig", "model", "", ""))).pack(side=tk.LEFT, padx=10)
        ttk.Button(btns, text="🗑️ Delete Selected", 
                  command=lambda: [self.pins_tree.delete(i) for i in self.pins_tree.selection()]).pack(side=tk.LEFT, padx=10)
        
        row += 1
        return row

    def _build_simulation_controls(self, parent, start_row):
        """Build simulation control buttons with futuristic effects."""
        row = start_row
        
        ttk.Label(parent, text="🚀 Run Simulation", font=("", 14, "bold")).grid(
            row=row, column=0, columnspan=4, pady=(10, 15), sticky="w"
        )
        row += 1
        
        # Button frame
        btn_container = ttk.Frame(parent)
        btn_container.grid(row=row, column=0, columnspan=4, pady=20)
        
        # Start conversion button
        self.run_button = ttk.Button(
            btn_container,
            text="⚡ Start Conversion",
            command=self.start_simulation,
            width=25
        )
        self.run_button.pack(side=tk.LEFT, padx=15)
        
        # Terminate button
        self.terminate_button = ttk.Button(
            btn_container,
            text="⏹ Abort Simulation",
            command=self.terminate_simulation,
            state="disabled",
            width=25
        )
        self.terminate_button.pack(side=tk.LEFT, padx=15)
        
        row += 1
        
        # Progress bar with label
        progress_frame = ttk.Frame(parent)
        progress_frame.grid(row=row, column=0, columnspan=4, sticky="ew", padx=50, pady=10)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready", font=("", 10))
        self.progress_label.pack(pady=(0, 5))
        
        self.progress = ttk.Progressbar(progress_frame, mode="indeterminate", length=600)
        self.progress.pack(fill="x")
        
        row += 1
        return row

    def _set_defaults(self):
        """Set default values."""
        default_out = Path.cwd() / "out"
        default_out.mkdir(parents=True, exist_ok=True)
        self.outdir = str(default_out)
        self.outdir_entry.delete(0, tk.END)
        self.outdir_entry.insert(0, self.outdir)
        
        # Auto-detect ibischk7 in resources/ibischk
        bundled_ibischk = Path(__file__).parent.parent.parent / "resources" / "ibischk" / "ibischk7.exe"
        if bundled_ibischk.exists():
            self.ibischk_path = str(bundled_ibischk)
            self.ibischk_entry.delete(0, tk.END)
            self.ibischk_entry.insert(0, str(bundled_ibischk))
            self.gui.log(f"Auto-detected ibischk7 → {bundled_ibischk.name}", "INFO")
        
        self.yaml_model.reset()
        
        # Populate UI with default values including global_defaults
        self._populate_ui_from_model()
        
        self.gui.log(f"Output directory → {default_out}", "INFO")

    # ===== FILE OPERATIONS =====
    
    def on_input_type_changed(self):
        """Update UI based on selected input type."""
        input_type = self.input_type.get()
        if input_type == "yaml":
            self.input_label.config(text="Input File:")
        else:
            self.input_label.config(text="Input File:")
    
    def load_input_file(self):
        """Load either YAML or .s2i file based on selected type."""
        input_type = self.input_type.get()
        
        if input_type == "yaml":
            self.load_yaml()
        else:
            self.load_s2i()
    
    def load_yaml(self):
        """Load a YAML configuration file."""
        path = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")])
        if not path:
            return
        
        try:
            self.yaml_model = YamlModel()
            self.yaml_model.load_from_file(path)
            self.current_yaml_file = path
            self.yaml_modified = False
            self.input_file = path
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)
            
            self.gui.log(f"✓ Loaded YAML: {Path(path).name}", "INFO")
            
            # Validate and resolve paths
            self._validate_and_fix_model_files(path)
            
            # Populate UI
            self._populate_ui_from_model()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load YAML:\n{e}")
            self.gui.log(f"YAML load error: {e}", "ERROR")
    
    def load_s2i(self):
        """Load a .s2i file and convert to YAML internally."""
        path = filedialog.askopenfilename(filetypes=[("S2I files", "*.s2i"), ("All files", "*.*")])
        if not path:
            return
        
        self.input_file = path
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, path)
        
        try:
            # Convert .s2i to YAML
            s2i_path = Path(path)
            yaml_path = s2i_path.with_suffix('.yaml')
            
            self.gui.log(f"Converting {s2i_path.name} to YAML...", "INFO")
            convert_s2i_to_yaml(s2i_path, yaml_path)
            
            # Load the converted YAML
            self.yaml_model = YamlModel()
            self.yaml_model.load_from_file(str(yaml_path))
            self.current_yaml_file = str(yaml_path)
            self.yaml_modified = False
            
            # Update input_file to use YAML path
            self.input_file = str(yaml_path)
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, str(yaml_path))
            
            self.gui.log(f"✓ Converted and saved: {yaml_path.name}", "INFO")
            
            # Validate and resolve paths
            self._validate_and_fix_model_files(str(yaml_path))
            
            # Populate UI
            self._populate_ui_from_model()
            
            # Also parse for legacy compatibility
            try:
                parser = S2IParser()
                ibis, global_, mList = parser.parse(str(path))
                self.gui.ibis = ibis
                self.gui.global_ = global_
                self.gui.mList = mList
            except Exception as e:
                self.gui.log(f"Legacy parser warning: {e}", "WARNING")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load .s2i:\n{e}")
            self.gui.log(f"S2I load error: {e}", "ERROR")

    def new_file(self):
        """Create a new blank YAML file."""
        if self.yaml_modified and not messagebox.askyesno("Unsaved changes", "Discard changes?"):
            return
        
        self.yaml_model = YamlModel()
        self.yaml_model.reset()
        self.current_yaml_file = None
        self.yaml_modified = False
        self._populate_ui_from_model()
        self.gui.log("New YAML file created", "INFO")

    def save(self):
        """Save the current file."""
        if not self.current_yaml_file:
            self.save_as()
            return
        
        try:
            self._collect_and_sync_data()
            self.yaml_model.save_to_file(self.current_yaml_file)
            self.yaml_modified = False
            self.gui.log(f"✓ Saved: {Path(self.current_yaml_file).name}", "INFO")
        except ValidationError as e:
            messagebox.showerror("Error", f"Validation failed:\n{e}")
            self.gui.log(f"Validation error: {e}", "ERROR")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed:\n{e}")
            self.gui.log(f"Save error: {e}", "ERROR")

    def save_as(self):
        """Save with a new filename."""
        path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml *.yml")]
        )
        if path:
            self.current_yaml_file = path
            self.input_file = path
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)
            self.save()

    def open_spice(self):
        """Parse a SPICE netlist and populate the editor."""
        if not NETLIST_PARSER_AVAILABLE:
            messagebox.showerror("Error", "SPICE parser not available")
            return
        
        if self.yaml_modified and not messagebox.askyesno("Unsaved changes", "Discard changes?"):
            return
        
        path = filedialog.askopenfilename(filetypes=[("SPICE files", "*.sp *.spi *.cir")])
        if not path:
            return
        
        try:
            result = parse_netlist(path)
            self.yaml_model = YamlModel()
            
            if "component" in result:
                self.yaml_model.data["component"]["name"] = result["component"]
            if "models" in result:
                self.yaml_model.data["models"] = result["models"]
            if "pins" in result:
                self.yaml_model.data["pins"] = result["pins"]
            
            self.current_yaml_file = None
            self.yaml_modified = True
            self._populate_ui_from_model()
            self.gui.log(f"✓ Parsed SPICE: {Path(path).name}", "INFO")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse SPICE:\n{e}")
            self.gui.log(f"Parse error: {e}", "ERROR")

    # ===== UI SYNC =====
    
    def _collect_and_sync_data(self):
        """Collect data from UI widgets and sync to model."""
        # General settings
        component_fields = {"component", "manufacturer", "spiceFile"}
        for key, widget in self.entries.items():
            # Skip StringVar entries (they're accessed via the widget)
            if key.endswith("_var"):
                continue
            if key in component_fields:
                continue
            
            # Handle different widget types
            if f"{key}_var" in self.entries:
                # Dropdown or checkbox - get value from StringVar
                value = self.entries[f"{key}_var"].get()
            else:
                # Regular Entry widget
                value = widget.get()
            
            # Only save non-empty values or values that already exist in the data
            if value and value.strip():
                self.yaml_model.set_field(key, value)
            elif key in self.yaml_model.data and not value:
                # If field was in original YAML but is now empty, keep it empty
                self.yaml_model.set_field(key, value)
        
        # Global defaults - map flat UI keys back to nested YAML structure
        # Only save non-empty values
        temp_global_defaults = {}
        
        for key, widget in self.global_entries.items():
            value = widget.get().strip() if widget.get() else ""
            if value:  # Only include non-empty values
                self._set_nested_global_value(temp_global_defaults, key, value)
        
        # Clean up empty nested structures
        self._cleanup_empty_dicts(temp_global_defaults)
        
        # Only set global_defaults if there's actual data
        if temp_global_defaults:
            self.yaml_model.data["global_defaults"] = temp_global_defaults
        elif "global_defaults" in self.yaml_model.data:
            # Remove global_defaults if all fields are now empty
            del self.yaml_model.data["global_defaults"]
        
        # Component info
        if "components" not in self.yaml_model.data or not isinstance(self.yaml_model.data["components"], list):
            self.yaml_model.data["components"] = [{}]
        if len(self.yaml_model.data["components"]) == 0:
            self.yaml_model.data["components"].append({})
        
        comp = self.yaml_model.data["components"][0]
        if "component" in self.entries:
            val = self.entries["component"].get()
            if val or "component" in comp:
                comp["component"] = val
        if "manufacturer" in self.entries:
            val = self.entries["manufacturer"].get()
            if val or "manufacturer" in comp:
                comp["manufacturer"] = val
        if "spiceFile" in self.entries:
            val = self.entries["spiceFile"].get()
            if val or "spiceFile" in comp:
                comp["spiceFile"] = val
        
        # Models
        models = []
        for item in self.models_tree.get_children():
            vals = self.models_tree.item(item, "values")
            model_name = vals[0]
            
            # Preserve existing model data
            existing_model = None
            for m in self.yaml_model.data.get("models", []):
                if m.get("name") == model_name:
                    existing_model = m.copy()
                    break
            
            if existing_model:
                model = existing_model
                model["name"] = vals[0]
                model["type"] = vals[1]
                if vals[2]:
                    model["enable"] = vals[2]
                elif "enable" in model and not vals[2]:
                    del model["enable"]
                if vals[3]:
                    model["polarity"] = vals[3]
                elif "polarity" in model and not vals[3]:
                    del model["polarity"]
                # Handle nomodel flag
                if len(vals) > 4 and vals[4] and vals[4].lower() in ["yes", "true", "1"]:
                    model["nomodel"] = True
                elif "nomodel" in model:
                    del model["nomodel"]
            else:
                model = {"name": vals[0], "type": vals[1]}
                if vals[2]:
                    model["enable"] = vals[2]
                if vals[3]:
                    model["polarity"] = vals[3]
                # Handle nomodel flag
                if len(vals) > 4 and vals[4] and vals[4].lower() in ["yes", "true", "1"]:
                    model["nomodel"] = True
            
            models.append(model)
        self.yaml_model.update_models(models)
        
        # Pins
        pins = []
        for item in self.pins_tree.get_children():
            vals = self.pins_tree.item(item, "values")
            pin = {
                "pinName": vals[0],
                "signalName": vals[1],
                "modelName": vals[2],
            }
            if vals[3]:
                pin["inputPin"] = vals[3]
            if vals[4]:
                pin["enablePin"] = vals[4]
            pins.append(pin)
        self.yaml_model.update_pins(pins)

    def _populate_ui_from_model(self):
        """Populate UI widgets from model data."""
        data = self.yaml_model.get_data()
        flat_data = self._flatten_yaml_data(data)
        
        # General settings
        for key, widget in self.entries.items():
            # Skip StringVar entries (they're accessed via the widget)
            if key.endswith("_var"):
                continue
            
            value = flat_data.get(key, "")
            
            # Handle different widget types
            if f"{key}_var" in self.entries:
                # Dropdown or checkbox - set via StringVar
                var = self.entries[f"{key}_var"]
                var.set(str(value) if value is not None and value != "" else "")
            else:
                # Regular Entry widget
                widget.delete(0, tk.END)
                widget.insert(0, str(value) if value is not None and value != "" else "")
        
        # Global defaults - map nested YAML structure to flat UI keys
        global_defaults = data.get("global_defaults", {})
        for key, widget in self.global_entries.items():
            value = self._get_nested_global_value(global_defaults, key)
            widget.delete(0, tk.END)
            widget.insert(0, str(value) if value is not None and value != "" else "")
        
        # Models
        for item in self.models_tree.get_children():
            self.models_tree.delete(item)
        for m in self.yaml_model.get_models():
            self.models_tree.insert("", "end", values=(
                m.get("name", ""),
                m.get("type", "I/O"),
                m.get("enable", ""),
                m.get("polarity", ""),
                "Yes" if m.get("nomodel", False) else ""
            ))
        
        # Pins
        for item in self.pins_tree.get_children():
            self.pins_tree.delete(item)
        for p in self.yaml_model.get_pins():
            self.pins_tree.insert("", "end", values=(
                p.get("pinName", ""),
                p.get("signalName", ""),
                p.get("modelName", ""),
                p.get("inputPin", ""),
                p.get("enablePin", "")
            ))

    def _flatten_yaml_data(self, data: dict) -> dict:
        """Flatten nested YAML structures for UI display."""
        flat = data.copy()
        
        # Flatten components array
        if "components" in data and isinstance(data["components"], list) and len(data["components"]) > 0:
            comp = data["components"][0]
            flat["component"] = comp.get("component", "")
            flat["manufacturer"] = comp.get("manufacturer", "")
            flat["spiceFile"] = comp.get("spiceFile", "")
        
        return flat
    
    def _get_nested_global_value(self, global_defaults: dict, key: str) -> str:
        """Map flat UI key to nested YAML structure for reading."""
        # Temperature: temp_typ -> temp_range.typ
        if key.startswith("temp_"):
            suffix = key[5:]  # typ, min, max
            return global_defaults.get("temp_range", {}).get(suffix, "")
        # Voltage: voltage_typ -> voltage_range.typ
        elif key.startswith("voltage_"):
            suffix = key[8:]  # typ, min, max
            return global_defaults.get("voltage_range", {}).get(suffix, "")
        # VIL: vil_typ -> vil.typ
        elif key.startswith("vil_"):
            suffix = key[4:]  # typ, min, max
            return global_defaults.get("vil", {}).get(suffix, "")
        # VIH: vih_typ -> vih.typ
        elif key.startswith("vih_"):
            suffix = key[4:]  # typ, min, max
            return global_defaults.get("vih", {}).get(suffix, "")
        # Pullup: pullup_typ -> pullup.typ
        elif key.startswith("pullup_"):
            suffix = key[7:]  # typ, min, max
            return global_defaults.get("pullup", {}).get(suffix, "")
        # Pulldown: pulldown_typ -> pulldown.typ
        elif key.startswith("pulldown_"):
            suffix = key[9:]  # typ, min, max
            return global_defaults.get("pulldown", {}).get(suffix, "")
        # Power clamp: power_clamp_typ -> power_clamp.typ
        elif key.startswith("power_clamp_"):
            suffix = key[12:]  # typ, min, max
            return global_defaults.get("power_clamp", {}).get(suffix, "")
        # GND clamp: gnd_clamp_typ -> gnd_clamp.typ
        elif key.startswith("gnd_clamp_"):
            suffix = key[10:]  # typ, min, max
            return global_defaults.get("gnd_clamp", {}).get(suffix, "")
        # Pin parasitics: r_pkg_typ -> pin_parasitics.R_pkg.typ
        elif key.startswith("r_pkg_"):
            suffix = key[6:]  # typ, min, max
            return global_defaults.get("pin_parasitics", {}).get("R_pkg", {}).get(suffix, "")
        elif key.startswith("l_pkg_"):
            suffix = key[6:]  # typ, min, max
            return global_defaults.get("pin_parasitics", {}).get("L_pkg", {}).get(suffix, "")
        elif key.startswith("c_pkg_"):
            suffix = key[6:]  # typ, min, max
            return global_defaults.get("pin_parasitics", {}).get("C_pkg", {}).get(suffix, "")
        # Direct mapping: sim_time, r_load
        else:
            return global_defaults.get(key, "")
    
    def _cleanup_empty_dicts(self, d: dict):
        """Recursively remove empty dictionaries from nested structure."""
        keys_to_delete = []
        for key, value in d.items():
            if isinstance(value, dict):
                self._cleanup_empty_dicts(value)
                if not value:  # If dict is now empty, mark for deletion
                    keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del d[key]
    
    def _set_nested_global_value(self, global_defaults: dict, key: str, value: str):
        """Map flat UI key to nested YAML structure for writing."""
        # Temperature: temp_typ -> temp_range.typ
        if key.startswith("temp_"):
            suffix = key[5:]  # typ, min, max
            if "temp_range" not in global_defaults:
                global_defaults["temp_range"] = {}
            global_defaults["temp_range"][suffix] = value
        # Voltage: voltage_typ -> voltage_range.typ
        elif key.startswith("voltage_"):
            suffix = key[8:]  # typ, min, max
            if "voltage_range" not in global_defaults:
                global_defaults["voltage_range"] = {}
            global_defaults["voltage_range"][suffix] = value
        # VIL: vil_typ -> vil.typ
        elif key.startswith("vil_"):
            suffix = key[4:]  # typ, min, max
            if "vil" not in global_defaults:
                global_defaults["vil"] = {}
            global_defaults["vil"][suffix] = value
        # VIH: vih_typ -> vih.typ
        elif key.startswith("vih_"):
            suffix = key[4:]  # typ, min, max
            if "vih" not in global_defaults:
                global_defaults["vih"] = {}
            global_defaults["vih"][suffix] = value
        # Pullup: pullup_typ -> pullup.typ
        elif key.startswith("pullup_"):
            suffix = key[7:]  # typ, min, max
            if "pullup" not in global_defaults:
                global_defaults["pullup"] = {}
            global_defaults["pullup"][suffix] = value
        # Pulldown: pulldown_typ -> pulldown.typ
        elif key.startswith("pulldown_"):
            suffix = key[9:]  # typ, min, max
            if "pulldown" not in global_defaults:
                global_defaults["pulldown"] = {}
            global_defaults["pulldown"][suffix] = value
        # Power clamp: power_clamp_typ -> power_clamp.typ
        elif key.startswith("power_clamp_"):
            suffix = key[12:]  # typ, min, max
            if "power_clamp" not in global_defaults:
                global_defaults["power_clamp"] = {}
            global_defaults["power_clamp"][suffix] = value
        # GND clamp: gnd_clamp_typ -> gnd_clamp.typ
        elif key.startswith("gnd_clamp_"):
            suffix = key[10:]  # typ, min, max
            if "gnd_clamp" not in global_defaults:
                global_defaults["gnd_clamp"] = {}
            global_defaults["gnd_clamp"][suffix] = value
        # Pin parasitics: r_pkg_typ -> pin_parasitics.R_pkg.typ
        elif key.startswith("r_pkg_"):
            suffix = key[6:]  # typ, min, max
            if "pin_parasitics" not in global_defaults:
                global_defaults["pin_parasitics"] = {}
            if "R_pkg" not in global_defaults["pin_parasitics"]:
                global_defaults["pin_parasitics"]["R_pkg"] = {}
            global_defaults["pin_parasitics"]["R_pkg"][suffix] = value
        elif key.startswith("l_pkg_"):
            suffix = key[6:]  # typ, min, max
            if "pin_parasitics" not in global_defaults:
                global_defaults["pin_parasitics"] = {}
            if "L_pkg" not in global_defaults["pin_parasitics"]:
                global_defaults["pin_parasitics"]["L_pkg"] = {}
            global_defaults["pin_parasitics"]["L_pkg"][suffix] = value
        elif key.startswith("c_pkg_"):
            suffix = key[6:]  # typ, min, max
            if "pin_parasitics" not in global_defaults:
                global_defaults["pin_parasitics"] = {}
            if "C_pkg" not in global_defaults["pin_parasitics"]:
                global_defaults["pin_parasitics"]["C_pkg"] = {}
            global_defaults["pin_parasitics"]["C_pkg"][suffix] = value
        # Direct mapping: sim_time, r_load
        else:
            global_defaults[key] = value

    # ===== MODELS & PINS EDITING =====
    
    def edit_cell(self, event):
        """Edit a treeview cell on double-click."""
        tree = event.widget
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        if not item or not column:
            return
        
        col_idx = int(column[1:]) - 1
        x, y, w, h = tree.bbox(item, column)
        entry = ttk.Entry(tree)
        entry.insert(0, tree.item(item, "values")[col_idx])
        entry.select_range(0, tk.END)
        entry.focus()
        entry.place(x=x, y=y, width=w, height=h)

        def save():
            values = list(tree.item(item, "values"))
            values[col_idx] = entry.get()
            tree.item(item, values=values)
            entry.destroy()
            self.yaml_modified = True

        entry.bind("<Return>", lambda e: save())
        entry.bind("<FocusOut>", lambda e: save())

    def add_model(self):
        """Add a new model."""
        self._edit_model_dialog(None)
    
    def edit_model(self):
        """Edit selected model."""
        selection = self.models_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a model to edit")
            return
        self._edit_model_dialog(selection[0])
    
    def _edit_model_dialog(self, item_id=None):
        """Show dialog to edit model details including modelFile fields."""
        from tkinter import Toplevel, StringVar
        
        dialog = Toplevel(self.gui.root)
        dialog.title("Edit Model" if item_id else "Add Model")
        dialog.geometry("500x600")
        dialog.transient(self.gui.root)
        dialog.grab_set()
        
        # Get current values
        if item_id:
            vals = self.models_tree.item(item_id, "values")
            current_data = {"name": vals[0], "type": vals[1], "enable": vals[2], "polarity": vals[3],
                          "nomodel": len(vals) > 4 and vals[4] in ["Yes", "yes", "True", "true", "1"]}
            for m in self.yaml_model.data.get("models", []):
                if m.get("name") == vals[0]:
                    current_data["modelFile"] = m.get("modelFile", "")
                    current_data["modelFileMin"] = m.get("modelFileMin", "")
                    current_data["modelFileMax"] = m.get("modelFileMax", "")
                    current_data["nomodel"] = m.get("nomodel", current_data["nomodel"])
                    break
        else:
            current_data = {"name": "new_model", "type": "I/O", "enable": "", "polarity": "Non-Inverting",
                          "modelFile": "", "modelFileMin": "", "modelFileMax": "", "nomodel": False}
        
        # Create form
        entries = {}
        row = 0
        
        # Name
        ttk.Label(dialog, text="Name *:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        entries["name"] = ttk.Entry(dialog, width=40)
        entries["name"].insert(0, current_data["name"])
        entries["name"].grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        row += 1
        
        # Type
        ttk.Label(dialog, text="Type *:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        type_var = StringVar(value=current_data["type"])
        type_combo = ttk.Combobox(dialog, textvariable=type_var, width=38, state="readonly")
        type_combo['values'] = ("Input", "Output", "I/O", "3-state", "Open_drain", "Open_sink", 
                                "Open_source", "I/O_Open_drain", "I/O_Open_sink", "I/O_Open_source")
        type_combo.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        entries["type_var"] = type_var
        row += 1
        
        # Enable
        ttk.Label(dialog, text="Enable:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        entries["enable"] = ttk.Entry(dialog, width=40)
        entries["enable"].insert(0, current_data["enable"])
        entries["enable"].grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        row += 1
        
        # Polarity
        ttk.Label(dialog, text="Polarity:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        pol_var = StringVar(value=current_data["polarity"])
        pol_combo = ttk.Combobox(dialog, textvariable=pol_var, width=38, state="readonly")
        pol_combo['values'] = ("Non-Inverting", "Inverting")
        pol_combo.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        entries["polarity_var"] = pol_var
        row += 1
        
        # NoModel checkbox
        ttk.Label(dialog, text="No Model:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        nomodel_var = tk.BooleanVar(value=current_data.get("nomodel", False))
        ttk.Checkbutton(dialog, variable=nomodel_var, text="Skip simulation for this model").grid(row=row, column=1, padx=10, pady=5, sticky="w")
        entries["nomodel_var"] = nomodel_var
        row += 1
        
        # Separator
        ttk.Separator(dialog, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=15)
        row += 1
        
        # Model Files
        ttk.Label(dialog, text="Model Files (Optional)", font=("", 10, "bold")).grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        for field_name, label_text in [("modelFile", "Model File (typ)"), 
                                        ("modelFileMin", "Model File (min)"), 
                                        ("modelFileMax", "Model File (max)")]:
            ttk.Label(dialog, text=label_text + ":").grid(row=row, column=0, padx=10, pady=5, sticky="e")
            file_frame = ttk.Frame(dialog)
            file_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
            file_frame.grid_columnconfigure(0, weight=1)
            entries[field_name] = ttk.Entry(file_frame)
            entries[field_name].insert(0, current_data.get(field_name, ""))
            entries[field_name].grid(row=0, column=0, sticky="ew")
            ttk.Button(file_frame, text="Browse", width=10,
                      command=lambda e=entries[field_name]: self._browse_model_file(e)).grid(row=0, column=1, padx=(5,0))
            row += 1
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        def save_model():
            name = entries["name"].get().strip()
            if not name:
                messagebox.showerror("Error", "Model name is required")
                return
            
            # Update treeview
            if item_id:
                self.models_tree.item(item_id, values=(name, type_var.get(), entries["enable"].get().strip(), pol_var.get(), "Yes" if nomodel_var.get() else ""))
            else:
                self.models_tree.insert("", "end", values=(name, type_var.get(), entries["enable"].get().strip(), pol_var.get(), "Yes" if nomodel_var.get() else ""))
            
            # Update model data with modelFile fields
            models = []
            for item in self.models_tree.get_children():
                vals = self.models_tree.item(item, "values")
                model_dict = {"name": vals[0], "type": vals[1]}
                if vals[2]:
                    model_dict["enable"] = vals[2]
                if vals[3]:
                    model_dict["polarity"] = vals[3]
                if len(vals) > 4 and vals[4] in ["Yes", "yes", "True", "true", "1"]:
                    model_dict["nomodel"] = True
                
                if vals[0] == name:
                    for field in ["modelFile", "modelFileMin", "modelFileMax"]:
                        val = entries[field].get().strip()
                        if val:
                            model_dict[field] = val
                else:
                    # Preserve existing modelFile data
                    for m in self.yaml_model.data.get("models", []):
                        if m.get("name") == vals[0]:
                            for field in ["modelFile", "modelFileMin", "modelFileMax"]:
                                if m.get(field):
                                    model_dict[field] = m[field]
                            break
                
                models.append(model_dict)
            
            self.yaml_model.update_models(models)
            self.yaml_modified = True
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Save", command=save_model).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
        dialog.grid_columnconfigure(1, weight=1)

    # ===== UTILITY =====
    
    def browse_outdir(self):
        d = filedialog.askdirectory(title="Select or Create Output Directory")
        if not d:
            return
        path = Path(d)
        try:
            path.mkdir(parents=True, exist_ok=True)
            self.outdir = str(path)
            self.outdir_entry.delete(0, tk.END)
            self.outdir_entry.insert(0, self.outdir)
            self.gui.log(f"Output directory: {path}", "INFO")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create directory:\n{e}")

    def browse_ibischk(self):
        p = filedialog.askopenfilename(filetypes=[("EXE", "*.exe")])
        if p:
            self.ibischk_path = p
            self.ibischk_entry.delete(0, tk.END)
            self.ibischk_entry.insert(0, p)

    def _browse_spice_file(self):
        path = filedialog.askopenfilename(
            title="Select SPICE File",
            filetypes=[("SPICE files", "*.sp *.spi *.cir"), ("All files", "*.*")]
        )
        if path and "spiceFile" in self.entries:
            self.entries["spiceFile"].delete(0, tk.END)
            self.entries["spiceFile"].insert(0, path)

    def _browse_model_file(self, entry_widget):
        """Browse for model file and update entry."""
        path = filedialog.askopenfilename(
            title="Select Model File",
            filetypes=[("Model files", "*.mod *.lib"), ("All files", "*.*")]
        )
        if path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, path)

    def _validate_and_fix_model_files(self, yaml_file_path):
        """Validate and resolve model file and spice file paths."""
        import os
        yaml_dir = os.path.dirname(os.path.abspath(yaml_file_path))
        cwd = os.getcwd()
        
        def resolve_file_path(file_path, file_type):
            if not file_path:
                return None, False
            
            if os.path.exists(file_path) and os.path.isabs(file_path):
                self.gui.log(f"✓ {file_type}: {file_path}", "INFO")
                return file_path, False
            
            search_dirs = [yaml_dir, cwd, os.path.join(yaml_dir, "..")]
            
            for base_dir in search_dirs:
                test_path = os.path.join(base_dir, file_path)
                if os.path.exists(test_path):
                    resolved_path = os.path.abspath(test_path)
                    self.gui.log(f"✓ Resolved {file_type}: {file_path} → {resolved_path}", "INFO")
                    return resolved_path, True
            
            self.gui.log(f"⚠ {file_type} not found: {file_path}", "WARNING")
            return None, False
        
        modified = False
        
        # Check model files
        models = self.yaml_model.data.get("models", [])
        for model in models:
            for field in ["modelFile", "modelFileMin", "modelFileMax"]:
                model_file = model.get(field, "")
                if model_file:
                    resolved_path, was_resolved = resolve_file_path(model_file, f"Model {field}")
                    if was_resolved and resolved_path:
                        model[field] = resolved_path
                        modified = True
        
        if modified:
            self.yaml_model.data["models"] = models
        
        # Check spice files
        components = self.yaml_model.data.get("components", [])
        for comp in components:
            spice_file = comp.get("spiceFile", "")
            if spice_file:
                resolved_path, was_resolved = resolve_file_path(spice_file, "Spice file")
                if was_resolved and resolved_path:
                    comp["spiceFile"] = resolved_path
                    modified = True
        
        if modified:
            self.yaml_model.data["components"] = components
            try:
                self.yaml_model.save_to_file(yaml_file_path)
                self.yaml_modified = False
                self.gui.log("Auto-saved YAML with resolved paths", "INFO")
            except Exception as e:
                self.gui.log(f"Failed to auto-save: {e}", "ERROR")
                self.yaml_modified = True

    # ===== SIMULATION CONTROLS =====
    
    def start_simulation(self):
        """Start the SPICE → IBIS conversion."""
        if not self.input_file:
            messagebox.showerror("Error", "Please select an input file first.")
            return
        if not self.outdir:
            messagebox.showerror("Error", "Please set an output directory.")
            return
        
        # Save current data before simulation
        if self.current_yaml_file:
            try:
                self._collect_and_sync_data()
                self.yaml_model.save_to_file(self.current_yaml_file)
                self.gui.log("Auto-saved YAML before simulation", "INFO")
            except Exception as e:
                self.gui.log(f"Warning: Could not auto-save: {e}", "WARNING")
        
        self.simulation_running = True
        self.run_button.config(state="disabled")
        self.terminate_button.config(state="normal")
        self.progress_label.config(text="Running conversion...")
        self.progress.start(8)
        self.gui.status_var.set("Running SPICE → IBIS conversion...")
        self.gui.run_correlation_after_conversion = True
        
        # Build CLI args
        argv = [
            self.input_file,
            "--outdir", self.outdir,
            "--spice-type", self.spice_type_var.get(),
            "--iterate", "1" if self.iterate_var.get() else "0",
            "--cleanup", "1" if self.cleanup_var.get() else "0",
        ]
        if self.ibischk_path:
            argv += ["--ibischk", self.ibischk_path]
        if self.verbose_var.get():
            argv.append("--verbose")
        
        def thread_target():
            start_time = datetime.now()
            try:
                rc = run_conversion(argv, gui=self.gui)
                elapsed = str(datetime.now() - start_time).split(".")[0]
                self.gui.root.after(0, self.simulation_finished, rc, elapsed)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.gui.root.after(0, self.simulation_finished, -1, "0:00")
        
        self.simulation_thread = threading.Thread(target=thread_target, daemon=True)
        self.simulation_thread.start()

    def simulation_finished(self, rc: int, elapsed: str):
        """Handle simulation completion."""
        self.simulation_running = False
        self.progress.stop()
        self.progress_label.config(text="Ready")
        self.run_button.config(state="normal")
        self.terminate_button.config(state="disabled")
        
        if rc == 0:
            self.gui.load_ibs_output()
            self.gui.notebook.select(self.gui.viewer_tab.frame)
            
            msg = (
                f"✓ IBIS model generated successfully!\n"
                f"→ {self.gui.last_ibis_path.name if hasattr(self.gui, 'last_ibis_path') and self.gui.last_ibis_path else 'output.ibs'}\n"
                f"Time: {elapsed}"
            )
            self.gui.log("Conversion completed!", "INFO")
            messagebox.showinfo("Success", msg)
            self.gui.status_var.set(f"Success • {elapsed}")
        else:
            self.gui.status_var.set(f"Failed (code {rc})")
            if rc == 11:
                # Simulator not found — show clear guidance
                self.gui.log("SPICE simulator executable not found — aborted before conversion.", "ERROR")
                messagebox.showerror(
                    "Simulator Not Found",
                    "The selected SPICE simulator executable was not found.\n\n"
                    "Resolution:\n"
                    "- Install the simulator (e.g. HSPICE / Spectre / Eldo), or\n"
                    "- Set the full path via the 'SPICE Command' field, or\n"
                    "- Choose another simulator type if available."
                )
            else:
                self.gui.log(f"Conversion failed with return code {rc}", "ERROR")
                messagebox.showerror("Failed", f"Conversion failed with return code {rc}")

    def terminate_simulation(self):
        """Terminate the running simulation."""
        if self.simulation_running:
            # Note: Python threading doesn't support clean termination
            # This is a soft abort - the thread will continue but UI will reset
            self.gui.log("⚠ Simulation abort requested (thread will complete in background)", "WARNING")
            self.simulation_running = False
            self.progress.stop()
            self.progress_label.config(text="Aborted")
            self.run_button.config(state="normal")
            self.terminate_button.config(state="disabled")
            self.gui.status_var.set("Simulation aborted")
            messagebox.showwarning("Aborted", "Simulation abort requested.\nNote: Background thread may continue to completion.")
