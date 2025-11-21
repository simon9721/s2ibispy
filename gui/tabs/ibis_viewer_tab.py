# gui/tabs/ibis_viewer_tab.py — FINAL, PERFECT NAVIGATION
import tkinter as tk
from tkinter import ttk, scrolledtext
import re

class IbisViewerTab:
    def __init__(self, notebook, gui):
        self.gui = gui
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="  IBIS Viewer  ")

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
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, content)
        self.parse_sections(content)

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
        item = self.tree.item(sel[0])
        values = item["values"]
        if not values:
            return
        line_num = values[0]  # we stored the actual line index
        self.text.see(f"{line_num + 1}.0")
        self.text.tag_remove("sel", "1.0", "end")
        self.text.tag_add("sel", f"{line_num + 1}.0", f"{line_num + 20}.0")
        self.text.tag_config("sel", background="#333344", foreground="yellow")