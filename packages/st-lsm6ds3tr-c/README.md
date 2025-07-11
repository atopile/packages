# STMicroelectronics LSM6DS3TR-C 6-DoF Accelerometer & Gyroscope

STMicroelectronics LSM6DS3TR-C is a system-in-package featuring a 3D digital accelerometer and a 3D digital gyroscope. This high-performance IMU sensor is designed for use in mobile applications such as smartphones, tablets, and wearable devices.

## Features

- 6-axis motion sensing: 3-axis accelerometer + 3-axis gyroscope
- Wide supply voltage range: 1.71V to 3.6V
- I2C and SPI digital interfaces
- Configurable I2C address (0x6A or 0x6B)
- Two programmable interrupt pins
- LGA-14 package (2.5mm x 3.0mm)

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "st-lsm6ds3tr-c.ato" import ST_LSM6DS3TR_C

module Usage:
    """
    Minimal usage example for ST_LSM6DS3TR_C.
    Shows how to connect the IMU with I2C interface and power supply.
    """

    # Create IMU instance
    imu = new ST_LSM6DS3TR_C

    # Create power supply
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # Create I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz
    i2c_bus.address = 0x6A

    # Connect interfaces
    power_3v3 ~ imu.power
    i2c_bus ~ imu.i2c
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
