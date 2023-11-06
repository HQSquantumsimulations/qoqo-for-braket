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
import numpy as np


def test_oqc_error() -> None:
    """Test running with OQC, fails OperationNotInBackend."""
    backend = BraketBackend()
    backend.force_oqc_verbatim()

    # OperationNotInBackend
    circuit = Circuit()
    circuit += ops.PragmaDamping(1, 1.0, 1.0)
    with pytest.raises(RuntimeError):
        backend.run_circuit(circuit)

    # Too many operations
    circuit = Circuit()
    circuit += ops.RotateZ(3, np.pi)
    circuit += ops.SqrtPauliX(1)
    circuit += ops.PauliX(2)
    with pytest.raises(ValueError):
        backend.change_max_circuit_length(2)
        backend.run_circuit(circuit)

    # Too many shots
    circuit = Circuit()
    circuit += ops.PragmaSetNumberOfMeasurements(10, "ro")
    with pytest.raises(ValueError):
        backend.change_max_shots(2)
        backend.run_circuit(circuit)


def test_oqc_all_gates() -> None:
    """Test running with OQC."""
    backend = BraketBackend()
    backend.force_oqc_verbatim()

    oqc_circuit = Circuit()
    oqc_circuit += ops.DefinitionBit("ro", 4, True)
    oqc_circuit += ops.RotateZ(0, np.pi)
    oqc_circuit += ops.RotateZ(3, np.pi)
    oqc_circuit += ops.SqrtPauliX(1)
    oqc_circuit += ops.PauliX(2)
    oqc_circuit += ops.MeasureQubit(0, "ro", 0)
    oqc_circuit += ops.MeasureQubit(1, "ro", 1)
    oqc_circuit += ops.MeasureQubit(2, "ro", 2)
    oqc_circuit += ops.MeasureQubit(3, "ro", 3)
    oqc_circuit += ops.PragmaSetNumberOfMeasurements(10, "ro")
    (oqc_bit_res, _, _) = backend.run_circuit(oqc_circuit)
    assert "ro" in oqc_bit_res.keys()
    oqc_registers = oqc_bit_res["ro"]
    assert oqc_registers.shape == (10, 4)
    for oqc_measurement in oqc_registers:
        for qubit in oqc_measurement:
            assert qubit == 1 or qubit == 0


if __name__ == "__main__":
    pytest.main(sys.argv)
