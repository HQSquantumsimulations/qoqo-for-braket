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
"""Interface for the Rigetti AWS braket devices."""

from braket.circuits import Circuit
import qoqo
import numpy as np

ALLOWED_OPERATIONS = [
    "PragmaRepeatedMeasurement",
    "PragmaSetNumberOfMeasurements",
    "MeasureQubit",
    "DefinitionBit",
]


def call_circuit(circuit: qoqo.Circuit) -> Circuit:
    """Convert a qoqo Circuit to a Braket Circuit with verbatim instructions for Rigetti.

    Args:
        circuit: the qoqo Circuit to be translated

    Returns:
        Circuit: the converted circuit in Braket form

    Raises:
        RuntimeError: Unsupported operation for Rigetti verbatim interface.
    """
    braket_circuit = Circuit()
    for op in circuit:
        if op.hqslang() == "PauliX":
            braket_circuit.rx(op.qubit(), np.pi)
        elif op.hqslang() == "SqrtPauliX":
            braket_circuit.rx(op.qubit(), np.pi / 2)
        elif op.hqslang() == "InvSqrtPauliX":
            braket_circuit.rx(op.qubit(), -np.pi / 2)
        elif op.hqslang() == "RotateZ":
            braket_circuit.rz(op.qubit(), op.theta())
        elif op.hqslang() == "ControlledPauliZ":
            braket_circuit.cz(op.control(), op.target())
        elif op.hqslang() == "ControlledPhaseShift":
            braket_circuit.cphaseshift(op.control(), op.target(), op.theta())
        elif op.hqslang() == "XY":
            braket_circuit.xy(op.control(), op.target(), op.theta())
        elif op.hqslang() in ALLOWED_OPERATIONS:
            pass
        else:
            raise RuntimeError(
                f"Unsupported operation {op.hqslang()} for Rigetti verbatim interface."
            )

    return_circuit = Circuit()
    # This is necessary to avoid recompilation see
    #  https://github.com/aws/amazon-braket-examples/blob/main/examples/braket_features/Verbatim_Compilation.ipynb
    return_circuit.add_verbatim_box(braket_circuit, target_mapping=qoqo_to_rigetti)
    return return_circuit


qoqo_to_rigetti = {
    0: 0,
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
    7: 7,
    8: 10,
    9: 11,
    10: 12,
    11: 13,
    12: 14,
    13: 15,
    14: 16,
    15: 17,
    16: 20,
    17: 21,
    18: 22,
    19: 23,
    20: 24,
    21: 25,
    22: 26,
    23: 27,
    24: 30,
    25: 31,
    26: 32,
    27: 33,
    28: 34,
    29: 35,
    30: 36,
    31: 37,
    32: 40,
    33: 41,
    34: 42,
    35: 43,
    36: 44,
    37: 45,
    38: 46,
    39: 47,
    40: 100,
    41: 101,
    42: 102,
    43: 103,
    44: 104,
    45: 105,
    46: 106,
    47: 107,
    48: 110,
    49: 111,
    50: 112,
    51: 113,
    52: 114,
    53: 115,
    54: 116,
    55: 117,
    56: 120,
    57: 121,
    58: 122,
    59: 123,
    60: 124,
    61: 125,
    62: 126,
    63: 127,
    64: 130,
    65: 131,
    66: 132,
    67: 133,
    68: 134,
    69: 135,
    70: 136,
    71: 137,
    72: 140,
    73: 141,
    74: 142,
    75: 143,
    76: 144,
    77: 145,
    78: 146,
    79: 147,
}
