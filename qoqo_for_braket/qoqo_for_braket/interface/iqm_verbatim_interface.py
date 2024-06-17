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
"""Interface for the IQM AWS braket devices."""

from braket.circuits import Circuit as BraketCircuit
import qoqo

ALLOWED_OPERATIONS = [
    "PragmaRepeatedMeasurement",
    "PragmaSetNumberOfMeasurements",
    "MeasureQubit",
    "DefinitionBit",
    "PragmaGlobalPhase",
]


def call_circuit(circuit: qoqo.Circuit) -> BraketCircuit:
    """Convert a qoqo Circuit to a Braket Circuit with verbatim instructions for IQM.

    Args:
        circuit: the qoqo Circuit to be translated

    Returns:
        BraketCircuit: the converted circuit in Braket form

    Raises:
        RuntimeError: Unsupported operation for IQM verbatim interface.
    """
    braket_circuit = BraketCircuit()
    for op in circuit:
        if op.hqslang() == "RotateXY":
            braket_circuit.prx(op.qubit(), op.theta(), op.phi())
        elif op.hqslang() == "ControlledPauliZ":
            braket_circuit.cz(op.control(), op.target())
        elif op.hqslang() in ALLOWED_OPERATIONS:
            pass
        else:
            raise RuntimeError(f"Unsupported operation {op.hqslang()} for IQM verbatim interface.")

    return_circuit = BraketCircuit()
    # This is necessary to avoid recompilation see
    # https://github.com/aws/amazon-braket-examples/blob/main/examples/
    # braket_features/Verbatim_Compilation.ipynb
    return_circuit.add_verbatim_box(braket_circuit)
    return return_circuit
