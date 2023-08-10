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

//! AWS Devices
//!
//! Provides the devices that are used to execute quantum programs on AWS's devices.

use roqoqo::devices::{GenericDevice, QoqoDevice};
use roqoqo::RoqoqoError;

mod aws_ionq_harmony;
pub use crate::devices::aws_ionq_harmony::IonQHarmonyDevice;

mod aws_ionq_aria1;
pub use crate::devices::aws_ionq_aria1::IonQAria1Device;

mod aws_oqc_lucy;
pub use crate::devices::aws_oqc_lucy::OQCLucyDevice;

mod aws_rigetti_aspen_m3;
pub use crate::devices::aws_rigetti_aspen_m3::RigettiAspenM3Device;

/// Collection of AWS quantum devices.
///
pub enum AWSDevice {
    IonQHarmonyDevice(IonQHarmonyDevice),
    IonQAria1Device(IonQAria1Device),
    OQCLucyDevice(OQCLucyDevice),
    RigettiAspenM3Device(RigettiAspenM3Device),
}

impl AWSDevice {
    /// Returns the device's identifier.
    ///
    /// # Returns
    ///
    /// A str of the name AWS uses as identifier.
    pub fn name(self) -> &'static str {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.name(),
            AWSDevice::IonQAria1Device(x) => x.name(),
            AWSDevice::OQCLucyDevice(x) => x.name(),
            AWSDevice::RigettiAspenM3Device(x) => x.name(),
        }
    }

    /// Returns the device's region.
    ///
    /// # Returns
    ///
    /// A str of the region device runs on.
    pub fn region(self) -> &'static str {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.region(),
            AWSDevice::IonQAria1Device(x) => x.region(),
            AWSDevice::OQCLucyDevice(x) => x.region(),
            AWSDevice::RigettiAspenM3Device(x) => x.region(),
        }
    }

    /// Setting the gate time of a single qubit gate.
    ///
    /// # Arguments
    ///
    /// * `gate` - hqslang name of the single-qubit-gate.
    /// * `qubit` - The qubit for which the gate time is set.
    /// * `gate_time` - gate time for the given gate.
    pub fn set_single_qubit_gate_time(
        &mut self,
        gate: &str,
        qubit: usize,
        gate_time: f64,
    ) -> Result<(), RoqoqoError> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.set_single_qubit_gate_time(gate, qubit, gate_time),
            AWSDevice::IonQAria1Device(x) => x.set_single_qubit_gate_time(gate, qubit, gate_time),
            AWSDevice::OQCLucyDevice(x) => x.set_single_qubit_gate_time(gate, qubit, gate_time),
            AWSDevice::RigettiAspenM3Device(x) => {
                x.set_single_qubit_gate_time(gate, qubit, gate_time)
            }
        }
    }

    /// Setting the gate time of a two qubit gate.
    ///
    /// # Arguments
    ///
    /// * `gate` - hqslang name of the two-qubit-gate.
    /// * `control` - The control qubit for which the gate time is set.
    /// * `target` - The target qubit for which the gate time is set.
    /// * `gate_time` - gate time for the given gate.
    pub fn set_two_qubit_gate_time(
        &mut self,
        gate: &str,
        control: usize,
        target: usize,
        gate_time: f64,
    ) -> Result<(), RoqoqoError> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => {
                x.set_two_qubit_gate_time(gate, control, target, gate_time)
            }
            AWSDevice::IonQAria1Device(x) => {
                x.set_two_qubit_gate_time(gate, control, target, gate_time)
            }
            AWSDevice::OQCLucyDevice(x) => {
                x.set_two_qubit_gate_time(gate, control, target, gate_time)
            }
            AWSDevice::RigettiAspenM3Device(x) => {
                x.set_two_qubit_gate_time(gate, control, target, gate_time)
            }
        }
    }

    /// Adds qubit damping to noise rates.
    ///
    /// # Arguments
    ///
    /// * `qubit` - The qubit for which the dampins is added.
    /// * `daming` - The damping rates.
    pub fn add_damping(&mut self, qubit: usize, damping: f64) -> Result<(), RoqoqoError> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.add_damping(qubit, damping),
            AWSDevice::IonQAria1Device(x) => x.add_damping(qubit, damping),
            AWSDevice::OQCLucyDevice(x) => x.add_damping(qubit, damping),
            AWSDevice::RigettiAspenM3Device(x) => x.add_damping(qubit, damping),
        }
    }

    /// Adds qubit dephasing to noise rates.
    ///
    /// # Arguments
    ///
    /// * `qubit` - The qubit for which the dephasing is added.
    /// * `dephasing` - The dephasing rates.
    pub fn add_dephasing(&mut self, qubit: usize, dephasing: f64) -> Result<(), RoqoqoError> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.add_dephasing(qubit, dephasing),
            AWSDevice::IonQAria1Device(x) => x.add_dephasing(qubit, dephasing),
            AWSDevice::OQCLucyDevice(x) => x.add_dephasing(qubit, dephasing),
            AWSDevice::RigettiAspenM3Device(x) => x.add_dephasing(qubit, dephasing),
        }
    }

    /// Converts the device to a qoqo GenericDevice.
    ///
    /// # Returns
    ///
    /// * `GenericDevice` - The converted device.
    /// * `RoqoqoError` - The error propagated from adding gate times and decoherence rates.
    pub fn to_generic_device(&self) -> Result<GenericDevice, RoqoqoError> {
        let mut new_generic_device = GenericDevice::new(self.number_qubits());

        // Gate times
        for gate in self.single_qubit_gate_names() {
            for qubit in 0..self.number_qubits() {
                if let Some(x) = self.single_qubit_gate_time(gate.as_str(), &qubit) {
                    new_generic_device.set_single_qubit_gate_time(gate.as_str(), qubit, x)?;
                }
            }
        }
        for gate in self.two_qubit_gate_names() {
            for (control, target) in self.two_qubit_edges() {
                if let Some(x) = self.two_qubit_gate_time(gate.as_str(), &control, &target) {
                    new_generic_device.set_two_qubit_gate_time(
                        gate.as_str(),
                        control,
                        target,
                        x,
                    )?;
                }
            }
            for (control, target) in self.two_qubit_edges() {
                if let Some(x) = self.two_qubit_gate_time(gate.as_str(), &target, &control) {
                    new_generic_device.set_two_qubit_gate_time(
                        gate.as_str(),
                        target,
                        control,
                        x,
                    )?;
                }
            }
        }

        // Decoherence rates
        for qubit in 0..self.number_qubits() {
            if let Some(x) = self.qubit_decoherence_rates(&qubit) {
                new_generic_device.set_qubit_decoherence_rates(qubit, x)?;
            }
        }

        Ok(new_generic_device)
    }
}

