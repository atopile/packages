# STMicroelectronics LSM6DSOX 6-Axis IMU

The LSM6DSOX is a system-in-package featuring a high-performance 3-axis digital accelerometer and 3-axis digital gyroscope from STMicroelectronics. It features ultra-low power consumption (0.55 mA in combo high-performance mode), always-on experience, smart FIFO up to 9 kbytes, machine learning core, finite state machine, and advanced motion detection capabilities.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "atopile/st-lsm6dsox/st-lsm6dsox.ato" import ST_LSM6DSOX

module Usage:
    """
    Minimal usage example for ST LSM6DSOX 6-axis IMU.
    Demonstrates basic I2C connection and dual power supply configuration.
    """

    # IMU instance
    imu = new ST_LSM6DSOX

    # External interfaces
    power_3v3 = new ElectricPower
    """
    3.3V power supply for core (VDD) and I/O (VDDIO)
    """

    i2c_bus = new I2C

    # Connect power supplies
    power_3v3 ~ imu.power
    power_3v3 ~ imu.power_io

    assert power_3v3.voltage within 3.0V to 3.6V

    # Connect I2C bus
    i2c_bus ~ imu.i2c

    # Configure I2C address (0x6A when SA0=GND, 0x6B when SA0=VDD)
    # Default configuration uses SA0=GND for address 0x6A
    assert imu.i2c.address within 0x6A

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
