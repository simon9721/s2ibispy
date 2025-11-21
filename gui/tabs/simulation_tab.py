# gui/tabs/simulation_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import threading
from datetime import datetime

class SimulationTab:
    def __init__(self, notebook, gui):
        self.gui = gui
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="  Simulation  ")

        ttk.Label(self.frame, text="Run SPICE to IBIS Conversion", font=("", 14, "bold")).pack(pady=40)
        self.run_button = ttk.Button(
            self.frame,
            text="Start Conversion",
            image=self.gui.icons["run"],
            compound="left",
            command=self.start
        )
        self.run_button.pack(pady=20)
        self.progress = ttk.Progressbar(self.frame, mode="indeterminate")
        self.progress.pack(fill="x", padx=120, pady=20)

    def start(self):
        input_tab = self.gui.input_tab
        if not input_tab.input_file or not input_tab.outdir:
            messagebox.showerror("Missing", "Please set input .s2i and output directory")
            return

        self.run_button.config(state="disabled")
        self.progress.start(8)
        self.gui.status_var.set("Running conversion...")

        from main import main as s2ibispy_main
        argv = [
            input_tab.input_file, "--outdir", input_tab.outdir,
            "--spice-type", input_tab.spice_type_var.get(),
            "--iterate", "1" if input_tab.iterate_var.get() else "0",
            "--cleanup", "1" if input_tab.cleanup_var.get() else "0",
        ]
        if input_tab.ibischk_path:
            argv += ["--ibischk", input_tab.ibischk_path]
        if input_tab.verbose_var.get():
            argv.append("--verbose")

        def run():
            start = datetime.now()
            try:
                rc = s2ibispy_main(argv)
                elapsed = str(datetime.now() - start).split(".")[0]
                self.gui.root.after(0, self.done, rc, elapsed)
            except Exception as e:
                self.gui.root.after(0, self.done, -1, "0:00")

        threading.Thread(target=run, daemon=True).start()

    def done(self, rc, elapsed):
        self.progress.stop()
        self.run_button.config(state="normal")
        if rc == 0:
            self.gui.status_var.set(f"Success • Generated in {elapsed}")
            messagebox.showinfo("Success", "IBIS model generated!")
            self.gui.load_ibs_output()
        else:
            self.gui.status_var.set(f"Failed • RC={rc}")
            messagebox.showerror("Failed", f"Conversion failed (RC={rc})")