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
"""Test running a hybrid job."""

from qoqo_for_braket import BraketBackend
from qoqo import Circuit
from qoqo import operations as ops
from braket.aws.aws_session import AwsSession
from numpy import testing as npt
from qoqo import measurements

import numpy as np
import os

os.environ["AWS_REGION"] = "eu-west-2"

circuit = Circuit()
circuit += ops.DefinitionBit("ro", 3, False)
circuit += ops.PauliX(0)
circuit += ops.PauliX(1)
circuit += ops.PauliX(2)
circuit += ops.MeasureQubit(0, "ro", 0)
circuit += ops.MeasureQubit(1, "ro", 1)
circuit += ops.MeasureQubit(2, "ro", 2)
circuit += ops.PragmaSetNumberOfMeasurements(2, "ro")

measurement = measurements.ClassicalRegister(constant_circuit=None, circuits=[circuit])

aws_session = AwsSession()
backend = BraketBackend(
    aws_session=aws_session,
    device="arn:aws:braket:::device/quantum-simulator/amazon/sv1",
)
backend.change_max_shots(2)

(bit_res, _, _) = backend.run_measurement_registers_hybrid(measurement)
assert "ro" in bit_res.keys()
registers = bit_res["ro"]

assert len(registers) == 2
assert len(registers[0]) == 3

for reg in registers:
    npt.assert_array_equal(reg, [True, True, True])

constant_circuit = Circuit()
constant_circuit += ops.PauliX(0)
constant_circuit += ops.PauliX(0)

circuit_1 = Circuit()
circuit_1 += ops.DefinitionBit("ro", 1, False)
circuit_1 += ops.PauliX(0)
circuit_1 += ops.MeasureQubit(0, "ro", 0)
circuit_1 += ops.PragmaSetNumberOfMeasurements(2, "ro")

circuit_2 = Circuit()
circuit_2 += ops.DefinitionBit("ro", 1, False)
circuit_2 += ops.RotateZ(0, np.pi)
circuit_2 += ops.MeasureQubit(0, "ro", 0)
circuit_2 += ops.PragmaSetNumberOfMeasurements(2, "ro")

input_z = measurements.PauliZProductInput(number_qubits=3, use_flipped_measurement=False)
input_z.add_pauliz_product("ro", [0])
input_z.add_linear_exp_val("0Z", {0: 1.0})
measurement = measurements.PauliZProduct(
    constant_circuit=constant_circuit,
    circuits=[circuit_1, circuit_2],
    input=input_z,
)

res = backend.run_measurement_registers_hybrid(measurement)

assert len(res.keys()) == 1
assert np.isclose(res["0Z"], 0.0)
