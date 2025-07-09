# InvenSense MPU-6050 6-Axis IMU

The **MPU-6050** from **TDK InvenSense** is a popular 6-axis motion tracking device, integrating a 3-axis gyroscope and 3-axis accelerometer plus an on-chip Digital Motion Processor™ (DMP).

This package provides an ato driver that models the device for use in Atopile projects. It handles power-rail definitions, I²C wiring, address selection via the `AD0` pin and adds basic decoupling.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import I2C
from "invensense-mpu6050.ato" import Invensense_MPU6050

module Demo:
    power = new ElectricPower
    i2c = new I2C

    imu = new Invensense_MPU6050

    imu.power_core ~ power
    imu.power_io ~ power
    imu.i2c ~ i2c
```

## PCB footprints & symbol

The footprint, symbol and 3-D model are auto-generated from LCSC part **C24112** and come bundled with this package.

## License

MIT © Atopile
