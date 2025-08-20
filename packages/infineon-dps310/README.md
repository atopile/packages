# Infineon DPS310 Barometric Pressure and Altitude Sensor

The Infineon DPS310 is a miniaturized digital barometric pressure sensor capable of measuring both pressure and temperature. It features high precision and low current consumption, making it ideal for mobile applications, wearables, and IoT devices.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")
#pragma experiment("MODULE_TEMPLATING")

import ElectricPower
import I2C

from "atopile/infineon-dps310/infineon-dps310.ato" import Infineon_DPS310

module Usage:
    """
    Minimal usage example for infineon-dps310.
    Infineon DPS310 barometric pressure and altitude sensor with I²C interface.
    """

    # DPS310 sensor instance
    pressure_sensor = new Infineon_DPS310

    # Shared 3.3V rail
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # I²C bus
    i2c_bus = new I2C
    i2c_bus.address = 0x76  # SDO pin low

    # Connect power and I²C
    power_3v3 ~ pressure_sensor.power
    i2c_bus ~ pressure_sensor.i2c
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
