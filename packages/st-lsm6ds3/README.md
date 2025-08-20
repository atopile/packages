# ST LSM6DS3 6-Axis IMU (Accelerometer + Gyroscope)

The **LSM6DS3** is a low-power, high-performance 3-axis accelerometer and 3-axis gyroscope from STMicroelectronics.  It supports both I²C and SPI bus interfaces; this package models the device in I²C mode by default.

## Usage

```ato
import ElectricPower
import I2C

from "atopile/st-lsm6ds3/st-lsm6ds3.ato" import ST_LSM6DS3

module Usage:
    """Minimal example for the ST_LSM6DS3 accelerometer."""

    # Sensor
    accelerometer = new ST_LSM6DS3

    # Power supply (3.3V typical)
    power = new ElectricPower
    assert power.voltage within 3.3V +/- 5%
    power ~ accelerometer.power

    # I²C bus (would connect to your MCU)
    i2c = new I2C
    i2c ~ accelerometer.i2c

```

## Contributing
Contributions are welcome! Feel free to open issues or pull requests.

## License
This package is provided under the [MIT License](https://opensource.org/license/mit).
