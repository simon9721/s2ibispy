# yaml_editor.py — THE REFACTORED EDITION
# Clean separation of concerns: UI layer uses business logic from YamlModel

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime

from yaml_editor_config import (
    UI_SCHEMA, DEFAULTS, COLORS, FONTS, EDITOR_CONFIG,
    EXAMPLE_MODELS, EXAMPLE_PINS
)
from yaml_editor_model import YamlModel, ValidationError

try:
    from parse_netlist import parse_netlist
    NETLIST_PARSER_AVAILABLE = True
except ImportError as e:
    NETLIST_PARSER_AVAILABLE = False
    parse_netlist = None
    _import_error = str(e)


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


class S2IbispyEditor:
    """Main YAML editor GUI application."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("s2ibispy YAML Editor — REFACTORED EDITION")
        self.root.geometry(f"{EDITOR_CONFIG['window_width']}x{EDITOR_CONFIG['window_height']}")
        self.root.minsize(EDITOR_CONFIG['min_width'], EDITOR_CONFIG['min_height'])

        self.model = YamlModel()
        self.current_file = None
        self.modified = False

        # Widget registries
        self.entries = {}
        self.global_entries = {}
        self.models_tree = None
        self.pins_tree = None

        self.setup_ui()
        self.setup_keyboard_shortcuts()
        
        # Start with fresh file
        self.root.after(100, self.new_file)
        self.root.after(EDITOR_CONFIG["auto_backup_interval"], self.auto_backup)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """Build the UI layout."""
        style = ttk.Style()
        style.theme_use('clam')

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Top bar with buttons
        self._build_top_bar()

        # Scrollable canvas for form
        self._build_scrollable_canvas()

        # Log console at bottom
        self._build_log_console()

    def _build_top_bar(self):
        """Build the top toolbar with buttons."""
        top = ttk.Frame(self.root, padding=8)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(0, weight=1)

        ttk.Button(top, text="New File (Ctrl+N)", command=self.new_file).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Open YAML (Ctrl+O)", command=self.open_yaml).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Open SPICE", command=self.open_spice,
                   state="normal" if NETLIST_PARSER_AVAILABLE else "disabled").pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Save (Ctrl+S)", command=self.save).pack(side=tk.RIGHT, padx=4)

    def _build_scrollable_canvas(self):
        """Build the scrollable form area."""
        canvas = tk.Canvas(self.root, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.content = ttk.Frame(canvas, padding=20)

        self.content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Build form sections
        self._build_form()

    def _build_form(self):
        """Build all form sections."""
        row = 0
        
        # General settings
        row = self._build_section(self.content, row, "general_settings")
        row += 1
        
        # Multiline fields
        row = self._build_multiline_fields(self.content, row)
        row += 1
        
        # Component section
        row = self._build_section(self.content, row, "component")
        row += 1
        
        # Global defaults
        row = self._build_global_defaults(self.content, row)
        row += 1
        
        # Models treeview
        row = self._build_models_section(self.content, row)
        row += 1
        
        # Pins treeview
        row = self._build_pins_section(self.content, row)

    def _build_section(self, parent, start_row, section_key):
        """Build a generic form section from schema."""
        schema = UI_SCHEMA.get(section_key)
        if not schema:
            return start_row
        
        row = start_row
        
        # Title
        if schema.get("title"):
            title_font = FONTS["title_medium"] if section_key == "component" else FONTS["title_large"]
            pady = (20, 10) if section_key == "component" else (0, 20)
            ttk.Label(parent, text=schema["title"], font=title_font).grid(
                row=row, column=0, columnspan=6, pady=pady, sticky="w"
            )
            row += 1
        
        # Fields
        fields = schema.get("fields", [])
        cols = schema.get("cols", 1)
        col = 0
        
        for field_info in fields:
            if col >= cols * 2 and col > 0:
                row += 1
                col = 0
            
            label_text, key, tip = field_info[0], field_info[1], field_info[2] if len(field_info) > 2 else ""
            
            # Label
            lbl = ttk.Label(parent, text=label_text + ":")
            lbl.grid(row=row, column=col, sticky="w", padx=(0, 10))
            if tip:
                Tooltip(lbl, tip)
            
            # Entry
            width = 70 if section_key == "component" else 30
            e = ttk.Entry(parent, width=width)
            e.grid(row=row, column=col+1, padx=5, pady=3, sticky="ew")
            self.entries[key] = e
            if tip:
                Tooltip(e, tip)
            e.bind("<KeyRelease>", lambda evt: self.mark_modified())
            
            col += 2 if cols > 1 else 6
        
        return row + 1

    def _build_multiline_fields(self, parent, start_row):
        """Build multiline text fields (Source, Notes, Disclaimer)."""
        schema = UI_SCHEMA["multiline_fields"]
        row = start_row
        
        for label_text, key, default, tip in schema["fields"]:
            frame = ttk.Frame(parent)
            frame.grid(row=row, column=0, columnspan=6, sticky="ew", padx=10, pady=12)
            frame.grid_columnconfigure(1, weight=1)

            # Preview entry (compact view)
            preview = ttk.Entry(frame, font=FONTS["monospace"])
            preview.grid(row=0, column=1, sticky="ew", padx=(8, 0))

            # Full editor (hidden until expanded)
            editor = tk.Text(frame, height=6, wrap=tk.WORD, font=FONTS["monospace"])
            editor.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=(4, 0))
            editor.grid_remove()

            ttk.Label(frame, text=label_text + ":", font=FONTS["title_small"]).grid(
                row=0, column=0, sticky="w", padx=(0, 8)
            )
            if tip:
                Tooltip(frame, tip)

            self.entries[key] = editor
            # Store StringVar and preview widget for later access
            self.entries[f"{key}_var"] = tk.StringVar(value=default)
            self.entries[f"{key}_preview"] = preview
            var = self.entries[f"{key}_var"]

            def update_preview(var_ref=var, preview_ref=preview):
                text = var_ref.get()
                first = text.split("\n", 1)[0] if text else ""
                preview_ref.delete(0, tk.END)
                preview_ref.insert(0, first + ("..." if "\n" in text or len(text) > 100 else ""))

            def open_editor(event=None, var_ref=var, editor_ref=editor):
                if "\n" in var_ref.get() or len(var_ref.get()) > 80:
                    editor_ref.grid()
                    editor_ref.delete("1.0", tk.END)
                    editor_ref.insert("1.0", var_ref.get())
                    editor_ref.focus()

            def save_and_close(event=None, var_ref=var, editor_ref=editor):
                var_ref.set(editor_ref.get("1.0", "end-1c"))
                editor_ref.grid_remove()
                update_preview()
                self.mark_modified()

            preview.bind("<FocusIn>", open_editor)
            preview.bind("<Double-1>", open_editor)
            editor.bind("<FocusOut>", lambda e, fn=save_and_close: self.root.after(300, fn))
            editor.bind("<Control-Return>", save_and_close)
            editor.bind("<Escape>", save_and_close)
            # Use trace_add() instead of deprecated trace()
            var.trace_add("write", lambda *args, fn=update_preview: fn())
            update_preview()
            
            row += 1
        
        return row

    def _build_global_defaults(self, parent, start_row):
        """Build Global Defaults section with grouped fields."""
        schema = UI_SCHEMA["global_defaults"]
        row = start_row
        
        ttk.Label(parent, text=schema["title"], font=FONTS["title_large"]).grid(
            row=row, column=0, columnspan=6, pady=(30, 15), sticky="w"
        )
        row += 1
        
        for group_title, items in schema["groups"]:
            ttk.Label(parent, text=group_title, font=FONTS["title_small"]).grid(
                row=row, column=0, columnspan=6, sticky="w", padx=15, pady=(15, 5)
            )
            row += 1
            
            col = 0
            for item in items:
                label, key = item[0], item[1]
                tip = item[2] if len(item) > 2 else ""
                
                if col >= 6:
                    row += 1
                    col = 0
                
                ttk.Label(parent, text=label + ":").grid(row=row, column=col, sticky="e", padx=(15, 5))
                e = ttk.Entry(parent, width=14)
                e.grid(row=row, column=col+1, padx=(0, 15), pady=2)
                self.global_entries[key] = e
                if tip:
                    Tooltip(e, tip)
                e.bind("<KeyRelease>", lambda evt: self.mark_modified())
                col += 2
            
            row += 1
        
        return row

    def _build_models_section(self, parent, start_row):
        """Build Models treeview section."""
        schema = UI_SCHEMA["models"]
        row = start_row
        
        ttk.Label(parent, text=schema["title"], font=FONTS["title_large"]).grid(
            row=row, column=0, columnspan=6, pady=(30, 10), sticky="w"
        )
        row += 1
        
        tree = ttk.Treeview(parent, columns=schema["columns"], show="headings", height=schema["height"])
        for c in tree["columns"]:
            tree.heading(c, text=c)
            tree.column(c, width=280, anchor="center")
        tree.grid(row=row, column=0, columnspan=6, sticky="ew", pady=10)
        self.models_tree = tree
        tree.bind("<Double-1>", self.edit_cell)
        row += 1
        
        # Buttons
        btns = ttk.Frame(parent)
        btns.grid(row=row, column=0, columnspan=6, pady=8)
        ttk.Button(btns, text="Add Model", 
                   command=lambda: self.models_tree.insert("", "end", values=("new_model", "I/O", "", ""))).pack(side=tk.LEFT, padx=10)
        ttk.Button(btns, text="Delete Selected", 
                   command=lambda: [self.models_tree.delete(i) for i in self.models_tree.selection()]).pack(side=tk.LEFT, padx=10)
        
        return row + 1

    def _build_pins_section(self, parent, start_row):
        """Build Pins treeview section."""
        schema = UI_SCHEMA["pins"]
        row = start_row
        
        ttk.Label(parent, text=schema["title"], font=FONTS["title_large"]).grid(
            row=row, column=0, columnspan=6, pady=(30, 10), sticky="w"
        )
        row += 1
        
        tree = ttk.Treeview(parent, columns=schema["columns"], show="headings", height=schema["height"])
        for c in tree["columns"]:
            tree.heading(c, text=c)
            tree.column(c, width=220, anchor="center")
        tree.grid(row=row, column=0, columnspan=6, sticky="ew", pady=10)
        self.pins_tree = tree
        tree.bind("<Double-1>", self.edit_cell)
        row += 1
        
        # Buttons
        btns = ttk.Frame(parent)
        btns.grid(row=row, column=0, columnspan=6, pady=10)
        ttk.Button(btns, text="Add Pin", 
                   command=lambda: self.pins_tree.insert("", "end", values=("A1", "sig", "model", "", ""))).pack(side=tk.LEFT, padx=10)
        ttk.Button(btns, text="Delete Selected", 
                   command=lambda: [self.pins_tree.delete(i) for i in self.pins_tree.selection()]).pack(side=tk.LEFT, padx=10)
        
        return row + 1

    def _build_log_console(self):
        """Build the log console at the bottom."""
        log_frame = ttk.LabelFrame(self.root, text=" Log — You Are Unstoppable ", padding=8)
        log_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        self.log_widget = scrolledtext.ScrolledText(
            log_frame, height=EDITOR_CONFIG["log_height"], state='disabled',
            bg=COLORS["log_bg"], fg=COLORS["log_fg_info"], font=FONTS["monospace"]
        )
        self.log_widget.pack(fill=tk.X)
        
        self.log("S2IBISPY EDITOR — REFACTORED & MAINTAINABLE", "success")
        self.log("Clean architecture • Testable logic • Easy to extend", "success")

    def log(self, msg, level="info"):
        """Log a message to the console."""
        self.log_widget.config(state='normal')
        colors = {
            "info": COLORS["log_fg_info"],
            "success": COLORS["log_fg_success"],
            "warning": COLORS["log_fg_warning"],
            "error": COLORS["log_fg_error"]
        }
        tag = level
        ts = datetime.now().strftime('%H:%M:%S')
        self.log_widget.insert(tk.END, f"{ts} | {msg}\n", tag)
        self.log_widget.tag_config(tag, foreground=colors.get(level, COLORS["log_fg_info"]))
        self.log_widget.see(tk.END)
        self.log_widget.config(state='disabled')

    def setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts."""
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_yaml())
        self.root.bind("<Control-s>", lambda e: self.save())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_as())
        self.root.bind("<Control-q>", lambda e: self.on_closing())

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
            self.mark_modified()

        entry.bind("<Return>", lambda e: save())
        entry.bind("<FocusOut>", lambda e: save())

    def mark_modified(self):
        """Mark the document as modified."""
        if not self.modified:
            self.modified = True
            title = self.root.title()
            if not title.startswith("● "):
                self.root.title("● " + title)

    def auto_backup(self):
        """Auto-backup modified files at intervals."""
        if self.modified and self.current_file:
            backup_path = self.current_file + ".autosave"
            try:
                self._collect_and_sync_data()
                self.model.save_to_file(backup_path)
                self.log("Auto-backup created", "info")
            except Exception as e:
                self.log(f"Auto-backup failed: {e}", "error")
        
        self.root.after(EDITOR_CONFIG["auto_backup_interval"], self.auto_backup)

    def on_closing(self):
        """Handle window close event."""
        if self.modified:
            ans = messagebox.askyesnocancel("Unsaved changes", "Save before closing?")
            if ans:  # Yes
                self.save()
                if self.modified:
                    return
            elif ans is None:  # Cancel
                return
        self.root.destroy()

    def new_file(self):
        """Create a new file."""
        self.current_file = None
        self.modified = False
        self.root.title("Untitled — s2ibispy YAML Editor — REFACTORED v1")
        self.log("New file created", "success")
        self.clear_all()
        self.model.reset()
        self.load_ui_from_model()

    def clear_all(self):
        """Clear all UI fields."""
        for w in self.entries.values():
            # Skip StringVar and Entry (preview) helper objects
            if isinstance(w, tk.StringVar):
                continue
            if isinstance(w, ttk.Entry):
                continue
            
            if isinstance(w, tk.Text):
                w.delete("1.0", tk.END)
            elif hasattr(w, 'delete'):
                w.delete(0, tk.END)
        for e in self.global_entries.values():
            e.delete(0, tk.END)
        for tree in (self.models_tree, self.pins_tree):
            for i in tree.get_children():
                tree.delete(i)

    def _flatten_yaml_data(self, data):
        """Flatten nested YAML structures for UI population."""
        flat = data.copy()
        
        # Flatten global_defaults nested structure
        if "global_defaults" in data and isinstance(data["global_defaults"], dict):
            gd = data["global_defaults"]
            flat["sim_time"] = gd.get("sim_time", "")
            flat["r_load"] = gd.get("r_load", "")
            
            # Temperature range
            tr = gd.get("temp_range", {})
            flat["temp_typ"] = tr.get("typ", "")
            flat["temp_min"] = tr.get("min", "")
            flat["temp_max"] = tr.get("max", "")
            
            # Voltage range
            vr = gd.get("voltage_range", {})
            flat["voltage_typ"] = vr.get("typ", "")
            flat["voltage_min"] = vr.get("min", "")
            flat["voltage_max"] = vr.get("max", "")
            
            # Pullup ref
            pu = gd.get("pullup_ref", {})
            flat["pullup_typ"] = pu.get("typ", "")
            flat["pullup_min"] = pu.get("min", "")
            flat["pullup_max"] = pu.get("max", "")
            
            # Pulldown ref
            pd = gd.get("pulldown_ref", {})
            flat["pulldown_typ"] = pd.get("typ", "")
            flat["pulldown_min"] = pd.get("min", "")
            flat["pulldown_max"] = pd.get("max", "")
            
            # Power clamp ref
            pc = gd.get("power_clamp_ref", {})
            flat["power_clamp_typ"] = pc.get("typ", "")
            flat["power_clamp_min"] = pc.get("min", "")
            flat["power_clamp_max"] = pc.get("max", "")
            
            # GND clamp ref
            gc = gd.get("gnd_clamp_ref", {})
            flat["gnd_clamp_typ"] = gc.get("typ", "")
            flat["gnd_clamp_min"] = gc.get("min", "")
            flat["gnd_clamp_max"] = gc.get("max", "")
            
            # VIL
            vil = gd.get("vil", {})
            flat["vil_typ"] = vil.get("typ", "")
            flat["vil_min"] = vil.get("min", "")
            flat["vil_max"] = vil.get("max", "")
            
            # VIH
            vih = gd.get("vih", {})
            flat["vih_typ"] = vih.get("typ", "")
            flat["vih_min"] = vih.get("min", "")
            flat["vih_max"] = vih.get("max", "")
            
            # Pin parasitics
            pp = gd.get("pin_parasitics", {})
            r_pkg = pp.get("R_pkg", {})
            flat["r_pkg_typ"] = r_pkg.get("typ", "")
            flat["r_pkg_min"] = r_pkg.get("min", "")
            flat["r_pkg_max"] = r_pkg.get("max", "")
            
            l_pkg = pp.get("L_pkg", {})
            flat["l_pkg_typ"] = l_pkg.get("typ", "")
            flat["l_pkg_min"] = l_pkg.get("min", "")
            flat["l_pkg_max"] = l_pkg.get("max", "")
            
            c_pkg = pp.get("C_pkg", {})
            flat["c_pkg_typ"] = c_pkg.get("typ", "")
            flat["c_pkg_min"] = c_pkg.get("min", "")
            flat["c_pkg_max"] = c_pkg.get("max", "")
        
        return flat

    def load_ui_from_model(self):
        """Sync UI widgets from model data."""
        data = self.model.get_data()
        
        # Flatten nested structures from YAML for UI
        flat_data = self._flatten_yaml_data(data)
        
        # Simple entries (skip _var and _preview helper entries)
        for key, widget in self.entries.items():
            if key.endswith("_var") or key.endswith("_preview"):
                continue
            
            value = flat_data.get(key, "")
            if isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
                widget.insert("1.0", str(value) if value else "")
                # Also update the StringVar for multiline fields
                if f"{key}_var" in self.entries:
                    self.entries[f"{key}_var"].set(str(value) if value else "")
                    # Update preview
                    preview = self.entries.get(f"{key}_preview")
                    if preview:
                        text = str(value) if value else ""
                        first = text.split("\n", 1)[0] if text else ""
                        preview.delete(0, tk.END)
                        preview.insert(0, first + ("..." if "\n" in text or len(text) > 100 else ""))
            else:
                widget.delete(0, tk.END)
                widget.insert(0, str(value) if value else "")
        
        # Global entries - load from flattened data
        for key, widget in self.global_entries.items():
            value = flat_data.get(key, "")
            widget.delete(0, tk.END)
            widget.insert(0, str(value) if value else "")
        
        # Models and pins
        models = self.model.get_models()
        for m in models:
            self.models_tree.insert("", "end", values=(
                m.get("name", ""),
                m.get("type", "I/O"),
                m.get("enable", ""),
                m.get("polarity", "")
            ))
        
        pins = self.model.get_pins()
        for p in pins:
            self.pins_tree.insert("", "end", values=(
                p.get("pinName", ""),
                p.get("signalName", ""),
                p.get("modelName", ""),
                p.get("inputPin", ""),
                p.get("enablePin", "")
            ))

    def _collect_and_sync_data(self):
        """Collect all UI data and sync into model."""
        # Collect simple entries (skip _var and _preview helper entries)
        for key, widget in self.entries.items():
            if key.endswith("_var") or key.endswith("_preview"):
                continue
            
            if isinstance(widget, tk.Text):
                value = widget.get("1.0", "end-1c").strip()
            else:
                value = widget.get().strip()
            self.model.set_field(key, value)
        
        # Collect global entries
        for key, widget in self.global_entries.items():
            value = widget.get().strip()
            self.model.set_field(key, value)
        
        # Collect models
        models = []
        for iid in self.models_tree.get_children():
            v = self.models_tree.item(iid, "values")
            models.append({
                "name": v[0],
                "type": v[1],
                "enable": v[2] if v[2] else None,
                "polarity": v[3] if v[3] else None
            })
        self.model.update_models(models)
        
        # Collect pins
        pins = []
        for iid in self.pins_tree.get_children():
            v = self.pins_tree.item(iid, "values")
            pins.append({
                "pinName": v[0],
                "signalName": v[1],
                "modelName": v[2],
                "inputPin": v[3] if v[3] else None,
                "enablePin": v[4] if v[4] else None
            })
        self.model.update_pins(pins)
        
        # Rebuild global_defaults structure
        self.model._build_global_defaults_structure()

    def open_yaml(self):
        """Open and load a YAML file."""
        path = filedialog.askopenfilename(filetypes=[("YAML", "*.yaml *.yml")])
        if not path:
            return
        try:
            self.model.load_from_file(path)
            self.current_file = path
            self.root.title(f"{Path(path).name} — s2ibispy YAML Editor")
            self.clear_all()
            self.load_ui_from_model()
            self.modified = False
            self.log(f"Loaded {Path(path).name}", "success")
        except ValidationError as e:
            messagebox.showerror("Error", f"Cannot load file:\n{e}")
            self.log(f"Load error: {e}", "error")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{e}")
            self.log(f"Unexpected error: {e}", "error")

    def open_spice(self):
        """Open and parse a SPICE file."""
        if not NETLIST_PARSER_AVAILABLE:
            messagebox.showerror("Missing", "parse_netlist.py not found")
            return
        
        path = filedialog.askopenfilename(filetypes=[("SPICE", "*.sp *.cir")])
        if not path:
            return
        
        try:
            dummy_cfg = {'voltage_range': {'typ': '3.3'}, 'r_load': '50', 'sim_time': '6e-9'}
            parsed = parse_netlist(path, dummy_cfg)
            
            self.entries["spiceFile"].delete(0, tk.END)
            self.entries["spiceFile"].insert(0, str(path))
            
            # Clear and reload models
            for i in self.models_tree.get_children():
                self.models_tree.delete(i)
            for m in parsed.get("models", []):
                self.models_tree.insert("", "end", values=(
                    m.get("name", ""),
                    m.get("type", "I/O"),
                    m.get("enable", ""),
                    m.get("polarity", "")
                ))
            
            # Clear and reload pins
            for i in self.pins_tree.get_children():
                self.pins_tree.delete(i)
            for p in parsed.get("pins", []):
                self.pins_tree.insert("", "end", values=(
                    p.get("pin", ""),
                    p.get("signal", ""),
                    p.get("model", ""),
                    "",
                    ""
                ))
            
            self.log(f"SPICE loaded: {Path(path).name}", "success")
            self.mark_modified()
        except Exception as e:
            messagebox.showerror("Parse error", str(e))
            self.log(f"SPICE parse error: {e}", "error")

    def save(self):
        """Save the current file."""
        if not self.current_file:
            self.save_as()
            return
        
        try:
            self._collect_and_sync_data()
            
            # Validate before saving
            errors = self.model.validate()
            if errors:
                msg = "Validation warnings:\n" + "\n".join(errors)
                if messagebox.askokcancel("Validation", msg + "\n\nSave anyway?"):
                    pass
                else:
                    self.log("Save cancelled due to validation errors", "warning")
                    return
            
            self.model.save_to_file(self.current_file)
            self.modified = False
            self.root.title(f"{Path(self.current_file).name} — s2ibispy YAML Editor")
            self.log(f"Saved {Path(self.current_file).name}", "success")
        except ValidationError as e:
            messagebox.showerror("Error", f"Save failed:\n{e}")
            self.log(f"Save error: {e}", "error")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{e}")
            self.log(f"Unexpected error: {e}", "error")

    def save_as(self):
        """Save the file with a new name."""
        path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml *.yml")]
        )
        if path:
            self.current_file = path
            self.save()


if __name__ == "__main__":
    root = tk.Tk()
    app = S2IbispyEditor(root)
    root.mainloop()