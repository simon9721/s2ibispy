def test_no_transients_for_input_model(io_env):
    ibis, global_, mlist, comp, sig = io_env
    # Switch the model type to INPUT
    sig.model.modelType = CS.ModelType.INPUT

    util = S2IUtil(mlist)
    util.complete_data_structures(ibis, global_)

    # Pre-seed lists anyway; analyzer should ignore them
    sig.model.risingWaveList = [IbisWaveTable()]
    sig.model.fallingWaveList = [IbisWaveTable()]

    fake = FakeSpiceTransient(mlist)
    ap = AnalyzePin(fake)

    pwr = next(p for p in comp.pList if p.modelName.upper() == "POWER")
    gnd = next(p for p in comp.pList if p.modelName.upper() == "GND")
    en  = next(p for p in comp.pList if p.pinName == "EN")
    din = next(p for p in comp.pList if p.pinName == "DIN")

    rc = ap.analyze_pin(
        sig, en, din, pwr, gnd, pwr, gnd,
        spice_type=CS.SpiceType.HSPICE,
        spice_file="dummy.sp",
        series_spice_file="series.sp",
        spice_command="run",
        iterate=0,
        cleanup=0,
    )
    assert rc == 0
    assert fake.calls["generate_ramp_data"] == []
    assert fake.calls["generate_wave_data"] == []
