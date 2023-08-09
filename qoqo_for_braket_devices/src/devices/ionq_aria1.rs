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

use ndarray::Array2;
use numpy::{PyArray2, ToPyArray};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use bincode::deserialize;

use qoqo::devices::GenericDeviceWrapper;
use roqoqo::devices::QoqoDevice;
use roqoqo_for_braket_devices::{AWSDevice, IonQAria1Device};

/// AWS IonQ Aria1 device
///
#[pyclass(name = "IonQAria1Device", module = "aws_devices")]
#[derive(Clone, Debug, PartialEq)]
pub struct IonQAria1DeviceWrapper {
    /// Internal storage of [roqoqo_for_braket_devices::IonQAria1Device]
    pub internal: IonQAria1Device,
}

#[pymethods]
impl IonQAria1DeviceWrapper {
    /// Create a new IonQAria1Device instance.
    #[new]
    pub fn new() -> Self {
        Self {
            internal: IonQAria1Device::new(),
        }
    }

    /// AWS's identifier.
    ///
    /// Returns:
    ///     str: The AWS's identifier of the Device.
    pub fn name(&self) -> &str {
        roqoqo_for_braket_devices::IonQAria1Device::name(&self.internal)
    }

    /// The device's region.
    ///
    /// Returns:
    ///     str: The region the device is defined on.
    pub fn region(&self) -> &str {
        roqoqo_for_braket_devices::IonQAria1Device::region(&self.internal)
    }

    /// Returns the gate time of a single qubit operation if the single qubit operation is available on device.
    ///
    /// Args:
    ///     hqslang[str]: The hqslang name of a single qubit gate.
    ///     qubit[int]: The qubit the gate acts on.
    ///
    /// Returns:
    ///     Option[float]: None if gate is not available.
    ///
    /// Raises:
    ///     PyValueError: Qubit is not in device.
    #[pyo3(text_signature = "(gate, qubit)")]
    pub fn single_qubit_gate_time(&self, hqslang: &str, qubit: usize) -> Option<f64> {
        self.internal.single_qubit_gate_time(hqslang, &qubit)
    }

    /// Set the gate time of a single qubit gate.
    ///
    /// Args:
    ///     gate (str): hqslang name of the single-qubit-gate.
    ///     qubit (int): The qubit for which the gate time is set.
    ///     gate_time (float): The gate time for the given gate.
    ///
    /// Raises:
    ///     PyValueError: Qubit is not in device.
    #[pyo3(text_signature = "(gate, qubit, gate_time)")]
    pub fn set_single_qubit_gate_time(
        &mut self,
        gate: &str,
        qubit: usize,
        gate_time: f64,
    ) -> PyResult<()> {
        self.internal
            .set_single_qubit_gate_time(gate, qubit, gate_time)
            .map_err(|err| PyValueError::new_err(format!("{:?}", err)))
    }

    /// Returns the names of a single qubit operations available on the device.
    ///
    /// Returns:
    ///     List[str]: The list of gate names.
    pub fn single_qubit_gate_names(&self) -> Vec<String> {
        self.internal.single_qubit_gate_names()
    }

    /// Returns the gate time of a two qubit operation if the two qubit operation is available on device.
    ///
    /// Args:
    ///     hqslang[str]: The hqslang name of a single qubit gate.
    ///     control[int]: The control qubit the gate acts on.
    ///     target[int]: The target qubit the gate acts on.
    ///
    /// Returns:
    ///     Option[float]: None if gate is not available.
    ///
    /// Raises:
    ///     PyValueError: Qubit is not in device.
    ///
    #[pyo3(text_signature = "(gate, control, target)")]
    pub fn two_qubit_gate_time(&self, hqslang: &str, control: usize, target: usize) -> Option<f64> {
        self.internal
            .two_qubit_gate_time(hqslang, &control, &target)
    }

