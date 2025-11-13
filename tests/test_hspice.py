import pytest
import os
import shutil
from pathlib import Path
import sys
sys.path.append("C:\\Users\\sh3qm\\PycharmProjects\\s2ibispy")
from s2ispice import S2ISpice

# Setup paths
TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent


@pytest.fixture(scope="module", autouse=True)
def setup_test_dir():
    """Ensure test directory is clean."""
    yield
    for f in TEST_DIR.glob("*.out") + TEST_DIR.glob("*.msg") + TEST_DIR.glob("*.lis") + TEST_DIR.glob("hspice*"):
        try:
            f.unlink()
        except Exception:
            pass


@pytest.fixture
def s2i():
    """Initialize S2ISpice with real HSPICE."""
    s2i = S2ISpice(mList=[], spice_type=1, hspice_path="hspice")  # Assumes hspice in PATH
    s2i.allow_mock_fallback = False  # Disable mock fallback
    return s2i


@pytest.fixture
def spice_files():
    """Create valid and invalid SPICE input files."""
    valid_spice = TEST_DIR / "test_valid.spi"
    invalid_spice = TEST_DIR / "test_invalid.spi"

    valid_content = """
* Simple HSPICE Test
V1 1 0 DC 1
R1 1 0 1k
.DC V1 1 1 1
.PRINT DC V(1)
.END
"""
    invalid_content = """
* Invalid HSPICE Test
V1 1 0 DC 1
R1 1 0 1k
.DC INVALID 1 1 1
.END
"""

    valid_spice.write_text(valid_content)
    invalid_spice.write_text(invalid_content)

    yield valid_spice, invalid_spice

    # Cleanup
    for f in [valid_spice, invalid_spice]:
        if f.exists():
            f.unlink()


def test_call_spice_success(s2i, spice_files):
    """Test call_spice with a valid SPICE deck."""
    valid_spice, _ = spice_files
    spice_in = str(valid_spice)
    spice_out = str(TEST_DIR / "test_valid.out")
    spice_msg = str(TEST_DIR / "test_valid.msg")

    result = s2i.call_spice(
        iterate=0,
        spice_command="",  # Use default: hspice -i <in> -o <out>
        spice_in=spice_in,
        spice_out=spice_out,
        spice_msg=spice_msg
    )

    assert result == 0, f"call_spice should succeed for valid SPICE deck, got rc={result}"
    assert Path(spice_out).exists(), "Output file (.out) should be created"
    assert Path(spice_msg).exists(), "Message file (.msg) should be created"

    # Check for .lis file handling (HSPICE may produce .lis)
    lis_file = Path(spice_out.replace(".out", ".lis"))
    assert not lis_file.exists(), ".lis file should be renamed to .out"

    # Verify runner script exists
    is_windows = os.path.pathsep == ";"
    script_file = TEST_DIR / ("hspice_run.bat" if is_windows else "hspice.sh")
    assert script_file.exists(), "Runner script should be created"

    # Basic content check
    out_content = Path(spice_out).read_text()
    msg_content = Path(spice_msg).read_text()
    assert "hspice" in msg_content.lower(), "Message file should contain HSPICE output"
    assert "v(1)" in out_content.lower() or "1.0" in out_content, "Output file should contain simulation results"


def test_call_spice_failure(s2i, spice_files):
    """Test call_spice with an invalid SPICE deck."""
    _, invalid_spice = spice_files
    spice_in = str(invalid_spice)
    spice_out = str(TEST_DIR / "test_invalid.out")
    spice_msg = str(TEST_DIR / "test_invalid.msg")

    result = s2i.call_spice(
        iterate=0,
        spice_command="",
        spice_in=spice_in,
        spice_out=spice_out,
        spice_msg=spice_msg
    )

    assert result == 1, "call_spice should fail for invalid SPICE deck"
    assert Path(spice_msg).exists(), "Message file (.msg) should be created"
    assert not Path(spice_out).exists() or Path(
        spice_out).stat().st_size == 0, "Output file (.out) should not exist or be empty"

    # Check for error in .msg
    msg_content = Path(spice_msg).read_text()
    assert "error" in msg_content.lower(), "Message file should contain error information"


def test_call_spice_iterate(s2i, spice_files):
    """Test call_spice with iterate=1 and existing output."""
    valid_spice, _ = spice_files
    spice_in = str(valid_spice)
    spice_out = str(TEST_DIR / "test_valid.out")
    spice_msg = str(TEST_DIR / "test_valid.msg")

    # Run once to create output
    result = s2i.call_spice(
        iterate=0,
        spice_command="",
        spice_in=spice_in,
        spice_out=spice_out,
        spice_msg=spice_msg
    )
    assert result == 0, "Initial run should succeed"
    assert Path(spice_out).exists(), "Output file should be created"

    # Run again with iterate=1
    result = s2i.call_spice(
        iterate=1,
        spice_command="",
        spice_in=spice_in,
        spice_out=spice_out,
        spice_msg=spice_msg
    )

    assert result == 0, "call_spice should skip run with iterate=1 and existing output"
    assert Path(spice_out).exists(), "Output file should still exist"
    assert Path(spice_msg).exists(), "Message file should exist (from first run)"


if __name__ == "__main__":
    pytest.main(["-v", __file__])