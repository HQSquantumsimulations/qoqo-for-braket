"""Mock Properties."""
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

from typing import Union, List


class MockedProperties:
    """Mocks braket's BackendProperties class."""

    def __init__(self) -> None:
        """Create a new MockedProperties instance."""
        pass

    def gate_property(self, gate: str, qubits: Union[int, List[int]], name: str) -> float:
        """Gate property mocked time.

        Args:
            gate (str): The gate name.
            qubits (Union[int, List[int]]): The involved qubit(s).
            name (str): The property name.

        Returns:
            float: Gate property mocked time.
        """
        return (50.0, 0)

    def t1(self, qubit: int) -> float:
        """T1 mocked time.

        Args:
            qubit (int): The involved qubit.

        Returns:
            float: T1 mocked time.
        """
        return 100.0

    def t2(self, qubit: int) -> float:
        """T2 mocked time.

        Args:
            qubit (int): The involved qubit.

        Returns:
            float: T2 mocked time.
        """
        return 100.0
