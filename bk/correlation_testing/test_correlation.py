# test_correlation.py — FINAL, PERFECT VERSION
import os
import logging
from parser import S2IParser
from s2iutil import S2IUtil
from s2ianaly import S2IAnaly
from s2ioutput import IbisWriter
from correlation import generate_and_run_correlation, find_model_for_correlation

logging.basicConfig(level=logging.INFO)

# === CONFIG ===
s2i_file = "buffer_sp_files/io_buf.s2i"  # your real file
outdir = "out_test"
os.makedirs(outdir, exist_ok=True)

# 1. Parse
parser = S2IParser()
ibis, global_, mList = parser.parse(s2i_file)

# Critical: attach models to ibis
ibis.mList = mList

# 2. Complete data structures
util = S2IUtil(mList)
util.complete_data_structures(ibis, global_)

# 3. Run golden extraction
analy = S2IAnaly(
    mList=mList,
    spice_type=0,
    iterate=1,
    cleanup=0,
    spice_command="",
    global_=global_,
    outdir=outdir,
    s2i_file=s2i_file,
)

rc = analy.run_all(ibis, global_)
if rc != 0:
    print("Golden analysis failed")
    exit(1)

# === WRITE .ibs USING THE REAL FILENAME FROM THE TOOL ===
# ibis.thisFileName is already set correctly by the parser!
ibis_filename = ibis.thisFileName or "unknown.ibs"
ibis_path = os.path.join(outdir, ibis_filename)

writer = IbisWriter(ibis_head=ibis)
writer.write_ibis_file(ibis_path)

logging.info(f"IBIS file written: {ibis_path}")
logging.info(f"ibis.thisFileName = {ibis.thisFileName}")

# === PRESERVE ABSOLUTE SPICE PATH (from golden extraction) ===
for comp in ibis.cList:
    for pin in comp.pList:
        if pin.model and pin.model.spice_file:
            # Use the path that was resolved during golden runs
            if not os.path.isabs(pin.model.spice_file):
                candidate = os.path.join(os.path.dirname(s2i_file), pin.model.spice_file)
                if os.path.exists(candidate):
                    pin.model.spice_file = os.path.abspath(candidate)
            else:
                pin.model.spice_file = os.path.abspath(pin.model.spice_file)
            logging.info(f"Ensured absolute spice_file: {pin.model.spice_file}")

# === Run correlation ===
model = find_model_for_correlation(ibis)
if not model:
    print("No valid model found for correlation")
    exit(1)

print(f"Running correlation for model: {model.modelName}")
generate_and_run_correlation(
    model=model,
    ibis=ibis,
    outdir=outdir,
    s2ispice=analy.spice,
    config={"pattern": "101"}
)