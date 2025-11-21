# gui/tabs/input_tab.py
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import filedialog, messagebox  # ← Add messagebox here
from pathlib import Path

class InputTab:
    def __init__(self, notebook, gui):
        self.gui = gui
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="  Input & Settings  ")

        self.input_file = ""
        self.outdir = ""
        self.ibischk_path = ""

        self.build_ui()

    def build_ui(self):
        f = self.frame
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

        opts = ttk.LabelFrame(f, text=" Simulation Options ")
        opts.grid(row=r+1, column=0, columnspan=3, sticky="ew", padx=10, pady=15, ipadx=10, ipady=10)

        self.spice_type_var = tk.StringVar(value="hspice")
        ttk.Label(opts, text="SPICE Type:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ttk.Combobox(opts, textvariable=self.spice_type_var, values=["hspice", "spectre", "eldo"], state="readonly", width=12).grid(row=0, column=1, sticky="w", padx=10)

        self.iterate_var = tk.BooleanVar(value=False)
        self.cleanup_var = tk.BooleanVar(value=True)
        self.verbose_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(opts, text="Reuse existing SPICE data (--iterate)", variable=self.iterate_var).grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=3)
        ttk.Checkbutton(opts, text="Cleanup intermediate files", variable=self.cleanup_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=3)
        ttk.Checkbutton(opts, text="Verbose logging", variable=self.verbose_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=3)

    def load_s2i(self):
        path = filedialog.askopenfilename(filetypes=[("S2I files", "*.s2i")])
        if not path: return
        self.input_file = path
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, path)

        try:
            from parser import S2IParser
            parser = S2IParser()
            ibis, global_, mList = parser.parse(path)

            # Store data in GUI for other tabs
            self.gui.ibis = ibis
            self.gui.global_ = global_
            self.gui.mList = mList

            # Populate Models and Pins tabs
            self.gui.models_tab.populate(mList)
            self.gui.pins_tab.populate(ibis)

            
            real_models = [m for m in mList if str(getattr(m, "modelType", "")).strip().upper() not in {"NOMODEL", "NO MODEL", ""}]
            self.gui.log(f"Loaded .s2i: {Path(path).name} — {len(real_models)} model(s)", "INFO")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse .s2i:\n{e}")
            self.gui.log(f"Parse error: {e}", "ERROR")

    def browse_outdir(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(title="Select or Create Output Directory")
        if not d:
            return
        path = Path(d)
        try:
            path.mkdir(parents=True, exist_ok=True)  # ← Creates if not exists!
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