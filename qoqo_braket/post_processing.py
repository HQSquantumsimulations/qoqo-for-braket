# Copyright © 2023 HQS Quantum Simulations GmbH. All Rights Reserved.
"""Post processing helper function."""
from typing import Dict, List, Tuple, Any


def _post_process_circuit_result(
    results: Any, metadata: Dict[Any, Any]
) -> Tuple[
    Dict[str, List[List[bool]]], Dict[str, List[List[float]]], Dict[str, List[List[complex]]]
]:
    """Post processes the result returned from an AWSQuantumTask.

    Handles translation of samples of all qubits (the default)
    into qoqo registers.

    Args:
        results: results to be processed
        metadata: associated metadata of the job

    Returns:
        Tuple[Dict[str, List[List[bool]]],
              Dict[str, List[List[float]]],
              Dict[str, List[List[complex]]]: processed results
    """
    bit_results = {}
    measurements = results.measurements
    bit_field = measurements > 0
    bit_results[metadata["readout_name"]] = bit_field
    return (bit_results, {}, {})
