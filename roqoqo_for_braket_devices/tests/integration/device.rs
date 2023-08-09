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

use ndarray::array;
use roqoqo::devices::{Device, QoqoDevice};
use roqoqo_for_braket_devices::*;
use test_case::test_case;

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_default(device: AWSDevice) {
    match device {
        AWSDevice::OQCLucyDevice(x) => assert_eq!(x, OQCLucyDevice::default()),
        AWSDevice::IonQAria1Device(x) => assert_eq!(x, IonQAria1Device::default()),
        AWSDevice::IonQHarmonyDevice(x) => assert_eq!(x, IonQHarmonyDevice::default()),
        AWSDevice::RigettiAspenM3Device(x) => assert_eq!(x, RigettiAspenM3Device::default()),
    }
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_from(device: AWSDevice) {
    match device {
        AWSDevice::OQCLucyDevice(x) => _ = AWSDevice::from(&x),
        AWSDevice::IonQAria1Device(x) => _ = AWSDevice::from(&x),
        AWSDevice::IonQHarmonyDevice(x) => _ = AWSDevice::from(&x),
        AWSDevice::RigettiAspenM3Device(x) => _ = AWSDevice::from(&x),
    }
}

#[test_case(AWSDevice::from(IonQAria1Device::new()), "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-1"; "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()), "arn:aws:braket:us-east-1::device/qpu/ionq/Harmony"; "IonQHarmonyDevice")]
#[test_case(AWSDevice::from(OQCLucyDevice::new()), "arn:aws:braket:eu-west-2::device/qpu/oqc/Lucy"; "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()), "arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-3"; "RigettiAspenM3Device")]
fn test_device_name(device: AWSDevice, name: &str) {
    assert_eq!(device.name(), name);
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
fn test_single_qubit_gate_time_ionq(device: AWSDevice) {
    assert_eq!(device.single_qubit_gate_time("RotateZ", &0), 1.0.into());
    assert_eq!(device.single_qubit_gate_time("GPi", &0), 1.0.into());
    assert_eq!(device.single_qubit_gate_time("GPi2", &0), 1.0.into());
}

#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_single_qubit_gate_time_oqc(device: AWSDevice) {
    assert_eq!(device.single_qubit_gate_time("RotateZ", &0), 1.0.into());
    assert_eq!(device.single_qubit_gate_time("SqrtPauliX", &0), 1.0.into());
    assert_eq!(device.single_qubit_gate_time("PauliX", &0), 1.0.into());
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
fn test_set_single_qubit_gate_time_ionq(mut device: AWSDevice) {
    assert!(device.set_single_qubit_gate_time("RotateZ", 0, 0.5).is_ok());
    assert_eq!(device.single_qubit_gate_time("RotateZ", &0).unwrap(), 0.5);
    assert!(device.set_single_qubit_gate_time("RotateZ", 0, 0.2).is_ok());
    assert_eq!(device.single_qubit_gate_time("RotateZ", &0).unwrap(), 0.2);

    assert!(device.set_single_qubit_gate_time("GPi", 0, 0.5).is_ok());
    assert_eq!(device.single_qubit_gate_time("GPi", &0).unwrap(), 0.5);
    assert!(device.set_single_qubit_gate_time("GPi", 0, 0.2).is_ok());
    assert_eq!(device.single_qubit_gate_time("GPi", &0).unwrap(), 0.2);

    assert!(device.set_single_qubit_gate_time("GPi2", 0, 0.5).is_ok());
    assert_eq!(device.single_qubit_gate_time("GPi2", &0).unwrap(), 0.5);
    assert!(device.set_single_qubit_gate_time("GPi2", 0, 0.2).is_ok());
    assert_eq!(device.single_qubit_gate_time("GPi2", &0).unwrap(), 0.2);

    assert!(device
        .set_single_qubit_gate_time("PauliZ", 34, 0.0)
        .is_err());
}

#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_set_single_qubit_gate_time_oqc(mut device: AWSDevice) {
    assert!(device.set_single_qubit_gate_time("RotateZ", 0, 0.5).is_ok());
    assert_eq!(device.single_qubit_gate_time("RotateZ", &0).unwrap(), 0.5);
    assert!(device.set_single_qubit_gate_time("RotateZ", 0, 0.2).is_ok());
    assert_eq!(device.single_qubit_gate_time("RotateZ", &0).unwrap(), 0.2);

    assert!(device
        .set_single_qubit_gate_time("SqrtPauliX", 0, 0.5)
        .is_ok());
    assert_eq!(
        device.single_qubit_gate_time("SqrtPauliX", &0).unwrap(),
        0.5
    );
    assert!(device
        .set_single_qubit_gate_time("SqrtPauliX", 0, 0.2)
        .is_ok());
    assert_eq!(
        device.single_qubit_gate_time("SqrtPauliX", &0).unwrap(),
        0.2
    );

    assert!(device.set_single_qubit_gate_time("PauliX", 0, 0.5).is_ok());
    assert_eq!(device.single_qubit_gate_time("PauliX", &0).unwrap(), 0.5);
    assert!(device.set_single_qubit_gate_time("PauliX", 0, 0.2).is_ok());
    assert_eq!(device.single_qubit_gate_time("PauliX", &0).unwrap(), 0.2);

    assert!(device
        .set_single_qubit_gate_time("PauliZ", 34, 0.0)
        .is_err());
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
fn test_single_qubit_gate_names_ionq(device: AWSDevice) {
    assert_eq!(
        device.single_qubit_gate_names(),
        vec!["RotateZ".to_string(), "GPi".to_string(), "GPi2".to_string(),]
    );
}

#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_single_qubit_gate_names_oqc(device: AWSDevice) {
    assert_eq!(
        device.single_qubit_gate_names(),
        vec![
            "RotateZ".to_string(),
            "SqrtPauliX".to_string(),
            "PauliX".to_string(),
        ]
    );
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
fn test_two_qubit_gate_time_ionq(device: AWSDevice) {
    assert_eq!(
        device.two_qubit_gate_time("MolmerSorensenXX", &0, &1),
        1.0.into()
    );
}

#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_two_qubit_gate_time_oqc(device: AWSDevice) {
    assert_eq!(device.two_qubit_gate_time("MolmerSorensenXX", &0, &1), None);
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
fn test_set_two_qubit_gate_time_ionq(mut device: AWSDevice) {
    // Correct setters
    assert!(device
        .set_two_qubit_gate_time("MolmerSorensenXX", 0, 1, 0.5)
        .is_ok());
    assert_eq!(
        device
            .two_qubit_gate_time("MolmerSorensenXX", &0, &1)
            .unwrap(),
        0.5
    );
    assert!(device
        .set_two_qubit_gate_time("MolmerSorensenXX", 0, 1, 0.2)
        .is_ok());
    assert_eq!(
        device
            .two_qubit_gate_time("MolmerSorensenXX", &0, &1)
            .unwrap(),
        0.2
    );

    // Qubit's value too big
    assert!(device
        .set_two_qubit_gate_time("MolmerSorensenXX", 0, 30, 0.3)
        .is_err());
    assert!(device
        .set_two_qubit_gate_time("MolmerSorensenXX", 30, 3, 0.4)
        .is_err());

    // // Unconnected qubits
    // assert!(device.set_two_qubit_gate_time("MolmerSorensenXX", 0, 4, 0.8).is_err());
}

#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_set_two_qubit_gate_time_oqc(mut device: AWSDevice) {
    // Qubit's value too big
    assert!(device
        .set_two_qubit_gate_time("MolmerSorensenXX", 0, 30, 0.3)
        .is_err());
    assert!(device
        .set_two_qubit_gate_time("MolmerSorensenXX", 30, 3, 0.4)
        .is_err());

    // // Unconnected qubits
    // assert!(device.set_two_qubit_gate_time("MolmerSorensenXX", 0, 4, 0.8).is_err());
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
fn test_two_qubit_gate_names_ioq(device: AWSDevice) {
    assert_eq!(
        device.two_qubit_gate_names(),
        vec!["MolmerSorensenXX".to_string()]
    );
}

#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_two_qubit_gate_names_oqc(device: AWSDevice) {
    assert_eq!(device.two_qubit_gate_names(), Vec::<String>::new());
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_three_qubit_gate_time(device: AWSDevice) {
    assert_eq!(
        device.three_qubit_gate_time("ControlledControlledPauliZ", &0, &1, &2),
        None
    );
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_multi_qubit_gate_time(device: AWSDevice) {
    assert_eq!(
        device.multi_qubit_gate_time("MultiQubitZZ", &[0, 1, 2]),
        None
    );
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_multi_qubit_gate_names(device: AWSDevice) {
    assert!(device.multi_qubit_gate_names().is_empty());
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_qubit_decoherence_rates(device: AWSDevice) {
    assert_eq!(device.qubit_decoherence_rates(&0), None);
}

#[test_case(AWSDevice::from(IonQAria1Device::new()), 25; "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()), 11; "IonQHarmonyDevice")]
#[test_case(AWSDevice::from(OQCLucyDevice::new()), 8; "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()), 80; "RigettiAspenM3Device")]
fn test_number_qubits(device: AWSDevice, qubits: usize) {
    assert_eq!(device.number_qubits(), qubits);
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_add_damping(mut device: AWSDevice) {
    device.add_damping(0, 0.5).unwrap();
    assert_eq!(
        device.qubit_decoherence_rates(&0).unwrap(),
        array![[0.5, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    );

    assert!(device.add_damping(200, 0.2).is_err());
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
#[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_add_dephasing(mut device: AWSDevice) {
    device.add_dephasing(0, 0.5).unwrap();
    assert_eq!(
        device.qubit_decoherence_rates(&0).unwrap(),
        array![[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.5]]
    );

    assert!(device.add_dephasing(200, 0.2).is_err());
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
// #[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_longest_chain(device: AWSDevice) {
    assert!(!device.longest_chains().is_empty());
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
// #[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_longest_closed_chain(device: AWSDevice) {
    // If there are no closed chains bigger than 2, this checks that
    //  nothing is missing from the hard-coded chains and edges.
    assert!(device.longest_closed_chains().iter().all(|lcc_el| {
        device
            .two_qubit_edges()
            .iter()
            .any(|edge| edge.0 == lcc_el[0] && edge.1 == lcc_el[1])
            || device
                .two_qubit_edges()
                .iter()
                .any(|edge| edge.1 == lcc_el[0] && edge.0 == lcc_el[1])
    }));
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
// #[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_edges(device: AWSDevice) {
    assert!(!device.two_qubit_edges().is_empty());
}

#[test_case(AWSDevice::from(IonQAria1Device::new()); "IonQAria1Device")]
#[test_case(AWSDevice::from(IonQHarmonyDevice::new()); "IonQHarmonyDevice")]
// #[test_case(AWSDevice::from(OQCLucyDevice::new()); "OQCLucyDevice")]
// #[test_case(AWSDevice::from(RigettiAspenM3Device::new()); "RigettiAspenM3Device")]
fn test_to_generic_device(device: AWSDevice) {
    let created_generic = device.to_generic_device().unwrap();
    assert_eq!(device.number_qubits(), created_generic.number_qubits());
    let mut aws_single_sorted = device.single_qubit_gate_names();
    aws_single_sorted.sort();
    let mut generic_single_sorted = created_generic.single_qubit_gate_names();
    generic_single_sorted.sort();
    assert!(aws_single_sorted == generic_single_sorted);
    for i in 0..device.number_qubits() {
        for gate in device.single_qubit_gate_names() {
            assert_eq!(
                device.single_qubit_gate_time(gate.as_str(), &i),
                created_generic.single_qubit_gate_time(gate.as_str(), &i)
            );
        }
        assert_eq!(
            device.qubit_decoherence_rates(&i),
            created_generic.qubit_decoherence_rates(&i)
        );
    }
    let mut aws_two_sorted = device.two_qubit_gate_names();
    aws_two_sorted.sort();
    let mut generic_two_sorted = created_generic.two_qubit_gate_names();
    generic_two_sorted.sort();
    assert!(aws_two_sorted == generic_two_sorted);
    for gate in device.two_qubit_gate_names() {
        for i in 0..device.number_qubits() - 1 {
            for j in 1..device.number_qubits() {
                assert_eq!(
                    device.two_qubit_gate_time(gate.as_str(), &i, &j),
                    created_generic.two_qubit_gate_time(gate.as_str(), &i, &j)
                );
            }
        }
    }
    assert_eq!(
        device.multi_qubit_gate_names(),
        created_generic.multi_qubit_gate_names()
    );
    assert_eq!(device.two_qubit_edges(), created_generic.two_qubit_edges());
}
