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

"""Provides the BraketBackend class."""

import os
import shutil
import tempfile
from typing import Tuple, Dict, List, Any, Optional, Union
from qoqo import Circuit
from braket.circuits import Circuit as BraketCircuit
from qoqo import operations as ops
import qoqo_qasm
from qoqo_for_braket.interface import (
    rigetti_verbatim_interface,
    ionq_verbatim_interface,
    oqc_verbatim_interface,
)
import json
from qoqo_for_braket.post_processing import _post_process_circuit_result
from qoqo_for_braket.queued_results import QueuedCircuitRun, QueuedProgramRun, QueuedHybridRun
from braket.aws import AwsQuantumTask, AwsDevice, AwsQuantumTaskBatch, AwsQuantumJob
from braket.jobs.local import LocalQuantumJob
from braket.devices import LocalSimulator
from braket.ir import openqasm
from braket.aws.aws_session import AwsSession
import numpy as np


LOCAL_SIMULATORS_LIST: List[str] = ["braket_sv", "braket_dm", "braket_ahs"]
REMOTE_SIMULATORS_LIST: List[str] = [
    "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
    "arn:aws:braket:::device/quantum-simulator/amazon/tn1",
    "arn:aws:braket:::device/quantum-simulator/amazon/dm1",
]


class BraketBackend:
    """Qoqo backend execution qoqo objects on AWS braket.

    Args:
        device: The AWS device the circuit should run on.
                provided as aws arn or for local devices
                starting with "local:" as for the braket QuantumJob
        aws_session: An optional braket AwsSession. If set to None
                     AwsSession will be created automatically.
        verbatim_mode: Only use native gates for real devices and block
                       recompilation by devices
        batch_mode: Run circuits in batch mode when running measurements.
                    Does not work when circuits define different numbers of shots.
    """

    def __init__(
        self,
        device: Optional[str] = None,
        aws_session: Optional[AwsSession] = None,
        verbatim_mode: bool = False,
        batch_mode: bool = False,
        use_hybrid_jobs: bool = True,
    ) -> None:
        """Initialise the BraketBackend class.

        Args:
            device: Optional ARN of the Braket device to use. If none is provided, the \
                    default LocalSimulator will be used.
            aws_session: Optional AwsSession to use. If none is provided, a new one will be created
            verbatim_mode: Whether to use verbatim boxes to avoid recompilation
            batch_mode: Run circuits in batch mode when running measurements. \
                    Does not work when circuits define different numbers of shots.
            use_hybrid_jobs: Uses hybrid jobs to run measurements and register measurements.

        """
        self.aws_session = aws_session
        self.device = "braket_sv" if device is None else device
        self.verbatim_mode = verbatim_mode

        self.__use_actual_hardware = False
        self.__force_rigetti_verbatim = False
        self.__force_ionq_verbatim = False
        self.__force_oqc_verbatim = False
        self.__max_circuit_length = 100
        self.__max_number_shots = 100
        self.batch_mode = batch_mode
        self.use_hybrid_jobs = use_hybrid_jobs

    def _create_config(self) -> Dict[str, Any]:
        return {
            "device": self.device,
            "verbatim_mode": self.verbatim_mode,
            "max_shots": self.__max_number_shots,
            "max_circuit_length": self.__max_circuit_length,
            "use_actual_hardware": self.__use_actual_hardware,
            "force_rigetti_verbatim": self.__force_rigetti_verbatim,
            "force_oqc_verbatim": self.__force_oqc_verbatim,
            "force_ionq_verbatim": self.__force_ionq_verbatim,
            "batch_mode": self.batch_mode,
        }

    def _load_config(self, config: Dict[str, Any]) -> None:
        self.device = config["device"]
        self.verbatim_mode = config["verbatim_mode"]
        self.__max_number_shots = config["max_shots"]
        self.__max_circuit_length = config["max_circuit_length"]
        self.__use_actual_hardware = config["use_actual_hardware"]
        self.__force_rigetti_verbatim = config["force_rigetti_verbatim"]
        self.__force_oqc_verbatim = config["force_oqc_verbatim"]
        self.__force_ionq_verbatim = config["force_ionq_verbatim"]
        self.batch_mode = config["batch_mode"]

    def allow_use_actual_hardware(self) -> None:
        """Allow the use of actual hardware - will cost money."""
        self.__use_actual_hardware = True

    def disallow_use_actual_hardware(self) -> None:
        """Disallow the use of actual hardware."""
        self.__use_actual_hardware = False

    def force_rigetti_verbatim(self) -> None:
        """Force the use of rigetti verbatim. Mostly used for testing purposes."""
        self.__force_rigetti_verbatim = True
        self.verbatim_mode = True

    def force_ionq_verbatim(self) -> None:
        """Force the use of ionq verbatim. Mostly used for testing purposes."""
        self.__force_ionq_verbatim = True
        self.verbatim_mode = True

    def force_oqc_verbatim(self) -> None:
        """Force the use of oqc verbatim. Mostly used for testing purposes."""
        self.__force_oqc_verbatim = True
        self.verbatim_mode = True

    def change_max_shots(self, shots: int) -> None:
        """Change the maximum number of shots allowed.

        Args:
            shots: new maximum allowed number of shots
        """
        self.__max_number_shots = shots

    def change_max_circuit_length(self, length: int) -> None:
        """Change the maximum circuit length allowed.

        Args:
            length: new maximum allowed length of circuit
        """
        self.__max_circuit_length = length

    def __create_device(self) -> Union[LocalSimulator, AwsDevice]:
        """Creates the device and returns it.

        Returns:
            The instanciated device (either an AwsDevice or a LocalSimulator)

        Raises:
            ValueError: Device specified isn't allowed. You can allow it by calling the
                        `allow_use_actual_hardware` function, but please be aware that
                        this may incur significant monetary charges.
        """
        if self.device.startswith("local:") or self.device in LOCAL_SIMULATORS_LIST:
            device = LocalSimulator(self.device)
        elif self.device in REMOTE_SIMULATORS_LIST:
            device = AwsDevice(self.device)
        else:
            if self.__use_actual_hardware:
                # allow list simulator devices of AWS e.g. state vector simulator
                device = AwsDevice(self.device)
            else:
                raise ValueError(
                    "Device specified isn't allowed. You can allow it by calling the "
                    + "`allow_use_actual_hardware` function, but please be aware that "
                    + "this may incur significant monetary charges."
                )
        return device

    # runs a circuit internally and can be used to produce sync and async results
    def _run_circuit(
        self,
        circuit: Circuit,
    ) -> Tuple[AwsQuantumTask, Dict[Any, Any]]:
        """Simulate a Circuit on a AWS backend.

        The default number of shots for the simulation is 100.
        Any kind of Measurement instruction only works as intended if
        it is the last instruction in the Circuit.
        Currently only one simulation is performed, meaning different measurements on different
        registers are not supported.

        Args:
            circuit (Circuit): the Circuit to simulate.

        Returns:
            (AwsQuantumTask, {readout})

        Raises:
            ValueError: Circuit contains multiple ways to set the number of measurements
        """
        (task_specification, shots, readout) = self._prepare_circuit_for_run(circuit)
        return (
            self.__create_device().run(task_specification, shots=shots),
            {"readout_name": readout},
        )

    # runs a circuit internally and can be used to produce sync and async results
    def _run_circuits_batch(
        self,
        circuits: List[Circuit],
    ) -> Tuple[AwsQuantumTaskBatch, List[Dict[Any, Any]]]:
        """Run a list of Circuits on a AWS backend in batch mode.

        The default number of shots for the simulation is 100.
        Any kind of Measurement instruction only works as intended if
        it is the last instruction in the Circuit.
        Currently only one simulation is performed, meaning different measurements on different
        registers are not supported.

        Args:
            circuits (List[Circuit]): the Circuits to simulate.

        Returns:
            (AwsQuantumTaskBatch, {readout})

        Raises:
            ValueError: Circuit contains multiple ways to set the number of measurements
        """
        task_specifications: List[BraketCircuit] = []
        shots_list = []
        readouts = []
        for circuit in circuits:
            (task_specification, shots, readout) = self._prepare_circuit_for_run(circuit)
            task_specifications.append(task_specification)
            shots_list.append(shots)
            readouts.append({"readout_name": readout})
        unique_shots = np.unique(shots_list)
        if len(unique_shots) > 1:
            raise ValueError("Circuits contains multiple ways to set the number of measurements")
        else:
            shots = unique_shots[0]
        return (
            self.__create_device().run_batch(task_specifications, shots=int(shots)),
            readouts,
        )

    def _prepare_circuit_for_run(self, circuit: Circuit) -> Tuple[BraketCircuit, int, str]:
        """Prepares a braket circuit for running on braket.

        Args:
            circuit (Circuit): The qoqo Circuit that should be run.

        Returns:
            (BraketCircuit, int, str): The braket circuit, the number of shots and the readout.
        """
        measurement_vector: List[ops.Operation] = [
            item
            for sublist in [
                circuit.filter_by_tag("PragmaSetNumberOfMeasurements"),
                circuit.filter_by_tag("PragmaRepeatedMeasurement"),
            ]
            for item in sublist
        ]
        measure_qubit_vector: List[ops.Operation] = circuit.filter_by_tag("MeasureQubit")
        if len(measurement_vector) > 1:
            raise ValueError("Circuit contains multiple ways to set the number of measurements")

        shots = measurement_vector[0].number_measurements() if measurement_vector else 100
        if measurement_vector:
            readout = measurement_vector[0].readout()
        elif measure_qubit_vector:
            readout = measure_qubit_vector[0].readout()
        else:
            readout = "ro"

        if not self.verbatim_mode:
            qasm_backend = qoqo_qasm.QasmBackend("q", "3.0Braket")
            qasm_string = qasm_backend.circuit_to_qasm_str(circuit)
            task_specification = openqasm.Program(source=qasm_string)

        elif "Aspen" in self.device or self.__force_rigetti_verbatim:
            task_specification = rigetti_verbatim_interface.call_circuit(circuit)
        elif "ionq" in self.device or self.__force_ionq_verbatim:
            task_specification = ionq_verbatim_interface.call_circuit(circuit)

        elif "Lucy" in self.device or self.__force_oqc_verbatim:
            task_specification = oqc_verbatim_interface.call_circuit(circuit)

        if (
            self.__use_actual_hardware
            or self.__force_ionq_verbatim
            or self.__force_oqc_verbatim
            or self.__force_rigetti_verbatim
        ):
            if shots > self.__max_number_shots:
                raise ValueError(
                    "Number of shots specified exceeds the number of shots allowed for hardware"
                )
            if len(circuit) > self.__max_circuit_length:
                raise ValueError(
                    "Circuit generated is longer that the max circuit length allowed for hardware"
                )
        return (task_specification, shots, readout)

    def run_circuit(self, circuit: Circuit) -> Tuple[
        Dict[str, List[List[bool]]],
        Dict[str, List[List[float]]],
        Dict[str, List[List[complex]]],
    ]:
        """Simulate a Circuit on a AWS backend.

        The default number of shots for the simulation is 100.
        Any kind of Measurement instruction only works as intended if
        it is the last instruction in the Circuit.
        Currently only one simulation is performed, meaning different measurements on different
        registers are not supported.

        Args:
            circuit (Circuit): the Circuit to simulate.

        Returns:
            Tuple[Dict[str, List[List[bool]]],
                  Dict[str, List[List[float]]],
                  Dict[str, List[List[complex]]]]: bit, float and complex registers dictionaries.
        """
        (quantum_task, metadata) = self._run_circuit(circuit)
        results = quantum_task.result()
        return _post_process_circuit_result(results, metadata)

    def run_circuits_batch(self, circuits: List[Circuit]) -> Tuple[
        Dict[str, List[List[bool]]],
        Dict[str, List[List[float]]],
        Dict[str, List[List[complex]]],
    ]:
        """Run a list of Circuits on a AWS backend in batch mode.

        The default number of shots for the simulation is 100.
        Any kind of Measurement instruction only works as intended if
        it is the last instruction in the Circuit.
        Currently only one simulation is performed, meaning different measurements on different
        registers are not supported.

        Args:
            circuits (List[Circuit]): the Circuit to simulate.

        Returns:
            Tuple[Dict[str, List[List[bool]]],
                  Dict[str, List[List[float]]],
                  Dict[str, List[List[complex]]]]: bit, float and complex registers dictionaries.
        """
        (quantum_task_batch, batch_metadata) = self._run_circuits_batch(circuits)
        bool_register_dict: Dict[str, List[List[bool]]] = {}
        float_register_dict: Dict[str, List[List[float]]] = {}
        complex_register_dict: Dict[str, List[List[complex]]] = {}
        for quantum_task, metadata in zip(quantum_task_batch.results(), batch_metadata):
            results = quantum_task
            (
                tmp_bool_register_dict,
                tmp_float_register_dict,
                tmp_complex_register_dict,
            ) = _post_process_circuit_result(results, metadata)
            bool_register_dict.update(tmp_bool_register_dict)
            float_register_dict.update(tmp_float_register_dict)
            complex_register_dict.update(tmp_complex_register_dict)
        return (bool_register_dict, float_register_dict, complex_register_dict)

    def run_measurement_registers(self, measurement: Any) -> Tuple[
        Dict[str, List[List[bool]]],
        Dict[str, List[List[float]]],
        Dict[str, List[List[complex]]],
    ]:
        """Run all circuits of a measurement with the AWS Braket backend.

        Args:
            measurement: The measurement that is run.

        Returns:
            Tuple[Dict[str, List[List[bool]]],
                  Dict[str, List[List[float]]],
                  Dict[str, List[List[complex]]]]
        """
        constant_circuit = measurement.constant_circuit()
        output_bit_register_dict: Dict[str, List[List[bool]]] = {}
        output_float_register_dict: Dict[str, List[List[float]]] = {}
        output_complex_register_dict: Dict[str, List[List[complex]]] = {}
        run_circuits = []
        for circuit in measurement.circuits():
            if constant_circuit is None:
                run_circuits.append(circuit)
            else:
                run_circuits.append(constant_circuit + circuit)
        if self.batch_mode:
            (
                output_bit_register_dict,
                output_float_register_dict,
                output_complex_register_dict,
            ) = self.run_circuits_batch(run_circuits)
        else:
            for run_circuit in run_circuits:
                (
                    tmp_bit_register_dict,
                    tmp_float_register_dict,
                    tmp_complex_register_dict,
                ) = self.run_circuit(run_circuit)

                output_bit_register_dict.update(tmp_bit_register_dict)
                output_float_register_dict.update(tmp_float_register_dict)
                output_complex_register_dict.update(tmp_complex_register_dict)

        return (
            output_bit_register_dict,
            output_float_register_dict,
            output_complex_register_dict,
        )

    def run_measurement_registers_hybrid(self, measurement: Any) -> Tuple[
        Dict[str, List[List[bool]]],
        Dict[str, List[List[float]]],
        Dict[str, List[List[complex]]],
    ]:
        """Run all circuits of a measurement with the AWS Braket backend using hybrid jobs.

        Using hybrid jobs allows us to naturally group the circuits from a measurement.

        Args:
            measurement: The measurement that is run.

        Returns:
            Tuple[Dict[str, List[List[bool]]],
                  Dict[str, List[List[float]]],
                  Dict[str, List[List[complex]]]]
        """
        job = self._run_measurement_registers_hybrid(measurement)
        with tempfile.TemporaryDirectory() as tmpdir:
            jobname = job.name
            job.download_result(extract_to=tmpdir)
            if isinstance(job, AwsQuantumJob):
                with open(os.path.join(os.path.join(tmpdir, jobname), "output.json")) as f:
                    outputs = json.load(f)
            elif isinstance(job, LocalQuantumJob):
                with open(os.path.join(os.path.join(os.getcwd(), jobname), "output.json")) as f:
                    outputs = json.load(f)
                shutil.rmtree(os.path.join(os.getcwd(), jobname))

        return outputs

    def run_measurement_registers_hybrid_queued(self, measurement: Any) -> QueuedHybridRun:
        """Run all circuits of a measurement with the AWS Braket backend using hybrid jobs.

        Using hybrid jobs allows us to naturally group the circuits from a measurement.

        Args:
            measurement: The measurement that is run.

        Returns:
            QueuedQuantumProgramHybrid
        """
        job = self._run_measurement_registers_hybrid(measurement, wait_until_complete=False)
        return QueuedHybridRun(self.aws_session, job, job.metadata(), measurement)

    def _run_measurement_registers_hybrid(
        self, measurement: Any, wait_until_complete: bool = True
    ) -> AwsQuantumJob:
        """Run all circuits of a measurement with the AWS Braket backend using hybrid jobs.

        Using hybrid jobs allows us to naturally group the circuits from a measurement.

        Args:
            measurement: The measurement that is run.
            wait_until_complete: Whether to wait for the job to complete.\
                Should be False when using queued runs.

        Returns:
            Tuple[Dict[str, List[List[bool]]],
                  Dict[str, List[List[float]]],
                  Dict[str, List[List[complex]]]]
        """
        # get path of this file
        file_path = os.path.dirname(os.path.realpath(__file__))
        measurement_json = measurement.to_json()
        helper_file_path = os.path.join(file_path, "qoqo_hybrid_helper.py")
        # create named temporary directory with tempfile
        os.mkdir("_tmp_hybrid_helper")
        shutil.copyfile(
            helper_file_path, os.path.join("_tmp_hybrid_helper", "qoqo_hybrid_helper.py")
        )
        requirement_lines = ["qoqo >= 1.9\n", "qoqo-for-braket >= 0.4"]
        with open(os.path.join("_tmp_hybrid_helper", "requirements.txt"), "w") as f:
            # write each line from requirement_lines to separate lines in file
            f.writelines(requirement_lines)
        with open(".tmp_measurement_input.json", "w") as f:
            f.write(measurement_json)
        with open(".tmp_config_input.json", "w") as f:
            json.dump(self._create_config(), f)
        device_for_run = self.__create_device()
        if isinstance(device_for_run, LocalSimulator):
            job = LocalQuantumJob.create(
                device=self.device,
                source_module="_tmp_hybrid_helper",
                entry_point="_tmp_hybrid_helper.qoqo_hybrid_helper:run_measurement_register",
                input_data={
                    "measurement": ".tmp_measurement_input.json",
                    "config": ".tmp_config_input.json",
                },
            )
        elif isinstance(device_for_run, AwsDevice):
            job = AwsQuantumJob.create(
                device=device_for_run._arn,
                source_module="_tmp_hybrid_helper",
                entry_point="_tmp_hybrid_helper.qoqo_hybrid_helper:run_measurement_register",
                wait_until_complete=wait_until_complete,
                input_data={
                    "measurement": ".tmp_measurement_input.json",
                    "config": ".tmp_config_input.json",
                },
            )
        shutil.rmtree("_tmp_hybrid_helper")
        os.remove(".tmp_measurement_input.json")
        os.remove(".tmp_config_input.json")
        return job

    def run_measurement(self, measurement: Any) -> Optional[Dict[str, float]]:
        """Run a circuit with the AWS Braket backend.

        Args:
            measurement: The measurement that is run.

        Returns:
            Optional[Dict[str, float]]
        """
        (
            output_bit_register_dict,
            output_float_register_dict,
            output_complex_register_dict,
        ) = self.run_measurement_registers(measurement)

        return measurement.evaluate(
            output_bit_register_dict,
            output_float_register_dict,
            output_complex_register_dict,
        )

    def run_circuit_queued(self, circuit: Circuit) -> QueuedCircuitRun:
        """Run a Circuit on a AWS backend and return a queued Job Result.

        The default number of shots for the simulation is 100.
        Any kind of Measurement instruction only works as intended if
        it are the last instructions in the Circuit.
        Currently only one simulation is performed, meaning different measurements on different
        registers are not supported.

        Args:
            circuit (Circuit): the Circuit to simulate.

        Returns:
            QueuedCircuitRun
        """
        (quantum_task, metadata) = self._run_circuit(circuit)
        return QueuedCircuitRun(self.aws_session, quantum_task, metadata)

    def run_measurement_queued(self, measurement: Any) -> QueuedProgramRun:
        """Run a qoqo measurement on a AWS backend and return a queued Job Result.

        The default number of shots for the simulation is 100.
        Any kind of Measurement instruction only works as intended if
        it are the last instructions in the Circuit.
        Currently only one simulation is performed, meaning different measurements on different
        registers are not supported.

        Args:
            measurement (qoqo.measurement): the measurement to simulate.

        Returns:
            QueuedProgramRun
        """
        queued_circuits = []
        constant_circuit = measurement.constant_circuit()
        for circuit in measurement.circuits():
            if constant_circuit is None:
                run_circuit = circuit
            else:
                run_circuit = constant_circuit + circuit

            queued_circuits.append(self.run_circuit_queued(run_circuit))
        return QueuedProgramRun(measurement, queued_circuits)
