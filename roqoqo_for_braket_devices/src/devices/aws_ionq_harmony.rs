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

use itertools::Itertools;
use std::collections::HashMap;

use roqoqo::{devices::QoqoDevice, RoqoqoError};

use ndarray::{array, Array2};

use crate::AWSDevice;

#[derive(Debug, PartialEq, Clone, serde::Serialize, serde::Deserialize)]
pub struct IonQHarmonyDevice {
    /// The number of qubits
    number_qubits: usize,
    /// Gate times for all single qubit gates
    single_qubit_gates: HashMap<String, HashMap<usize, f64>>,
    /// Gate times for all two qubit gates
    two_qubit_gates: HashMap<String, TwoQubitGates>,
    /// Decoherence rates for all qubits
    decoherence_rates: HashMap<usize, Array2<f64>>,
}

type TwoQubitGates = HashMap<(usize, usize), f64>;

impl IonQHarmonyDevice {
    /// Creates a new IonQHarmonyDevice.
    ///
    /// # Returns
    ///
    /// An initiated IonQHarmonyDevice with single and two-qubit gates and decoherence rates set to zero.
    ///
    pub fn new() -> Self {
        let mut device = Self {
            number_qubits: 11,
            single_qubit_gates: HashMap::new(),
            two_qubit_gates: HashMap::new(),
            decoherence_rates: HashMap::new(),
        };

        for qubit in 0..device.number_qubits() {
            for gate in device.single_qubit_gate_names() {
                device
                    .set_single_qubit_gate_time(&gate, qubit, 1.0)
                    .unwrap();
            }
        }
        for edge in device.two_qubit_edges() {
            for gate in device.two_qubit_gate_names() {
                device
                    .set_two_qubit_gate_time(&gate, edge.0, edge.1, 1.0)
                    .unwrap();
                device
                    .set_two_qubit_gate_time(&gate, edge.1, edge.0, 1.0)
                    .unwrap();
            }
        }

        device
    }

    /// Returns the device's identifier.
    ///
    /// # Returns
    ///
    /// A str of the name device uses as identifier.
    pub fn name(&self) -> &'static str {
        "arn:aws:braket:us-east-1::device/qpu/ionq/Harmony"
    }

    /// Returns the device's region.
    ///
    /// # Returns
    ///
    /// A str of the region device runs on.
    pub fn region(&self) -> &'static str {
        "us-east-1"
    }
}

impl Default for IonQHarmonyDevice {
    fn default() -> Self {
        Self::new()
    }
}

impl From<&IonQHarmonyDevice> for AWSDevice {
    fn from(input: &IonQHarmonyDevice) -> Self {
        Self::IonQHarmonyDevice(input.clone())
    }
}

impl From<IonQHarmonyDevice> for AWSDevice {
    fn from(input: IonQHarmonyDevice) -> Self {
        Self::IonQHarmonyDevice(input)
    }
}

impl IonQHarmonyDevice {
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
        if qubit >= self.number_qubits {
            return Err(RoqoqoError::GenericError {
                msg: format!(
                    "Qubit {} larger than number qubits {}",
                    qubit, self.number_qubits
                ),
            });
        }
        match self.single_qubit_gates.get_mut(gate) {
            Some(gate_times) => {
                let gatetime = gate_times.entry(qubit).or_insert(gate_time);
                *gatetime = gate_time;
            }
            None => {
                let mut new_map = HashMap::new();
                new_map.insert(qubit, gate_time);
                self.single_qubit_gates.insert(gate.to_string(), new_map);
            }
        }
        Ok(())
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
        if control >= self.number_qubits {
            return Err(RoqoqoError::GenericError {
                msg: format!(
                    "Qubit {} larger than number qubits {}",
                    control, self.number_qubits
                ),
            });
        }
        if target >= self.number_qubits {
            return Err(RoqoqoError::GenericError {
                msg: format!(
                    "Qubit {} larger than number qubits {}",
                    target, self.number_qubits
                ),
            });
        }
        if !self
            .two_qubit_edges()
            .iter()
            .any(|&(a, b)| (a, b) == (control, target) || (a, b) == (target, control))
        {
            return Err(RoqoqoError::GenericError {
                msg: format!(
                    "Qubits {} and {} are not connected in the device",
                    control, target
                ),
            });
        }

