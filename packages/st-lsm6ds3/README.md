# STMicroelectronics LSM6DS3 – 6-Axis IMU (Accel + Gyro)

This package provides an Ato driver for the **LSM6DS3TR-C** inertial measurement
unit, featuring a 3-axis accelerometer and 3-axis gyroscope.

The driver exposes separate core (VDD) and I/O (VDDIO) power rails, an I²C bus,
configurable I²C address pin (SDO/SA0), and two interrupt outputs (INT1/INT2).

## Usage

```ato
import I2C, ElectricPower
from "atopile/st-lsm6ds3/st-lsm6ds3.ato" import ST_LSM6DS3_driver

module MyBoard:
    # Create shared 3 V power rail
    power_3v = new ElectricPower
    power_3v.voltage = 3.3V +/- 5%

    # I²C bus
    i2c = new I2C

    # Instantiate IMU
    imu = new ST_LSM6DS3_driver

    # Connect power (both rails tied to the same 3 V source here)
    imu.power_core ~ power_3v
    imu.power_io   ~ power_3v

    # Connect I²C lines
    i2c ~ imu.i2c
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

Distributed under the [MIT License](https://opensource.org/license/mit/).
