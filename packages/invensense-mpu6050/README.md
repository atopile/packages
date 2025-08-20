# InvenSense MPU-6050 6-Axis IMU

The **MPU-6050** from **TDK InvenSense** is a popular 6-axis motion tracking device, integrating a 3-axis gyroscope and 3-axis accelerometer plus an on-chip Digital Motion Processor™ (DMP).

This package provides an ato driver that models the device for use in Atopile projects. It handles power-rail definitions, I²C wiring, address selection via the `AD0` pin and adds basic decoupling.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import I2C
from "atopile/invensense-mpu6050/invensense-mpu6050.ato" import Invensense_MPU6050

module Usage:
    """Minimal usage example for `invensense-mpu6050`.
    Shows how to wire the IMU to a shared 3V3 power rail and I²C bus.
    """

    # Shared rails / busses
    power_3v3 = new ElectricPower
    i2c_bus = new I2C

    # IMU instance
    imu = new Invensense_MPU6050

    # Connections
    imu.power_core ~ power_3v3
    imu.power_io ~ power_3v3
    imu.i2c ~ i2c_bus

    # Configure I²C address (AD0 pulled low => 0x68)
    i2c_bus.address = 0x68

```

## PCB footprints & symbol

The footprint, symbol and 3-D model are auto-generated from LCSC part **C24112** and come bundled with this package.

## License

MIT © Atopile
