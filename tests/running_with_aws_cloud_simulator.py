# Copyright © 2023 HQS Quantum Simulations GmbH. All Rights Reserved.
"""Test running local operation with qasm backend."""
from qoqo_for_braket import BraketBackend
from qoqo import Circuit
from qoqo import operations as ops
from braket.aws.aws_session import AwsSession
from numpy import testing as npt


import os

os.environ["AWS_REGION"] = "eu-west-2"

circuit = Circuit()
circuit += ops.DefinitionBit("ro", 3, False)
circuit += ops.PauliX(0)
circuit += ops.PauliX(1)
circuit += ops.PauliX(2)
circuit += ops.MeasureQubit(0, "ro", 0)
circuit += ops.MeasureQubit(1, "ro", 1)
circuit += ops.MeasureQubit(2, "ro", 2)
circuit += ops.PragmaSetNumberOfMeasurements(2, "ro")

aws_session = AwsSession()
backend = BraketBackend(
    aws_session=aws_session,
    device="arn:aws:braket:::device/quantum-simulator/amazon/sv1",
)
backend.change_max_shots(2)

# (bit_res, _, _) = backend.run_circuit(circuit)
# assert "ro" in bit_res.keys()
# registers = bit_res["ro"]

# assert registers.shape == (2, 3)

# for reg in registers:
#     npt.assert_array_equal(reg, [True, True, True])
