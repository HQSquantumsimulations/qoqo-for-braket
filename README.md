<img src="qoqo_Logo_vertical_color.png" alt="qoqo logo" width="300" />

# qoqo-for-braket
A braket backend for the qoqo quantum computing toolkit by [HQS Quantum Simulations](https://quantumsimulations.de). The API documentation is available [here](https://hqsquantumsimulations.github.io/qoqo-for-braket/qoqo_for_braket_api/html/generated/qoqo_for_braket.html).

## Usage on AWS

There are two ways to use this repository to run jobs on AWS Braket: using hybrid jobs and using standard jobs.

### Hybrid jobs using qoqo-for-braket

The prefered mode to use qoqo-for-braket is the hybrid job submission mode. This mode corresponds closest to using the qoqo concept of a `QuantumProgram`, where several circuits are bundled, executed and post-processed together. A `QuantumProgram` can easily be serialized to json. qoqo-for-braket uses the flexibility of the AWS braket hybrid job model to upload the serialized version of a `QuantumProgram` and run it completely on the hybrid instance with `qoqo` and `qoqo-for-braket` installed on the hybrid instance. 

After having installed qoqo-for-braket from either source or pypi, you can run the following snippet (provided you have AWS credentials):

```python
from qoqo_for_braket import BraketBackend
from qoqo import Circuit
from qoqo import operations as ops
from braket.aws.aws_session import AwsSession
from qoqo import measurements

circuit = Circuit()
circuit += ops.DefinitionBit("ro", 3, False)
circuit += ops.PauliX(0)
circuit += ops.PauliX(1)
circuit += ops.PauliX(2)
circuit += ops.MeasureQubit(0, "ro", 0)
circuit += ops.MeasureQubit(1, "ro", 1)
circuit += ops.MeasureQubit(2, "ro", 2)
circuit += ops.PragmaSetNumberOfMeasurements(2, "ro")

measurement = measurements.ClassicalRegister(constant_circuit=None, circuits=[circuit])

aws_session = AwsSession()
backend = BraketBackend(
    aws_session=aws_session,
    device="arn:aws:braket:::device/quantum-simulator/amazon/sv1",
)
backend.change_max_shots(2)

(bit_res, _, _) = backend.run_measurement_registers_hybrid(measurement)

```
Note, it is also possible to run async hybrid jobs using the `run_measurement_registers_hybrid_queued` instead of `run_measurement_registers_hybrid`.

### Standard jobs using qoqo-for-braket

After having installed qoqo-for-braket from either source or pypi, you can run the following snippet:

```python
from qoqo_for_braket import BraketBackend
from qoqo import Circuit
from qoqo import operations as ops

circuit = Circuit()
circuit += ops.PauliX(0)
circuit += ops.PauliX(2)
circuit += ops.PauliX(2)
circuit += ops.ControlledPauliZ(0, 1)
circuit += ops.MeasureQubit(0, "ro", 0)
circuit += ops.MeasureQubit(1, "ro", 1)
circuit += ops.MeasureQubit(2, "ro", 2)
circuit += ops.PragmaSetNumberOfMeasurements(2, "ro")

backend = BraketBackend(None)
(bit_res, _, _) = backend.run_circuit(circuit)
```
Note, it is also possible to run async standard jobs using the `run_circuit_queued` instead of `run_circuit`. There are also measurement equivalent functions, `run_measurement` and `run_measurement_queued`.

## General Notes

This software is still in the beta stage. Functions and documentation are not yet complete and breaking changes can occur.

## Contributing

We welcome contributions to the project. If you want to contribute code, please have a look at CONTRIBUTE.md for our code contribution guidelines.
