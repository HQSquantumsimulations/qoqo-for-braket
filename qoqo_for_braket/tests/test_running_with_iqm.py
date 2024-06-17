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
from qoqo import Circuit
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
    (iqm_bit_res, _, _) = backend.run_circuit(iqm_circuit)
    assert "ro" in iqm_bit_res.keys()
    iqm_registers = iqm_bit_res["ro"]
    print(iqm_registers)
    assert len(iqm_registers) == 10
    assert len(iqm_registers[0]) == 3
    for iqm_measurement in iqm_registers:
        for qubit in iqm_measurement:
            assert qubit == 1 or qubit == 0


if __name__ == "__main__":
    pytest.main(sys.argv)
