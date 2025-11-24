# gui/tabs/correlation_tab.py
# Correlation runs automatically — this tab only displays results

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class CorrelationTab:
    def __init__(self, notebook, gui):
        self.gui = gui
        self.frame = ttk.Frame(notebook)
        self.waveforms = {}
        self.selected = {}
        self.fig = None
        self.ax = None
        self.canvas = None
        self.popout = None

        self.build_ui()
        # Auto-load when tab becomes visible
        self.frame.bind("<Visibility>", lambda e: self.load_latest_results())

    def build_ui(self):
        main_pane = ttk.PanedWindow(self.frame, orient=tk.VERTICAL)
        main_pane.pack(fill="both", expand=True, padx=8, pady=8)

        # Header
        header = ttk.Frame(main_pane)
        main_pane.add(header, weight=0)

        ttk.Label(
            header,
            text="Correlation runs automatically after conversion",
            foreground="#00ff88",
            font=("", 11, "bold")
        ).pack(pady=12)

        btns = ttk.Frame(header)
        btns.pack(pady=4)

        ttk.Button(btns, text="Refresh", image=self.gui.icons.get("refresh"),
                   compound="left", command=self.load_latest_results).pack(side="left", padx=4)
        ttk.Button(btns, text="Plot", image=self.gui.icons["plot"],
                   compound="left", command=self.plot_selected).pack(side="left", padx=4)
        ttk.Button(btns, text="Pop Out", image=self.gui.icons["popout"],
                   compound="left", command=self.popout_plot).pack(side="left", padx=4)
        ttk.Button(btns, text="Clear", image=self.gui.icons["clear"],
                   compound="left", command=self.clear_plot).pack(side="left", padx=4)

        # Waveform list
        list_frame = ttk.LabelFrame(main_pane, text=" Correlation Waveforms ")
        main_pane.add(list_frame, weight=1)

        cols = ("Sel", "Signal", "Points", "Min (V)", "Max (V)")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=14)
        for c, w in zip(cols, [60, 300, 100, 110, 110]):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center" if c == "Sel" else "w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=6)
        self.tree.bind("<Button-1>", self.on_tree_click)

        # Plot
        plot_frame = ttk.LabelFrame(main_pane, text=" SPICE vs IBIS Correlation ")
        main_pane.add(plot_frame, weight=4)
        self.canvas_frame = ttk.Frame(plot_frame)
        self.canvas_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def run_correlation(self):
        """Kept for compatibility — correlation is automatic"""
        self.gui.log("Correlation already ran automatically after conversion", "INFO")
        self.load_latest_results()

    def load_latest_results(self):
        outdir = Path(self.gui.input_tab.outdir)
        tr0_files = list(outdir.glob("compare_*.tr0"))
        if not tr0_files:
            self.gui.log("No correlation results yet — run conversion first", "INFO")
            self.waveforms.clear()
            self.refresh_tree()
            return

        latest = max(tr0_files, key=lambda p: p.stat().st_mtime)
        self.load_tr0(latest)

    def load_tr0(self, path: Path):
        from gui.utils.tr0_reader import parse_tr0_file
        try:
            self.waveforms = parse_tr0_file(path)
            self.refresh_tree()
            self.gui.log(f"Loaded correlation: {path.name} ({len(self.waveforms)} signals)", "INFO")
        except Exception as e:
            self.gui.log(f"Failed to load {path.name}: {e}", "ERROR")

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.selected.clear()

        if not self.waveforms:
            return

        for name, (t, v) in sorted(self.waveforms.items()):
            var = tk.BooleanVar(value="spice" in name.lower())
            mins = f"{v.min():.4f}"
            maxs = f"{v.max():.4f}"
            iid = self.tree.insert("", "end", values=(
                "Check" if var.get() else "", name, len(v), mins, maxs
            ))
            self.selected[iid] = var

    def on_tree_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item or self.tree.identify_column(event.x) != "#1":
            return
        var = self.selected[item]
        var.set(not var.get())
        self.tree.set(item, "Sel", "Check" if var.get() else "")

    def ensure_canvas(self):
        if self.canvas:
            return
        plt.style.use('dark_background')
        self.fig = plt.Figure(figsize=(10, 6), facecolor="#1e1e1e")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#1e1e1e")
        self.canvas = FigureCanvasTkAgg(self.fig, self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        NavigationToolbar2Tk(self.canvas, self.canvas_frame)

    def plot_selected(self):
        self.ensure_canvas()
        self.ax.clear()

        plotted = False
        for iid, var in self.selected.items():
            if var.get():
                name = self.tree.item(iid)["values"][1]
                t, v = self.waveforms[name]
                style = '-' if "spice" in name.lower() else '--'
                color = '#ff6b6b' if "spice" in name.lower() else '#4ecdc4'
                label = name.replace("_spice", " (SPICE)").replace("_ibis", " (IBIS)")
                self.ax.plot(t * 1e9, v, style, linewidth=2.5, label=label)
                plotted = True

        if plotted:
            self.ax.set_xlabel("Time (ns)")
            self.ax.set_ylabel("Voltage (V)")
            self.ax.set_title("SPICE vs IBIS Correlation")
            self.ax.legend(fontsize=10)
            self.ax.grid(True, alpha=0.3)
            self.canvas.draw()

    def clear_plot(self):
        if self.canvas:
            self.ax.clear()
            self.canvas.draw()

    def popout_plot(self):
        if not self.canvas:
            return
        if self.popout and self.popout.winfo_exists():
            self.popout.lift()
            return
        self.popout = tk.Toplevel(self.gui.root)
        self.popout.title("Correlation — Full View")
        self.popout.geometry("1400x900")
        canvas = FigureCanvasTkAgg(self.fig, self.popout)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        NavigationToolbar2Tk(canvas, self.popout)
        canvas.draw()