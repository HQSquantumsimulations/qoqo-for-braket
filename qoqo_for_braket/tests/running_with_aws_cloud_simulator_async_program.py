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
from qoqo_for_braket import BraketBackend
from qoqo import Circuit, measurements
from qoqo import operations as ops
from braket.aws.aws_session import AwsSession
from numpy import testing as npt
import numpy as np


import os

os.environ["AWS_REGION"] = "eu-west-2"

input_z = measurements.PauliZProductInput(number_qubits=3, use_flipped_measurement=False)

constant_circuit = Circuit()
constant_circuit += ops.PauliX(0)
constant_circuit += ops.PauliX(0)

circuit_1 = Circuit()
circuit_1 += ops.DefinitionBit("ro_1", 3, False)
circuit_1 += ops.PauliX(0)
circuit_1 += ops.PauliX(1)
circuit_1 += ops.PauliX(2)
circuit_1 += ops.MeasureQubit(0, "ro_1", 0)
circuit_1 += ops.MeasureQubit(1, "ro_1", 1)
circuit_1 += ops.MeasureQubit(2, "ro_1", 2)
circuit_1 += ops.PragmaSetNumberOfMeasurements(2, "ro_1")

input_z.add_pauliz_product("ro_1", [0])
input_z.add_pauliz_product("ro_1", [1])
input_z.add_pauliz_product("ro_1", [2])
input_z.add_linear_exp_val("0Z_1", {0: 1.0, 1: 0.0, 2: 0.0})
input_z.add_linear_exp_val("1Z_1", {0: 0.0, 1: 1.0, 2: 0.0})
input_z.add_linear_exp_val("2Z_1", {0: 0.0, 1: 0.0, 2: 1.0})

circuit_2 = Circuit()
circuit_2 += ops.DefinitionBit("ro_2", 3, False)
circuit_2 += ops.RotateZ(0, np.pi)
circuit_2 += ops.RotateZ(1, np.pi)
circuit_2 += ops.RotateZ(2, np.pi)
circuit_2 += ops.MeasureQubit(0, "ro_2", 0)
circuit_2 += ops.MeasureQubit(1, "ro_2", 1)
circuit_2 += ops.MeasureQubit(2, "ro_2", 2)
circuit_2 += ops.PragmaSetNumberOfMeasurements(2, "ro_2")

input_z.add_pauliz_product("ro_2", [0])
input_z.add_pauliz_product("ro_2", [1])
input_z.add_pauliz_product("ro_2", [2])
input_z.add_linear_exp_val("0Z_2", {0: 1.0, 1: 0.0, 2: 0.0})
input_z.add_linear_exp_val("1Z_2", {0: 0.0, 1: 1.0, 2: 0.0})
input_z.add_linear_exp_val("2Z_2", {0: 0.0, 1: 0.0, 2: 1.0})

measurement = measurements.PauliZProduct(
    constant_circuit=constant_circuit, circuits=[circuit_1, circuit_2], input=input_z
)

aws_session = AwsSession()
backend = BraketBackend(
    aws_session=aws_session,
    device="arn:aws:braket:::device/quantum-simulator/amazon/sv1",
)
backend.change_max_shots(2)

queued = backend.run_measurement_queued(measurement)
i = 0
while queued.poll_result() is None:
    i += 1
    if i > 50:
        raise RuntimeError("Timed out waiting for job to complete")
result = queued.poll_result()

assert "0Z_1" in result.keys()
assert result["0Z_1"] == -1.0
assert "1Z_1" in result.keys()
assert result["1Z_1"] == -1.0
assert "2Z_1" in result.keys()
assert result["2Z_1"] == -1.0

assert "0Z_2" in result.keys()
assert result["0Z_2"] == -1.0
assert "1Z_2" in result.keys()
assert result["1Z_2"] == -1.0
assert "2Z_2" in result.keys()
assert result["2Z_2"] == -1.0
