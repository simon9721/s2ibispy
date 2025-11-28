"""Package copy of s2i_constants (complete)."""
from enum import IntEnum
import re


class ConstantStuff:
    # ---------------------------
    # Version / general limits
    # ---------------------------
    MAX_PIN_MAPPING_NAME_LENGTH = None
    MAX_PACKAGE_MODEL_NAME_LENGTH = None
    IS_USE_NA = -999.0


    IBIS_PRINT_WIDTH = 60


    SI_SUFFIX_STRING = ["f", "p", "n", "u", "m", "", "k", "M", "G"]
    VERSION_STRING = "3.2"

    # Sentinels (match legacy Java behavior + Python NaN)
    USE_NA = float('nan')
    NOT_USED = -1.33287736222333e18  # used for per-pin parasitics when absent

    FILENAME_EXTENSION = "ibs"
    MAX_FILENAME_BASE_LENGTH = 20        # manual: 20 (historically 8 for DOS; s2ibis3 uses 20)
    MAX_LINE_LENGTH = 80                 # IBIS line length recommendation
    MAX_IBIS_STRING_LENGTH = 1024
    MAX_TABLE_SIZE = 100                 # IBIS 1.x restriction
    MAX_WAVEFORM_TABLES = 100
    MAX_SERIES_TABLES = 100

    MAX_COMPONENT_NAME_LENGTH = 40
    MAX_PIN_NAME_LENGTH = 5              # manual: 5
    MAX_SIGNAL_NAME_LENGTH = 20
    MAX_MODEL_NAME_LENGTH = 20
    MAX_FILE_REV_LENGTH = 4

    # ---------------------------
    # Analysis defaults (manual)
    # ---------------------------
    LIN_RANGE_DEFAULT = 5.0
    SWEEP_STEP_DEFAULT = 0.01            # per s2iHeader.java rev note
    DIODE_DROP_DEFAULT = 1.0             # manual: 1.0 V
    ECL_TERMINATION_VOLTAGE_DEFAULT = -2.0
    WAVE_POINTS_DEFAULT = 100

    # Global/component defaults (manual)
    RLOAD_DEFAULT = 50
    C_COMP_DEFAULT = 5e-12
    TEMP_TYP_DEFAULT = 27
    TEMP_MIN_DEFAULT = 100
    TEMP_MAX_DEFAULT = 0
    VOLTAGE_RANGE_TYP_DEFAULT = 5.0
    VOLTAGE_RANGE_MIN_DEFAULT = 4.5
    VOLTAGE_RANGE_MAX_DEFAULT = 5.5
    SIM_TIME_DEFAULT = 10e-9
    DERATE_VI_PCT_DEFAULT = 0
    DERATE_RAMP_PCT_DEFAULT = 0
    CLAMP_TOLERANCE_DEFAULT = 0
    R_SERIES_DEFAULT = 1e6
    ECL_SWEEP_RANGE_DEFAULT = 2.0  # reasonable default; tune if needed

    # HSPICE formatting
    HSPICE_INGOLD_DEFAULT = 2

    NUM_PTS_LINEAR_REGION = 10

    # ---------------------------
    # SPICE types and defaults
    # ---------------------------
    class SpiceType(IntEnum):
        HSPICE = 0
        PSPICE = 1
        SPICE2 = 2
        SPICE3 = 3
        SPECTRE = 4
        ELDO = 5

    SPICE_TYPE_DEFAULT = SpiceType.HSPICE

    # Default commands for simulators (rough emulation of s2iHeader.java)
    DEFAULT_SPICE_CMD = {
        SpiceType.HSPICE: "hspice {in} >{out}",  # 2>{msg} (optional)
        SpiceType.PSPICE: "pspice {in} {out} /D0",
        SpiceType.SPICE2: "spice {in} {out}",
        SpiceType.SPICE3: "spice3 -b {in} >{out} 2>{msg}",
        SpiceType.SPECTRE: "spectre -f nutascii -c 132 {in} -r {out} >{msg}",
        SpiceType.ELDO: "eldo -b -i {in} -o {out} -silent",
    }

    # ---------------------------
    # Model types (subset aligned to your code)
    # ---------------------------
    class ModelType(IntEnum):
        I_O = 3
        INPUT = 1
        OUTPUT = 2
        IO = 3
        SERIES = 4
        SERIES_SWITCH = 5
        TERMINATOR = 6
        IO_OPEN_DRAIN = 7
        IO_OPEN_SINK = 8
        OPEN_DRAIN = 9
        OPEN_SINK = 10
        OPEN_SOURCE = 11
        IO_OPEN_SOURCE = 12
        OUTPUT_ECL = 13
        IO_ECL = 14
        INPUT_ECL = 15  # <- add this
        THREE_STATE = 16

    # ---------------------------
    # Curve types
    # ---------------------------
    class CurveType(IntEnum):
        PULLUP = 1
        PULLDOWN = 2
        POWER_CLAMP = 3
        GND_CLAMP = 4
        SERIES_VI = 5
        RISING_RAMP = 6
        FALLING_RAMP = 7
        RISING_WAVE = 8
        FALLING_WAVE = 9
        DISABLED_PULLUP = 10
        DISABLED_PULLDOWN = 11
        ISSO_PULLUP = 12
        ISSO_PULLDOWN = 13

    curve_name_string = {
        CurveType.PULLUP: "pullup",
        CurveType.PULLDOWN: "pulldown",
        CurveType.POWER_CLAMP: "power_clamp",
        CurveType.GND_CLAMP: "gnd_clamp",
        CurveType.SERIES_VI: "series_vi",
        CurveType.RISING_RAMP: "rising_ramp",
        CurveType.FALLING_RAMP: "falling_ramp",
        CurveType.RISING_WAVE: "rising_wave",
        CurveType.FALLING_WAVE: "falling_wave",
        CurveType.DISABLED_PULLUP: "pullup_disabled",
        CurveType.DISABLED_PULLDOWN: "pulldown_disabled",
        CurveType.ISSO_PULLUP:     "isso_pullup",
        CurveType.ISSO_PULLDOWN:   "isso_puldown",
    }

    # ---------------------------
    # Simulation cases (manual)
    # ---------------------------
    TYP_CASE = 0
    MIN_CASE = -1
    MAX_CASE = 1
    CASE_LABELS = {TYP_CASE: "typ", MIN_CASE: "min", MAX_CASE: "max"}

    # ---------------------------
    # Polarity / enable text
    # ---------------------------
    MODEL_POLARITY_INVERTING = "inverting"
    MODEL_POLARITY_NON_INVERTING = "non_inverting"
    MODEL_ENABLE_ACTIVE_HIGH = "active_high"
    MODEL_ENABLE_ACTIVE_LOW = "active_low"

    # ---------------------------
    # Output/enable state flags
    # ---------------------------
    ENABLE_OUTPUT = 1
    OUTPUT_RISING = 1
    OUTPUT_FALLING = 0

    # ---------------------------
    # File name prefixes (kept consistent with your flow)
    # ---------------------------
    spice_file_min_prefix = {
        CurveType.PULLUP: "pun",
        CurveType.PULLDOWN: "pdn",
        CurveType.POWER_CLAMP: "pcn",
        CurveType.GND_CLAMP: "gcn",
        CurveType.DISABLED_PULLUP: "dun",
        CurveType.DISABLED_PULLDOWN: "ddn",
        CurveType.RISING_RAMP: "run",
        CurveType.FALLING_RAMP: "rdn",
        CurveType.RISING_WAVE: "b",
        CurveType.FALLING_WAVE: "y",
        CurveType.SERIES_VI: "vin",
        CurveType.ISSO_PULLUP: "iun",
        CurveType.ISSO_PULLDOWN: "idn",
    }
    spice_file_max_prefix = {
        CurveType.PULLUP: "pux",
        CurveType.PULLDOWN: "pdx",
        CurveType.POWER_CLAMP: "pcx",
        CurveType.GND_CLAMP: "gcx",
        CurveType.DISABLED_PULLUP: "dux",
        CurveType.DISABLED_PULLDOWN: "ddx",
        CurveType.RISING_RAMP: "rux",
        CurveType.FALLING_RAMP: "rdx",
        CurveType.RISING_WAVE: "c",
        CurveType.FALLING_WAVE: "z",
        CurveType.SERIES_VI: "vix",
        CurveType.ISSO_PULLUP: "iux",
        CurveType.ISSO_PULLDOWN: "idx",
    }
    spice_file_typ_prefix = {
        CurveType.PULLUP: "put",
        CurveType.PULLDOWN: "pdt",
        CurveType.POWER_CLAMP: "pct",
        CurveType.GND_CLAMP: "gct",
        CurveType.DISABLED_PULLUP: "dut",
        CurveType.DISABLED_PULLDOWN: "ddt",
        CurveType.RISING_RAMP: "rut",
        CurveType.FALLING_RAMP: "rdt",
        CurveType.RISING_WAVE: "a",
        CurveType.FALLING_WAVE: "x",
        CurveType.SERIES_VI: "vit",
        CurveType.ISSO_PULLUP: "iut",
        CurveType.ISSO_PULLDOWN: "idt",
    }

    VI_PREFIXES = (
    "put", "pun", "pux", "pdt", "pdn", "pdx", "pct", "pcn", "pcx", "gct", "gcn", "gcx", "dut", "dun", "dux", "ddt",
    "ddn", "ddx", "vit", "vin", "vix")
    VT_PREFIXES = ("a", "b", "c", "x", "y", "z")

    VIDataBeginMarker = {SpiceType.HSPICE: "******"}
    tranDataBeginMarker = {SpiceType.HSPICE: "******"}
    abortMarker = {SpiceType.HSPICE: "aborted"}
    convergenceMarker = {SpiceType.HSPICE: "convergence failure"}

    VI_COLUMN_HINTS = ("volt", "current")
    TRAN_COLUMN_HINTS = ("time", "voltage", "current")  # Updated: now includes supply current (I_supply)

    FLOAT_RE = r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?"
    VI_ROW_RE = re.compile(rf"^\s*({FLOAT_RE})\s+({FLOAT_RE})\s*$")

    MAX_READ_RETRIES = 1

    VERSION_ONE_ZERO = 100
    VERSION_ONE_ONE = 101
    VERSION_TWO_ZERO = 200
    VERSION_TWO_ONE = 201
    VERSION_THREE_TWO = 302
    VERSION_FIVE_ZERO = 500
    VERSION_FIVE_ONE = 501
    VERSION_SIX_ZERO = 600
    VERSION_SEVEN_ZERO = 700
