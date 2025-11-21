# gui/tabs/pins_tab.py
from tkinter import ttk
from s2i_constants import ConstantStuff as CS

class PinsTab:
    def __init__(self, notebook, gui):
        self.gui = gui
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="  Pins  ")

        self.tree = ttk.Treeview(
            self.frame,
            columns=("Pin", "Signal", "Model", "Rpin", "Lpin", "Cpin"),
            show="headings"
        )
        for col, w in zip(self.tree["columns"], [80, 180, 160, 90, 90, 90]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def populate(self, ibis_top):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for comp in ibis_top.cList:
            for pin in comp.pList:
                self.tree.insert("", "end", values=(
                    pin.pinName,
                    pin.signalName,
                    pin.modelName,
                    f"{pin.R_pin:.4f}" if pin.R_pin != CS.NOT_USED else "",
                    f"{pin.L_pin:.4f}" if pin.L_pin != CS.NOT_USED else "",
                    f"{pin.C_pin:.4f}" if pin.C_pin != CS.NOT_USED else ""
                ))