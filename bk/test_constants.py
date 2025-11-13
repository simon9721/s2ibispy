import pytest
import math
from s2i_constants import ConstantStuff as CS

def test_version_and_general_constants():
    """Test general constants like VERSION_STRING and MAX_TABLE_SIZE."""
    assert CS.VERSION_STRING == "1.1", "Incorrect version string"
    assert math.isnan(CS.USE_NA), "USE_NA should be nan"  # Fixed nan comparison
    assert CS.FILENAME_EXTENSION == "ibs", "Incorrect filename extension"
    assert CS.MAX_TABLE_SIZE == 100, "Incorrect max table size"
    assert CS.MAX_WAVEFORM_TABLES == 100, "Incorrect max waveform tables"
    assert CS.MAX_SERIES_TABLES == 100, "Incorrect max series tables"
    assert CS.MAX_COMPONENT_NAME_LENGTH == 40, "Incorrect max component name length"
    assert CS.MAX_PIN_NAME_LENGTH == 5, "Incorrect max pin name length"
    assert CS.MAX_SIGNAL_NAME_LENGTH == 20, "Incorrect max signal name length"
    assert CS.MAX_MODEL_NAME_LENGTH == 20, "Incorrect max model name length"
    assert CS.MAX_FILE_REV_LENGTH == 4, "Incorrect max file rev length"

def test_simulation_defaults():
    """Test simulation default constants."""
    assert CS.SWEEP_STEP_DEFAULT == 0.01, "Incorrect sweep step default"
    assert CS.WAVE_POINTS_DEFAULT == 100, "Incorrect wave points default"
    assert CS.R_SERIES_DEFAULT == 1e6, "Incorrect R series default"
    assert CS.NUM_PTS_LINEAR_REGION == 10, "Incorrect num points linear region"
    assert CS.LIN_RANGE_DEFAULT == 5.0, "Incorrect linear range default"
    assert CS.DIODE_DROP_DEFAULT == 0.7, "Incorrect diode drop default"
    assert CS.ECL_TERMINATION_VOLTAGE_DEFAULT == -2.0, "Incorrect ECL termination voltage"

def test_spice_type_enum():
    """Test SpiceType enum values."""
    assert CS.SpiceType.HSPICE == 1, "Incorrect HSPICE value"
    assert CS.SpiceType.SPECTRE == 2, "Incorrect SPECTRE value"
    assert CS.SpiceType.ELDO == 3, "Incorrect ELDO value"

def test_model_type_enum():
    """Test ModelType enum values."""
    assert CS.ModelType.INPUT == 1, "Incorrect INPUT value"
    assert CS.ModelType.OUTPUT == 2, "Incorrect OUTPUT value"
    assert CS.ModelType.IO == 3, "Incorrect IO value"
    assert CS.ModelType.SERIES == 4, "Incorrect SERIES value"
    assert CS.ModelType.SERIES_SWITCH == 5, "Incorrect SERIES_SWITCH value"
    assert CS.ModelType.TERMINATOR == 6, "Incorrect TERMINATOR value"
    assert CS.ModelType.IO_OPEN_DRAIN == 7, "Incorrect IO_OPEN_DRAIN value"
    assert CS.ModelType.IO_OPEN_SINK == 8, "Incorrect IO_OPEN_SINK value"
    assert CS.ModelType.OPEN_DRAIN == 9, "Incorrect OPEN_DRAIN value"
    assert CS.ModelType.OPEN_SINK == 10, "Incorrect OPEN_SINK value"
    assert CS.ModelType.OPEN_SOURCE == 11, "Incorrect OPEN_SOURCE value"
    assert CS.ModelType.IO_OPEN_SOURCE == 12, "Incorrect IO_OPEN_SOURCE value"
    assert CS.ModelType.OUTPUT_ECL == 13, "Incorrect OUTPUT_ECL value"
    assert CS.ModelType.IO_ECL == 14, "Incorrect IO_ECL value"

