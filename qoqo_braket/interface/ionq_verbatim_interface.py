# Copyright © 2023 HQS Quantum Simulations GmbH. All Rights Reserved.
# License details given in distributed LICENSE file.
"""Interface for the IonQ AWS braket devices."""

from braket.circuits import Circuit
import qoqo
from qoqo_calculator_pyo3 import CalculatorFloat
from typing import Dict

ALLOWED_OPERATIONS = ["PragmaRepeatedMeasurement", "PragmaSetNumberOfMeasurements", "MeasureQubit"]


def call_circuit(circuit: qoqo.Circuit) -> Circuit:
    """Convert a qoqo Circuit to a Braket Circuit with verbatim instructions for IonQ.

    Moving the RotateZ operations past the GPi, GPi2 and MS gates respects the following:
    * GPi(phi) RotateZ(0, theta) = RotateZ(theta) GPi(phi - theta)
    * GPi2(phi) RotateZ(0, theta) = RotateZ(theta) GPi2(phi - theta)
    * MS(0, 1, phi_0, phi_1) RotateZ(0, theta_0) RotateZ(1, theta_1) =
            RotateZ(0, theta_0) RotateZ(1, theta_1) MS(0, 1, phi_0 - theta_1, phi_1 - theta_0)

    Args:
        circuit: the qoqo Circuit to be translated

    Returns:
        Circuit: the converted circuit in Braket form

    Raises:
        RuntimeError: Unsupported operation for IonQ verbatim interface.
    """
    qubit_phase: Dict[int, CalculatorFloat] = dict()
    braket_circuit = Circuit()
    for op in circuit:
        if op.hqslang() == "RotateZ":
            qubit_phase[op.qubit()] = qubit_phase.get(op.qubit(), 0.0) + op.theta()
        elif op.hqslang() == "GPi":
            braket_circuit.gpi(op.qubit(), op.theta() - qubit_phase.get(op.qubit(), 0.0))
        elif op.hqslang() == "GPi2":
            braket_circuit.gpi2(op.qubit(), op.theta() - qubit_phase.get(op.qubit(), 0.0))
        elif op.hqslang() == "MolmerSorensenXX":
            braket_circuit.ms(
                op.control(),
                op.target(),
                0.0 - qubit_phase.get(op.target(), 0.0),
                0.0 - qubit_phase.get(op.control(), 0.0),
            )
        elif op.hqslang() in ALLOWED_OPERATIONS:
            pass
        else:
            raise RuntimeError(
                f"Unsupported operation {op.hqslang()} for IonQ verbatim interface."
            )

    return_circuit = Circuit()
    # This is necessary to avoid recompilation see
    #  https://github.com/aws/amazon-braket-examples/blob/main/examples/
    # braket_features/Verbatim_Compilation.ipynb
    return_circuit.add_verbatim_box(braket_circuit)
    return return_circuit
