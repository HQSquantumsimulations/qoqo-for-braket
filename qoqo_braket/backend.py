# Copyright © 2023 HQS Quantum Simulations GmbH. All Rights Reserved.
# License details given in distributed LICENSE file.

"""Provides the BraketBackend class."""

from typing import Tuple, Dict, List, Any, Optional, Union
from qoqo import Circuit
from qoqo import operations as ops
import qoqo_qasm
from qoqo_braket.interface import (
    rigetti_verbatim_interface,
    ionq_verbatim_interface,
    oqc_verbatim_interface,
)

from qoqo_braket.post_processing import _post_process_circuit_result
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
            ValueError: Device specified isn't allowed
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
                raise ValueError("Device specified isn't allowed")
        return device

    # runs a circuit internally and can be used to produce sync and async results
    def _run_circuit(
        self,
        circuit: Circuit,
    ) -> Tuple[AwsQuantumTask, Dict[Any, Any]]:
        """Simulate a Circuit on a AWS backend.

        The default number of shots for the simulation is 100.
        Any kind of Measurement instruction only works as intended if
        it are the last instructions in the Circuit.
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
        it are the last instructions in the Circuit.
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
        output_bit_register_dict: Dict[str, List[List[bool]]] = dict()
        output_float_register_dict: Dict[str, List[List[float]]] = dict()
        output_complex_register_dict: Dict[str, List[List[complex]]] = dict()

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
