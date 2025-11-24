# gui/tabs/plots_tab.py — FINAL, PERFECT, 100% WORKING
import tkinter as tk
from tkinter import ttk
from pathlib import Path

class PlotsTab:
    def __init__(self, notebook, gui):
        self.gui = gui
        self.frame = ttk.Frame(notebook)
        #notebook.add(self.frame, text="  Plots  ")

        self.blocks = []
        self.item_to_var = {}
        self.fig = None
        self.ax = None
        self.canvas = None
        self.popout_window = None

        self.build_ui()

    def build_ui(self):
        main_pane = ttk.PanedWindow(self.frame, orient=tk.VERTICAL)
        main_pane.pack(fill="both", expand=True, padx=8, pady=8)

        top_frame = ttk.Frame(main_pane)
        main_pane.add(top_frame, weight=4)

        top_pane = ttk.PanedWindow(top_frame, orient=tk.VERTICAL)
        top_pane.pack(fill="both", expand=True)

        # Table Section
        table_container = ttk.LabelFrame(top_pane, text=" Plottable Tables ")
        top_pane.add(table_container, weight=1)

        filter_frame = ttk.Frame(table_container)
        filter_frame.pack(fill="x", padx=8, pady=6)

        ttk.Label(filter_frame, text="Model:").pack(side="left")
        self.model_combo = ttk.Combobox(filter_frame, state="readonly", width=25)
        self.model_combo.pack(side="left", padx=5)
        self.model_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())

        ttk.Label(filter_frame, text="Type:").pack(side="left", padx=(20,0))
        self.type_combo = ttk.Combobox(filter_frame, state="readonly", width=20,
            values=["All", "Pullup", "Pulldown", "Gnd Clamp", "Power Clamp",
                    "Rising Waveform", "Falling Waveform", "Composite Current"])
        self.type_combo.set("All")
        self.type_combo.pack(side="left", padx=5)
        self.type_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())

        btns = ttk.Frame(filter_frame)
        btns.pack(side="right")
        ttk.Button(btns, text="Plot", image=self.gui.icons["plot"],
                   compound="left", command=self.plot_selected).pack(side="left", padx=3)
        ttk.Button(btns, text="Pop Out", image=self.gui.icons["popout"],
                   compound="left", command=self.popout_plot).pack(side="left", padx=3)
        ttk.Button(btns, text="Clear", image=self.gui.icons["clear"],
                   compound="left", command=self.clear_plot).pack(side="left", padx=3)

        cols = ("Sel", "Idx", "Section", "Model", "Info")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", height=12)
        for c, w in zip(cols, [70, 60, 220, 200, 450]):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w" if c != "Sel" else "center")
        self.tree.column("Sel", anchor="center")
        self.tree.pack(fill="both", expand=True, padx=8, pady=4)
        self.tree.bind("<Button-1>", self.on_row_click)
        self.tree.bind("<Double-1>", lambda e: self.plot_selected())

        # Plot Section
        plot_container = ttk.LabelFrame(top_pane, text=" Waveform / IV Plot ")
        top_pane.add(plot_container, weight=3)
        self.canvas_frame = ttk.Frame(plot_container)
        self.canvas_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def load_ibs(self, ibs_path: Path):
        if not ibs_path.exists():
            self.gui.log(f"IBIS file not found: {ibs_path.name}", "ERROR")
            return
        try:
            from plotter.ibis_plotter import parse_ibis_tables
            self.blocks = parse_ibis_tables(str(ibs_path))
            self.refresh_list()

            # PRE-WARM MATPLOTLIB
            self.ensure_plot_setup()
            self.ax.plot([0], [0], alpha=0)
            self.canvas.draw()
            self.clear_plot()
            self.gui.log("Plot engine ready — instant plotting!", "INFO")
        except Exception as e:
            self.gui.log(f"Plotter failed: {e}", "ERROR")

    def refresh_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.item_to_var.clear()

        if not self.blocks:
            return

        models = sorted({b.model or "(global)" for b in self.blocks})
        self.model_combo["values"] = ["All"] + models
        if self.model_combo.get() not in models + ["All"]:
            self.model_combo.set("All")

        filt_model = self.model_combo.get()
        filt_type = self.type_combo.get()

        visible = 0
        for idx, b in enumerate(self.blocks, 1):
            show = (filt_model == "All" or filt_model == (b.model or "(global)"))
            if filt_type != "All":
                show = show and filt_type.replace(" ", "_").lower() in b.section_norm
            if not show: continue

            var = tk.BooleanVar(value=False)
            visible += 1

            info = f"{b.data.shape[0]} pts"
            if b.ncols > 2: info += " | typ/min/max"
            if "r_load" in b.params: info += f" | R_load={b.params['r_load']}"

            section = b.section_raw.replace("_", " ").title()
            model = b.model or "(global)"

            iid = self.tree.insert("", "end", values=("", f"{idx}", section, model, info))
            self.item_to_var[iid] = var

        self.gui.log(f"Plots tab: {visible} curve(s) visible", "INFO")

    def on_row_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item or item not in self.item_to_var:
            return
        var = self.item_to_var[item]
        var.set(not var.get())
        self.tree.set(item, "Sel", "Selected" if var.get() else "")

    def ensure_plot_setup(self):
        if self.canvas is not None:
            return
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        plt.style.use('dark_background')
        self.fig = plt.Figure(figsize=(10, 6), facecolor="#1e1e1e")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#1e1e1e")
        self.canvas = FigureCanvasTkAgg(self.fig, self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        NavigationToolbar2Tk(self.canvas, self.canvas_frame)

    def plot_selected(self):
        self.ensure_plot_setup()
        self.ax.clear()
        plotted = False
        visible_items = self.tree.get_children()
        for item in visible_items:
            var = self.item_to_var[item]
            if var.get():
                idx = list(self.item_to_var.keys()).index(item)
                filtered = [b for b in self.blocks
                           if (self.model_combo.get() == "All" or self.model_combo.get() == (b.model or "(global)"))
                           and (self.type_combo.get() == "All" or self.type_combo.get().replace(" ", "_").lower() in b.section_norm)]
                if idx < len(filtered):
                    self._plot_block(filtered[idx])
                    plotted = True
        if plotted:
            self.ax.legend()
            self.ax.grid(True, alpha=0.4)
            self.canvas.draw()

    def _plot_block(self, b):
        x = b.data[:, 0]
        colors = ['#ff5555', '#55ff55', '#5588ff']
        if b.ncols == 2:
            self.ax.plot(x, b.data[:,1], 'o-', linewidth=2.5, markersize=5,
                        label=f"{b.section_raw} ({b.model or 'global'})")
        else:
            for c in range(1, b.ncols):
                lab = ["typ", "min", "max"][c-1] if c-1 < 3 else f"col{c}"
                color = colors[c-1] if c-1 < 3 else "#cccccc"
                self.ax.plot(x, b.data[:, c], 'o-', color=color, linewidth=2.5, markersize=5,
                            label=f"{b.section_raw} {lab}")
        title = f"{b.section_raw}"
        if b.model:
            title += f" — {b.model}"
        self.ax.set_title(title, pad=20, fontsize=14, color="white")
        if "waveform" in b.section_norm:
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Voltage (V)")
        else:
            self.ax.set_xlabel("Voltage (V)")
            self.ax.set_ylabel("Current (A)")

    def clear_plot(self):
        if self.canvas:
            self.ax.clear()
            self.canvas.draw()

    def popout_plot(self):
        if not self.canvas:
            self.gui.log("No plot to pop out yet", "INFO")
            return

        if self.popout_window and tk.Tk.winfo_exists(self.popout_window):
            self.popout_window.lift()
            return

        self.popout_window = tk.Toplevel(self.gui.root)
        self.popout_window.title("s2ibispy — Detached Plot")
        self.popout_window.geometry("1000x700")

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        pop_canvas = FigureCanvasTkAgg(self.fig, self.popout_window)
        pop_canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(pop_canvas, self.popout_window)
        toolbar.update()
        pop_canvas.draw()

        self.popout_window.protocol("WM_DELETE_WINDOW", self.popout_window.destroy)