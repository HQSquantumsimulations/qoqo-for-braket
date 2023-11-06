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
from qoqo import Circuit
from qoqo import operations as ops
import pytest
import sys


def test_rigetti_error() -> None:
    """Test running with Rigetti, fails OperationNotInBackend."""
    backend = BraketBackend()
    backend.force_rigetti_verbatim()

    # OperationNotInBackend
    circuit = Circuit()
    circuit += ops.PragmaDamping(1, 1.0, 1.0)
    with pytest.raises(RuntimeError):
        backend.run_circuit(circuit)

    # Too many operations
    circuit = Circuit()
    circuit += ops.RotateZ(1, 1.0)
    circuit += ops.ControlledPauliZ(2, 3)
    circuit += ops.ControlledPhaseShift(3, 1, 1.0)
    with pytest.raises(ValueError):
        backend.change_max_circuit_length(2)
        backend.run_circuit(circuit)

    # Too many shots
    circuit = Circuit()
    circuit += ops.PragmaSetNumberOfMeasurements(10, "ro")
    with pytest.raises(ValueError):
        backend.change_max_shots(2)
        backend.run_circuit(circuit)


def test_rigetti_all_gates() -> None:
    """Test running with Rigetti."""
    backend = BraketBackend()
    backend.force_rigetti_verbatim()

    rigetti_circuit = Circuit()
    rigetti_circuit += ops.DefinitionBit("ro", 4, True)
    rigetti_circuit += ops.PauliX(0)
    rigetti_circuit += ops.SqrtPauliX(0)
    rigetti_circuit += ops.InvSqrtPauliX(0)
    rigetti_circuit += ops.RotateZ(1, 1.0)
    rigetti_circuit += ops.ControlledPauliZ(2, 3)
    rigetti_circuit += ops.ControlledPhaseShift(3, 1, 1.0)
    rigetti_circuit += ops.XY(0, 2, 1.0)
    rigetti_circuit += ops.MeasureQubit(0, "ro", 0)
    rigetti_circuit += ops.MeasureQubit(1, "ro", 1)
    rigetti_circuit += ops.MeasureQubit(2, "ro", 2)
    rigetti_circuit += ops.MeasureQubit(3, "ro", 3)
    rigetti_circuit += ops.PragmaSetNumberOfMeasurements(10, "ro")
    (rigetti_bit_res, _, _) = backend.run_circuit(rigetti_circuit)
    assert "ro" in rigetti_bit_res.keys()
    rigetti_registers = rigetti_bit_res["ro"]
    assert rigetti_registers.shape == (10, 4)
    for rigetti_measurement in rigetti_registers:
        for qubit in rigetti_measurement:
            assert qubit == 1 or qubit == 0


if __name__ == "__main__":
    pytest.main(sys.argv)
