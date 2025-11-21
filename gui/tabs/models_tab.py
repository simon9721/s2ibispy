# gui/tabs/models_tab.py
import tkinter as tk
from tkinter import ttk

class ModelsTab:
    def __init__(self, notebook, gui):
        self.gui = gui
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="  Models  ")

        self.tree = ttk.Treeview(
            self.frame,
            columns=("Name", "Type", "Vinl", "Vinh", "Ccomp"),
            show="headings", height=20
        )
        for col, w in zip(self.tree["columns"], [180, 140, 100, 100, 120]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def populate(self, models):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for m in models:
            mt_str = getattr(m, "modelType", None)
            if mt_str is None: continue
            if str(mt_str).strip().upper() in {"NOMODEL", "NO MODEL", "NONE", ""}:
                continue
            if m.modelName.upper() in {"POWER", "GND", "VCC", "VDD", "VSS"}:
                continue

            self.tree.insert("", "end", values=(
                m.modelName,
                self._model_type_str(mt_str),
                f"{getattr(m.Vinl, 'typ', 'NA'):.3f}",
                f"{getattr(m.Vinh, 'typ', 'NA'):.3f}",
                f"{getattr(m.c_comp, 'typ', 'NA'):.4f}"
            ))

    def _model_type_str(self, mt):
        mapping = {
            1: "Input", 2: "Output", 3: "I/O", 4: "Series", 5: "Series_switch",
            6: "Terminator", 7: "I/O_Open_drain", 8: "I/O_Open_sink",
            9: "Open_drain", 10: "Open_sink", 11: "Open_source",
            12: "I/O_Open_source", 13: "Output_ECL", 14: "I/O_ECL", 16: "3-state",
        }
        if isinstance(mt, (int, float)):
            return mapping.get(int(mt), f"Unknown({int(mt)})")
        if isinstance(mt, str):
            s = mt.strip().lower()
            rev_map = {v.lower().replace("/", "_").replace("-", "_"): v for k, v in mapping.items() if isinstance(k, int)}
            return rev_map.get(s, s.replace("_", " ").title())
        return "Unknown"