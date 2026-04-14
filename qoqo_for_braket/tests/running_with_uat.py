# Copyright © 2023 HQS Quantum Simulations GmbH.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing permissions and limitations under
# the License.
"""Test running local operation with qasm backend."""
import boto3
import logging
import os
from qoqo import Circuit
from qoqo import operations as ops
from qoqo_for_braket import BraketBackend
import sys
import pytest
import subprocess


# def test__create_uat():
# Set default region
os.environ["AWS_DEFAULT_REGION"] = "eu-west-2" # or your preferred region
# Enable debug logging
boto3.set_stream_logger("", logging.DEBUG)
# Use SV1 simulator
DEVICE_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
backend = BraketBackend(device=DEVICE_ARN)
# Simple circuit
circuit = Circuit()
circuit += ops.Hadamard(qubit=0)
circuit += ops.CNOT(control=0, target=1)
circuit += ops.MeasureQubit(qubit=0, readout="ro", readout_index=0)
circuit += ops.MeasureQubit(qubit=1, readout="ro", readout_index=1)
circuit += ops.PragmaSetNumberOfMeasurements(number_measurements=10, readout="ro")
output = subprocess.run(backend.run_circuit(circuit), capture_output=True)
assert "APN/1.0 HQS" in output.stdout


# if __name__ == "__main__":
#     pytest.main(sys.argv)
