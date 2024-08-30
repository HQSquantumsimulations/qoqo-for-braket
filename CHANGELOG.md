# Changelog

This changelog track changes to the qoqo-for-braket project starting at version 0.1.0

## Unpublished

## 0.6.1

* Fixed missing support for using InputBit to add bit register entries that are not measured from quantum register
* Fixed not being able to run `.run_program` with a single set of parameters

## 0.6.0

* Added iqm_verbatim interface to qoqo_for_braket
* Added import of the `GarnetDevice` from qoqo_iqm to qoqo_for_braket_devices

## 0.5.0

* Modified `run_measurement_registers_hybrid()` to handle non-ClassicalRegister measurements
* Added `run_program()`, `run_program_queued()` allowing for multiple runs in one call thanks to a list of lists of parameter values

## 0.4.3

* Fixed overwriting registers bug
* Fixed missing registers checks from QueuedProgramRun.poll_results()

## 0.4.2

* Fixed ClassicalRegister typo in the Queued classes

## 0.4.1

* Added keys to the config dictionary to allow for correct verbatim mode runs
* Added LocalQuantumJob functionality for run_measurement_hybrid_queued and QueuedHybridRun

## 0.4.0

* Bugfix for the IonQ interface (VirtualZ for VariableMSXX)
* Added support using hybrid jobs to completely run QuantumPrograms on the cloud (qoqo QuantumProgram is serailized to json, uploaded in a AwsQuantumJob and deserialized and executed on AWS instance with qoqo and qoqo-for-braket installed from requirements)

## 0.3.1

* Updated to pyo3 0.20

## 0.3.0

* Adding option to run circuits from measurements in aws braket batch mode

## 0.2.6

* Added VariableMSXX gate for ionq interface
* Modified rigetti interface gates from rotatex to paulix, sqrtpaulix and invsqrtpaulix
* Modified running with aws async program example

## 0.2.5

* Moved rigetti remapping dictionary to verbatim box in rigetti interface

## 0.2.4

* Fixed typo in `ionq` name in real devices

## 0.2.3

* Bugfix for commutation of RZ past MSXX gate in IonQ interface

## 0.2.2

* Added run_queued_measurement function and unittest

## 0.2.1

* Added devices and async functionality

## 0.2.0

* Changed name to qoqo-for-braket