        match self.two_qubit_gates.get_mut(gate) {
            Some(gate_times) => {
                let gatetime = gate_times.entry((control, target)).or_insert(gate_time);
                *gatetime = gate_time;
            }
            None => {
                let mut new_map = HashMap::new();
                new_map.insert((control, target), gate_time);
                self.two_qubit_gates.insert(gate.to_string(), new_map);
            }
        }
        Ok(())
    }

    /// Adds qubit damping to noise rates.
    ///
    /// # Arguments
    ///
    /// * `qubit` - The qubit for which the dampins is added.
    /// * `daming` - The damping rates.
    pub fn add_damping(&mut self, qubit: usize, damping: f64) -> Result<(), RoqoqoError> {
        if qubit > self.number_qubits {
            return Err(RoqoqoError::GenericError {
                msg: format!(
                    "Qubit {} out of range for device of size {}",
                    qubit, self.number_qubits
                ),
            });
        }
        let aa = self
            .decoherence_rates
            .entry(qubit)
            .or_insert_with(|| Array2::zeros((3, 3)));
        *aa = aa.clone() + array![[damping, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]];
        Ok(())
    }

    /// Adds qubit dephasing to noise rates.
    ///
    /// # Arguments
    ///
    /// * `qubit` - The qubit for which the dephasing is added.
    /// * `dephasing` - The dephasing rates.
    pub fn add_dephasing(&mut self, qubit: usize, dephasing: f64) -> Result<(), RoqoqoError> {
        if qubit > self.number_qubits {
            return Err(RoqoqoError::GenericError {
                msg: format!(
                    "Qubit {} out of range for device of size {}",
                    qubit, self.number_qubits
                ),
            });
        }
        let aa = self
            .decoherence_rates
            .entry(qubit)
            .or_insert_with(|| Array2::zeros((3, 3)));
        *aa = aa.clone() + array![[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, dephasing]];
        Ok(())
    }
}

/// Implements QoqoDevice trait for IonQHarmonyDevice.
///
/// The QoqoDevice trait defines standard functions available for roqoqo devices.
///
impl QoqoDevice for IonQHarmonyDevice {
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
    #[allow(unused_variables)]
    fn single_qubit_gate_time(&self, hqslang: &str, qubit: &usize) -> Option<f64> {
        match self.single_qubit_gates.get(hqslang) {
            Some(x) => x.get(qubit).copied(),
            None => None,
        }
    }

    /// Returns the names of a single qubit operations available on the device.
    ///
    /// # Returns
    ///
    /// * `Vec<String>` - The list of gate names.
    ///
    fn single_qubit_gate_names(&self) -> Vec<String> {
        vec!["RotateZ".to_string(), "GPi".to_string(), "GPi2".to_string()]
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
    #[allow(unused_variables)]
    fn two_qubit_gate_time(&self, hqslang: &str, control: &usize, target: &usize) -> Option<f64> {
        match self.two_qubit_gates.get(&hqslang.to_string()) {
            Some(x) => x.get(&(*control, *target)).copied(),
            None => None,
        }
    }

    /// Returns the names of a two qubit operations available on the device.
    ///
    /// # Returns
    ///
    /// * `Vec<String>` - The list of gate names.
    ///
    fn two_qubit_gate_names(&self) -> Vec<String> {
        vec!["MolmerSorensenXX".to_string()]
    }

    /// Returns the gate time of a three qubit operation if the three qubit operation is available on device.
    ///
    /// # Arguments
    ///
    /// * `hqslang` - The hqslang name of a two qubit gate.
    /// * `control_0` - The control_0 qubit the gate acts on.
    /// * `control_1` - The control_1 qubit the gate acts on.
    /// * `target` - The target qubit the gate acts on.
    ///
    /// # Returns
    ///
    /// * `Some<f64>` - The gate time.
    /// * `None` - The gate is not available on the device.
    ///
    #[allow(unused_variables)]
    fn three_qubit_gate_time(
        &self,
        hqslang: &str,
        control_0: &usize,
        control_1: &usize,
        target: &usize,
    ) -> Option<f64> {
        None
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
    #[allow(unused_variables)]
    fn multi_qubit_gate_time(&self, hqslang: &str, qubits: &[usize]) -> Option<f64> {
        None
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
        vec![]
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
    #[allow(unused_variables)]
    fn qubit_decoherence_rates(&self, qubit: &usize) -> Option<Array2<f64>> {
        self.decoherence_rates.get(qubit).cloned()
    }

    /// Returns the number of qubits the device supports.
    ///
    /// # Returns
    ///
    /// * `usize` - The number of qubits in the device.
    ///
    fn number_qubits(&self) -> usize {
        self.number_qubits
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
        vec![vec![0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
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
        vec![vec![0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
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
        let edges: Vec<(usize, usize)> = (0..self.number_qubits)
            .combinations(2)
            .map(|x| (x[0], x[1]))
            .collect();
        edges
    }
}
