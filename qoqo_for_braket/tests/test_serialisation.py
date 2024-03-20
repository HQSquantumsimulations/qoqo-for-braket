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
"""Test running local operation with qasm backend (Queued Jobs)."""

import copy
import sys

import numpy as np
import pytest
from braket.aws.aws_session import AwsSession
from qoqo import Circuit, QuantumProgram, measurements
from qoqo import operations as ops

from qoqo_for_braket import BraketBackend, QueuedCircuitRun, QueuedHybridRun, QueuedProgramRun


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
    assert deserialised._results[0]["ro"] == queued._results[0]["ro"]


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
    assert deserialised._results[0]["ro"] == queued._results[0]["ro"]


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
    assert np.isclose(results["0Z"], 0.0)
    assert np.isclose(results_queued["0Z"], 0.0)

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
    assert np.isclose(results["0Z"], 0.0)
    assert np.isclose(results_queued["0Z"], 0.0)


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
    assert np.isclose(results["0Z"], 0.0)
    assert np.isclose(results_queued["0Z"], 0.0)


def test_serialisation_using_config() -> None:
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

    serialised = backend._create_config()
    backend_config = copy.deepcopy(backend)
    BraketBackend._load_config(backend_config, config=serialised)

    assert backend_config.device == backend.device
    assert backend_config.batch_mode == backend.batch_mode
    assert backend_config.aws_session == backend.aws_session
    assert backend_config.use_hybrid_jobs == backend.use_hybrid_jobs

    # After polling: result is not None
    queued = backend.run_measurement_queued(measurement)
    queued_config = backend_config.run_measurement_queued(measurement)
    i = 0
    while queued.poll_result() is None:
        i += 1
        if i > 50:
            raise RuntimeError("Timed out waiting for job to complete")
    while queued_config.poll_result() is None:
        i += 1
        if i > 50:
            raise RuntimeError("Timed out waiting for job to complete")

    results = queued.poll_result()
    results_config = queued_config.poll_result()
    assert len(results.keys()) == len(results_config.keys()) == 1
    assert np.isclose(results["0Z"], 0.0)
    assert np.isclose(results_config["0Z"], 0.0)


@pytest.mark.skip()
def test_serialisation_hybrid_async() -> None:
    """Test to_json and from_json methods for QueuedHybridRun for an async job."""
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
        # device="arn:aws:braket:::device/quantum-simulator/amazon/sv1",
    )
    backend.change_max_shots(2)

    queued = backend.run_measurement_registers_hybrid_queued(measurement)

    serialised = queued.to_json()
    deserialised = QueuedHybridRun.from_json(serialised)

    # After polling: result is not None
    i = 0
    while queued.poll_result() is None:
        i += 1
        if i > 50:
            raise RuntimeError("Timed out waiting for job to complete")

    results = queued.poll_result()
    results_queued = deserialised.poll_result()
    assert len(results.keys()) == len(results_queued.keys()) == 1
    assert np.isclose(results["0Z"], 0.0)
    assert np.isclose(results_queued["0Z"], 0.0)

    queued.delete_tmp_folder()
    deserialised.delete_tmp_folder()


def test_serialization_program_overwrite():
    backend = BraketBackend()

    circuit_1 = Circuit()
    circuit_1 += ops.DefinitionBit("same", 1, True)
    circuit_1 += ops.PauliX(0)
    circuit_1 += ops.MeasureQubit(0, "same", 0)
    circuit_1 += ops.PragmaSetNumberOfMeasurements(2, "same")

    circuit_2 = Circuit()
    circuit_2 += ops.DefinitionBit("same", 1, True)
    circuit_2 += ops.PauliX(0)
    circuit_2 += ops.PauliX(0)
    circuit_2 += ops.MeasureQubit(0, "same", 0)
    circuit_2 += ops.PragmaSetNumberOfMeasurements(2, "same")

    measurement = measurements.ClassicalRegister(
        constant_circuit=None, circuits=[circuit_1, circuit_2]
    )

    queued = backend.run_measurement_queued(measurement)

    i = 0
    while queued.poll_result() is None:
        i += 1
        if i > 50:
            raise RuntimeError("Timed out waiting for job to complete")

    serialised = queued.to_json()
    deserialised = QueuedProgramRun.from_json(serialised)

    results = queued.poll_result()
    results_queued = deserialised.poll_result()

    assert len(results[0].keys()) == len(results_queued[0].keys()) == 1
    assert len(results[0]["same"]) == len(results_queued[0]["same"]) == 4
    assert results[0]["same"][0][0]
    assert results[0]["same"][1][0]
    assert not results[0]["same"][2][0]
    assert not results[0]["same"][3][0]
    assert not results[1]
    assert not results[2]
    assert results_queued[0]["same"][0][0]
    assert results_queued[0]["same"][1][0]
    assert not results_queued[0]["same"][2][0]
    assert not results_queued[0]["same"][3][0]
    assert not results_queued[1]
    assert not results_queued[2]


