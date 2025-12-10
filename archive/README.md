This CHANGELOG includes the old content regarding the packages `qoqo_for_braket_devices` and `roqoqo_for_braket_devices`. Kept for archiving purposes.

# qoqo_for_braket_devices

Braket devices interface for the qoqo quantum toolkit by [HQS Quantum Simulations](https://quantumsimulations.de). The API documentation is available [here](https://hqsquantumsimulations.github.io/qoqo-for-braket/qoqo_for_braket_devices_api/html/generated/generated/qoqo_for_braket_devices.devices.html#module-qoqo_for_braket_devices.devices).

In order to make the update a device instance with Braket's information possible, the user has to run the following code before using this package:
```python
TODO
```

### Installation

We provide pre-built binaries for linux, macos and windows on x86_64 hardware and macos on arm64. Simply install the pre-built wheels with

```shell
pip install qoqo-for-braket-devices
```

## General

Braket is under the Apache-2.0 license ( see https://github.com/aws/amazon-braket-sdk-python/blob/main/LICENSE ).

qoqo_for_braket_devices itself is also provided under the Apache-2.0 license.

## Testing

This software is still in the beta stage. Functions and documentation are not yet complete and breaking changes can occur.

If you find unexpected behaviour please open a github issue.

# roqoqo_for_braket_devices

Braket devices interface for the qoqo quantum toolkit by [HQS Quantum Simulations](https://quantumsimulations.de). The API documentation is available [here](https://hqsquantumsimulations.github.io/qoqo-for-braket/roqoqo_for_braket_devices_api/roqoqo_for_braket_devices/index.html).

### Installation

To use roqoqo_for_braket_devices in a Rust project simply add

```TOML
roqoqo_for_braket_devices = { version="0.1" }
```

to the `[dependencies]` section of the project Cargo.toml.