def test_curve_type_enum():
    """Test CurveType enum values."""
    assert CS.CurveType.PULLUP == 1, "Incorrect PULLUP value"
    assert CS.CurveType.PULLDOWN == 2, "Incorrect PULLDOWN value"
    assert CS.CurveType.POWER_CLAMP == 3, "Incorrect POWER_CLAMP value"
    assert CS.CurveType.GND_CLAMP == 4, "Incorrect GND_CLAMP value"
    assert CS.CurveType.SERIES_VI == 5, "Incorrect SERIES_VI value"
    assert CS.CurveType.RISING_RAMP == 6, "Incorrect RISING_RAMP value"
    assert CS.CurveType.FALLING_RAMP == 7, "Incorrect FALLING_RAMP value"
    assert CS.CurveType.RISING_WAVE == 8, "Incorrect RISING_WAVE value"
    assert CS.CurveType.FALLING_WAVE == 9, "Incorrect FALLING_WAVE value"
    assert CS.CurveType.DISABLED_PULLUP == 10, "Incorrect DISABLED_PULLUP value"
    assert CS.CurveType.DISABLED_PULLDOWN == 11, "Incorrect DISABLED_PULLDOWN value"

def test_simulation_cases():
    """Test simulation case constants."""
    assert CS.TYP_CASE == 0, "Incorrect TYP_CASE value"
    assert CS.MIN_CASE == 1, "Incorrect MIN_CASE value"
    assert CS.MAX_CASE == 2, "Incorrect MAX_CASE value"

def test_polarity_and_enable():
    """Test polarity and enable constants."""
    assert CS.MODEL_POLARITY_INVERTING == "inverting", "Incorrect polarity inverting"
    assert CS.MODEL_ENABLE_ACTIVE_LOW == "active-low", "Incorrect enable active-low"

def test_output_states():
    """Test output state constants."""
    assert CS.ENABLE_OUTPUT == 1, "Incorrect ENABLE_OUTPUT value"
    assert CS.OUTPUT_RISING == 1, "Incorrect OUTPUT_RISING value"
    assert CS.OUTPUT_FALLING == 0, "Incorrect OUTPUT_FALLING value"

def test_curve_name_strings():
    """Test curve_name_string dictionary."""
    assert CS.curve_name_string[CS.CurveType.PULLUP] == "pullup", "Incorrect pullup name"
    assert CS.curve_name_string[CS.CurveType.PULLDOWN] == "pulldown", "Incorrect pulldown name"
    assert CS.curve_name_string[CS.CurveType.POWER_CLAMP] == "power_clamp", "Incorrect power_clamp name"
    assert CS.curve_name_string[CS.CurveType.GND_CLAMP] == "gnd_clamp", "Incorrect gnd_clamp name"
    assert CS.curve_name_string[CS.CurveType.SERIES_VI] == "series_vi", "Incorrect series_vi name"
    assert CS.curve_name_string[CS.CurveType.RISING_RAMP] == "rising ramp", "Incorrect rising ramp name"
    assert CS.curve_name_string[CS.CurveType.FALLING_RAMP] == "falling ramp", "Incorrect falling ramp name"
    assert CS.curve_name_string[CS.CurveType.RISING_WAVE] == "rising_wave", "Incorrect rising_wave name"
    assert CS.curve_name_string[CS.CurveType.FALLING_WAVE] == "falling_wave", "Incorrect falling_wave name"

def test_spice_file_prefixes():
    """Test spice file prefix dictionaries."""
    assert CS.spice_file_typ_prefix[CS.CurveType.PULLUP] == "put", "Incorrect typ pullup prefix"
    assert CS.spice_file_min_prefix[CS.CurveType.PULLUP] == "pun", "Incorrect min pullup prefix"
    assert CS.spice_file_max_prefix[CS.CurveType.PULLUP] == "pux", "Incorrect max pullup prefix"
    assert CS.spice_file_typ_prefix[CS.CurveType.SERIES_VI] == "srt", "Incorrect typ series_vi prefix"

def test_spice_markers():
    """Test SPICE marker dictionaries for HSPICE."""
    assert CS.VIDataBeginMarker[CS.SpiceType.HSPICE] == "****** mos model parameters", "Incorrect VI data marker"
    assert CS.tranDataBeginMarker[CS.SpiceType.HSPICE] == "****** job statistics summary", "Incorrect transient data marker"
    assert CS.abortMarker[CS.SpiceType.HSPICE] == "aborted", "Incorrect abort marker"
    assert CS.convergenceMarker[CS.SpiceType.HSPICE] == "non convergence", "Incorrect convergence marker"