def test_serialisation_run_program():
    """Test run_program_queued."""
    backend = BraketBackend()

    init_circuit = Circuit()
    init_circuit += ops.RotateX(0, "angle_0")
    init_circuit += ops.RotateY(0, "angle_1")

    z_circuit = Circuit()
    z_circuit += ops.DefinitionBit("ro_z", 1, is_output=True)
    z_circuit += ops.PragmaRepeatedMeasurement("ro_z", 1000, None)

    x_circuit = Circuit()
    x_circuit += ops.DefinitionBit("ro_x", 1, is_output=True)
    x_circuit += ops.Hadamard(0)
    x_circuit += ops.PragmaRepeatedMeasurement("ro_x", 1000, None)

    measurement_input = measurements.PauliZProductInput(1, False)
    z_basis_index = measurement_input.add_pauliz_product(
        "ro_z",
        [
            0,
        ],
    )
    x_basis_index = measurement_input.add_pauliz_product(
        "ro_x",
        [
            0,
        ],
    )
    measurement_input.add_linear_exp_val(
        "<H>",
        {x_basis_index: 0.1, z_basis_index: 0.2},
    )

    measurement = measurements.PauliZProduct(
        constant_circuit=init_circuit,
        circuits=[z_circuit, x_circuit],
        input=measurement_input,
    )

    program = QuantumProgram(measurement=measurement, input_parameter_names=["angle_0", "angle_1"])

    with pytest.raises(ValueError) as exc:
        _ = backend.run_program_queued(program=program, params_values=[[0.4]])
    assert "Wrong number of parameters 2 parameters expected 1 parameters given." in str(exc.value)

    with pytest.raises(NameError) as exc:
        _ = backend.run_program_queued(program=program, params_values=[])
    assert "Missing input variable 'angle_0'." in str(exc.value)

    queued_jobs = backend.run_program_queued(
        program=program, params_values=[[0.785, 0.238], [0.234, 0.653], [0.875, 0.612]]
    )

    assert len(queued_jobs) == 3

    for queued in queued_jobs:
        i = 0
        while queued.poll_result() is None:
            i += 1
            if i > 50:
                raise RuntimeError("Timed out waiting for job to complete")

        serialised = queued.to_json()
        deserialised = QueuedProgramRun.from_json(serialised)

        results = queued.poll_result()
        results_queued = deserialised.poll_result()

        assert len(results) == len(results_queued) == 1
        assert results["<H>"]


@pytest.mark.skip()
def test_serialisation_run_program_hybrid_async():
    """Test run_program_queued for QueuedHybridRun for an async job. """
    aws_session = AwsSession()
    backend = BraketBackend(
        aws_session=aws_session,
        # device="arn:aws:braket:::device/quantum-simulator/amazon/sv1",
    )
    backend.change_max_shots(2)

    init_circuit = Circuit()
    init_circuit += ops.RotateX(0, "angle_0")
    init_circuit += ops.RotateY(0, "angle_1")

    z_circuit = Circuit()
    z_circuit += ops.DefinitionBit("ro_z", 1, is_output=True)
    z_circuit += ops.PragmaRepeatedMeasurement("ro_z", 1000, None)

    x_circuit = Circuit()
    x_circuit += ops.DefinitionBit("ro_x", 1, is_output=True)
    x_circuit += ops.Hadamard(0)
    x_circuit += ops.PragmaRepeatedMeasurement("ro_x", 1000, None)

    measurement_input = measurements.PauliZProductInput(1, False)
    z_basis_index = measurement_input.add_pauliz_product(
        "ro_z",
        [
            0,
        ],
    )
    x_basis_index = measurement_input.add_pauliz_product(
        "ro_x",
        [
            0,
        ],
    )
    measurement_input.add_linear_exp_val(
        "<H>",
        {x_basis_index: 0.1, z_basis_index: 0.2},
    )

    measurement = measurements.PauliZProduct(
        constant_circuit=init_circuit,
        circuits=[z_circuit, x_circuit],
        input=measurement_input,
    )

    program = QuantumProgram(measurement=measurement, input_parameter_names=["angle_0", "angle_1"])

    queued_jobs = backend.run_program_queued(
        program=program, params_values=[[0.785, 0.238], [0.234, 0.653], [0.875, 0.612]], hybrid=True
    )

    assert len(queued_jobs) == 3

    for queued in queued_jobs:
        i = 0
        while queued.poll_result() is None:
            i += 1
            if i > 50:
                raise RuntimeError("Timed out waiting for job to complete")

        serialised = queued.to_json()
        deserialised = QueuedHybridRun.from_json(serialised)

        results = queued.poll_result()
        results_queued = deserialised.poll_result()

        assert len(results) == len(results_queued) == 1
        assert results["<H>"]


if __name__ == "__main__":
    pytest.main(sys.argv)
