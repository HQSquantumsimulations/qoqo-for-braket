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

from typing import Tuple, Dict, List, Any, Optional, Union
import json
from qoqo import Circuit
from qoqo import operations as ops
import qoqo_qasm
from qoqo_for_braket.interface import (
    rigetti_verbatim_interface,
    ionq_verbatim_interface,
    oqc_verbatim_interface,
)

from qoqo_for_braket.post_processing import _post_process_circuit_result
from qoqo_for_braket.queued_results import QueuedCircuitRun
from braket.aws import AwsQuantumTask, AwsDevice
from braket.devices import LocalSimulator
from braket.ir import openqasm
from braket.aws.aws_session import AwsSession


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
    """

    def __init__(
        self,
        device: Optional[str] = None,
        aws_session: Optional[AwsSession] = None,
        verbatim_mode: bool = False,
    ) -> None:
        """Initialise the BraketBackend class.

        Args:
            device: Optional ARN of the Braket device to use. If none is provided, the
                    default LocalSimulator will be used.
            aws_session: Optional AwsSession to use. If none is provided, a new one will be created
            verbatim_mode: Whether to use verbatim boxes to avoid recompilation
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

    def allow_use_actual_hardware(self) -> None:
        """Allow the use of actual hardware - will cost money."""
        self.__use_actual_hardware = True

    def disallow_use_actual_hardware(self) -> None:
        """Disallow the use of actual hardware."""
        self.__use_actual_hardware = False

    def force_rigetti_verbatim(self) -> None:
        """Force the use of rigetti verbatim. Mostly used for testing purposes."""
        self.__force_rigetti_verbatim = True

    def force_ionq_verbatim(self) -> None:
        """Force the use of ionq verbatim. Mostly used for testing purposes."""
        self.__force_ionq_verbatim = True

    def force_oqc_verbatim(self) -> None:
        """Force the use of oqc verbatim. Mostly used for testing purposes."""
        self.__force_oqc_verbatim = True

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

        if self.device == "arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-3":
            circuit = circuit.remap_qubits(qoqo_to_rigetti)

        if not self.verbatim_mode:
            qasm_backend = qoqo_qasm.QasmBackend("q", "3.0Braket")
            qasm_string = qasm_backend.circuit_to_qasm_str(circuit)
            task_specification = openqasm.Program(source=qasm_string)

        elif "Aspen" in self.device or self.__force_rigetti_verbatim:
            task_specification = rigetti_verbatim_interface.call_circuit(circuit)
        elif "ionQ" in self.device or self.__force_ionq_verbatim:
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
        return (
            self.__create_device().run(task_specification, shots=shots),
            {"readout_name": readout},
        )

    def run_circuit(
        self, circuit: Circuit
    ) -> Tuple[
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

    def run_measurement_registers(
        self, measurement: Any
    ) -> Tuple[
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

        for circuit in measurement.circuits():
            if constant_circuit is None:
                run_circuit = circuit
            else:
                run_circuit = constant_circuit + circuit

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

    def run_measurement_queued(self, measurement: Any) -> Optional[Dict[str, float]]:
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
        constant_circuit = measurement.constant_circuit()
        output_bit_register_dict: Dict[str, List[List[bool]]] = {}
        output_float_register_dict: Dict[str, List[List[float]]] = {}
        output_complex_register_dict: Dict[str, List[List[complex]]] = {}

        for circuit in measurement.circuits():
            if constant_circuit is None:
                run_circuit = circuit
            else:
                run_circuit = constant_circuit + circuit

            queued = self.run_circuit_queued(run_circuit)
            i = 0
            while queued.poll_result() is None:
                i += 1
                if i > 50:
                    raise RuntimeError("Timed out waiting for job to complete")
            (
                tmp_bit_register_dict,
                tmp_float_register_dict,
                tmp_complex_register_dict,
            ) = queued.poll_result()
            output_bit_register_dict.update(tmp_bit_register_dict)
            output_float_register_dict.update(tmp_float_register_dict)
            output_complex_register_dict.update(tmp_complex_register_dict)

        return measurement.evaluate(
            output_bit_register_dict,
            output_float_register_dict,
            output_complex_register_dict,
        )

    def queued_from_json(self, string: str) -> QueuedCircuitRun:
        """Get a queued result from a json string.

        Args:
            string (str): the json string to get the queued result from.

        Returns:
            QueuedCircuitRun

        Raises:
            ValueError: AwsSession has not been specified
        """
        return_dict = json.loads(string)
        if return_dict["type"] == "QueuedAWSCircuitRun":
            if self.aws_session is not None:
                task = self.aws_session.get_quantum_task(arn=return_dict["arn"])
            else:
                raise ValueError("AwsSession has not been specified")
        return task


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
