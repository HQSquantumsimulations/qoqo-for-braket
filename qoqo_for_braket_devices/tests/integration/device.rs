// Copyright © 2023 HQS Quantum Simulations GmbH. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
// in compliance with the License. You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software distributed under the
// License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
// express or implied. See the License for the specific language governing permissions and
// limitations under the License.

use pyo3::prelude::*;
use pyo3::types::PyType;

use qoqo::devices::GenericDeviceWrapper;
use qoqo_for_braket_devices::*;
use roqoqo_for_braket_devices::*;

use test_case::test_case;

// helper functions
fn new_device(device: AWSDevice) -> Py<PyAny> {
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| -> Py<PyAny> {
        let device_type: &PyType = match device {
            AWSDevice::IonQAria1Device(_) => py.get_type::<IonQAria1DeviceWrapper>(),
            AWSDevice::IonQHarmonyDevice(_) => py.get_type::<IonQHarmonyDeviceWrapper>(),
            AWSDevice::OQCLucyDevice(_) => py.get_type::<OQCLucyDeviceWrapper>(),
            AWSDevice::RigettiAspenM3Device(_) => py.get_type::<RigettiAspenM3DeviceWrapper>(),
        };
        device_type.call0().unwrap().into()
    })
}

/// Test single_qubit_gate_names and two_qubit_gate_names functions of the devices
#[test_case(new_device(AWSDevice::from(IonQHarmonyDevice::new())); "harmony")]
#[test_case(new_device(AWSDevice::from(IonQAria1Device::new())); "aria1")]
fn test_gate_names_ionq(device: Py<PyAny>) {
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| {
        let single_qubit_gates = device
            .call_method0(py, "single_qubit_gate_names")
            .unwrap()
            .extract::<Vec<String>>(py)
            .unwrap();
        assert!(single_qubit_gates.contains(&"RotateZ".to_string()));
        assert!(single_qubit_gates.contains(&"GPi".to_string()));
        assert!(single_qubit_gates.contains(&"GPi2".to_string()));

        let two_qubit_gates = device
            .call_method0(py, "two_qubit_gate_names")
            .unwrap()
            .extract::<Vec<String>>(py)
            .unwrap();
        assert_eq!(two_qubit_gates, vec!["MolmerSorensenXX".to_string()]);

        let multi_qubit_gates = device
            .call_method0(py, "multi_qubit_gate_names")
            .unwrap()
            .extract::<Vec<String>>(py)
            .unwrap();
        assert_eq!(multi_qubit_gates, Vec::<String>::new());
    })
}

#[test_case(new_device(AWSDevice::from(OQCLucyDevice::new())); "lucy")]
fn test_gate_names_oqc(device: Py<PyAny>) {
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| {
        let single_qubit_gates = device
            .call_method0(py, "single_qubit_gate_names")
            .unwrap()
            .extract::<Vec<String>>(py)
            .unwrap();
        assert!(single_qubit_gates.contains(&"RotateZ".to_string()));
        assert!(single_qubit_gates.contains(&"SqrtPauliX".to_string()));
        assert!(single_qubit_gates.contains(&"PauliX".to_string()));

        let two_qubit_gates = device
            .call_method0(py, "two_qubit_gate_names")
            .unwrap()
            .extract::<Vec<String>>(py)
            .unwrap();
        assert!(two_qubit_gates.contains(&"EchoCrossResonance".to_string()));

        let multi_qubit_gates = device
            .call_method0(py, "multi_qubit_gate_names")
            .unwrap()
            .extract::<Vec<String>>(py)
            .unwrap();
        assert_eq!(multi_qubit_gates, Vec::<String>::new());
    })
}

#[test_case(new_device(AWSDevice::from(RigettiAspenM3Device::new())); "aspen3")]
fn test_gate_names_rigetti(device: Py<PyAny>) {
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| {
        let single_qubit_gates = device
            .call_method0(py, "single_qubit_gate_names")
            .unwrap()
            .extract::<Vec<String>>(py)
            .unwrap();
        assert!(single_qubit_gates.contains(&"RotateZ".to_string()));
        assert!(single_qubit_gates.contains(&"RotateX".to_string()));

        let two_qubit_gates = device
            .call_method0(py, "two_qubit_gate_names")
            .unwrap()
            .extract::<Vec<String>>(py)
            .unwrap();
        assert!(two_qubit_gates.contains(&"ControlledPauliZ".to_string()));
        assert!(two_qubit_gates.contains(&"ControlledPhaseShift".to_string()));
        assert!(two_qubit_gates.contains(&"XY".to_string()));

        let multi_qubit_gates = device
            .call_method0(py, "multi_qubit_gate_names")
            .unwrap()
            .extract::<Vec<String>>(py)
            .unwrap();
        assert_eq!(multi_qubit_gates, Vec::<String>::new());
    })
}

