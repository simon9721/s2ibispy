#!/usr/bin/env python3
"""
demo_real_hspice.py
Run a real HSPICE-backed demo through S2IAnaly/S2ISpice.

Usage:
  python demo_real_hspice.py
  python demo_real_hspice.py --hspice hspice
  python demo_real_hspice.py --hspice "C:\\Synopsys\\Hspice\\bin\\hspice.exe"
"""

import argparse
import os
import sys
import subprocess
from glob import glob

# --- Project imports (assumes running from repo root) ---
from s2i_constants import ConstantStuff as CS
from s2ispice import S2ISpice
from s2ianaly import S2IAnaly
from models import (
    IbisModel, IbisPin, IbisComponent, IbisTOP, IbisGlobal,
    IbisVItable, IbisWaveTable, IbisTypMinMax
)


def ensure_buffer_cell(path: str) -> None:
    """Create a minimal 'buffer.sp' if it doesn't exist."""
    if os.path.exists(path):
        return
    contents = """* buffer.sp — minimal static "driver"
* Node order: OUT VDD 0
.subckt bufcell OUT VDD 0
* Simple resistive pullup/pulldown so DC & TRAN work
RPU OUT VDD 1k
RPD OUT 0   2k
.ends bufcell
"""
    with open(path, "w", newline="\n") as f:
        f.write(contents)
    print(f"[create] {path}")


def write_smoke_deck(path: str) -> None:
    """Tiny deck to prove hspice runs via call_spice."""
    contents = """* hello.spi — trivial run
V1 out 0 DC 1.2
R1 out 0 1k
.op
.end
"""
    with open(path, "w", newline="\n") as f:
        f.write(contents)
    print(f"[create] {path}")


def print_table_samples(title: str, vi: IbisVItable, k: int = 3) -> None:
    n = 0 if (not vi or vi.size is None) else vi.size
    print(f"{title}: size={n}")
    if not vi or n <= 0:
        return
    take = min(k, n)
    for i in range(take):
        e = vi.VIs[i]
        print(f"  [{i:02d}] V={e.v:.4g}  I_typ={e.i.typ:.4g}  I_min={e.i.min:.4g}  I_max={e.i.max:.4g}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Real HSPICE demo runner")
    ap.add_argument("--hspice", default="hspice", help="Path or name of the HSPICE executable")
    ap.add_argument("--workdir", default="demo_runs", help="Working directory to write decks/outputs")
    ap.add_argument("--spfile", default="buffer.sp", help="Buffer cell SPICE file")
    args = ap.parse_args()

    os.makedirs(args.workdir, exist_ok=True)
    os.chdir(args.workdir)

    # 1) Check HSPICE availability
    print(f"[check] invoking: {args.hspice} -v")
    try:
        vout = subprocess.run([args.hspice, "-v"], capture_output=True, text=True, timeout=15)
        print("[ok] HSPICE version banner/snippet:")
        print("-----")
        print((vout.stdout or vout.stderr).strip().splitlines()[0])
        print("-----")
    except Exception as e:
        print(f"[fail] Could not execute HSPICE: {e}")
        return 2

    # 2) Ensure buffer.sp exists (simple bufcell)
    ensure_buffer_cell(args.spfile)

    # 3) Smoke test through call_spice
    smoke_spi = "hello.spi"
    smoke_out = "hello.out"
    smoke_msg = "hello.msg"
    write_smoke_deck(smoke_spi)

    s = S2ISpice(mList=[], hspice_path=args.hspice)
    rc = s.call_spice(
        iterate=0,
        spice_command="",     # use default -i/-o form
        spice_in=smoke_spi,
        spice_out=smoke_out,
        spice_msg=smoke_msg,
    )
    print(f"[smoke] call_spice RC={rc}")
    if rc != 0 or not os.path.exists(smoke_out):
        print("[warn] Smoke test did not produce .out as expected (check .msg). Continuing…")
    else:
        print("[ok] Smoke .out present")

    # 1) Model
    m = IbisModel(modelName="BUF", modelType=CS.ModelType.OUTPUT)
    m.voltageRange = IbisTypMinMax(typ=3.3, min=3.0, max=3.6)
    m.simTime = 5e-9  # short transient so HSPICE returns quickly

    # 2) Pins (IMPORTANT: include POWER and GND)
    pin_out = IbisPin(pinName="OUT", spiceNodeName="OUT", modelName="BUF")
    pin_vcc = IbisPin(pinName="VCC", spiceNodeName="VCC", modelName="POWER")
    pin_gnd = IbisPin(pinName="VSS", spiceNodeName="0", modelName="GND")  # HSPICE ground node is "0"

    # 3) Component
    component = IbisComponent(component="DEMO")
    component.spiceFile = "buffer.sp"  # your buffer netlist used for VI/ramp/wave
    component.hasPinMapping = False  # simple fallback: first POWER/GND are used
    component.pList = [pin_out, pin_vcc, pin_gnd]

    # 4) IBIS top + globals
    ibis = IbisTOP()
    ibis.cList = [component]

    global_ = IbisGlobal()
    global_.voltageRange = IbisTypMinMax(typ=3.3, min=3.0, max=3.6)
    global_.simTime = 5e-9

    global_ = IbisGlobal()
    # Give reasonable rails so analysis isn’t NaN
    global_.voltageRange.typ = 3.3
    global_.voltageRange.min = 3.0
    global_.voltageRange.max = 3.6
    # Optional: shorten sim time a bit for the demo
    m.simTime = 5e-9

    analy = S2IAnaly(
        mList=[m],
        spice_type=CS.SpiceType.HSPICE,
        iterate=0,
        cleanup=0,
        spice_command="",     # let S2ISpice pick defaults
    )

    print("[run] S2IAnaly.run_all → real HSPICE")
    rc2 = analy.run_all(ibis, global_)
    print(f"[done] run_all RC={rc2}")

    # 5) Summarize: VI tables + Ramp
    print_table_samples("Pullup", getattr(m, "pullup", None))
    print_table_samples("Pulldown", getattr(m, "pulldown", None))

    if getattr(m, "ramp", None):
        r = m.ramp
        print("Ramp:")
        print(f"  dv_r typ/min/max = {getattr(r.dv_r, 'typ', float('nan')):.4g} / "
              f"{getattr(r.dv_r, 'min', float('nan')):.4g} / {getattr(r.dv_r, 'max', float('nan')):.4g}")
        print(f"  dt_r typ/min/max = {getattr(r.dt_r, 'typ', float('nan')):.4g} / "
              f"{getattr(r.dt_r, 'min', float('nan')):.4g} / {getattr(r.dt_r, 'max', float('nan')):.4g}")
        print(f"  dv_f typ/min/max = {getattr(r.dv_f, 'typ', float('nan')):.4g} / "
              f"{getattr(r.dv_f, 'min', float('nan')):.4g} / {getattr(r.dv_f, 'max', float('nan')):.4g}")
        print(f"  dt_f typ/min/max = {getattr(r.dt_f, 'typ', float('nan')):.4g} / "
              f"{getattr(r.dt_f, 'min', float('nan')):.4g} / {getattr(r.dt_f, 'max', float('nan')):.4g}")

    # 6) List artifacts to show audience
    print("\n[artifacts] .spi/.out/.msg generated here:")
    for pat in ("*.spi", "*.out", "*.msg", "*.lis", "*.st0"):
        files = sorted(glob(pat))
        if files:
            print(f"  {pat}:")
            for f in files:
                print(f"    - {f}")

    # Exit nonzero only if analyzer failed hard
    return 0 if rc2 == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
