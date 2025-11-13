# tests/test_output.py
import pytest
import sys
import os
import math
import re

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser import S2IParser
from s2iutil import S2IUtil
from s2ioutput import S2IOutput
from s2i_constants import ConstantStuff as CS

# Define project root for file paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_output_buffer():
    parser = S2IParser()
    ibis, global_ = parser.parse(os.path.join(PROJECT_ROOT, "tests", "buffer.s2i"))
    util = S2IUtil(parser.mList)
    util.complete_data_structures(ibis, global_)
    output = S2IOutput()
    output_file = os.path.join(PROJECT_ROOT, "tests", "buffer.ibs")
    output.write_ibis_file(ibis, global_, parser.mList, output_file)
    with open(output_file, 'r') as f:
        content = f.read()
    assert "[IBIS Ver] 3.2" in content
    assert "[File Name] buffer.ibs" in content
    assert "[Component] MCM Driver 1" in content
    assert "[Pin]" in content
    assert re.search(r"out\s+out\s+driver", content)  # Flexible spacing
    assert "[Model] driver" in content
    assert "[Model type] output" in content
    assert "[Rising Waveform]" in content
    assert "R_fixture = 500.0" in content
    assert "[Model] dummy" in content
    assert "[Model type] nomodel" in content

def test_output_ex3():
    parser = S2IParser()
    ibis, global_ = parser.parse(os.path.join(PROJECT_ROOT, "tests", "ex3.s2i"))
    util = S2IUtil(parser.mList)
    util.complete_data_structures(ibis, global_)
    output = S2IOutput()
    output_file = os.path.join(PROJECT_ROOT, "tests", "ex3.ibs")
    output.write_ibis_file(ibis, global_, parser.mList, output_file)
    with open(output_file, 'r') as f:
        content = f.read()
    assert "[IBIS Ver] 3.2" in content
    assert "[Component] Series MOSFET Test" in content
    assert re.search(r"1\s+pin1\s+series_model", content)
    assert "[Model] series_model" in content
    assert "[Model type] series_switch" in content
    assert "[On]" in content
    assert "[Off]" in content
    assert "[R Series] 1.000e+06 NA NA" in content
    assert "[Vds] 0.5" in content

def test_output_ex4():
    parser = S2IParser()
    ibis, global_ = parser.parse(os.path.join(PROJECT_ROOT, "tests", "ex4.s2i"))
    util = S2IUtil(parser.mList)
    util.complete_data_structures(ibis, global_)
    output = S2IOutput()
    output_file = os.path.join(PROJECT_ROOT, "tests", "ex4.ibs")
    output.write_ibis_file(ibis, global_, parser.mList, output_file)
    with open(output_file, 'r') as f:
        content = f.read()
    assert "[IBIS Ver] 3.2" in content
    assert "[Component] TriState Buffer" in content
    assert re.search(r"1\s+out\s+tri_model", content)
    assert "[Pin Mapping]" in content
    assert "pullup pulldown gnd_clamp power_clamp" in content
    assert "1 vdd1 gnd vdd1" in content
    assert "[Model] tri_model" in content
    assert "[Model type] 3-state" in content
    assert "[Enable] active-high" in content
    assert "[Model] en_model" in content
    assert "[Model type] input" in content
