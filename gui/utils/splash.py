# gui/utils/splash.py
import tkinter as tk
from PIL import Image, ImageTk
from pathlib import Path
import time

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# CONFIG: Change this to control minimum splash time
MINIMUM_SPLASH_TIME = 1.5   # seconds (1.5 is smooth and professional)
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

_start_time = None

def show_splash(root):
    global _start_time
    _start_time = time.time()

    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.configure(bg='#0a0a0a')

    width, height = 480, 480
    x = (splash.winfo_screenwidth() - width) // 2
    y = (splash.winfo_screenheight() - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")

    # Logo
    icon_path = Path(__file__).parent.parent.parent / "resources" / "icons" / "s2ibispy.png"
    try:
        img = Image.open(icon_path)
        img = img.resize((280, 280), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(splash, image=photo, bg='#0a0a0a', bd=0)
        label.image = photo
        label.pack(pady=(40, 20))
    except Exception as e:
        print(f"Splash icon load failed: {e}")
        tk.Label(splash, text="S2IBISpy", font=("Segoe UI", 36, "bold"),
                 fg="#00ffff", bg='#0a0a0a').pack(pady=(80, 20))

    tk.Label(splash, text="Loading, please wait...", font=("Segoe UI", 16),
             fg="#00ffff", bg='#0a0a0a').pack(pady=10)

    # Subtle pulse
    def pulse(alpha=255):
        if not splash.winfo_exists():
            return
        alpha = (alpha - 15) if alpha > 100 else 255
        splash.attributes("-alpha", alpha / 255)
        splash.after(50, pulse, alpha)
    splash.after(100, pulse)

    splash.update()
    return splash

def hide_splash(splash):
    if splash and splash.winfo_exists():
        # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
        # Enforce minimum display time
        # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
        elapsed = time.time() - _start_time
        if elapsed < MINIMUM_SPLASH_TIME:
            remaining = MINIMUM_SPLASH_TIME - elapsed
            time.sleep(remaining)  # Actually wait the remaining time
        splash.destroy()
        # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←