    /// Set the gate time of a two qubit gate.
    ///
    /// Args:
    ///     gate (str): hqslang name of the single-qubit-gate.
    ///     control (int): The control qubit for which the gate time is set.
    ///     target (int): The control qubit for which the gate time is set.
    ///     gate_time (float): The gate time for the given gate.
    ///
    /// Raises:
    ///     PyValueError: Qubit is not in device.
    #[pyo3(text_signature = "(gate, control, target, gate_time)")]
    pub fn set_two_qubit_gate_time(
        &mut self,
        gate: &str,
        control: usize,
        target: usize,
        gate_time: f64,
    ) -> PyResult<()> {
        self.internal
            .set_two_qubit_gate_time(gate, control, target, gate_time)
            .map_err(|err| PyValueError::new_err(format!("{:?}", err)))
    }

    /// Returns the names of a two qubit operations available on the device.
    ///
    /// Returns:
    ///     List[str]: The list of gate names.
    pub fn two_qubit_gate_names(&self) -> Vec<String> {
        self.internal.two_qubit_gate_names()
    }

    /// Returns the gate time of a three qubit operation if the three qubit operation is available on device.
    ///
    /// Args:
    ///     hqslang[str]: The hqslang name of a single qubit gate.
    ///     control_0[int]: The control_0 qubit the gate acts on.
    ///     control_1[int]: The control_1 qubit the gate acts on.
    ///     target[int]: The target qubit the gate acts on.
    ///
    /// Returns:
    ///     Option[float]: None if gate is not available.
    ///
    /// Raises:
    ///     PyValueError: Qubit is not in device.
    ///
    #[pyo3(text_signature = "(gate, control_0, control_1, target")]
    pub fn three_qubit_gate_time(
        &self,
        hqslang: &str,
        control_0: usize,
        control_1: usize,
        target: usize,
    ) -> Option<f64> {
        self.internal
            .three_qubit_gate_time(hqslang, &control_0, &control_1, &target)
    }

    /// Returns the gate time of a multi qubit operation if the multi qubit operation is available on device.
    ///
    /// Args:
    ///     hqslang[str]: The hqslang name of a multi qubit gate.
    ///     qubits[List[int]]: The qubits the gate acts on.
    ///
    /// Returns:
    ///     Option[float]: None if gate is not available.
    ///
    /// Raises:
    ///     PyValueError: Qubit is not in device.
    #[pyo3(text_signature = "(gate, qubits)")]
    pub fn multi_qubit_gate_time(&self, hqslang: &str, qubits: Vec<usize>) -> Option<f64> {
        self.internal.multi_qubit_gate_time(hqslang, &qubits)
    }

    /// Returns the names of a mutli qubit operations available on the device.
    ///
    /// The list of names also includes the three qubit gate operations.
    ///
    /// Returns:
    ///     List[str]: The list of gate names.
    ///
    pub fn multi_qubit_gate_names(&self) -> Vec<String> {
        self.internal.multi_qubit_gate_names()
    }

    /// Return the matrix of the decoherence rates of the Lindblad equation.
    ///
    /// Args:
    ///     qubit (int): The qubit for which the rate matrix M is returned.
    ///
    /// Returns:
    ///     numpy.array: 3 by 3 numpy array of decoherence rates.
    ///
    #[pyo3(text_signature = "(qubit)")]
    fn qubit_decoherence_rates(&self, qubit: usize) -> Py<PyArray2<f64>> {
        Python::with_gil(|py| -> Py<PyArray2<f64>> {
            match self.internal.qubit_decoherence_rates(&qubit) {
                Some(matrix) => matrix.to_pyarray(py).to_owned(),
                None => {
                    let matrix = Array2::<f64>::zeros((3, 3));
                    matrix.to_pyarray(py).to_owned()
                }
            }
        })
    }

    /// Adds single qubit damping to noise rates.
    ///
    /// Args:
    ///     qubit (int): The qubit for which the decoherence is added.
    ///     damping (float): The damping rates.
    ///
    /// Raises:
    ///     PyValueError: Qubit is not in device.
    #[pyo3(text_signature = "(qubit, damping)")]
    pub fn add_damping(&mut self, qubit: usize, damping: f64) -> PyResult<()> {
        self.internal
            .add_damping(qubit, damping)
            .map_err(|err| PyValueError::new_err(format!("Cannot add decoherence: {}", err)))
    }

