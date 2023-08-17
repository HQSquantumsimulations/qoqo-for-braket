# Copyright © 2023 HQS Quantum Simulations GmbH. All Rights Reserved.
# License details given in distributed LICENSE file.

"""Provides the BraketBackend class."""

from typing import Any, Dict, Optional, List, Tuple
from braket.tasks.local_quantum_task import LocalQuantumTask
from braket.tasks import QuantumTask
import json
import boto3
from qoqo_for_braket.post_processing import _post_process_circuit_result
from braket.aws.aws_session import AwsSession
from braket.aws.aws_quantum_task import AwsQuantumTask
from braket.schema_common import BraketSchemaBase
from braket.tasks import GateModelQuantumTaskResult
from braket.tracking.tracking_events import _TaskCompletionEvent
from braket.tracking.tracking_context import broadcast_event
import numpy as np


class QueuedCircuitRun:
    """Queued Result of the circuit."""

    def __init__(
        self, session: AwsSession, task: Optional[QuantumTask], metadata: Dict[Any, Any]
    ) -> None:
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
        self.internal_metadata = metadata
        if self._task is not None:
            self.aws_metadata = self._task.metadata()
        else:
            self.aws_metadata = None
        if isinstance(self._task, LocalQuantumTask):
            results = self._task.result()
            processed_results = _post_process_circuit_result(results, self.internal_metadata)
            self._results = processed_results

    def to_json(self) -> str:
        """Convert self to a json string.

        Returns:
            str: self as a json string
        """
        results = None
        if self._results is not None:
            results = {}
            for key, value in self._results[0].items():
                results[key] = value.tolist()
        if isinstance(self._task, LocalQuantumTask):
            json_dict = {
                "type": "QueuedLocalCircuitRun",
                "arn": None,
                "region": None,
                "metadata": self.internal_metadata,
                "results": results,
            }
        if isinstance(self._task, AwsQuantumTask):
            json_dict = {
                "type": "QueuedAWSCircuitRun",
                "arn": self._task.id,
                "region": self._task.id.split(":")[3],
                "metadata": self.internal_metadata,
                "results": results,
            }

        return json.dumps(json_dict)

    @staticmethod
    def from_json(string: str) -> "QueuedCircuitRun":
        """Convert a json string to an instance of QueuedCircuitRun.

        Args:
            string: json string to convert.

        Returns:
            QueuedCircuitRun: converted json string
        """
        json_dict = json.loads(string)
        if json_dict["type"] == "QueuedLocalCircuitRun":
            session = AwsSession()
            task = None
        elif json_dict["type"] == "QueuedAWSCircuitRun":
            session = AwsSession(boto3.session.Session(region_name=json_dict["region"]))
            task = AwsQuantumTask(json_dict["arn"])

        instance = QueuedCircuitRun(session=session, task=task, metadata=json_dict["metadata"])
        if json_dict["results"] is not None:
            results = {}
            for key, value in json_dict["results"].items():
                results[key] = np.array(value)
            instance._results = (results, {}, {})

        return instance

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
            if isinstance(self._task, AwsQuantumTask):
                state = self._task.state()
                if state == "COMPLETED":
                    result_string = self.session.retrieve_s3_object_body(
                        self.aws_metadata["outputS3Bucket"],
                        self.aws_metadata["outputS3Directory"] + f"/{self._task.RESULTS_FILENAME}",
                    )
                    schema_result = BraketSchemaBase.parse_raw_schema(result_string)
                    formatted_result = GateModelQuantumTaskResult.from_object(schema_result)
                    task_event = {
                        "arn": self._task.id,
                        "status": state,
                        "execution_duration": None,
                    }
                    broadcast_event(_TaskCompletionEvent(**task_event))
                    processed_results = _post_process_circuit_result(
                        formatted_result, self.internal_metadata
                    )
                    self._results = processed_results
                elif state == "FAILED":
                    raise RuntimeError("")
                elif state == "CANCELED":
                    raise RuntimeError("")
            else:
                return None
        return self._results
