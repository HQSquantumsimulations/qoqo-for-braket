"""Qoqo hybrid helper for running hybrid jobs on AWS."""

from qoqo_for_braket import BraketBackend
from qoqo import measurements
import os
import json


def run_measurement_register() -> None:
    """Run the measurement register on AWS."""
    input_dir = os.environ["AMZN_BRAKET_INPUT_DIR"]
    with open(os.path.join(input_dir, "measurement/.tmp_measurement_input.json"), "r") as f:
        measurement_json = f.read()
    with open(os.path.join(input_dir, "config/.tmp_config_input.json"), "r") as f:
        config = json.load(f)
    measurement = measurements.ClassicalRegister.from_json(measurement_json)
    backend = BraketBackend(device=os.environ["AMZN_BRAKET_DEVICE_ARN"])
    backend._load_config(config)
    backend.device = os.environ["AMZN_BRAKET_DEVICE_ARN"]
    backend.use_hybrid_jobs = False
    (bit_registers, float_registers, complex_registers) = backend.run_measurement_registers(
        measurement=measurement
    )

    with open(os.path.join(os.environ["AMZN_BRAKET_JOB_RESULTS_DIR"], "output.json"), "w") as f:
        json.dump((bit_registers, float_registers, complex_registers), f)
