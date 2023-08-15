# Copyright © 2023 HQS Quantum Simulations GmbH. All Rights Reserved.
# License details given in distributed LICENSE file.

"""Provides the BraketBackend class."""

from typing import Any, Dict, Optional, List, Tuple
from braket.tasks.local_quantum_task import LocalQuantumTask
from braket.tasks import QuantumTask
import json
from qoqo_for_braket.post_processing import _post_process_circuit_result
from braket.aws.aws_session import AwsSession
from braket.schema_common import BraketSchemaBase
from braket.tasks import GateModelQuantumTaskResult
from braket.tracking.tracking_events import _TaskCompletionEvent
from braket.tracking.tracking_context import broadcast_event


class QueuedCircuitRun:
    """Queued Result of the circuit."""

    def __init__(self, session: AwsSession, task: QuantumTask, metadata: Dict[Any, Any]) -> None:
        """Initialise the QueuedCircuitRun class.

        Args:
            task: Braket QuantumTask to query
            metadata: Additional information about the circuit
        """
        self._task: Optional[QuantumTask] = task
        self._results: Optional[
            Tuple[
                Dict[str, List[List[bool]]],
                Dict[str, List[List[float]]],
                Dict[str, List[List[complex]]],
            ]
        ] = None
        self.session = session
        self.metadata = metadata
        if isinstance(self._task, LocalQuantumTask):
            results = self._task.result()
            processed_results = _post_process_circuit_result(results, self.metadata)
            self._results = processed_results

    def to_json(self) -> str:
        """Convert self to a json string.

        Returns:
            str: self as a json string
        """
        if isinstance(self._task, LocalQuantumTask):
            results = self._results
            json_dict = {type: "QueuedLocalCircuitRun", "arn": None, "results": results}
        if isinstance(self._task, QuantumTask):
            json_dict = {
                type: "QueuedAWSCircuitRun",
                "arn": self._task.id(),
                "results": self._results,
            }

        return json.dumps(json_dict)

    def poll_result(
        self,
    ) -> Optional[
        Tuple[
            Dict[str, List[List[bool]]],
            Dict[str, List[List[float]]],
            Dict[str, List[List[complex]]],
        ]
    ]:
        """Poll the result until it's no longer pending.

        Returns:
            Optional[Tuple[Dict[str, List[List[bool]]],
                           Dict[str, List[List[float]]],
                           Dict[str, List[List[complex]]],]]: Result if task was successful.

        Raises:
            RuntimeError: job failed or cancelled
        """
        if self._results is not None:
            return self._results
        else:
            if isinstance(self._task, QuantumTask):
                state = self._task.state()
                if state == "COMPLETED":
                    result_string = self.session.retrieve_s3_object_body(
                        self.metadata["outputS3Bucket"],
                        self.metadata["outputS3Directory"] + f"/{self._task.RESULTS_FILENAME}"
                    )
                    schema_result = BraketSchemaBase.parse_raw_schema(result_string)
                    formatted_result = GateModelQuantumTaskResult.from_object(schema_result)
                    task_event = {"arn": self._task.id, "status": state, "execution_duration": None}
                    broadcast_event(_TaskCompletionEvent(**task_event))
                    processed_results = _post_process_circuit_result(formatted_result, self.metadata)
                    self._results = processed_results
                elif state == "FAILED":
                    raise RuntimeError("")
                elif state == "CANCELED":
                    raise RuntimeError("")
            else:
                return None
        return self._results
