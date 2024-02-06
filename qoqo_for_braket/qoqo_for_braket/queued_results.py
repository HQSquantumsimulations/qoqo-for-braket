# Copyright © 2023 HQS Quantum Simulations GmbH. All Rights Reserved.
# License details given in distributed LICENSE file.

"""Provides the QueuedCircuitRun class for async runs."""

from typing import Any, Dict, Optional, List, Tuple, Union
from braket.tasks.local_quantum_task import LocalQuantumTask
from braket.tasks import QuantumTask
from braket.aws import AwsQuantumJob
from braket.jobs.local import LocalQuantumJob
from braket.jobs.quantum_job import QuantumJob
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
from qoqo import measurements
import tempfile
import os
import copy
import datetime
import shutil
import warnings


class QueuedCircuitRun:
    """Queued Result of the circuit."""

    def __init__(
        self, session: AwsSession, task: Optional[QuantumTask], metadata: Dict[Any, Any]
    ) -> None:
        """Initialise the QueuedCircuitRun class.

        Args:
            session: Braket AwsSession to use
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
                if isinstance(value, np.ndarray):
                    results[key] = value.tolist()
                else:
                    results[key] = value
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
            session = None
            task = None
        elif json_dict["type"] == "QueuedAWSCircuitRun":
            session = AwsSession(boto3.session.Session(region_name=json_dict["region"]))
            task = AwsQuantumTask(json_dict["arn"])

        instance = QueuedCircuitRun(session=session, task=task, metadata=json_dict["metadata"])
        if json_dict["results"] is not None:
            instance._results = (json_dict["results"], {}, {})

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
        """Poll the result once.

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
                    raise RuntimeError("Job has failed on AWS")
                elif state == "CANCELED":
                    raise RuntimeError("Job was cancelled by AWS")
            else:
                return None
        return self._results


class QueuedProgramRun:
    """Queued Result of the measurement."""

    def __init__(self, measurement: Any, queued_circuits: List[QueuedCircuitRun]) -> None:
        """Initialise the QueuedProgramRun class.

        Args:
            measurement: the qoqo Measurement to run
            queued_circuits: the list of associated queued circuits
        """
        self._measurement = measurement
        self._queued_circuits: List[QueuedCircuitRun] = queued_circuits
        self._registers: Tuple[
            Dict[str, List[List[bool]]],
            Dict[str, List[List[float]]],
            Dict[str, List[List[complex]]],
        ] = ({}, {}, {})
        for circuit in self._queued_circuits:
            if circuit._results is not None:
                self._registers[0].update(circuit._results[0])
                self._registers[1].update(circuit._results[1])
                self._registers[2].update(circuit._results[2])

    def poll_result(
        self,
    ) -> Optional[
        Tuple[
            Dict[str, List[List[bool]]],
            Dict[str, List[List[float]]],
            Dict[str, List[List[complex]]],
        ]
    ]:
        """Poll the result once.

        Returns:
            Optional[Tuple[Dict[str, List[List[bool]]],
                           Dict[str, List[List[float]]],
                           Dict[str, List[List[complex]]],]
                     ]: Result if all tasks were successful.

        Raises:
            RuntimeError: job failed or cancelled
        """
        all_finished = [False] * len(self._queued_circuits)
        for i, queued_circuit in enumerate(self._queued_circuits):
            res = queued_circuit.poll_result()
            if res is not None:
                self._registers[0].update(res[0])  # add results to bit registers
                self._registers[1].update(res[1])  # add results to float registers
                self._registers[2].update(res[2])  # add results to complex registers
                all_finished[i] = True

        if not all(all_finished):
            return None
        else:
            if isinstance(self._measurement, measurements.ClassicalRegister):
                return self._registers
            else:
                return self._measurement.evaluate(
                    self._registers[0], self._registers[1], self._registers[2]
                )

    def to_json(self) -> str:
        """Convert self to a json string.

        Returns:
            str: self as a json string
        """
        queued_circuits_serialised: List[str] = []
        for circuit in self._queued_circuits:
            queued_circuits_serialised.append(circuit.to_json())

        if isinstance(self._measurement, measurements.PauliZProduct):
            measurement_type = "PauliZProduct"
        elif isinstance(self._measurement, measurements.CheatedPauliZProduct):
            measurement_type = "CheatedPauliZProduct"
        elif isinstance(self._measurement, measurements.Cheated):
            measurement_type = "Cheated"
        elif isinstance(self._measurement, measurements.ClassicalRegisters):
            measurement_type = "ClassicalRegisters"
        else:
            raise TypeError("Unknown measurement type")

        json_dict = {
            "type": "QueuedAWSProgramRun",
            "measurement_type": measurement_type,
            "measurement": self._measurement.to_json(),
            "queued_circuits": queued_circuits_serialised,
        }

        return json.dumps(json_dict)

    @staticmethod
    def from_json(string: str) -> "QueuedProgramRun":
        """Convert a json string to an instance of QueuedProgramRun.

        Args:
            string: json string to convert.

        Returns:
            QueuedProgramRun: converted json string
        """
        json_dict = json.loads(string)

        queued_circuits_deserialised: List[QueuedCircuitRun] = []
        registers: Tuple[
            Dict[str, List[List[bool]]],
            Dict[str, List[List[float]]],
            Dict[str, List[List[complex]]],
        ] = ({}, {}, {})
        for circuit in json_dict["queued_circuits"]:
            circ_instance = QueuedCircuitRun.from_json(circuit)
            queued_circuits_deserialised.append(circ_instance)
            if circ_instance._results is not None:
                registers[0].update(circ_instance._results[0])
                registers[1].update(circ_instance._results[1])
                registers[2].update(circ_instance._results[2])

        if json_dict["measurement_type"] == "PauliZProduct":
            measurement = measurements.PauliZProduct.from_json(json_dict["measurement"])
        elif json_dict["measurement_type"] == "CheatedPauliZProduct":
            measurement = measurements.CheatedPauliZProduct.from_json(json_dict["measurement"])
        elif json_dict["measurement_type"] == "Cheated":
            measurement = measurements.Cheated.from_json(json_dict["measurement"])
        elif json_dict["measurement_type"] == "ClassicalRegisters":
            measurement = measurements.ClassicalRegisters.from_json(json_dict["measurement"])
        else:
            raise TypeError("Unknown measurement type")

        instance = QueuedProgramRun(measurement, queued_circuits_deserialised)
        instance._registers = registers
        return instance


