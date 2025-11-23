#!/usr/bin/env python3
"""
s2ibispy_gui.py — The Modern Professional GUI for s2ibispy
Version 2.0 — Dark, Fast, Beautiful, Bidirectional
Replaces s2ibis3 forever.
"""

import os
import sys
import json
import threading
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# ----------------------------------------------------------------------
# Project Setup
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Backend imports
from main import main as s2ibispy_main
from parser import S2IParser
from models import IbisTOP, IbisGlobal, IbisModel, IbisPin, IbisTypMinMax
from s2i_constants import ConstantStuff as CS
from s2ioutput import IbisWriter

# Session config
CONFIG_FILE = Path.home() / ".s2ibispy_gui.json"

def load_session():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_session(data: dict) -> None:
    try:
        # Explicitly open with encoding and use TextIOWrapper → satisfies type checker
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass  # silent fail – same as before


# ----------------------------------------------------------------------
# Main Application
# ----------------------------------------------------------------------
class S2IBISpyGUI:
    VERSION = "2.0.0"

    def __init__(self, root):
        self.root = root
        self.root.title(f"s2ibispy — SPICE to IBIS Converter v{self.VERSION}")
        self.root.geometry("1400x920")
        self.root.minsize(1150, 720)

        # Data
        self.input_file: str = ""
        self.outdir: str = ""
        self.ibischk_path: str = ""
        self.ibis: Optional[IbisTOP] = None
        self.global_: Optional[IbisGlobal] = None
        self.mList: List[IbisModel] = []

        # Threading
        self.thread = None
        self.start_time = None

        # Session
        self.session = load_session()

        # GUI Setup
        self.setup_theme()
        self.create_widgets()
        self.restore_session()

    def setup_theme(self):
        style = ttk.Style()
        try:
            style.theme_use("forest-dark")
        except:
            try:
                style.theme_use("equilux")
            except:
                style.theme_use("clam")

        style.configure("Treeview", rowheight=22, font=("Segoe UI", 10))
        style.configure("TNotebook.Tab", padding=(16, 10), font=("Segoe UI", 11))

    def create_widgets(self):
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load .s2i", command=self.load_s2i, accelerator="Ctrl+O")
        file_menu.add_command(label="Save .s2i As...", command=self.save_s2i)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Main vertical split
        main_pane = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_pane.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        # Notebook
        self.notebook = ttk.Notebook(main_pane)
        main_pane.add(self.notebook, weight=4)

        # Tabs
        self.tab_input = ttk.Frame(self.notebook)
        self.tab_models = ttk.Frame(self.notebook)
        self.tab_pins = ttk.Frame(self.notebook)
        self.tab_sim = ttk.Frame(self.notebook)
        self.tab_viewer = ttk.Frame(self.notebook)
        self.tab_plots = ttk.Frame(self.notebook)
        self.tab_corr = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_input, text="  Input & Settings  ")
        self.notebook.add(self.tab_models, text="  Models  ")
        self.notebook.add(self.tab_pins, text="  Pins  ")
        self.notebook.add(self.tab_sim, text="  Simulation  ")
        self.notebook.add(self.tab_viewer, text="  IBIS Viewer  ")
        self.notebook.add(self.tab_plots, text="  Plots  ")
        self.notebook.add(self.tab_corr, text="  Correlation  ")

        # Build tabs
        self.create_input_tab()
        self.create_models_tab()
        self.create_pins_tab()
        self.create_sim_tab()
        self.create_viewer_tab()
        self.create_plots_tab()
        self.create_correlation_tab()

        # Log Panel (bottom)
        log_frame = ttk.LabelFrame(main_pane, text=" Log Output ")
        main_pane.add(log_frame, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, font=("Consolas", 10), bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="white", selectbackground="#555555", height=12
        )
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.setup_logging()

        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        status_bar.pack(side="bottom", fill="x")

        # Bindings
        self.root.bind("<Control-o>", lambda e: self.load_s2i())

    def setup_logging(self):
        self.log_text.tag_config("INFO", foreground="#88ff88")
        self.log_text.tag_config("WARNING", foreground="#ffff88")
        self.log_text.tag_config("ERROR", foreground="#ff8888")
        self.log_text.tag_config("SUCCESS", foreground="#88ffff", font=("Consolas", 10, "bold"))

        class LogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record)
                tag = "INFO"
                if record.levelno >= logging.ERROR:
                    tag = "ERROR"
                elif record.levelno >= logging.WARNING:
                    tag = "WARNING"
                elif "success" in msg.lower() or "done" in msg.lower():
                    tag = "SUCCESS"

                def update():
                    self.text_widget.insert(tk.END, f"[{datetime.now():%H:%M:%S}] {msg}\n", tag)
                    self.text_widget.see(tk.END)

                self.text_widget.after(0, update)

        handler = LogHandler(self.log_text)
        handler.setFormatter(logging.Formatter("%(levelname)s → %(message)s"))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

        # Fixed stdout redirector
        class StdoutRedirector:
            def __init__(self, text_widget):
                self.text_widget = text_widget

            def write(self, s):
                if s.strip():
                    self.text_widget.after(0, lambda: (
                        self.text_widget.insert(tk.END, s),
                        self.text_widget.see(tk.END)
                    ))

            def flush(self): pass

        sys.stdout = StdoutRedirector(self.log_text)
        sys.stderr = StdoutRedirector(self.log_text)

    # ===================================================================
    # TAB: Input & Settings
    # ===================================================================
    def create_input_tab(self):
        f = self.tab_input
        r = 0
        ttk.Label(f, text="Input .s2i File:", font=("", 10, "bold")).grid(row=r, column=0, sticky="w", padx=10, pady=8)
        self.input_entry = ttk.Entry(f, width=80)
        self.input_entry.grid(row=r, column=1, padx=8, pady=8)
        ttk.Button(f, text="Browse", command=self.load_s2i).grid(row=r, column=2, padx=8, pady=8)
        r += 1

        ttk.Label(f, text="Output Directory:").grid(row=r, column=0, sticky="w", padx=10, pady=5)
        self.outdir_entry = ttk.Entry(f, width=80)
        self.outdir_entry.grid(row=r, column=1, padx=8, pady=5)
        ttk.Button(f, text="Browse", command=self.browse_outdir).grid(row=r, column=2, padx=8, pady=5)
        r += 1

        ttk.Label(f, text="ibischk7 Path (optional):").grid(row=r, column=0, sticky="w", padx=10, pady=5)
        self.ibischk_entry = ttk.Entry(f, width=80)
        self.ibischk_entry.grid(row=r, column=1, padx=8, pady=5)
        ttk.Button(f, text="Browse", command=self.browse_ibischk).grid(row=r, column=2, padx=8, pady=5)
        r += 1

        # Options frame
        opts = ttk.LabelFrame(f, text=" Simulation Options ")
        opts.grid(row=r, column=0, columnspan=3, sticky="ew", padx=10, pady=15)
        opts.columnconfigure(1, weight=1)

        self.spice_type_var = tk.StringVar(value="hspice")
        ttk.Label(opts, text="SPICE Type:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ttk.Combobox(opts, textvariable=self.spice_type_var, values=["hspice", "spectre", "eldo"], state="readonly", width=12).grid(row=0, column=1, sticky="w", padx=10)

        self.iterate_var = tk.BooleanVar(value=False)
        self.cleanup_var = tk.BooleanVar(value=True)
        self.verbose_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(opts, text="Reuse existing SPICE data (--iterate)", variable=self.iterate_var).grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=3)
        ttk.Checkbutton(opts, text="Cleanup intermediate files", variable=self.cleanup_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=3)
        ttk.Checkbutton(opts, text="Verbose logging", variable=self.verbose_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=3)

        # Global parameters (simplified — add more if needed)
        gframe = ttk.LabelFrame(f, text=" Global Parameters ")
        gframe.grid(row=r+1, column=0, columnspan=3, sticky="ew", padx=10, pady=15)
        # ... (you can expand this later)

    def create_models_tab(self):
        f = self.tab_models
        self.models_tree = ttk.Treeview(f, columns=("Name", "Type", "Vinl", "Vinh", "Ccomp"), show="headings", height=20)
        for col, w in zip(self.models_tree["columns"], [150, 120, 100, 100, 100]):
            self.models_tree.heading(col, text=col)
            self.models_tree.column(col, width=w, anchor="center")
        self.models_tree.pack(fill="both", expand=True, padx=10, pady=10)

    def create_pins_tab(self):
        f = self.tab_pins
        self.pins_tree = ttk.Treeview(f, columns=("Pin", "Signal", "Model", "Rpin", "Lpin", "Cpin"), show="headings")
        for col, w in zip(self.pins_tree["columns"], [80, 150, 150, 80, 80, 80]):
            self.pins_tree.heading(col, text=col)
            self.pins_tree.column(col, width=w)
        self.pins_tree.pack(fill="both", expand=True, padx=10, pady=10)

    def create_sim_tab(self):
        f = self.tab_sim
        ttk.Label(f, text="Run SPICE → IBIS Conversion", font=("", 14, "bold")).pack(pady=30)
        self.run_button = ttk.Button(f, text="Start Conversion", command=self.start_simulation)
        self.run_button.pack(pady=20)
        self.progress = ttk.Progressbar(f, mode="indeterminate")
        self.progress.pack(fill="x", padx=100, pady=20)

    def create_viewer_tab(self):
        f = self.tab_viewer
        paned = ttk.PanedWindow(f, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # Left: Section tree (fixed width using a frame wrapper)
        left_frame = ttk.Frame(paned, width=300, relief="sunken", borderwidth=1)
        left_frame.pack_propagate(False)  # This is the key!
        paned.add(left_frame, weight=1)

        self.section_tree = ttk.Treeview(left_frame, show="tree", selectmode="browse")
        self.section_tree.pack(fill="both", expand=True)

        # Right: IBIS text viewer
        self.ibis_viewer = scrolledtext.ScrolledText(paned, font=("Courier New", 10), wrap="none")
        self.ibis_viewer.pack(fill="both", expand=True)
        paned.add(self.ibis_viewer, weight=4)

        # Bind double-click to jump to section
        self.section_tree.bind("<Double-1>", self.on_section_double_click)

    def on_section_double_click(self, event=None):
        """Jump to the selected section in the IBIS viewer"""
        selection = self.section_tree.selection()
        if not selection:
            return
        item_text = self.section_tree.item(selection[0])["text"]

        content = self.ibis_viewer.get(1.0, tk.END)
        try:
            pos = content.index(item_text)
            line_num = content.count("\n", 0, pos) + 1
            self.ibis_viewer.see(f"{line_num}.0")
            self.ibis_viewer.tag_add("sel", f"{line_num}.0", f"{line_num + 20}.0")
            self.ibis_viewer.tag_config("sel", background="#333344", foreground="yellow")
        except ValueError:
            pass  # section name not found in text

    def create_plots_tab(self):
        f = self.tab_plots
        lbl = ttk.Label(f, text="IBIS Waveform & IV Curve Plotter\nComing soon — drop your script here!", font=("", 14), foreground="#8888ff")
        lbl.pack(expand=True)

    def create_correlation_tab(self):
        f = self.tab_corr
        lbl = ttk.Label(f, text="SPICE vs IBIS Correlation Viewer\nComing soon — the killer feature!", font=("", 14), foreground="#88ff88")
        lbl.pack(expand=True)

    # ===================================================================
    # GUI ↔ Data Sync
    # ===================================================================
    def apply_gui_to_objects(self):
        if not self.ibis or not self.global_:
            return
        # Add more fields here as you expand the GUI
        pass

    def populate_gui(self):
        if not self.ibis or not self.global_ or not self.mList:
            return

        # Models (hide NoModel)
        for item in self.models_tree.get_children():
            self.models_tree.delete(item)
        for m in self.mList:
            # Safely detect "NoModel" — works whether it's string, enum, or missing
            model_type = getattr(m, "modelType", None)
            if model_type is None:
                continue

            # Convert to string safely
            mt_str = str(model_type).strip().upper()

            # Skip NoModel (used for power/GND pins with no buffer model)
            if mt_str in {"NOMODEL", "NO MODEL", "NONE", ""}:
                continue

            # Optional: also skip pure power/ground if you want (common)
            if m.modelName.upper() in {"POWER", "GND", "VCC", "VDD", "VSS"}:
                continue

            self.models_tree.insert("", "end", values=(
                m.modelName,
                self._model_type_str(m.modelType),
                f"{getattr(m.Vinl, 'typ', 'NA'):.3f}",
                f"{getattr(m.Vinh, 'typ', 'NA'):.3f}",
                f"{getattr(m.c_comp, 'typ', 'NA'):.4f}"
            ))

        # Pins
        for item in self.pins_tree.get_children():
            self.pins_tree.delete(item)
        for comp in self.ibis.cList:
            for pin in comp.pList:
                self.pins_tree.insert("", "end", values=(
                    pin.pinName, pin.signalName, pin.modelName,
                    f"{pin.R_pin:.4f}" if pin.R_pin != CS.NOT_USED else "",
                    f"{pin.L_pin:.4f}" if pin.L_pin != CS.NOT_USED else "",
                    f"{pin.C_pin:.4f}" if pin.C_pin != CS.NOT_USED else ""
                ))


    def _model_type_str(self, mt) -> str:
        """Convert any model type (int, enum, str) → proper IBIS string like 'I/O', 'Open_drain', etc."""
        from s2i_constants import ConstantStuff as CS

        # Full mapping — matches IBIS spec exactly
        mapping = {
            CS.ModelType.INPUT: "Input",
            CS.ModelType.OUTPUT: "Output",
            CS.ModelType.I_O: "I/O",
            CS.ModelType.SERIES: "Series",
            CS.ModelType.SERIES_SWITCH: "Series_switch",
            CS.ModelType.TERMINATOR: "Terminator",
            CS.ModelType.OPEN_DRAIN: "Open_drain",
            CS.ModelType.OPEN_SINK: "Open_sink",
            CS.ModelType.OPEN_SOURCE: "Open_source",
            CS.ModelType.IO_OPEN_DRAIN: "I/O_Open_drain",
            CS.ModelType.IO_OPEN_SINK: "I/O_Open_sink",
            CS.ModelType.IO_OPEN_SOURCE: "I/O_Open_source",
            CS.ModelType.OUTPUT_ECL: "Output_ECL",
            CS.ModelType.IO_ECL: "I/O_ECL",
            CS.ModelType.THREE_STATE: "3-state",
        }

        # 1. If it's already an enum → direct lookup
        if isinstance(mt, CS.ModelType):
            return mapping.get(mt, "Unknown")

        # 2. If it's an int → convert to enum
        if isinstance(mt, int):
            try:
                return mapping.get(CS.ModelType(mt), str(mt))
            except ValueError:
                return str(mt)

        # 3. If it's a string → try to parse
        if isinstance(mt, str):
            mt = mt.strip()
            if mt.isdigit():
                try:
                    return mapping.get(CS.ModelType(int(mt)), mt)
                except ValueError:
                    pass
            # Try direct match in mapping values
            for enum_val, name in mapping.items():
                if mt.replace(" ", "_").replace("/", "_").lower() == name.replace(" ", "_").lower():
                    return name
            return mt  # fallback

        return "Unknown"

    # ===================================================================
    # File Operations
    # ===================================================================
    def load_s2i(self):
        path = filedialog.askopenfilename(filetypes=[("S2I files", "*.s2i")])
        if not path: return
        self.input_file = path
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, path)

        try:
            parser = S2IParser()
            self.ibis, self.global_, self.mList = parser.parse(path)
            self.log("Loaded .s2i successfully", "INFO")
            self.populate_gui()
            save_session({"last_input": path, "last_outdir": self.outdir, "last_ibischk": self.ibischk_path})
        except Exception as e:
            messagebox.showerror("Parse Error", str(e))

    def save_s2i(self):
        if not self.ibis:
            messagebox.showwarning("No Data", "Nothing to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".s2i", filetypes=[("S2I files", "*.s2i")])
        if path:
            self.apply_gui_to_objects()
            try:
                with open(path, "w") as f:
                    writer = IbisWriter(ibis_head=self.ibis)
                    writer.write_s2i_file(f)  # assuming you have this method
                self.log(f"Saved .s2i → {Path(path).name}", "SUCCESS")
            except Exception as e:
                messagebox.showerror("Save Failed", str(e))

    def browse_outdir(self):
        d = filedialog.askdirectory()
        if d:
            self.outdir = d
            self.outdir_entry.delete(0, tk.END)
            self.outdir_entry.insert(0, d)

    def browse_ibischk(self):
        p = filedialog.askopenfilename(filetypes=[("EXE", "*.exe")])
        if p:
            self.ibischk_path = p
            self.ibischk_entry.delete(0, tk.END)
            self.ibischk_entry.insert(0, p)

    # ===================================================================
    # Simulation
    # ===================================================================
    def start_simulation(self):
        if not self.input_file or not self.outdir:
            messagebox.showerror("Missing", "Please set input file and output directory.")
            return

        self.apply_gui_to_objects()
        self.run_button.config(state="disabled")
        self.progress.start(8)
        self.start_time = datetime.now()
        self.status_var.set("Running conversion...")

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

        self.thread = threading.Thread(target=self.run_main, args=(argv,), daemon=True)
        self.thread.start()

    def run_main(self, argv):
        try:
            rc = s2ibispy_main(argv)
            elapsed = str(datetime.now() - self.start_time).split(".")[0]
            self.root.after(0, self.simulation_done, rc, elapsed)
        except Exception as e:
            self.root.after(0, self.simulation_done, -1, "0:00:00")

    def simulation_done(self, rc, elapsed):
        self.progress.stop()
        self.run_button.config(state="normal")
        if rc == 0:
            self.status_var.set(f"Success • Generated in {elapsed}")
            messagebox.showinfo("Success!", "IBIS model generated successfully!\nReady for signal integrity analysis.")
            self.load_ibs_output()
        else:
            self.status_var.set(f"Failed • RC={rc}")
            messagebox.showerror("Conversion Failed", f"Process exited with code {rc}\n\nCheck log for details.")

    def load_ibs_output(self):
        path = Path(self.outdir) / (Path(self.input_file).stem + ".ibs")
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.ibis_viewer.delete(1.0, tk.END)
            self.ibis_viewer.insert(tk.END, content)
            self.parse_ibis_sections(content)
            self.notebook.select(self.tab_viewer)
        else:
            self.log("No .ibs file found!", "ERROR")

    def parse_ibis_sections(self, content):
        lines = content.splitlines()
        self.section_tree.delete(*self.section_tree.get_children())
        current = ""
        for line in lines:
            if line.startswith("["):
                section = line.split()[0]
                iid = self.section_tree.insert("", "end", text=section)
                self.section_tree.set(iid, "line", len(self.section_tree.get_children(iid)))
            elif line.startswith("[Component]"):
                self.section_tree.insert("", "end", text="[Component]")
            elif line.startswith("[Model]"):
                name = line.split()[1] if len(line.split()) > 1 else "Unknown"
                self.section_tree.insert("", "end", text=f"[Model] {name}")
        # Simple jump
        def jump():
            sel = self.section_tree.selection()
            if not sel: return
            text = self.section_tree.item(sel[0])["text"]
            if text in content:
                pos = content.index(text)
                line_num = content.count("\n", 0, pos) + 1
                self.ibis_viewer.see(f"{line_num}.0")
        self.section_tree.bind("<Double-1>", lambda e: jump())

    def on_section_select(self, event):
        pass  # enhanced later

    def restore_session(self):
        s = self.session
        if s.get("last_input") and Path(s["last_input"]).exists():
            self.input_file = s["last_input"]
            self.input_entry.insert(0, self.input_file)
        if s.get("last_outdir"):
            self.outdir = s["last_outdir"]
            self.outdir_entry.insert(0, self.outdir)
        if s.get("last_ibischk"):
            self.ibischk_path = s["last_ibischk"]
            self.ibischk_entry.insert(0, self.ibischk_path)

    def log(self, msg, level="INFO"):
        logging.log(getattr(logging, level), msg)


# =======================================================================
# Run
# =======================================================================
if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.iconbitmap(str(PROJECT_ROOT / "resources" / "icon.ico"))
    except:
        pass
    app = S2IBISpyGUI(root)
    root.mainloop()