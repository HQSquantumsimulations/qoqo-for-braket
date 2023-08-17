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
from qoqo_for_braket import BraketBackend, QueuedCircuitRun
from qoqo import Circuit
from qoqo import operations as ops
import pytest
import sys
from braket.aws.aws_session import AwsSession


def test_serialisation() -> None:
    """Test to_json and from_json methods."""
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
        device=None,
    )
    queued = backend.run_circuit_queued(circuit)
    serialised = queued.to_json()
    deserialised = QueuedCircuitRun.from_json(serialised)
    assert deserialised._results[1] == queued._results[1]
    assert deserialised._results[2] == queued._results[2]
    assert deserialised._results[0].keys() == queued._results[0].keys()
    assert (deserialised._results[0]["ro"].all() == queued._results[0]["ro"].all()).all()


@pytest.mark.skip()
def test_serialisation_async() -> None:
    """Test to_json and from_json methods for an async job."""
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
    queued = backend.run_circuit_queued(circuit)

    # Before polling: result is None
    serialised = queued.to_json()
    deserialised = QueuedCircuitRun.from_json(serialised)
    assert deserialised._results == queued._results

    # After polling: result is not None
    i = 0
    while queued.poll_result() is None:
        i += 1
        if i > 50:
            raise RuntimeError("Timed out waiting for job to complete")
    serialised = queued.to_json()
    deserialised = QueuedCircuitRun.from_json(serialised)
    assert deserialised._results[1] == queued._results[1]
    assert deserialised._results[2] == queued._results[2]
    assert deserialised._results[0].keys() == queued._results[0].keys()
    assert (deserialised._results[0]["ro"].all() == queued._results[0]["ro"].all()).all()


if __name__ == "__main__":
    pytest.main(sys.argv)
