# gui/tabs/yaml_editor_tab.py
# Integrated YAML editor tab for s2ibispy GUI

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime

# Import the business logic and config from root
import sys
from pathlib import Path
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from yaml_editor_config import (
    UI_SCHEMA, DEFAULTS, COLORS, FONTS, EDITOR_CONFIG,
    EXAMPLE_MODELS, EXAMPLE_PINS
)
from yaml_editor_model import YamlModel, ValidationError

try:
    from parse_netlist import parse_netlist
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


class YamlEditorTab:
    """YAML Editor tab integrated into s2ibispy GUI."""
    
    def __init__(self, notebook, gui):
        self.gui = gui
        self.frame = ttk.Frame(notebook)
        
        self.model = YamlModel()
        self.current_file = None
        self.modified = False

        # Widget registries
        self.entries = {}
        self.global_entries = {}
        self.models_tree = None
        self.pins_tree = None

        self.setup_ui()
        
        # Start with fresh file
        self.frame.after(100, self.new_file)

    def setup_ui(self):
        """Build the UI layout."""
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Top bar with buttons
        self._build_top_bar()

        # Scrollable canvas for form
        self._build_scrollable_canvas()

        # No separate log console - use main GUI's log

    def _build_top_bar(self):
        """Build the top toolbar with buttons."""
        top = ttk.Frame(self.frame, padding=8)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(0, weight=1)

        ttk.Button(top, text="New", command=self.new_file).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Open YAML", command=self.open_yaml).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Open SPICE", command=self.open_spice,
                   state="normal" if NETLIST_PARSER_AVAILABLE else "disabled").pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Save", command=self.save).pack(side=tk.RIGHT, padx=4)
        ttk.Button(top, text="Save As", command=self.save_as).pack(side=tk.RIGHT, padx=4)
        
        # Status label
        self.status_label = ttk.Label(top, text="Ready", foreground="#88ff88")
        self.status_label.pack(side=tk.RIGHT, padx=20)

    def _build_scrollable_canvas(self):
        """Build the scrollable form area."""
        canvas = tk.Canvas(self.frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
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
            editor.bind("<FocusOut>", lambda e, fn=save_and_close: self.frame.after(300, fn))
            editor.bind("<Control-Return>", save_and_close)
            editor.bind("<Escape>", save_and_close)
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
            self.status_label.config(text="● Modified", foreground="#ffff88")

    def log(self, msg, level="INFO"):
        """Log to main GUI's log console."""
        self.gui.log(msg, level)

    # === File Operations ===
    
    def new_file(self):
        """Create a new blank YAML file."""
        if self.modified and not messagebox.askyesno("Unsaved changes", "Discard changes?"):
            return
        
        self.model = YamlModel()
        self.current_file = None
        self.modified = False
        self._populate_ui_from_model()
        self.status_label.config(text="New file", foreground="#88ff88")
        self.log("New YAML file created", "INFO")

    def open_yaml(self):
        """Open an existing YAML file."""
        if self.modified and not messagebox.askyesno("Unsaved changes", "Discard changes?"):
            return
        
        path = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml *.yml")])
        if not path:
            return
        
        try:
            self.model = YamlModel.from_file(path)
            self.current_file = path
            self.modified = False
            self._populate_ui_from_model()
            self.status_label.config(text=f"Loaded: {Path(path).name}", foreground="#88ff88")
            self.log(f"Opened: {Path(path).name}", "INFO")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open:\n{e}")
            self.log(f"Open error: {e}", "ERROR")

    def open_spice(self):
        """Parse a SPICE netlist and populate the editor."""
        if not NETLIST_PARSER_AVAILABLE:
            messagebox.showerror("Error", "SPICE parser not available")
            return
        
        if self.modified and not messagebox.askyesno("Unsaved changes", "Discard changes?"):
            return
        
        path = filedialog.askopenfilename(filetypes=[("SPICE files", "*.sp *.spi *.cir")])
        if not path:
            return
        
        try:
            result = parse_netlist(path)
            self.model = YamlModel()
            
            # Populate from netlist
            if "component" in result:
                self.model.data["component"]["name"] = result["component"]
            
            if "models" in result:
                self.model.data["models"] = result["models"]
            
            if "pins" in result:
                self.model.data["pins"] = result["pins"]
            
            self.current_file = None
            self.modified = True
            self._populate_ui_from_model()
            self.status_label.config(text=f"Parsed: {Path(path).name}", foreground="#88ff88")
            self.log(f"Parsed SPICE: {Path(path).name}", "INFO")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse SPICE:\n{e}")
            self.log(f"Parse error: {e}", "ERROR")

    def save(self):
        """Save the current file."""
        if not self.current_file:
            self.save_as()
            return
        
        try:
            self._collect_and_sync_data()
            self.model.save_to_file(self.current_file)
            self.modified = False
            self.status_label.config(text=f"Saved: {Path(self.current_file).name}", foreground="#88ff88")
            self.log(f"Saved: {Path(self.current_file).name}", "INFO")
        except ValidationError as e:
            messagebox.showerror("Error", f"Validation failed:\n{e}")
            self.log(f"Validation error: {e}", "ERROR")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed:\n{e}")
            self.log(f"Save error: {e}", "ERROR")

    def save_as(self):
        """Save with a new filename."""
        path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml *.yml")]
        )
        if path:
            self.current_file = path
            self.save()

    def _collect_and_sync_data(self):
        """Collect data from UI widgets and sync to model."""
        # General settings
        for key, widget in self.entries.items():
            if key.endswith("_var") or key.endswith("_preview"):
                continue
            if isinstance(widget, tk.Text):
                # Multiline field
                var = self.entries.get(f"{key}_var")
                if var:
                    self.model.set_field(key, var.get())
            else:
                # Regular entry
                self.model.set_field(key, widget.get())
        
        # Global defaults
        for key, widget in self.global_entries.items():
            self.model.set_field(key, widget.get())
        
        # Models
        models = []
        for item in self.models_tree.get_children():
            vals = self.models_tree.item(item, "values")
            models.append({
                "name": vals[0],
                "type": vals[1],
                "spice_file": vals[2],
                "series_spice_file": vals[3]
            })
        self.model.data["models"] = models
        
        # Pins
        pins = []
        for item in self.pins_tree.get_children():
            vals = self.pins_tree.item(item, "values")
            pins.append({
                "pin": vals[0],
                "signal": vals[1],
                "model": vals[2],
                "enable_pin": vals[3],
                "input_pin": vals[4]
            })
        self.model.data["pins"] = pins

    def _populate_ui_from_model(self):
        """Populate UI widgets from model data."""
        # General settings
        for key, widget in self.entries.items():
            if key.endswith("_var") or key.endswith("_preview"):
                continue
            val = self.model.get_field(key, "")
            if isinstance(widget, tk.Text):
                # Multiline field
                var = self.entries.get(f"{key}_var")
                if var:
                    var.set(val)
            else:
                # Regular entry
                widget.delete(0, tk.END)
                widget.insert(0, str(val) if val is not None else "")
        
        # Global defaults
        for key, widget in self.global_entries.items():
            val = self.model.get_field(key, "")
            widget.delete(0, tk.END)
            widget.insert(0, str(val) if val is not None else "")
        
        # Models
        for item in self.models_tree.get_children():
            self.models_tree.delete(item)
        for m in self.model.data.get("models", []):
            self.models_tree.insert("", "end", values=(
                m.get("name", ""),
                m.get("type", ""),
                m.get("spice_file", ""),
                m.get("series_spice_file", "")
            ))
        
        # Pins
        for item in self.pins_tree.get_children():
            self.pins_tree.delete(item)
        for p in self.model.data.get("pins", []):
            self.pins_tree.insert("", "end", values=(
                p.get("pin", ""),
                p.get("signal", ""),
                p.get("model", ""),
                p.get("enable_pin", ""),
                p.get("input_pin", "")
            ))
