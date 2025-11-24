# gui/tabs/simulation_tab.py
import threading
from datetime import datetime
from tkinter import messagebox, ttk
from pathlib import Path
from main import main as run_conversion


class SimulationTab:
    def __init__(self, notebook, gui):
        self.gui = gui
        self.frame = ttk.Frame(notebook)
        # ←←← REMOVE notebook.add() — done in app.py ←←←

        ttk.Label(self.frame, text="Run SPICE → IBIS Conversion", font=("", 14, "bold")).pack(pady=40)

        self.run_button = ttk.Button(
            self.frame,
            text="Start Conversion",
            image=self.gui.icons.get("run"),
            compound="left",
            command=self.start
        )
        self.run_button.pack(pady=20)

        self.progress = ttk.Progressbar(self.frame, mode="indeterminate")
        self.progress.pack(fill="x", padx=120, pady=20)

    def start(self):
        input_tab = self.gui.input_tab

        if not input_tab.input_file:
            messagebox.showerror("Error", "Please select an input .s2i file first.")
            return
        if not input_tab.outdir:
            messagebox.showerror("Error", "Please set an output directory.")
            return

        self.run_button.config(state="disabled")
        self.progress.start(10)
        self.gui.status_var.set("Running SPICE → IBIS conversion...")
        self.gui.run_correlation_after_conversion = True

        # Build CLI args exactly like before
        argv = [
            input_tab.input_file,
            "--outdir", input_tab.outdir,
            "--spice-type", input_tab.spice_type_var.get(),
            "--iterate", "1" if input_tab.iterate_var.get() else "0",
            "--cleanup", "1" if input_tab.cleanup_var.get() else "0",
        ]
        if input_tab.ibischk_path:
            argv += ["--ibischk", input_tab.ibischk_path]
        if input_tab.verbose_var.get():
            argv.append("--verbose")
        if getattr(input_tab, "auto_outdir_var", None) and input_tab.auto_outdir_var.get():
            argv += ["--auto-outdir", "1"]

        #from main import main as run_conversion

        def thread_target():
            start_time = datetime.now()
            try:
                rc = run_conversion(argv, gui=self.gui)
                #print(f"DEBUG: main() returned → {rc}")  # ← Add this
                elapsed = str(datetime.now() - start_time).split(".")[0]
                self.gui.root.after(0, self.conversion_finished, rc, elapsed)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.gui.root.after(0, self.conversion_finished, -1, "0:00")

        threading.Thread(target=thread_target, daemon=True).start()

    def conversion_finished(self, rc: int, elapsed: str):
        self.progress.stop()
        self.run_button.config(state="normal")

        if rc == 0:
            # main() already set:
            # - self.gui.last_ibis_path = real path
            # - self.gui.analy = real analysis engine
            # - self.gui.ibis = real IBIS object

            self.gui.load_ibs_output()                     # 100% reliable now
            self.gui.notebook.select(self.gui.viewer_tab.frame)

            msg = (
                f"IBIS model generated successfully!\n"
                f"→ {self.gui.last_ibis_path.name}\n"
                f"Time: {elapsed}"
            )
            self.gui.log("Conversion completed!", "INFO")
            messagebox.showinfo("Success", msg)
            self.gui.status_var.set(f"Success • {elapsed}")


            msg = f"IBIS + correlation completed!\nTime: {elapsed}"
            messagebox.showinfo("Success", msg)
            self.gui.status_var.set(f"Complete • {elapsed}")

        else:
            self.gui.status_var.set(f"Failed (code {rc})")
            self.gui.log(f"Conversion failed with return code {rc}", "ERROR")
            messagebox.showerror("Failed", f"Conversion failed with return code {rc}")