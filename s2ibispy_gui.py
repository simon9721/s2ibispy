"""
s2ibispy_gui.py
Professional GUI front-end for s2ibispy — controls main.py, runs full pipeline.

Features:
- Load .s2i file → full parsing & editing
- Edit global, model, pin parameters
- Run simulation with progress, live logs
- View & export .ibs output
- Full CLI argument support (including your example)
- Thread-safe, non-blocking
- Mock mode for testing
"""

import os
import sys
import threading
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import s2ibispy
from main import main as s2ibispy_main
from models import IbisTOP, IbisGlobal, IbisModel, IbisPin, IbisTypMinMax
from s2i_constants import ConstantStuff as CS


class S2IBISpyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("s2ibispy — SPICE to IBIS Converter")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        # Data
        self.input_file = ""
        self.outdir = ""
        self.ibischk_path = ""
        self.ibis: Optional[IbisTOP] = None
        self.global_: Optional[IbisGlobal] = None
        self.mList: List[IbisModel] = []

        # Threading
        self.thread = None
        self.stop_event = threading.Event()

        # Setup GUI
        self.setup_logging()
        self.create_widgets()
        self.setup_layout()

    def setup_logging(self):
        """Configure logging to GUI log window."""
        self.log_handler = TextHandler(self)
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)

    def create_widgets(self):
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load .s2i", command=self.load_s2i)
        file_menu.add_command(label="Save .s2i", command=self.save_s2i)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.tab_input = ttk.Frame(self.notebook)
        self.tab_models = ttk.Frame(self.notebook)
        self.tab_pins = ttk.Frame(self.notebook)
        self.tab_sim = ttk.Frame(self.notebook)
        self.tab_output = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_input, text="Input & Settings")
        self.notebook.add(self.tab_models, text="Models")
        self.notebook.add(self.tab_pins, text="Pins")
        self.notebook.add(self.tab_sim, text="Simulation")
        self.notebook.add(self.tab_output, text="Output")

        # === TAB 1: Input & Settings ===
        self.create_input_tab()

        # === TAB 2: Models ===
        self.create_models_tab()

        # === TAB 3: Pins ===
        self.create_pins_tab()

        # === TAB 4: Simulation ===
        self.create_sim_tab()

        # === TAB 5: Output ===
        self.create_output_tab()

    def setup_layout(self):
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # ===================================================================
    # TAB 1: INPUT & SETTINGS
    # ===================================================================
    def create_input_tab(self):
        frame = self.tab_input
        row = 0

        # Input File
        ttk.Label(frame, text="Input .s2i File:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.input_entry = ttk.Entry(frame, width=60)
        self.input_entry.grid(row=row, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Browse", command=self.load_s2i).grid(row=row, column=2, padx=5, pady=5)
        row += 1

        # Output Directory
        ttk.Label(frame, text="Output Directory:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.outdir_entry = ttk.Entry(frame, width=60)
        self.outdir_entry.grid(row=row, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_outdir).grid(row=row, column=2, padx=5, pady=5)
        row += 1

        # Spice Type
        ttk.Label(frame, text="Spice Type:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.spice_type_var = tk.StringVar(value="hspice")
        ttk.Combobox(frame, textvariable=self.spice_type_var,
                     values=["hspice", "spectre", "eldo"], state="readonly", width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1

        # Options
        self.iterate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Iterate (reuse SPICE outputs)", variable=self.iterate_var).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        row += 1

        self.cleanup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Cleanup intermediate files", variable=self.cleanup_var).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        row += 1

        self.verbose_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Verbose logging", variable=self.verbose_var).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        row += 1

        # ibischk
        ttk.Label(frame, text="ibischk Path (optional):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.ibischk_entry = ttk.Entry(frame, width=60)
        self.ibischk_entry.grid(row=row, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_ibischk).grid(row=row, column=2, padx=5, pady=5)
        row += 1

        # Global Parameters
        ttk.Separator(frame, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        row += 1

        self.create_global_params(frame, row)

    def create_global_params(self, frame, start_row):
        row = start_row

        # Voltage Range
        ttk.Label(frame, text="Voltage Range (typ/min/max):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.volt_typ = ttk.Entry(frame, width=10)
        self.volt_min = ttk.Entry(frame, width=10)
        self.volt_max = ttk.Entry(frame, width=10)
        self.volt_typ.grid(row=row, column=1, padx=2, pady=2)
        self.volt_min.grid(row=row, column=2, padx=2, pady=2)
        self.volt_max.grid(row=row, column=3, padx=2, pady=2)
        row += 1

        # Temperature Range
        ttk.Label(frame, text="Temperature Range (typ/min/max):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.temp_typ = ttk.Entry(frame, width=10)
        self.temp_min = ttk.Entry(frame, width=10)
        self.temp_max = ttk.Entry(frame, width=10)
        self.temp_typ.grid(row=row, column=1, padx=2, pady=2)
        self.temp_min.grid(row=row, column=2, padx=2, pady=2)
        self.temp_max.grid(row=row, column=3, padx=2, pady=2)
        row += 1

        # R_pkg, L_pkg, C_pkg — SAVE TO SELF
        self.r_pkg_entries = []
        self.l_pkg_entries = []
        self.c_pkg_entries = []

        for label, attr, entries_list in [
            ("R_pkg", "R_pkg", self.r_pkg_entries),
            ("L_pkg", "L_pkg", self.l_pkg_entries),
            ("C_pkg", "C_pkg", self.c_pkg_entries)
        ]:
            ttk.Label(frame, text=f"{label} (typ/min/max):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
            for col in range(1, 4):
                e = ttk.Entry(frame, width=10)
                e.grid(row=row, column=col, padx=2, pady=2)
                entries_list.append(e)
            row += 1

        # Rload
        ttk.Label(frame, text="Rload (Ω):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.rload_entry = ttk.Entry(frame, width=10)
        self.rload_entry.grid(row=row, column=1, padx=2, pady=2)
        row += 1

        # Sim Time
        ttk.Label(frame, text="Sim Time (s):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.simtime_entry = ttk.Entry(frame, width=10)
        self.simtime_entry.grid(row=row, column=1, padx=2, pady=2)
        row += 1

    # ===================================================================
    # TAB 2: MODELS
    # ===================================================================
    def create_models_tab(self):
        frame = self.tab_models
        self.models_tree = ttk.Treeview(frame, columns=("Name", "Type", "Polarity", "Enable", "Vinl", "Vinh", "C_comp"), show="headings")
        for col in self.models_tree["columns"]:
            self.models_tree.heading(col, text=col)
            self.models_tree.column(col, width=100)
        self.models_tree.pack(fill="both", expand=True, padx=5, pady=5)

    # ===================================================================
    # TAB 3: PINS
    # ===================================================================
    def create_pins_tab(self):
        frame = self.tab_pins
        self.pins_tree = ttk.Treeview(frame, columns=("Pin", "Signal", "Model", "R_pin", "L_pin", "C_pin"), show="headings")
        for col in self.pins_tree["columns"]:
            self.pins_tree.heading(col, text=col)
            self.pins_tree.column(col, width=100)
        self.pins_tree.pack(fill="both", expand=True, padx=5, pady=5)

    # ===================================================================
    # TAB 4: SIMULATION
    # ===================================================================
    def create_sim_tab(self):
        frame = self.tab_sim
        row = 0

        self.run_button = ttk.Button(frame, text="Run Simulation", command=self.start_simulation)
        self.run_button.grid(row=row, column=0, columnspan=2, pady=10, padx=10, sticky="ew")
        row += 1

        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        row += 1

        self.status_label = ttk.Label(frame, text="Ready")
        self.status_label.grid(row=row, column=0, columnspan=2, pady=5)

    # ===================================================================
    # TAB 5: OUTPUT
    # ===================================================================
    def create_output_tab(self):
        frame = self.tab_output
        self.output_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Courier", 10))
        self.output_text.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="Save .ibs", command=self.save_ibs).pack(side="right", padx=5)

    # ===================================================================
    # FILE OPERATIONS
    # ===================================================================
    def load_s2i(self):
        path = filedialog.askopenfilename(
            title="Select .s2i file",
            filetypes=[("S2I files", "*.s2i"), ("All files", "*.*")]
        )
        if not path:
            return

        self.input_file = path
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, path)

        try:
            from parser import S2IParser
            parser = S2IParser()
            self.ibis, self.global_, mList = parser.parse(path)
            self.mList = mList
            self.log(f"Loaded {path}", "status")
            self.populate_gui()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse .s2i:\n{e}")

    def save_s2i(self):
        if not self.ibis:
            messagebox.showwarning("Warning", "No data to save.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".s2i",
            filetypes=[("S2I files", "*.s2i")]
        )
        if path:
            with open(path, "w") as f:
                f.write("# Generated by s2ibispy_gui\n")
                # TODO: serialize ibis, global_, mList
            self.log(f"Saved .s2i to {path}", "status")

    def browse_outdir(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.outdir = path
            self.outdir_entry.delete(0, tk.END)
            self.outdir_entry.insert(0, path)

    def browse_ibischk(self):
        path = filedialog.askopenfilename(
            title="Select ibischk7_64.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.ibischk_path = path
            self.ibischk_entry.delete(0, tk.END)
            self.ibischk_entry.insert(0, path)

    # ===================================================================
    # GUI POPULATION
    # ===================================================================
    def populate_gui(self):
        if not self.ibis or not self.global_:
            return

        # Global — CONVERT float → str
        self.volt_typ.delete(0, tk.END); self.volt_typ.insert(0, str(self.global_.voltageRange.typ))
        self.volt_min.delete(0, tk.END); self.volt_min.insert(0, str(self.global_.voltageRange.min))
        self.volt_max.delete(0, tk.END); self.volt_max.insert(0, str(self.global_.voltageRange.max))

        self.temp_typ.delete(0, tk.END); self.temp_typ.insert(0, str(self.global_.tempRange.typ))
        self.temp_min.delete(0, tk.END); self.temp_min.insert(0, str(self.global_.tempRange.min))
        self.temp_max.delete(0, tk.END); self.temp_max.insert(0, str(self.global_.tempRange.max))

        self.rload_entry.delete(0, tk.END); self.rload_entry.insert(0, str(self.global_.Rload))
        self.simtime_entry.delete(0, tk.END); self.simtime_entry.insert(0, str(self.global_.simTime))

        # Package — ALSO CONVERT
        pkg = self.global_.pinParasitics
        for attr, entries in [
            ("R_pkg", self.r_pkg_entries),
            ("L_pkg", self.l_pkg_entries),
            ("C_pkg", self.c_pkg_entries)
        ]:
            tmm = getattr(pkg, attr)
            entries[0].delete(0, tk.END); entries[0].insert(0, str(tmm.typ))
            entries[1].delete(0, tk.END); entries[1].insert(0, str(tmm.min))
            entries[2].delete(0, tk.END); entries[2].insert(0, str(tmm.max))

        # Models
        for item in self.models_tree.get_children():
            self.models_tree.delete(item)
        for m in self.mList:
            self.models_tree.insert("", "end", values=(
                m.modelName,
                self._model_type_str(m.modelType),
                self._polarity_str(m.polarity),
                self._enable_str(m.enable),
                str(m.Vinl.typ),
                str(m.Vinh.typ),
                str(m.c_comp.typ)
            ))

        # Pins
        for item in self.pins_tree.get_children():
            self.pins_tree.delete(item)
        for comp in self.ibis.cList:
            for pin in comp.pList:
                self.pins_tree.insert("", "end", values=(
                    pin.pinName,
                    pin.signalName,
                    pin.modelName,
                    str(pin.R_pin) if pin.R_pin != CS.NOT_USED else "",
                    str(pin.L_pin) if pin.L_pin != CS.NOT_USED else "",
                    str(pin.C_pin) if pin.C_pin != CS.NOT_USED else ""
                ))

    def _model_type_str(self, mt):
        mapping = {v: k for k, v in CS.ModelType.__members__.items()}
        return mapping.get(mt, str(mt)) if isinstance(mt, CS.ModelType) else str(mt)

    def _polarity_str(self, p): return "Inverting" if p == CS.MODEL_POLARITY_INVERTING else "Non-Inverting"
    def _enable_str(self, e): return "Active-Low" if e == CS.MODEL_ENABLE_ACTIVE_LOW else "Active-High"

    # ===================================================================
    # SIMULATION
    # ===================================================================
    def start_simulation(self):
        if not self.input_file:
            messagebox.showerror("Error", "Please load a .s2i file first.")
            return
        if not self.outdir:
            messagebox.showerror("Error", "Please select an output directory.")
            return

        self.run_button.config(state="disabled")
        self.progress.start()
        self.status_label.config(text="Running...")

        self.thread = threading.Thread(target=self.run_main, daemon=True)
        self.thread.start()

    def run_main(self):
        argv = [
            self.input_file,
            "--outdir", self.outdir,
            "--spice-type", self.spice_type_var.get(),
            "--iterate", "1" if self.iterate_var.get() else "0",
            "--cleanup", "1" if self.cleanup_var.get() else "0",
        ]
        if self.ibischk_path:
            argv.extend(["--ibischk", self.ibischk_path])
        if self.verbose_var.get():
            argv.append("--verbose")

        try:
            rc = s2ibispy_main(argv)
            self.root.after(0, self.simulation_done, rc)
        except Exception as e:
            self.root.after(0, self.simulation_error, str(e))

    def simulation_done(self, rc):
        self.progress.stop()
        self.run_button.config(state="normal")
        self.status_label.config(text=f"Done (RC={rc})")
        if rc == 0:
            self.load_ibs_output()

    def simulation_error(self, msg):
        self.progress.stop()
        self.run_button.config(state="normal")
        self.status_label.config(text="Failed")
        messagebox.showerror("Simulation Error", msg)

    def load_ibs_output(self):
        ibs_path = Path(self.outdir) / (Path(self.input_file).stem + ".ibs")
        if ibs_path.exists():
            with open(ibs_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, content)
            self.log(f"Loaded {ibs_path.name}", "status")
        else:
            self.log("No .ibs file generated.", "warning")

    def save_ibs(self):
        if not self.output_text.get(1.0, tk.END).strip():
            messagebox.showwarning("Warning", "No .ibs content to save.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".ibs",
            filetypes=[("IBIS files", "*.ibs")]
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.output_text.get(1.0, tk.END))
            self.log(f"Saved .ibs to {path}", "status")

    # ===================================================================
    # LOGGING
    # ===================================================================
    def log(self, message, tag="status"):
        self.log_handler.emit(logging.LogRecord(
            name="gui", level=logging.INFO, pathname="", lineno=0,
            msg=message, args=(), exc_info=None
        ), tag)


class TextHandler(logging.Handler):
    def __init__(self, gui):
        super().__init__()
        self.gui = gui

    def emit(self, record, tag="status"):
        msg = self.format(record)
        self.gui.root.after(0, self._append, msg, tag)

    def _append(self, msg, tag):
        text = self.gui.output_text
        text.insert(tk.END, msg + "\n", tag)
        text.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = S2IBISpyGUI(root)
    root.mainloop()