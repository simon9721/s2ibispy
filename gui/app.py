# gui/app.py
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import logging
from datetime import datetime
from .utils.session import load_session, save_session
from .tabs import (
    MainEntryTab,
    IbisViewerTab, PlotsTab, CorrelationTab
)

class S2IBISpyGUI:
    VERSION = "2.1.0"

    def __init__(self, root):
        self.root = root
        self.root.title(f"s2ibispy — SPICE to IBIS Converter v{self.VERSION}")
        # Adaptive sizing: 90% of screen, with sensible minimums
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            w = max(1200, int(sw * 0.9))
            h = max(750, int(sh * 0.9))
            # Center window
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
            self.root.geometry(f"{w}x{h}+{x}+{y}")
            self.root.minsize(1000, 700)
        except Exception:
            # Fallback defaults
            self.root.geometry("1450x960")
            self.root.minsize(1200, 750)

        # ←←← ADD THESE 3 LINES HERE ←←←
        self.ibis = None       # Will hold the parsed IbisTOP object
        self.global_ = None    # Will hold the global settings
        self.mList = []        # Will hold list of IbisModel objects
        # ←←← END OF NEW LINES ←←←
        self.analy = None
        
        self.icons = {
            "open": self.load_icon("open"),
            "run": self.load_icon("run"),
            "plot": self.load_icon("plot"),
            "popout": self.load_icon("popout"),
            "clear": self.load_icon("clear"),
        } 

        self.setup_theme()
        self.create_widgets()
        self.setup_logging()
        self.run_correlation_after_conversion = True  # default
      
        self.restore_session()
        self.last_ibis_path: Path | None = None   # ← Add this line in __init__

    def setup_theme(self):
        style = ttk.Style()
        try:
            style.theme_use("forest-dark")
        except:
            try: style.theme_use("equilux")
            except: style.theme_use("clam")

        style.configure("Treeview", rowheight=24, font=("Segoe UI", 10))
        style.configure("TNotebook.Tab", padding=(16, 10), font=("Segoe UI", 11, "bold"))

    def create_widgets(self):
        # 1. Main layout
        main_pane = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        # 2. Notebook
        self.notebook = ttk.Notebook(main_pane)
        main_pane.add(self.notebook, weight=4)

        # 3. CREATE ALL TABS FIRST
        self.main_tab = MainEntryTab(self.notebook, self)
        self.viewer_tab = IbisViewerTab(self.notebook, self)
        self.plots_tab = PlotsTab(self.notebook, self)
        self.corr_tab = CorrelationTab(self.notebook, self)

        # 4. NOW ADD TABS TO NOTEBOOK
        self.notebook.add(self.main_tab.frame, text="  🏠 Main  ")
        self.notebook.add(self.viewer_tab.frame, text="  📄 IBIS Viewer  ")
        self.notebook.add(self.plots_tab.frame, text="  📊 Plots  ")
        self.notebook.add(self.corr_tab.frame, text="  🔬 Correlation  ")

        # 5. NOW CREATE MENU — AFTER ALL TABS EXIST!
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="Load Input File",
            command=self.main_tab.load_input_file,
            image=self.icons.get("open"),
            compound="left",
            accelerator="Ctrl+O"
        )
            file_menu.add_command(
                label="Open IBIS (.ibs) in Viewer",
                command=lambda: self.viewer_tab.browse_and_load(),
                image=self.icons.get("open"),
                compound="left",
                accelerator="Ctrl+I"
            )
            file_menu.add_command(
                label="Open IBIS (.ibs) in Plots",
                command=lambda: self.plots_tab.browse_and_load_ibs(),
                image=self.icons.get("open"),
                compound="left",
                accelerator="Ctrl+P"
            )
            file_menu.add_command(
                label="Open Correlation (.tr0)",
                command=lambda: self.corr_tab.browse_and_load_tr0(),
                image=self.icons.get("open"),
                compound="left",
                accelerator="Ctrl+T"
            )
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=self.root.quit)

        # 6. Log panel
        log_frame = ttk.LabelFrame(main_pane, text=" Log Output ")
        main_pane.add(log_frame, weight=1)
        
        # Create frame to hold text and scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Add scrollbar
        log_scrollbar = ttk.Scrollbar(log_container)
        log_scrollbar.pack(side="right", fill="y")
        
        self.log_text = tk.Text(
            log_container, height=12, bg="#1e1e1e", fg="#d4d4d4",
            font=("Consolas", 10), insertbackground="white",
            yscrollcommand=log_scrollbar.set
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.config(command=self.log_text.yview)

        # 7. Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, padding=6)
        status.pack(side="bottom", fill="x")

        # 8. Shortcut
        self.root.bind("<Control-o>", lambda e: self.main_tab.load_input_file())
            self.root.bind("<Control-i>", lambda e: self.viewer_tab.browse_and_load())
            self.root.bind("<Control-p>", lambda e: self.plots_tab.browse_and_load_ibs())
            self.root.bind("<Control-t>", lambda e: self.corr_tab.browse_and_load_tr0())
    def setup_logging(self):
        self.log_text.tag_config("INFO", foreground="#88ff88")
        self.log_text.tag_config("WARNING", foreground="#ffff88")
        self.log_text.tag_config("ERROR", foreground="#ff8888")
        self.log_text.tag_config("SUCCESS", foreground="#88ffff", font=("Consolas", 10, "bold"))

        class LogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget  # ← Save reference

            def emit(self, record):
                msg = self.format(record)
                tag = "INFO"
                if record.levelno >= logging.ERROR: tag = "ERROR"
                elif record.levelno >= logging.WARNING: tag = "WARNING"
                elif "success" in msg.lower(): tag = "SUCCESS"

                def update():
                    self.text_widget.insert(tk.END, f"[{datetime.now():%H:%M:%S}] {msg}\n", tag)
                    self.text_widget.see(tk.END)
                self.text_widget.after(0, update)  # ← Thread-safe

        handler = LogHandler(self.log_text)
        handler.setFormatter(logging.Formatter("%(levelname)s → %(message)s"))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

    def log(self, msg, level="INFO"):
        logging.log(getattr(logging, level), msg)

    def load_ibs_output(self):
        """Called after successful conversion — loads IBIS into viewer + plots"""
        # Use the path set by CLI (already correct)
        if hasattr(self, "last_ibis_path") and self.last_ibis_path:
            ibs_path = self.last_ibis_path
        elif hasattr(self.main_tab, "input_file") and self.main_tab.input_file:
            # Fallback: calculate from input file (may be wrong for YAML with custom file_name)
            ibs_path = Path(self.main_tab.outdir) / (Path(self.main_tab.input_file).stem + ".ibs")
        else:
            return

        if not ibs_path.exists():
            self.log(f"No .ibs file found: {ibs_path}", "ERROR")
            return

        # Load into IBIS Viewer
        try:
            with open(ibs_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.viewer_tab.text.delete(1.0, tk.END)
            self.viewer_tab.text.insert(tk.END, content)
            self.viewer_tab.parse_sections(content)
            self.notebook.select(self.viewer_tab.frame)
            self.log(f"IBIS loaded: {ibs_path.name}", "INFO")
        except Exception as e:
            self.log(f"Failed to load IBIS viewer: {e}", "ERROR")

        # Load into Plots tab — THIS WAS BROKEN BEFORE
        try:
            self.plots_tab.load_ibs(ibs_path)
            self.log("Plots tab updated with new curves", "INFO")
        except Exception as e:
            self.log(f"Plots tab failed: {e}", "ERROR")

    def restore_session(self):
        s = load_session()
        if s.get("last_input") and Path(s["last_input"]).exists():
            self.main_tab.input_file = s["last_input"]
            self.main_tab.input_entry.insert(0, s["last_input"])
        if s.get("last_outdir"):
            self.main_tab.outdir = s["last_outdir"]
            self.main_tab.outdir_entry.insert(0, s["last_outdir"])
        if s.get("last_ibischk"):
            self.main_tab.ibischk_path = s["last_ibischk"]
            self.main_tab.ibischk_entry.insert(0, s["last_ibischk"])

    def load_icon(self, name):
        path = Path(__file__).parent.parent / "resources" / "icons" / f"{name}.png"
        try:
            return tk.PhotoImage(file=str(path))
        except:
            return None