"""Test qoqo_for_braket_devices initialization"""
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

from qoqo_for_braket_devices import aws_devices


def test_aria1():
    """Test IonQAria1Device initialization."""
    aria1 = aws_devices.IonQAria1Device()


def test_harmony():
    """Test IonQHarmonyDevice initialization."""
    harmony = aws_devices.IonQHarmonyDevice()


def test_lucy():
    """Test OQCLucyDevice initialization."""
    lucy = aws_devices.OQCLucyDevice()


def test_aspen_m3():
    """Test RigettiAspenM3Device initialization."""
    aspen_m3 = aws_devices.RigettiAspenM3Device()


if __name__ == "__main__":
    pytest.main(sys.argv)
