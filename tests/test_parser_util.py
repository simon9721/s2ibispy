import logging
import math
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
from parser import S2IParser
from s2iutil import S2IUtil
from models import IbisTOP, IbisGlobal, IbisModel, IbisComponent, IbisPin, IbisDiffPin, IbisSeriesPin, \
    IbisSeriesSwitchGroup
from s2i_constants import ConstantStuff as CS

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


def test_parser_s2iutil_dump():
    input_file = "tests/buffer.s2i"
    parser = S2IParser()

    try:
        ibis, global_, mList = parser.parse(input_file)
    except FileNotFoundError:
        logging.error(f"Input file {input_file} not found")
        assert False, "Test requires buffer.s2i"

    # Run S2IUtil to propagate globals
    util = S2IUtil(mList)
    util.complete_data_structures(ibis, global_)

    # Dump IbisTOP
    logging.info("IbisTOP:")
    logging.info(f"  ibisVersion: {ibis.ibisVersion}")
    logging.info(f"  thisFileName: {ibis.thisFileName}")
    logging.info(f"  fileRev: {ibis.fileRev}")
    logging.info(f"  date: {ibis.date}")
    logging.info(f"  source: {ibis.source}")
    logging.info(f"  notes: {ibis.notes}")
    logging.info(f"  disclaimer: {ibis.disclaimer}")
    logging.info(f"  copyright: {ibis.copyright}")
    logging.info(f"  spiceType: {ibis.spiceType}")
    logging.info(f"  spiceCommand: {ibis.spiceCommand}")
    logging.info(f"  iterate: {ibis.iterate}")
    logging.info(f"  cleanup: {ibis.cleanup}")

    # Dump IbisGlobal
    logging.info("IbisGlobal:")
    logging.info(f"  tempRange: {global_.tempRange}")
    logging.info(f"  voltageRange: {global_.voltageRange}")
    logging.info(f"  pullupRef: {global_.pullupRef}")
    logging.info(f"  pulldownRef: {global_.pulldownRef}")
    logging.info(f"  powerClampRef: {global_.powerClampRef}")
    logging.info(f"  gndClampRef: {global_.gndClampRef}")
    logging.info(f"  vil: {global_.vil}")
    logging.info(f"  vih: {global_.vih}")
    logging.info(f"  Rload: {global_.Rload}")
    logging.info(f"  simTime: {global_.simTime}")
    logging.info(
        f"  pinParasitics: R_pkg={global_.pinParasitics.R_pkg}, L_pkg={global_.pinParasitics.L_pkg}, C_pkg={global_.pinParasitics.C_pkg}")

    # Dump Components and Pins
    for comp in ibis.cList:
        logging.info(f"Component: {comp.component}")
        logging.info(f"  manufacturer: {comp.manufacturer}")
        logging.info(f"  spiceFile: {comp.spiceFile}")
        logging.info(f"  seriesSpiceFile: {comp.seriesSpiceFile}")
        logging.info(f"  hasPinMapping: {comp.hasPinMapping}")
        logging.info(f"  tempRange: {comp.tempRange}")
        logging.info(f"  voltageRange: {comp.voltageRange}")
        for pin in comp.pList:
            logging.info(f"    Pin: {pin.pinName}")
            logging.info(f"      signalName: {pin.signalName}")
            logging.info(f"      modelName: {pin.modelName}")
            logging.info(f"      model: {pin.model.modelName if pin.model else 'None'}")
            logging.info(f"      inputPin: {pin.inputPin}")
            logging.info(f"      enablePin: {pin.enablePin}")
            logging.info(f"      spiceNodeName: {pin.spiceNodeName}")
            logging.info(f"      R_pin: {pin.R_pin}, L_pin: {pin.L_pin}, C_pin: {pin.C_pin}")
            logging.info(
                f"      pullupRef: {pin.pullupRef}, pulldownRef: {pin.pulldownRef}, powerClampRef: {pin.powerClampRef}, gndClampRef: {pin.gndClampRef}")
        for dp in comp.dpList:
            logging.info(f"    DiffPin: pinName={dp.pinName}, invPin={dp.invPin}, vdiff={dp.vdiff}, tdelay={dp.tdelay}")
        for sp in comp.spList:
            logging.info(
                f"    SeriesPin: pin1={sp.pin1}, pin2={sp.pin2}, modelName={sp.modelName}, fnTableGp={sp.fnTableGp}")
        for ssg in comp.ssgList:
            logging.info(f"    SeriesSwitchGroup: pins={ssg.pins}")
        for pm in comp.pmList:
            logging.info(f"    PinMapping: {pm}")

    # Dump Models
    for model in mList:
        logging.info(f"Model: {model.modelName}")
        logging.info(f"  modelType: {model.modelType}")
        logging.info(f"  polarity: {model.polarity}")
        logging.info(f"  enable: {model.enable}")
        logging.info(f"  modelFile: {model.modelFile}")
        logging.info(f"  modelFileMin: {model.modelFileMin}")
        logging.info(f"  modelFileMax: {model.modelFileMax}")
        logging.info(f"  spice_file: {model.spice_file}")
        logging.info(f"  ext_spice_cmd_file: {model.ext_spice_cmd_file}")
        logging.info(f"  Vinl: {model.Vinl}")
        logging.info(f"  Vinh: {model.Vinh}")
        logging.info(f"  Vmeas: {model.Vmeas}")
        logging.info(f"  Cref: {model.Cref}")
        logging.info(f"  Rref: {model.Rref}")
        logging.info(f"  Vref: {model.Vref}")
        logging.info(f"  vil: {model.vil}")
        logging.info(f"  vih: {model.vih}")
        logging.info(f"  tempRange: {model.tempRange}")
        logging.info(f"  voltageRange: {model.voltageRange}")
        logging.info(f"  pullupRef: {model.pullupRef}")
        logging.info(f"  pulldownRef: {model.pulldownRef}")
        logging.info(f"  powerClampRef: {model.powerClampRef}")
        logging.info(f"  gndClampRef: {model.gndClampRef}")
        logging.info(f"  c_comp: {model.c_comp}")
        logging.info(f"  Rload: {model.Rload}")
        logging.info(f"  simTime: {model.simTime}")
        logging.info(f"  risingWaveList: {len(model.risingWaveList)} entries")
        for w in model.risingWaveList:
            logging.info(f"    RisingWave: R_fixture={w.R_fixture}, V_fixture={w.V_fixture}")
        logging.info(f"  fallingWaveList: {len(model.fallingWaveList)} entries")
        for w in model.fallingWaveList:
            logging.info(f"    FallingWave: R_fixture={w.R_fixture}, V_fixture={w.V_fixture}")
        if model.seriesModel:
            logging.info(
                f"  seriesModel: OnState={model.seriesModel.OnState}, OffState={model.seriesModel.OffState}, RSeriesOff={model.seriesModel.RSeriesOff}, vdslist={model.seriesModel.vdslist}")
        # Verify vil/vih propagation
        assert not math.isnan(model.vil.typ), f"Model {model.modelName} has unset vil.typ (NaN) after S2IUtil"
        assert not math.isnan(model.vih.typ), f"Model {model.modelName} has unset vih.typ (NaN) after S2IUtil"


if __name__ == "__main__":
    test_parser_s2iutil_dump()
    print("Test completed: Parsed and propagated data dumped to log")