class QueuedHybridRun:
    """Queued Result of the running a QuantumProgram with a hybrid job."""

    def __init__(
        self,
        session: AwsSession,
        job: QuantumJob,
        metadata: Dict[Any, Any],
        measurement: measurements,
    ) -> None:
        """Initialise the QueuedCircuitRun class.

        Args:
            session: Braket AwsSession to use
            job: Braket QuantumJob to query
            metadata: Additional information about the circuit
            measurement: The qoqo measurement to be run
        """
        self._job: QuantumJob = job
        self._results: Optional[
            Tuple[
                Dict[str, List[List[bool]]],
                Dict[str, List[List[float]]],
                Dict[str, List[List[complex]]],
            ]
        ] = None
        self.session = session
        self.internal_metadata = metadata
        self._measurement = measurement

    def to_json(self) -> str:
        """Convert self to a json string.

        Returns:
            str: self as a json string
        """
        if isinstance(self._measurement, measurements.PauliZProduct):
            measurement_type = "PauliZProduct"
        elif isinstance(self._measurement, measurements.CheatedPauliZProduct):
            measurement_type = "CheatedPauliZProduct"
        elif isinstance(self._measurement, measurements.Cheated):
            measurement_type = "Cheated"
        elif isinstance(self._measurement, measurements.ClassicalRegisters):
            measurement_type = "ClassicalRegisters"
        else:
            raise TypeError("Unknown measurement type")

        results: Optional[Dict[str, Any]] = None
        if self._results is not None:
            results = {}
            for key, value in self._results[0].items():
                if isinstance(value, np.ndarray):
                    results[key] = value.tolist()
                else:
                    results[key] = value
        if isinstance(self._job, LocalQuantumJob):
            json_dict = {
                "type": "QueuedLocalQuantumJob",
                "arn": self._job.arn,
                "region": None,
                "metadata": self.internal_metadata,
                "results": results,
                "measurement_type": measurement_type,
                "measurement": self._measurement.to_json(),
            }
        if isinstance(self._job, AwsQuantumJob):
            metadata = copy.deepcopy(self.internal_metadata)
            metadata["createdAt"] = self.internal_metadata["createdAt"].isoformat()
            json_dict = {
                "type": "QueuedAWSQuantumJob",
                "arn": self._job.arn,
                "region": self._job.arn.split(":")[3],
                "metadata": metadata,
                "results": results,
                "measurement_type": measurement_type,
                "measurement": self._measurement.to_json(),
            }

        return json.dumps(json_dict)

    @staticmethod
    def from_json(string: str) -> "QueuedHybridRun":
        """Convert a json string to an instance of QueuedHybridRun.

        Args:
            string: json string to convert.

        Returns:
            QueuedHybridRun: converted json string
        """
        json_dict = json.loads(string)
        if json_dict["type"] == "QueuedLocalQuantumJob":
            session = AwsSession(boto3.session.Session(region_name=json_dict["region"]))
            job = LocalQuantumJob(json_dict["arn"])
            metadata = {}
        elif json_dict["type"] == "QueuedAWSQuantumJob":
            session = AwsSession(boto3.session.Session(region_name=json_dict["region"]))
            job = AwsQuantumJob(json_dict["arn"])
            metadata = json_dict["metadata"]
            metadata["createdAt"] = datetime.datetime.fromisoformat(metadata["createdAt"])

        if json_dict["measurement_type"] == "PauliZProduct":
            measurement = measurements.PauliZProduct.from_json(json_dict["measurement"])
        elif json_dict["measurement_type"] == "CheatedPauliZProduct":
            measurement = measurements.CheatedPauliZProduct.from_json(json_dict["measurement"])
        elif json_dict["measurement_type"] == "Cheated":
            measurement = measurements.Cheated.from_json(json_dict["measurement"])
        elif json_dict["measurement_type"] == "ClassicalRegisters":
            measurement = measurements.ClassicalRegisters.from_json(json_dict["measurement"])
        else:
            raise TypeError("Unknown measurement type")

        instance = QueuedHybridRun(
            session=session, job=job, metadata=metadata, measurement=measurement
        )
        if json_dict["results"] is not None:
            instance._results = (json_dict["results"], {}, {})

        return instance

    def poll_result(
        self,
    ) -> Optional[
        Union[
            Tuple[
                Dict[str, List[List[bool]]],
                Dict[str, List[List[float]]],
                Dict[str, List[List[complex]]],
            ],
            Dict[str, float],
        ]
    ]:
        """Poll the result once.

        Returns:
            Optional[Tuple[Dict[str, List[List[bool]]],
                           Dict[str, List[List[float]]],
                           Dict[str, List[List[complex]]],]]: Result if task was successful.

        Raises:
            RuntimeError: job failed or cancelled
        """
        if self._results is not None:
            if isinstance(self._measurement, measurements.ClassicalRegister):
                return self._results
            else:
                return self._measurement.evaluate(
                    self._results[0], self._results[1], self._results[2]
                )
        else:
            state = self._job.state()
            if state == "COMPLETED":
                with tempfile.TemporaryDirectory() as tmpdir:
                    jobname = self._job.name
                    self._job.download_result(tmpdir)
                    if isinstance(self._job, AwsQuantumJob):
                        with open(os.path.join(os.path.join(tmpdir, jobname), "output.json")) as f:
                            outputs = json.load(f)
                    elif isinstance(self._job, LocalQuantumJob):
                        with open(
                            os.path.join(os.path.join(os.getcwd(), jobname), "output.json")
                        ) as f:
                            outputs = json.load(f)
                    self._results = outputs
                    if isinstance(self._measurement, measurements.ClassicalRegister):
                        return self._results
                    else:
                        return self._measurement.evaluate(
                            self._results[0], self._results[1], self._results[2]
                        )
            elif state == "FAILED":
                raise RuntimeError("Job has failed on AWS")
            elif state == "CANCELED":
                raise RuntimeError("Job was cancelled by AWS")
            else:
                return None

    def delete_tmp_folder(self) -> None:
        """Delete the folder created by AWS for the LocalQuantumJob."""
        jobname = self._job.name
        if isinstance(self._job, LocalQuantumJob) & (self._results is not None):
            try:
                shutil.rmtree(os.path.join(os.getcwd(), jobname))
            except FileNotFoundError:
                warnings.warn("File is not present, has it already been deleted?", stacklevel=1)
