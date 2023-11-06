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
"""Interface for the IonQ AWS braket devices."""

from braket.circuits import Circuit
import qoqo
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from qoqo_calculator_pyo3 import CalculatorFloat

ALLOWED_OPERATIONS = [
    "PragmaRepeatedMeasurement",
    "PragmaSetNumberOfMeasurements",
    "MeasureQubit",
    "DefinitionBit",
]


def call_circuit(circuit: qoqo.Circuit) -> Circuit:
    """Convert a qoqo Circuit to a Braket Circuit with verbatim instructions for IonQ.

    Moving the RotateZ operations past the GPi, GPi2 and MS gates respects the following:
    * RotateZ(theta) GPi(phi) = GPi(phi + theta) RotateZ(theta)
    * RotateZ(theta) GPi2(phi) = GPi2(phi + theta) RotateZ(theta)
    * RotateZ(0, theta_0) RotateZ(1, theta_1) MS(0, 1, phi_0, phi_1)
        = MS(0, 1, phi_0 + theta_0, phi_1 + theta_1) RotateZ(0, theta_0) RotateZ(1, theta_1)

    Args:
        circuit: the qoqo Circuit to be translated

    Returns:
        Circuit: the converted circuit in Braket form

    Raises:
        RuntimeError: Unsupported operation for IonQ verbatim interface.
    """
    qubit_phase: Dict[int, CalculatorFloat] = {}
    braket_circuit = Circuit()
    for op in circuit:
        if op.hqslang() == "RotateZ":
            qubit_phase[op.qubit()] = qubit_phase.get(op.qubit(), 0.0) + op.theta()
        elif op.hqslang() == "GPi":
            braket_circuit.gpi(op.qubit(), op.theta() + qubit_phase.get(op.qubit(), 0.0))
        elif op.hqslang() == "GPi2":
            braket_circuit.gpi2(op.qubit(), op.theta() + qubit_phase.get(op.qubit(), 0.0))
        elif op.hqslang() == "MolmerSorensenXX":
            braket_circuit.ms(
                op.control(),
                op.target(),
                0.0 + qubit_phase.get(op.control(), 0.0),
                0.0 + qubit_phase.get(op.target(), 0.0),
            )
        elif op.hqslang() == "VariableMSXX":
            braket_circuit.ms(
                op.control(),
                op.target(),
                0.0 - qubit_phase.get(op.control(), 0.0),
                0.0 - qubit_phase.get(op.target(), 0.0),
                op.theta(),
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
