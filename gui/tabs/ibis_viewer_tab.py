# gui/tabs/ibis_viewer_tab.py — FINAL, PERFECT NAVIGATION
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from pathlib import Path
import re

class IbisViewerTab:
    def __init__(self, notebook, gui):
        self.gui = gui
        self.frame = ttk.Frame(notebook)
        #notebook.add(self.frame, text="  IBIS Viewer  ")

        # Top controls
        controls = ttk.Frame(self.frame)
        controls.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(controls, text="Load IBIS (.ibs):").pack(side="left")
        self.path_var = tk.StringVar()
        entry = ttk.Entry(controls, textvariable=self.path_var, width=60)
        entry.pack(side="left", padx=6, fill="x", expand=True)
        ttk.Button(controls, text="Browse…", command=self.browse_and_load).pack(side="left")

        paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(paned, width=350)
        left.pack_propagate(False)
        paned.add(left, weight=1)

        ttk.Label(left, text=" IBIS Sections ", font=("", 10, "bold")).pack(side="top", fill="x", pady=(8,4))
        self.tree = ttk.Treeview(left, show="tree", selectmode="browse")
        self.tree.pack(fill="both", expand=True, padx=8, pady=4)

        self.text = scrolledtext.ScrolledText(paned, font=("Courier New", 10), wrap="none")
        paned.add(self.text, weight=4)

        self.tree.bind("<Double-1>", self.jump_to_section)

    def load_ibs(self, path):
        p = Path(path)
        if not p.exists():
            self.gui.log(f"IBIS file not found: {p}", "ERROR")
            return
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, content)
        self.parse_sections(content)
        self.path_var.set(str(p))
        # Also feed Plots tab if available
        try:
            self.gui.plots_tab.load_ibs(p)
        except Exception:
            pass

    def browse_and_load(self):
        file_path = filedialog.askopenfilename(
            title="Select IBIS file",
            filetypes=[("IBIS files", "*.ibs"), ("All files", "*.*")]
        )
        if file_path:
            self.load_ibs(file_path)

    def parse_sections(self, content):
        self.tree.delete(*self.tree.get_children())
        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("[") and "]" in line:
                header_match = re.match(r"\[(.+?)\](.*)", line)
                if not header_match:
                    i += 1
                    continue
                section_name = header_match.group(1).strip()
                tail = header_match.group(2).strip()

                # Look ahead for fixture parameters
                fixtures = {}
                j = i + 1
                while j < len(lines):
                    param_line = lines[j].strip()
                    if param_line.startswith("[") or not param_line or param_line.startswith("|"):
                        break
                    if "=" in param_line:
                        key, val = param_line.split("=", 1)
                        key = key.strip().lower()
                        val = val.strip()
                        if key in {"v_fixture", "v_fixture_min", "v_fixture_max", "r_fixture", "c_fixture"}:
                            fixtures[key] = val
                    j += 1

                # Build display name
                display_parts = [f"[{section_name}]"]
                if fixtures:
                    if "v_fixture" in fixtures:
                        display_parts.append(f"Vf={fixtures['v_fixture']}")
                    if "v_fixture_min" in fixtures and "v_fixture_max" in fixtures:
                        display_parts.append(f"Vf_min={fixtures['v_fixture_min']} Vf_max={fixtures['v_fixture_max']}")
                    if "r_fixture" in fixtures:
                        display_parts.append(f"Rf={fixtures['r_fixture']}")
                else:
                    if tail:
                        display_parts.append(tail)

                display_text = " ".join(display_parts)
                self.tree.insert("", "end", text=display_text, values=(i,))  # store line number
            i += 1

    def jump_to_section(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        values = self.tree.item(item, "values")
        if not values:
            return

        # ←←← FIX: Convert string back to int!
        try:
            line_num = int(values[0])
        except (ValueError, IndexError):
            return

        # Get full content once
        content = self.text.get("1.0", "end")
        lines = content.splitlines()

        # Find the actual [Section] line (skip blank lines/comments above)
        actual_line = line_num
        while actual_line > 0 and not lines[actual_line].lstrip().startswith("["):
            actual_line -= 1

        target_line = actual_line + 1  # Tkinter is 1-indexed
        target = f"{target_line}.0"

        # Jump to it
        self.text.see(target)

        # Highlight section
        self.text.tag_remove("sel", "1.0", "end")
        end_line = min(target_line + 15, len(lines))
        self.text.tag_add("sel", target, f"{end_line}.0")

        # Beautiful highlight
        self.text.tag_config(
            "sel",
            background="#2d2d42",
            foreground="#ffdd88",
            font=("Courier New", 10, "bold")
        )

        # Flash effect (feels premium)
        def flash():
            self.text.tag_config("sel", background="#3a3a55")
            self.text.after(120, lambda: self.text.tag_config("sel", background="#2d2d42"))
        self.text.after(60, flash)