# Changelog

This changelog track changes to the qoqo-for-braket project starting at version 0.1.0

## Unpublished

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