/// Test single-qubit and two-qubit gates times setters and getters
#[test_case(new_device(AWSDevice::from(IonQHarmonyDevice::new())); "harmony")]
#[test_case(new_device(AWSDevice::from(IonQAria1Device::new())); "aria1")]
fn test_gate_timings_ionq(device: Py<PyAny>) {
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| {
        device
            .call_method1(py, "set_single_qubit_gate_time", ("RotateZ", 0, 0.5))
            .unwrap();
        let single_qubit_time = device
            .call_method1(py, "single_qubit_gate_time", ("RotateZ", 0))
            .unwrap()
            .extract::<f64>(py)
            .unwrap();
        assert_eq!(single_qubit_time, 0.5);
        device
            .call_method1(py, "set_single_qubit_gate_time", ("GPi", 0, 0.5))
            .unwrap();
        let single_qubit_time = device
            .call_method1(py, "single_qubit_gate_time", ("GPi", 0))
            .unwrap()
            .extract::<f64>(py)
            .unwrap();
        assert_eq!(single_qubit_time, 0.5);
        device
            .call_method1(py, "set_single_qubit_gate_time", ("GPi2", 0, 0.5))
            .unwrap();
        let single_qubit_time = device
            .call_method1(py, "single_qubit_gate_time", ("GPi2", 0))
            .unwrap()
            .extract::<f64>(py)
            .unwrap();
        assert_eq!(single_qubit_time, 0.5);

        device
            .call_method1(
                py,
                "set_two_qubit_gate_time",
                ("MolmerSorensenXX", 0, 1, 0.5),
            )
            .unwrap();
        let two_qubit_time = device
            .call_method1(py, "two_qubit_gate_time", ("MolmerSorensenXX", 0, 1))
            .unwrap()
            .extract::<f64>(py)
            .unwrap();
        assert_eq!(two_qubit_time, 0.5);
    });
}

/// Test single-qubit and two-qubit gates times setters and getters
#[test_case(new_device(AWSDevice::from(OQCLucyDevice::new())); "lucy")]
fn test_gate_timings_oqc(device: Py<PyAny>) {
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| {
        device
            .call_method1(py, "set_single_qubit_gate_time", ("RotateZ", 0, 0.5))
            .unwrap();
        let single_qubit_time = device
            .call_method1(py, "single_qubit_gate_time", ("RotateZ", 0))
            .unwrap()
            .extract::<f64>(py)
            .unwrap();
        assert_eq!(single_qubit_time, 0.5);
        device
            .call_method1(py, "set_single_qubit_gate_time", ("SqrtPauliX", 0, 0.5))
            .unwrap();
        let single_qubit_time = device
            .call_method1(py, "single_qubit_gate_time", ("SqrtPauliX", 0))
            .unwrap()
            .extract::<f64>(py)
            .unwrap();
        assert_eq!(single_qubit_time, 0.5);
        device
            .call_method1(py, "set_single_qubit_gate_time", ("PauliX", 0, 0.5))
            .unwrap();
        let single_qubit_time = device
            .call_method1(py, "single_qubit_gate_time", ("PauliX", 0))
            .unwrap()
            .extract::<f64>(py)
            .unwrap();
        assert_eq!(single_qubit_time, 0.5);

        device
            .call_method1(
                py,
                "set_two_qubit_gate_time",
                ("EchoCrossResonance", 0, 1, 0.5),
            )
            .unwrap();
        let two_qubit_time = device
            .call_method1(py, "two_qubit_gate_time", ("EchoCrossResonance", 0, 1))
            .unwrap()
            .extract::<f64>(py)
            .unwrap();
        assert_eq!(two_qubit_time, 0.5);
    });
}

