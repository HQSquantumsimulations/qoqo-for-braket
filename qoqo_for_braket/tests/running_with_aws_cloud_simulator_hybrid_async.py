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
import time
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

queued = backend.run_measurement_registers_hybrid_queued(measurement)

i = 0
while queued.poll_result() is None:
    print(f"Waiting for job to complete. {i*10} seconds")
    i += 1
    time.sleep(10)
    if i > 50:
        raise RuntimeError("Timed out waiting for job to complete")
(bit_res, _, _) = queued.poll_result()

registers = bit_res["ro"]


assert len(registers) == 2
assert len(registers[0]) == 3

for reg in registers:
    npt.assert_array_equal(reg, [True, True, True])
