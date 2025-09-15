# ST LSM6DS3 6-Axis IMU (Accelerometer + Gyroscope)

The **LSM6DS3** is a low-power, high-performance 3-axis accelerometer and 3-axis gyroscope from STMicroelectronics. It supports both I²C and SPI bus interfaces; this package models the device in I²C mode by default.

## Usage

```ato
#pragma experiment("TRAITS")

import ElectricPower
import I2C
import has_part_removed

from "atopile/st-lsm6ds3/st-lsm6ds3.ato" import ST_LSM6DS3

module MCU:
    """Host MCU providing I²C bus and power rail."""

    trait has_part_removed

    power = new ElectricPower
    i2c = new I2C

    trait has_part_removed

module Usage:
    """Minimal example for the ST_LSM6DS3 accelerometer."""

    # MCU & sensor
    mcu = new MCU
    accelerometer = new ST_LSM6DS3

    # Shared 3V3 rail
    power = new ElectricPower
    power.voltage = 3.3V
    power ~ mcu.power
    power ~ accelerometer.power

    # I²C connection
    mcu.i2c ~ accelerometer.i2c
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
