# pininfer_tests

A set of 10 SPICE netlists for exercising pininfer:
- simple_output.sp — basic CMOS output buffer
- tristate_output.sp — output with OE/OE_B gating
- open_drain.sp — NMOS open-drain driver
- input_only.sp — receiver chain (no output pad)
- diff_driver.sp — differential OUT_P/OUT_N
- series_element.sp — core driver + series switch to pad
- odd_rail_names.sp — VPWR/VSSD rail names
- weird_pad_name.sp — pad named PAD0, mixed case
- anonymous_pad.sp — pad named net7 (no hints)
- tristate_enb.sp — tri-state with active-low enable EN_B

Use with:
  python -m pininfer.cli build pininfer_tests\simple_output.sp > llm_prompt.txt
  python llm_runner.py llm_prompt.txt labels.json
  python -m pininfer.cli emit labels.json
