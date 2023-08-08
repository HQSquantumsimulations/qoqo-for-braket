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

//! # qoqo_for_braket_devices
//!
//! Braket devices' interface for qoqo.
//!
//! Collection of AWS's braket devices interfaces implementing qoqo's Device trait.

use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::wrap_pymodule;

pub mod devices;
pub use devices::*;

/// AWS python interface
///
/// Provides the devices that are used to execute quantum program on the Braket backend.
#[pymodule]
fn qoqo_for_braket_devices(_py: Python, module: &PyModule) -> PyResult<()> {
    let wrapper = wrap_pymodule!(devices::aws_devices);
    module.add_wrapped(wrapper)?;

    let system = PyModule::import(_py, "sys")?;
    let system_modules: &PyDict = system.getattr("modules")?.downcast()?;
    system_modules.set_item(
        "qoqo_for_braket_devices.devices",
        module.getattr("aws_devices")?,
    )?;
    Ok(())
}
