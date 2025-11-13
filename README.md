# SPICE → IBIS Converter (`s2ibis3`-style)

A lightweight, pure-Python pipeline that turns a **`.s2i` recipe** into a **valid `.ibs` IBIS model** using HSPICE, Spectre or ELDO.

No external dependencies – just Python 3.8+ and your simulator.

---

## Quick Start (less than or equal to 60 seconds)

```bash
# 1. Clone the repo
git clone https://github.com/your-username/s2ibis-converter.git
cd s2ibis-converter

# 2. (Optional) Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows PowerShell

# 3. Install dependencies (none required, but keeps workflow consistent)
pip install -r requirements.txt

# 4. Run the converter
python main.py path/to/your_recipe.s2i -o my_output
python main.py tests/buffer.s2i --outdir tests/output --spice-type hspice --iterate 1 --cleanup 0 --verbose
