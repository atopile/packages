# STMicroelectronics LIS2MDL 3-Axis Magnetometer

The LIS2MDL is a ultra-low-power, high-performance 3-axis digital magnetometer from STMicroelectronics. It features a wide magnetic field dynamic range up to ±50 gauss with 16-bit data output and supports both I²C and SPI interfaces.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "atopile/st-lis2mdl/st-lis2mdl.ato" import ST_LIS2MDL

module Usage:
    """
    Minimal usage example for ST LIS2MDL magnetometer.
    Demonstrates basic I2C connection and dual power supply configuration.
    """

    # Magnetometer instance
    magnetometer = new ST_LIS2MDL

    # External interfaces
    power_3v3 = new ElectricPower
    """
    3.3V power supply for core (VDD) and I/O (VDDIO)
    """

    i2c_bus = new I2C

    # Connect power supplies
    power_3v3 ~ magnetometer.power
    power_3v3 ~ magnetometer.power_io

    assert power_3v3.voltage within 3.0V to 3.6V

    # Connect I2C bus
    i2c_bus ~ magnetometer.i2c

    # Set I2C address
    assert magnetometer.i2c.address is 0x1E
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
