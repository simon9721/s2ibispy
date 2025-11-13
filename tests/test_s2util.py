import logging
import os
import sys
sys.path.append("C:\\Users\\sh3qm\\PycharmProjects\\s2ibispy")
from s2iutil import S2IUtil
from parser import S2IParser
from models import IbisTOP, IbisGlobal, IbisModel

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


def test_link_pins_to_models():
    # Setup
    input_file = "tests/buffer.s2i"  # Use your buffer.s2i
    parser = S2IParser()

    # Parse input file
    try:
        ibis, global_, mList = parser.parse(input_file)
    except FileNotFoundError:
        logging.error(f"Input file {input_file} not found")
        assert False, "Test requires buffer.s2i"

    # Run S2IUtil to link pins to models
    util = S2IUtil(mList)
    util.complete_data_structures(ibis, global_)

    # Check model list
    model_names = [m.modelName.lower() for m in mList]
    logging.info(f"Available models: {model_names}")
    assert "driver" in model_names, f"Model 'driver' not found in mList: {model_names}"

    # Check pin-to-model linking
    for comp in ibis.cList:
        logging.info(f"Checking component: {comp.component}")
        for pin in comp.pList:
            logging.info(f"Pin: {pin.pinName}, modelName: {pin.modelName}")
            if pin.modelName.lower() == "driver":
                assert pin.model is not None, f"Pin {pin.pinName} with modelName 'driver' has no model linked"
                assert pin.model.modelName.lower() == "driver", f"Pin {pin.pinName} linked to wrong model: {pin.model.modelName}"
            elif pin.modelName.upper() in {"POWER", "GND", "NC"}:
                assert pin.model is None, f"Pin {pin.pinName} with special modelName {pin.modelName} should have model=None"
            else:
                logging.warning(f"Unexpected modelName {pin.modelName} for pin {pin.pinName}")


if __name__ == "__main__":
    test_link_pins_to_models()
    print("Test passed successfully!")