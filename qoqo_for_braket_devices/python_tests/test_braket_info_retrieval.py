"""Test qoqo_for_braket_devices information retrieval"""
# Copyright © 2023 HQS Quantum Simulations GmbH. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing permissions and limitations under
# the License.

import pytest
import sys
import numpy as np

from qoqo_for_braket_devices import aws_devices, set_for_braket_noise_information


def test_rigetti_aspen_info_update():
    """Test RigettiAspenM3Device for_braket's info update."""
    aspen_m3 = aws_devices.RigettiAspenM3Device()

    assert aspen_m3.single_qubit_gate_time("RotateX", 0) == 1.0
    assert aspen_m3.single_qubit_gate_time("RotateZ", 0) == 1.0
    assert aspen_m3.two_qubit_gate_time("ControlledPauliZ", 0) == 1.0
    assert aspen_m3.two_qubit_gate_time("ControlledPhaseShift", 0) == 1.0
    assert aspen_m3.two_qubit_gate_time("XY", 0) == 1.0
    assert aspen_m3.three_qubit_gate_time("ControlledControlledPauliZ", 0, 1, 2) == None
    assert aspen_m3.multi_qubit_gate_time("MultiQubitMS", [0, 1, 2, 3]) == None
    assert np.all(aspen_m3.qubit_decoherence_rates(0) == 0.0)

    set_for_braket_noise_information(aspen_m3, get_mocked_information=True)

    assert aspen_m3.single_qubit_gate_time("RotateX", 0) != 1.0
    assert aspen_m3.single_qubit_gate_time("RotateZ", 0) != 1.0
    assert aspen_m3.two_qubit_gate_time("ControlledPauliZ", 0, 1) != 1.0
    assert aspen_m3.two_qubit_gate_time("ControlledPhaseShift", 0, 1) != 1.0
    assert aspen_m3.two_qubit_gate_time("XY", 0, 1) != 1.0
    assert aspen_m3.three_qubit_gate_time("ControlledControlledPauliZ", 0, 1, 2) == None
    assert aspen_m3.multi_qubit_gate_time("MultiQubitMS", [0, 1, 2, 3]) == None
    assert np.any(aspen_m3.qubit_decoherence_rates(0) != 0.0)


if __name__ == "__main__":
    pytest.main(sys.argv)
