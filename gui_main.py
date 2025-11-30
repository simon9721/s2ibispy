# gui_main.py
#!/usr/bin/env python3
import tkinter as tk
from gui.app import S2IBISpyGUI
from pathlib import Path
from gui.utils.matplotlib_fix import plt  # Forces correct backend
from gui.utils.splash import show_splash, hide_splash

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window during loading
    
    # Show splash screen
    splash = show_splash(root)
    
    # Window icon — FINAL, CORRECT PATH
    icon_path = Path(__file__).parent / "resources" / "icons" / "s2ibispy.ico"
    if icon_path.exists():
        try:
            root.iconbitmap(str(icon_path))
        except Exception as e:
            print(f"Icon failed to load: {e}")
    else:
        print("Icon not found at:", icon_path)
    
    # Initialize app (this may take time)
    app = S2IBISpyGUI(root)
    
    # Hide splash and show main window
    hide_splash(splash)
    root.deiconify()
    
    root.mainloop()