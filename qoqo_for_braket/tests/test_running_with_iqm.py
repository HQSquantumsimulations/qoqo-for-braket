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
from qoqo_for_braket.interface.iqm_verbatim_interface import call_circuit
from qoqo import Circuit, QuantumProgram, PauliZProductInput, PauliZProduct
from qoqo import operations as ops
import pytest
import sys
import numpy as np


def test_iqm_errors() -> None:
    """Test running with IQM, fails OperationNotInBackend."""
    backend = BraketBackend()
    backend.force_iqm_verbatim()

    # OperationNotInBackend
    circuit = Circuit()
    circuit += ops.PragmaDamping(1, 1.0, 1.0)
    with pytest.raises(RuntimeError):
        backend.run_circuit(circuit)

    # Too many operations
    circuit = Circuit()
    circuit += ops.RotateXY(0, np.pi, 0.0)
    circuit += ops.ControlledPauliZ(0, 1)
    circuit += ops.RotateXY(1, np.pi, 0.0)
    with pytest.raises(ValueError):
        backend.change_max_circuit_length(2)
        backend.run_circuit(circuit)

    # Too many shots
    circuit = Circuit()
    circuit += ops.PragmaSetNumberOfMeasurements(10, "ro")
    with pytest.raises(ValueError):
        backend.change_max_shots(2)
        backend.run_circuit(circuit)


def test_iqm_all_gates() -> None:
    """Test running with iqm."""
    backend = BraketBackend()
    backend.force_iqm_verbatim()

    iqm_circuit = Circuit()
    iqm_circuit += ops.DefinitionBit("ro", 3, True)
    iqm_circuit += ops.RotateXY(0, np.pi, np.pi * 0.5)
    iqm_circuit += ops.ControlledPauliZ(1, 2)
    iqm_circuit += ops.MeasureQubit(0, "ro", 0)
    iqm_circuit += ops.MeasureQubit(1, "ro", 1)
    iqm_circuit += ops.MeasureQubit(2, "ro", 2)
    iqm_circuit += ops.PragmaSetNumberOfMeasurements(10, "ro")
    iqm_bit_res, _, _ = backend.run_circuit(iqm_circuit)
    assert "ro" in iqm_bit_res.keys()
    iqm_registers = iqm_bit_res["ro"]
    print(iqm_registers)
    assert len(iqm_registers) == 10
    assert len(iqm_registers[0]) == 3
    for iqm_measurement in iqm_registers:
        for qubit in iqm_measurement:
            assert qubit == 1 or qubit == 0


def test_running_with_virtual_z_replacement() -> None:
    """Test running with virtual Z replacement."""
    circuit = Circuit()
    circuit += ops.DefinitionBit("ro", 2, True)
    circuit += ops.PauliX(0)
    circuit += ops.PauliX(1)
    circuit += ops.PauliZ(1)
    circuit += ops.PragmaSetNumberOfMeasurements(2, "ro")

    backend = BraketBackend()
    backend.force_iqm_verbatim()
    backend.set_virtual_z_replacement(replacement=False)
    bit_res, _, _ = backend.run_circuit(circuit)
    assert "ro" in bit_res.keys()
    registers = bit_res["ro"]

    print(registers)
    assert len(registers) == 2
    assert len(registers[0]) == 2
    assert registers[0] == [True, True]


def test_running_with_virtual_z_replacement_errors() -> None:
    """Test failing with virtual Z replacement."""
    circuit = Circuit()
    circuit += ops.DefinitionBit("ro", 2, True)
    circuit += ops.InputBit("ro", 1, True)
    circuit += ops.CNOT(0, 1)
    circuit += ops.PragmaSetNumberOfMeasurements(2, "ro")

    backend = BraketBackend()
    backend.force_iqm_verbatim()
    backend.set_virtual_z_replacement(replacement=False)
    with pytest.raises(ValueError):
        backend.run_circuit(circuit)


def test_quantum_program_virtual_Z():
    """Test running quantum program with virtual Z replacement."""
    backend = BraketBackend()
    backend.set_virtual_z_replacement(replacement=False)
    backend.force_iqm_verbatim()

    circuit = Circuit()
    circuit += ops.DefinitionBit("ro", 2, True)
    circuit += ops.InputBit("ro", 1, True)
    circuit += ops.PauliX(0)
    circuit += ops.RotateZ(0, "angle_0")

    meas_circuit = Circuit()
    meas_circuit += ops.PragmaSetNumberOfMeasurements(2, "ro")

    measurement_input = PauliZProductInput(1, False)
    z_basis_index = measurement_input.add_pauliz_product(
        "ro",
        [
            0,
        ],
    )
    measurement_input.add_linear_exp_val(
        "<H>",
        {z_basis_index: 0.2},
    )

    measurement = PauliZProduct(
        constant_circuit=circuit,
        circuits=[meas_circuit],
        input=measurement_input,
    )

    program = QuantumProgram(
        measurement=measurement,
        input_parameter_names=["angle_0"],
    )

    res = backend.run_program(program=program, params_values=[[1], [2], [3]])

    assert len(res) == 3
    for el in res:
        assert float(el["<H>"])


def test_quantum_program_virtual_Z_error():
    """Test failing quantum program with virtual Z replacement."""
    backend = BraketBackend()
    backend.set_virtual_z_replacement(replacement=False)
    backend.force_iqm_verbatim()

    circuit = Circuit()
    circuit += ops.DefinitionBit("ro", 2, True)
    circuit += ops.InputBit("ro", 1, True)
    circuit += ops.CNOT(0, 1)
    circuit += ops.RotateZ(0, "angle_0")

    meas_circuit = Circuit()
    meas_circuit += ops.PragmaSetNumberOfMeasurements(2, "ro")

    measurement_input = PauliZProductInput(1, False)
    z_basis_index = measurement_input.add_pauliz_product(
        "ro",
        [
            0,
        ],
    )
    measurement_input.add_linear_exp_val(
        "<H>",
        {z_basis_index: 0.2},
    )

    measurement = PauliZProduct(
        constant_circuit=circuit,
        circuits=[meas_circuit],
        input=measurement_input,
    )

    program = QuantumProgram(
        measurement=measurement,
        input_parameter_names=["angle_0"],
    )

    with pytest.raises(ValueError):
        backend.run_program(program=program, params_values=[[1], [2], [3]])


if __name__ == "__main__":
    pytest.main(sys.argv)
