# gui_main.py
#!/usr/bin/env python3
import tkinter as tk
from gui.app import S2IBISpyGUI
from pathlib import Path
from gui.utils.matplotlib_fix import plt  # Forces correct backend

if __name__ == "__main__":
    root = tk.Tk()
    
# Window icon — FINAL, CORRECT PATH
    icon_path = Path(__file__).parent / "resources" / "icons" / "s2ibispy.ico"
    if icon_path.exists():
        try:
            root.iconbitmap(str(icon_path))
        except Exception as e:
            print(f"Icon failed to load: {e}")
    else:
        print("Icon not found at:", icon_path)
    
    app = S2IBISpyGUI(root)
    root.mainloop()