/// Implements the Device trait for AWSDevice.
///
/// Defines standard functions available for roqoqo-iqm devices.
impl QoqoDevice for AWSDevice {
    /// Returns the gate time of a single qubit operation if the single qubit operation is available on device.
    ///
    /// # Arguments
    ///
    /// * `hqslang` - The hqslang name of a single qubit gate.
    /// * `qubit` - The qubit the gate acts on.
    ///
    /// # Returns
    ///
    /// * `Some<f64>` - The gate time.
    /// * `None` - The gate is not available on the device.
    ///
    fn single_qubit_gate_time(&self, hqslang: &str, qubit: &usize) -> Option<f64> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.single_qubit_gate_time(hqslang, qubit),
            AWSDevice::IonQAria1Device(x) => x.single_qubit_gate_time(hqslang, qubit),
            AWSDevice::OQCLucyDevice(x) => x.single_qubit_gate_time(hqslang, qubit),
            AWSDevice::RigettiAspenM3Device(x) => x.single_qubit_gate_time(hqslang, qubit),
        }
    }

    /// Returns the names of a single qubit operations available on the device.
    ///
    /// # Returns
    ///
    /// * `Vec<String>` - The list of gate names.
    ///
    fn single_qubit_gate_names(&self) -> Vec<String> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.single_qubit_gate_names(),
            AWSDevice::IonQAria1Device(x) => x.single_qubit_gate_names(),
            AWSDevice::OQCLucyDevice(x) => x.single_qubit_gate_names(),
            AWSDevice::RigettiAspenM3Device(x) => x.single_qubit_gate_names(),
        }
    }

    /// Returns the gate time of a two qubit operation if the two qubit operation is available on device.
    ///
    /// # Arguments
    ///
    /// * `hqslang` - The hqslang name of a two qubit gate.
    /// * `control` - The control qubit the gate acts on.
    /// * `target` - The target qubit the gate acts on.
    ///
    /// # Returns
    ///
    /// * `Some<f64>` - The gate time.
    /// * `None` - The gate is not available on the device.
    ///
    fn two_qubit_gate_time(&self, hqslang: &str, control: &usize, target: &usize) -> Option<f64> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.two_qubit_gate_time(hqslang, control, target),
            AWSDevice::IonQAria1Device(x) => x.two_qubit_gate_time(hqslang, control, target),
            AWSDevice::OQCLucyDevice(x) => x.two_qubit_gate_time(hqslang, control, target),
            AWSDevice::RigettiAspenM3Device(x) => x.two_qubit_gate_time(hqslang, control, target),
        }
    }

    /// Returns the names of a two qubit operations available on the device.
    ///
    /// # Returns
    ///
    /// * `Vec<String>` - The list of gate names.
    ///
    fn two_qubit_gate_names(&self) -> Vec<String> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.two_qubit_gate_names(),
            AWSDevice::IonQAria1Device(x) => x.two_qubit_gate_names(),
            AWSDevice::OQCLucyDevice(x) => x.two_qubit_gate_names(),
            AWSDevice::RigettiAspenM3Device(x) => x.two_qubit_gate_names(),
        }
    }

    /// Returns the gate time of a three qubit operation if the three qubit operation is available on device.
    ///
    /// # Arguments
    ///
    /// * `hqslang` - The hqslang name of a two qubit gate.
    /// * `control` - The control qubit the gate acts on.
    /// * `target` - The target qubit the gate acts on.
    ///
    /// # Returns
    ///
    /// * `Some<f64>` - The gate time.
    /// * `None` - The gate is not available on the device.
    ///
    fn three_qubit_gate_time(
        &self,
        hqslang: &str,
        control_0: &usize,
        control_1: &usize,
        target: &usize,
    ) -> Option<f64> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => {
                x.three_qubit_gate_time(hqslang, control_0, control_1, target)
            }
            AWSDevice::IonQAria1Device(x) => {
                x.three_qubit_gate_time(hqslang, control_0, control_1, target)
            }
            AWSDevice::OQCLucyDevice(x) => {
                x.three_qubit_gate_time(hqslang, control_0, control_1, target)
            }
            AWSDevice::RigettiAspenM3Device(x) => {
                x.three_qubit_gate_time(hqslang, control_0, control_1, target)
            }
        }
    }

    /// Returns the gate time of a multi qubit operation if the multi qubit operation is available on device.
    ///
    /// # Arguments
    ///
    /// * `hqslang` - The hqslang name of a multi qubit gate.
    /// * `qubits` - The qubits the gate acts on.
    ///
    /// # Returns
    ///
    /// * `Some<f64>` - The gate time.
    /// * `None` - The gate is not available on the device.
    ///
    fn multi_qubit_gate_time(&self, hqslang: &str, qubits: &[usize]) -> Option<f64> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.multi_qubit_gate_time(hqslang, qubits),
            AWSDevice::IonQAria1Device(x) => x.multi_qubit_gate_time(hqslang, qubits),
            AWSDevice::OQCLucyDevice(x) => x.multi_qubit_gate_time(hqslang, qubits),
            AWSDevice::RigettiAspenM3Device(x) => x.multi_qubit_gate_time(hqslang, qubits),
        }
    }

    /// Returns the names of a multi qubit operations available on the device.
    ///
    /// The list of names also includes the three qubit gate operations.
    ///
    /// # Returns
    ///
    /// * `Vec<String>` - The list of gate names.
    ///
    fn multi_qubit_gate_names(&self) -> Vec<String> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.multi_qubit_gate_names(),
            AWSDevice::IonQAria1Device(x) => x.multi_qubit_gate_names(),
            AWSDevice::OQCLucyDevice(x) => x.multi_qubit_gate_names(),
            AWSDevice::RigettiAspenM3Device(x) => x.multi_qubit_gate_names(),
        }
    }

    /// Returns the matrix of the decoherence rates of the Lindblad equation.
    ///
    /// # Arguments
    ///
    /// * `qubit` - The qubit for which the rate matrix is returned.
    ///
    /// # Returns
    ///
    /// * `Some<Array2<f64>>` - The decoherence rates.
    /// * `None` - The qubit is not part of the device.
    ///
    fn qubit_decoherence_rates(&self, qubit: &usize) -> Option<ndarray::Array2<f64>> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.qubit_decoherence_rates(qubit),
            AWSDevice::IonQAria1Device(x) => x.qubit_decoherence_rates(qubit),
            AWSDevice::OQCLucyDevice(x) => x.qubit_decoherence_rates(qubit),
            AWSDevice::RigettiAspenM3Device(x) => x.qubit_decoherence_rates(qubit),
        }
    }

    /// Returns the number of qubits the device supports.
    ///
    /// # Returns
    ///
    /// `usize` - The number of qubits in the device.
    ///
    fn number_qubits(&self) -> usize {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.number_qubits(),
            AWSDevice::IonQAria1Device(x) => x.number_qubits(),
            AWSDevice::OQCLucyDevice(x) => x.number_qubits(),
            AWSDevice::RigettiAspenM3Device(x) => x.number_qubits(),
        }
    }

    /// Return a list of longest linear chains through the device.
    ///
    /// Returns at least one chain of qubits with linear connectivity in the device,
    /// that has the maximum possible number of qubits with linear connectivity in the device.
    /// Can return more that one of the possible chains but is not guaranteed to return
    /// all possible chains. (For example for all-to-all connectivity only one chain will be returned).
    ///
    /// # Returns
    ///
    /// * `Vec<Vec<usize>>` - A list of the longest chains given by vectors of qubits in the chain.
    ///
    fn longest_chains(&self) -> Vec<Vec<usize>> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.longest_chains(),
            AWSDevice::IonQAria1Device(x) => x.longest_chains(),
            AWSDevice::OQCLucyDevice(x) => x.longest_chains(),
            AWSDevice::RigettiAspenM3Device(x) => x.longest_chains(),
        }
    }

    /// Return a list of longest closed linear chains through the device.
    ///
    /// Returns at least one chain of qubits with linear connectivity in the device ,
    /// that has the maximum possible number of qubits with linear connectivity in the device.
    /// The chain must be closed, the first qubit needs to be connected to the last qubit.
    /// Can return more that one of the possible chains but is not guaranteed to return
    /// all possible chains. (For example for all-to-all connectivity only one chain will be returned).
    ///
    /// # Returns
    ///
    /// * `Vec<Vec<usize>>` - A list of the longest chains given by vectors of qubits in the chain.
    ///
    fn longest_closed_chains(&self) -> Vec<Vec<usize>> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.longest_closed_chains(),
            AWSDevice::IonQAria1Device(x) => x.longest_closed_chains(),
            AWSDevice::OQCLucyDevice(x) => x.longest_closed_chains(),
            AWSDevice::RigettiAspenM3Device(x) => x.longest_closed_chains(),
        }
    }

    /// Returns the list of pairs of qubits linked with a native two-qubit-gate in the device.
    ///
    /// A pair of qubits is considered linked by a native two-qubit-gate if the device
    /// can implement a two-qubit-gate between the two qubits without decomposing it
    /// into a sequence of gates that involves a third qubit of the device.
    /// The two-qubit-gate also has to form a universal set together with the available
    /// single qubit gates.
    ///
    /// The returned vectors is a simple, graph-library independent, representation of
    /// the undirected connectivity graph of the device.
    /// It can be used to construct the connectivity graph in a graph library of the users
    /// choice from a list of edges and can be used for applications like routing in quantum algorithms.
    ///
    /// # Returns
    ///
    /// * `Vec<(usize, usize)>` - A list of pairs of qubits linked with a native two-qubit-gate in
    ///                           the device.
    ///
    fn two_qubit_edges(&self) -> Vec<(usize, usize)> {
        match self {
            AWSDevice::IonQHarmonyDevice(x) => x.two_qubit_edges(),
            AWSDevice::IonQAria1Device(x) => x.two_qubit_edges(),
            AWSDevice::OQCLucyDevice(x) => x.two_qubit_edges(),
            AWSDevice::RigettiAspenM3Device(x) => x.two_qubit_edges(),
        }
    }
}
