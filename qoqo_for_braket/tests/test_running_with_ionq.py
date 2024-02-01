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
from qoqo_for_braket.interface.ionq_verbatim_interface import call_circuit
from qoqo import Circuit
from qoqo import operations as ops
import pytest
import sys
import numpy as np


def test_ionq_errors() -> None:
    """Test running with IonQ, fails OperationNotInBackend."""
    backend = BraketBackend()
    backend.force_ionq_verbatim()

    # OperationNotInBackend
    circuit = Circuit()
    circuit += ops.PragmaDamping(1, 1.0, 1.0)
    with pytest.raises(RuntimeError):
        backend.run_circuit(circuit)

    # Too many operations
    circuit = Circuit()
    circuit += ops.GPi(0, np.pi)
    circuit += ops.RotateZ(0, np.pi)
    circuit += ops.GPi2(1, np.pi)
    with pytest.raises(ValueError):
        backend.change_max_circuit_length(2)
        backend.run_circuit(circuit)

    # Too many shots
    circuit = Circuit()
    circuit += ops.PragmaSetNumberOfMeasurements(10, "ro")
    with pytest.raises(ValueError):
        backend.change_max_shots(2)
        backend.run_circuit(circuit)


def test_ionq_all_gates() -> None:
    """Test running with IonQ."""
    backend = BraketBackend()
    backend.force_ionq_verbatim()

    ionq_circuit = Circuit()
    ionq_circuit += ops.DefinitionBit("ro", 4, True)
    ionq_circuit += ops.GPi(0, np.pi)
    ionq_circuit += ops.RotateZ(0, np.pi)
    ionq_circuit += ops.GPi2(1, np.pi)
    ionq_circuit += ops.RotateZ(2, np.pi)
    ionq_circuit += ops.GPi2(2, np.pi / 2)
    ionq_circuit += ops.MolmerSorensenXX(2, 3)
    ionq_circuit += ops.VariableMSXX(1, 2, np.pi)
    ionq_circuit += ops.MeasureQubit(0, "ro", 0)
    ionq_circuit += ops.MeasureQubit(1, "ro", 1)
    ionq_circuit += ops.MeasureQubit(2, "ro", 2)
    ionq_circuit += ops.MeasureQubit(3, "ro", 3)
    ionq_circuit += ops.PragmaSetNumberOfMeasurements(10, "ro")
    (ionq_bit_res, _, _) = backend.run_circuit(ionq_circuit)
    assert "ro" in ionq_bit_res.keys()
    ionq_registers = ionq_bit_res["ro"]
    assert len(ionq_registers) == 10
    assert len(ionq_registers[0]) == 4
    for ionq_measurement in ionq_registers:
        for qubit in ionq_measurement:
            assert qubit == 1 or qubit == 0


def test_ionq_sign() -> None:
    """Test running with IonQ."""
    backend = BraketBackend()
    backend.force_ionq_verbatim()

    circuit = Circuit()
    circuit += ops.RotateZ(0, -0.5 * np.pi)
    circuit += ops.GPi2(0, 0.0)
    circuit += ops.RotateZ(0, 0.5)
    circuit += ops.GPi2(0, np.pi)
    circuit += ops.RotateZ(0, 0.5 * np.pi)
    circuit += ops.RotateZ(1, 0.5 * np.pi)
    circuit += ops.GPi2(1, 0.0)
    circuit += ops.RotateZ(1, 0.5)
    circuit += ops.GPi2(1, np.pi)
    circuit += ops.RotateZ(1, -0.5 * np.pi)
    circuit += ops.VariableMSXX(0, 1, 0.3)
    circuit += ops.RotateZ(0, 0.5 * np.pi)
    circuit += ops.RotateZ(1, 0.5 * np.pi)
    circuit += ops.VariableMSXX(0, 1, 0.3)
    circuit += ops.RotateZ(0, -0.5 * np.pi)
    circuit += ops.GPi2(0, 0.0)
    circuit += ops.RotateZ(0, 0.5 * np.pi)
    circuit += ops.GPi2(0, np.pi)
    circuit += ops.RotateZ(1, -0.5 * np.pi)
    circuit += ops.GPi2(1, 0.0)
    circuit += ops.RotateZ(1, 0.5 * np.pi)
    circuit += ops.GPi2(1, np.pi)
    circuit += ops.VariableMSXX(0, 1, 0.3)
    circuit += ops.RotateZ(0, -0.2)
    circuit += ops.GPi2(0, 0.0)
    circuit += ops.RotateZ(0, 0.5 * np.pi)
    circuit += ops.GPi2(0, np.pi)
    circuit += ops.RotateZ(0, np.pi)
    circuit += ops.RotateZ(1, 0.2)
    circuit += ops.GPi2(1, 0.0)
    circuit += ops.RotateZ(1, 0.5 * np.pi)
    circuit += ops.GPi2(1, np.pi)
    circuit += ops.RotateZ(1, -np.pi)
    circuit += ops.MolmerSorensenXX(1, 0)
    unitary_matrices = []
    for op in circuit:
        if op.hqslang() in ["GPi", "GPi2", "RotateZ"]:
            if op.qubit() == 0:
                matrix = np.kron(op.unitary_matrix(), np.eye(2))
                unitary_matrices.append(matrix)
            elif op.qubit() == 1:
                matrix = np.kron(np.eye(2), op.unitary_matrix())
                unitary_matrices.append(matrix)
        else:
            matrix = op.unitary_matrix()
            unitary_matrices.append(matrix)

    unitary_matrix = np.eye(4)
    for matrix in list(reversed(unitary_matrices)):
        unitary_matrix = np.einsum("ij,jk->ik", matrix, unitary_matrix)

    unitary_matrix_vz_replacement = call_circuit(circuit).to_unitary()

    ratio_abs = np.abs(unitary_matrix / unitary_matrix_vz_replacement)

    assert np.allclose(ratio_abs, 1)


if __name__ == "__main__":
    pytest.main(sys.argv)