#[test_case(new_device(AWSDevice::from(RigettiAspenM3Device::new())); "aspen3")]
fn test_gate_timings_rigetti(device: Py<PyAny>) {
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| {
        device
            .call_method1(py, "set_single_qubit_gate_time", ("RotateZ", 0, 0.5))
            .unwrap();
        let single_qubit_time = device
            .call_method1(py, "single_qubit_gate_time", ("RotateZ", 0))
            .unwrap()
            .extract::<f64>(py)
            .unwrap();
        assert_eq!(single_qubit_time, 0.5);
        device
            .call_method1(py, "set_single_qubit_gate_time", ("RotateX", 0, 0.5))
            .unwrap();
        let single_qubit_time = device
            .call_method1(py, "single_qubit_gate_time", ("RotateX", 0))
            .unwrap()
            .extract::<f64>(py)
            .unwrap();
        assert_eq!(single_qubit_time, 0.5);

        device
            .call_method1(
                py,
                "set_two_qubit_gate_time",
                ("ControlledPauliX", 0, 1, 0.5),
            )
            .unwrap();
        let two_qubit_time = device
            .call_method1(py, "two_qubit_gate_time", ("ControlledPauliX", 0, 1))
            .unwrap()
            .extract::<f64>(py)
            .unwrap();
        assert_eq!(two_qubit_time, 0.5);
        device
            .call_method1(
                py,
                "set_two_qubit_gate_time",
                ("ControlledPhaseShift", 0, 1, 0.5),
            )
            .unwrap();
        let two_qubit_time = device
            .call_method1(py, "two_qubit_gate_time", ("ControlledPhaseShift", 0, 1))
            .unwrap()
            .extract::<f64>(py)
            .unwrap();
        assert_eq!(two_qubit_time, 0.5);
        device
            .call_method1(py, "set_two_qubit_gate_time", ("XY", 0, 1, 0.5))
            .unwrap();
        let two_qubit_time = device
            .call_method1(py, "two_qubit_gate_time", ("XY", 0, 1))
            .unwrap()
            .extract::<f64>(py)
            .unwrap();
        assert_eq!(two_qubit_time, 0.5);
    });
}

/// Test add_damping, add_dephasing, decoherence methods
#[test_case(new_device(AWSDevice::from(IonQHarmonyDevice::new())); "harmony")]
#[test_case(new_device(AWSDevice::from(IonQAria1Device::new())); "aria1")]
#[test_case(new_device(AWSDevice::from(OQCLucyDevice::new())); "lucy")]
#[test_case(new_device(AWSDevice::from(RigettiAspenM3Device::new())); "aspen3")]
fn test_damping_dephasing_decoherence(device: Py<PyAny>) {
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| {
        device.call_method1(py, "add_damping", (0, 0.5)).unwrap();
        device.call_method1(py, "add_dephasing", (0, 0.2)).unwrap();
        let rates = device
            .call_method1(py, "qubit_decoherence_rates", (0,))
            .unwrap()
            .extract::<Vec<Vec<f64>>>(py)
            .unwrap();
        assert_eq!(
            rates,
            vec![
                vec![0.5, 0.0, 0.0],
                vec![0.0, 0.0, 0.0],
                vec![0.0, 0.0, 0.2]
            ]
        )
    });
}

/// Test single_qubit_gate_names and two_qubit_gate_names functions of the devices
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()), new_device(AWSDevice::from(IonQHarmonyDevice::new())); "harmony")]
#[test_case(AWSDevice::from(IonQAria1Device::new()), new_device(AWSDevice::from(IonQAria1Device::new())); "aria1")]
#[test_case(AWSDevice::from(OQCLucyDevice::new()), new_device(AWSDevice::from(OQCLucyDevice::new())); "lucy")]
#[test_case(AWSDevice::from(RigettiAspenM3Device::new()), new_device(AWSDevice::from(RigettiAspenM3Device::new())); "aspen3")]
fn test_to_generic_device(device: AWSDevice, pyo3_device: Py<PyAny>) {
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| {
        let result = pyo3_device
            .call_method0(py, "to_generic_device")
            .unwrap()
            .extract::<GenericDeviceWrapper>(py)
            .unwrap();

        let rust_result: GenericDeviceWrapper = GenericDeviceWrapper {
            internal: device.to_generic_device().unwrap(),
        };
        assert_eq!(result, rust_result);
    })
}
