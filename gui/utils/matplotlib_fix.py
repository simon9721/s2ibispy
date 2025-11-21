# gui/utils/matplotlib_fix.py
import matplotlib
matplotlib.use('TkAgg')
matplotlib.set_loglevel("WARNING")  # Kills matplotlib debug

# KILL PIL/PNG DEBUG SPAM — THIS IS THE REAL FIX
import logging
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)

import matplotlib.pyplot as plt