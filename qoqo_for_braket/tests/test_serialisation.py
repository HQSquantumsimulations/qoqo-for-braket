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
from qoqo_for_braket import BraketBackend, QueuedCircuitRun, QueuedProgramRun
from qoqo import Circuit, measurements
from qoqo import operations as ops
import numpy as np
import pytest
import sys
from braket.aws.aws_session import AwsSession


def test_serialisation_circuit() -> None:
    """Test to_json and from_json methods for QueuedCircuitRun."""
    circuit = Circuit()
    circuit += ops.DefinitionBit("ro", 3, False)
    circuit += ops.PauliX(0)
    circuit += ops.PauliX(1)
    circuit += ops.PauliX(2)
    circuit += ops.MeasureQubit(0, "ro", 0)
    circuit += ops.MeasureQubit(1, "ro", 1)
    circuit += ops.MeasureQubit(2, "ro", 2)
    circuit += ops.PragmaSetNumberOfMeasurements(2, "ro")

    backend = BraketBackend(
        device=None,
    )
    queued = backend.run_circuit_queued(circuit)
    serialised = queued.to_json()
    deserialised = QueuedCircuitRun.from_json(serialised)
    assert deserialised._results[1] == queued._results[1]
    assert deserialised._results[2] == queued._results[2]
    assert deserialised._results[0].keys() == queued._results[0].keys()
    assert (deserialised._results[0]["ro"] == queued._results[0]["ro"]).all()


@pytest.mark.skip()
def test_serialisation_circuit_async() -> None:
    """Test to_json and from_json methods for QueuedCircuitRun for an async job."""
    circuit = Circuit()
    circuit += ops.DefinitionBit("ro", 3, False)
    circuit += ops.PauliX(0)
    circuit += ops.PauliX(1)
    circuit += ops.PauliX(2)
    circuit += ops.MeasureQubit(0, "ro", 0)
    circuit += ops.MeasureQubit(1, "ro", 1)
    circuit += ops.MeasureQubit(2, "ro", 2)
    circuit += ops.PragmaSetNumberOfMeasurements(2, "ro")

    aws_session = AwsSession()
    backend = BraketBackend(
        aws_session=aws_session,
        device="arn:aws:braket:::device/quantum-simulator/amazon/sv1",
    )
    backend.change_max_shots(2)
    queued = backend.run_circuit_queued(circuit)

    # Before polling: result is None
    serialised = queued.to_json()
    deserialised = QueuedCircuitRun.from_json(serialised)
    assert deserialised._results == queued._results

    # After polling: result is not None
    i = 0
    while queued.poll_result() is None:
        i += 1
        if i > 50:
            raise RuntimeError("Timed out waiting for job to complete")
    serialised = queued.to_json()
    deserialised = QueuedCircuitRun.from_json(serialised)
    assert deserialised._results[1] == queued._results[1]
    assert deserialised._results[2] == queued._results[2]
    assert deserialised._results[0].keys() == queued._results[0].keys()
    assert (deserialised._results[0]["ro"] == queued._results[0]["ro"]).all()


def test_serialisation_program() -> None:
    """Test to_json and from_json methods for QueuedProgramRun."""
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
    backend = BraketBackend(
        device=None,
    )
    backend.change_max_shots(2)
    queued = backend.run_measurement_queued(measurement)

    serialised = queued.to_json()
    deserialised = QueuedProgramRun.from_json(serialised)

    # Before polling: result is not None as tasks are local
    results = measurement.evaluate(
        deserialised._registers[0],
        deserialised._registers[1],
        deserialised._registers[2],
    )
    results_queued = deserialised._measurement.evaluate(
        deserialised._registers[0],
        deserialised._registers[1],
        deserialised._registers[2],
    )
    assert len(results.keys()) == len(results_queued.keys()) == 1
    assert results["0Z"] == results_queued["0Z"] == 1.0

    # After polling: result is not None
    i = 0
    while queued.poll_result() is None:
        i += 1
        if i > 50:
            raise RuntimeError("Timed out waiting for job to complete")
    serialised = queued.to_json()
    deserialised = QueuedProgramRun.from_json(serialised)

    results = queued.poll_result()
    results_queued = deserialised.poll_result()
    assert len(results.keys()) == len(results_queued.keys()) == 1
    assert results["0Z"] == results_queued["0Z"] == 1.0


@pytest.mark.skip()
def test_serialisation_program_async() -> None:
    """Test to_json and from_json methods for QueuedProgramRun for an async job."""
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

    aws_session = AwsSession()
    backend = BraketBackend(
        aws_session=aws_session,
        device="arn:aws:braket:::device/quantum-simulator/amazon/sv1",
    )
    backend.change_max_shots(2)
    queued = backend.run_measurement_queued(measurement)

    serialised = queued.to_json()
    deserialised = QueuedProgramRun.from_json(serialised)

    # Before polling: result is None
    assert deserialised.poll_result() == queued.poll_result()

    # After polling: result is not None

    # After polling: result is not None
    i = 0
    while queued.poll_result() is None:
        i += 1
        if i > 50:
            raise RuntimeError("Timed out waiting for job to complete")
    serialised = queued.to_json()
    deserialised = QueuedProgramRun.from_json(serialised)

    results = queued.poll_result()
    results_queued = deserialised.poll_result()
    assert len(results.keys()) == len(results_queued.keys()) == 1
    assert results["0Z"] == results_queued["0Z"] == 1.0


if __name__ == "__main__":
    pytest.main(sys.argv)