    /// Adds single qubit dephasing to noise rates.
    ///
    /// Args:
    ///     qubit (int): The qubit for which the decoherence is added.
    ///     dephasing (float): The dephasing rates.
    ///
    /// Raises:
    ///     PyValueError: Qubit is not in device.
    #[pyo3(text_signature = "(qubit, dephasing)")]
    pub fn add_dephasing(&mut self, qubit: usize, dephasing: f64) -> PyResult<()> {
        self.internal
            .add_dephasing(qubit, dephasing)
            .map_err(|err| PyValueError::new_err(format!("Cannot add decoherence: {}", err)))
    }

    /// Return number of qubits in device.
    ///
    /// Returns:
    ///     int: The number of qubits.
    pub fn number_qubits(&self) -> usize {
        self.internal.number_qubits()
    }

    /// Return a list of longest linear chains through the device.
    ///
    /// Returns at least one chain of qubits with linear connectivity in the device,
    /// that has the maximum possible number of qubits with linear connectivity in the device.
    /// Can return more that one of the possible chains but is not guaranteed to return
    /// all possible chains. (For example for all-to-all connectivity only one chain will be returned).
    ///
    /// Returns:
    ///     List[List[usize]]: A list of the longest chains given by vectors of qubits in the chain.
    ///
    pub fn longest_chains(&self) -> Vec<Vec<usize>> {
        self.internal.longest_chains()
    }

    /// Return a list of longest closed linear chains through the device.
    ///
    /// Returns at least one chain of qubits with linear connectivity in the device ,
    /// that has the maximum possible number of qubits with linear connectivity in the device.
    /// The chain must be closed, the first qubit needs to be connected to the last qubit.
    /// Can return more that one of the possible chains but is not guaranteed to return
    /// all possible chains. (For example for all-to-all connectivity only one chain will be returned).
    ///
    /// Returns:
    ///     List[List[usize]]: A list of the longest closed chains given by vectors of qubits in the chain.
    ///
    pub fn longest_closed_chains(&self) -> Vec<Vec<usize>> {
        self.internal.longest_closed_chains()
    }

    /// Return the list of pairs of qubits linked by a native two-qubit-gate in the device.
    ///
    /// A pair of qubits is considered linked by a native two-qubit-gate if the device
    /// can implement a two-qubit-gate between the two qubits without decomposing it
    /// into a sequence of gates that involves a third qubit of the device.
    /// The two-qubit-gate also has to form a universal set together with the available
    /// single qubit gates.
    ///
    /// The returned vectors is a simple, graph-library independent, representation of
    /// the undirected connectivity graph of the device.
    /// It can be used to construct the connectivity graph in a graph library of the user's
    /// choice from a list of edges and can be used for applications like routing in quantum algorithms.
    ///
    /// Returns:
    ///     List[(int, int)]: List of two qubit edges in the undirected connectivity graph.
    ///
    pub fn two_qubit_edges(&self) -> Vec<(usize, usize)> {
        self.internal.two_qubit_edges()
    }

    /// Convert the device to a qoqo GenericDevice.
    ///
    /// Returns:
    ///     GenericDevice: converted device.
    ///
    /// Raises:
    ///     PyValueError: Could not convert the device to a qoqo GenericDevice.
    pub fn to_generic_device(&self) -> PyResult<GenericDeviceWrapper> {
        let aws_device: AWSDevice = self.internal.clone().into();
        Ok(GenericDeviceWrapper {
            internal: aws_device.to_generic_device().map_err(|err| {
                PyValueError::new_err(format!("Cannot convert device to generic device: {}", err))
            })?,
        })
    }
}

impl IonQAria1DeviceWrapper {
    /// Fallible conversion of generic python object...
    pub fn from_pyany(input: Py<PyAny>) -> PyResult<IonQAria1Device> {
        Python::with_gil(|py| -> PyResult<IonQAria1Device> {
            let input = input.as_ref(py);
            if let Ok(try_downcast) = input.extract::<IonQAria1DeviceWrapper>() {
                Ok(try_downcast.internal)
            } else {
                let get_bytes = input.call_method0("to_bincode")?;
                let bytes = get_bytes.extract::<Vec<u8>>()?;
                deserialize(&bytes[..]).map_err(|err| {
                    PyValueError::new_err(format!("Cannot treat input as IonQAria1Device: {}", err))
                })
            }
        })
    }
}

impl Default for IonQAria1DeviceWrapper {
    fn default() -> Self {
        Self::new()
    }
}
