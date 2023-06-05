# Copyright © 2023 HQS Quantum Simulations GmbH. All Rights Reserved.
"""Test running local operation with qasm backend."""
from qoqo_braket import BraketBackend
from qoqo import Circuit
from qoqo.measurements import ClassicalRegister, PauliZProductInput, PauliZProduct
from qoqo import operations as ops
from typing import List, Any, Optional
import pytest
import sys
import numpy.testing as npt

list_of_operations = [
    [ops.PauliX(1), ops.PauliX(0), ops.PauliZ(2), ops.PauliX(3), ops.PauliY(4)],
    [
        ops.Hadamard(0),
        ops.CNOT(0, 1),
        ops.CNOT(1, 2),
        ops.CNOT(2, 3),
        ops.CNOT(3, 4),
    ],
    [ops.RotateX(0, 0.23), ops.RotateY(1, 0.12), ops.RotateZ(2, 0.34)],
]


@pytest.mark.parametrize("device", [None, "braket_sv"])
def test_all_no_device(device: Optional[str]) -> None:
    """Test running simple program."""
    circuit = Circuit()
    circuit += ops.PauliX(0)
    circuit += ops.PauliX(2)
    circuit += ops.PauliX(2)
    circuit += ops.ControlledPauliZ(0, 1)
    circuit += ops.MeasureQubit(0, "ro", 0)
    circuit += ops.MeasureQubit(1, "ro", 1)
    circuit += ops.MeasureQubit(2, "ro", 2)
    circuit += ops.PragmaSetNumberOfMeasurements(2, "ro")

    backend = BraketBackend(device)
    (bit_res, _, _) = backend.run_circuit(circuit)
    assert "ro" in bit_res.keys()
    registers = bit_res["ro"]

    assert registers.shape == (2, 3)

    for reg in registers:
        npt.assert_array_equal(reg, [True, False, False])


@pytest.mark.parametrize("operations", list_of_operations)
def test_measurement_register_classicalregister(operations: List[Any]):
    backend = BraketBackend()

    circuit = Circuit()
    involved_qubits = set()
    for op in operations:
        involved_qubits.update(op.involved_qubits())
        circuit += op

    circuit += ops.PragmaRepeatedMeasurement("ri", 10)

    measurement = ClassicalRegister(constant_circuit=None, circuits=[circuit])

    try:
        output = backend.run_measurement_registers(measurement=measurement)
    except:
        assert False

    assert len(output[0]["ri"][0]) == len(involved_qubits)
    assert not output[1]
    assert not output[2]


@pytest.mark.parametrize("operations", list_of_operations)
def test_measurement(operations: List[Any]):
    backend = BraketBackend()

    circuit = Circuit()
    involved_qubits = set()
    for op in operations:
        involved_qubits.update(op.involved_qubits())
        circuit += op

    circuit += ops.PragmaRepeatedMeasurement("ri", 10)

    input = PauliZProductInput(number_qubits=len(involved_qubits), use_flipped_measurement=True)

    measurement = PauliZProduct(constant_circuit=None, circuits=[circuit], input=input)

    try:
        _ = backend.run_measurement(measurement=measurement)
    except:
        assert False


if __name__ == "__main__":
    pytest.main(sys.argv)
