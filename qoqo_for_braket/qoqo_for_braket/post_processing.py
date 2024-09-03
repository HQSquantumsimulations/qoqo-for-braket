# Copyright © 2023 HQS Quantum Simulations GmbH.
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
"""Post processing helper function."""

from typing import Any, Dict, List, Tuple, Optional

from qoqo import Circuit


def _post_process_circuit_result(
    results: Any, metadata: Dict[Any, Any], input_bit_circuit: Optional[Circuit]
) -> Tuple[
    Dict[str, List[List[bool]]],
    Dict[str, List[List[float]]],
    Dict[str, List[List[complex]]],
]:
    """Post processes the result returned from an AWSQuantumTask.

    Handles translation of samples of all qubits (the default)
    into qoqo registers.

    Args:
        results: results to be processed
        metadata: associated metadata of the job
        input_bit_circuit: the circuit containing InputBit operations

    Returns:
        Tuple[Dict[str, List[List[bool]]],
              Dict[str, List[List[float]]],
              Dict[str, List[List[complex]]]: processed results
    """
    bit_results = metadata["output_registers"][0]
    float_results = metadata["output_registers"][1]
    complex_results = metadata["output_registers"][2]
    measurements = results.measurements
    bit_field = measurements > 0
    # dictionary of all mearusement results that might be shorter than the output lenght
    bit_results[metadata["readout_name"]] = [res.tolist() for res in bit_field]
    if input_bit_circuit:
        # create final
        bit_results_final: dict = {}
        # Extension bits to fill in additional bits not measured because they do not correspont to
        #  measured qubits
        extension_bits = [
            False for _ in range(metadata["output_register_lengths"][0][metadata["readout_name"]])
        ]
        # Write input bit circuit values to extension bits
        for op in input_bit_circuit:
            extension_bits[op.index()] = op.value()
        # Shorten extension bits to only the bits exceeding measurement
        extension_bits = [
            extension_bits[index]
            for index in range(
                len(bit_results[metadata["readout_name"]][0]),
                metadata["output_register_lengths"][0][metadata["readout_name"]],
            )
        ]

        # Appending extension bits to each measured result
        for key, value in bit_results.items():
            bit_results_final[key] = []
            for val in value:
                bit_results_final[key].append(val + extension_bits)

        bit_results = bit_results_final

    return (bit_results, float_results, complex_results)
