# STMicroelectronics LIS3DH – 3-Axis Accelerometer

This package provides an Ato driver for the **LIS3DH** MEMS digital accelerometer.
It exposes separate core (VDD) and I/O (VDD_IO) power rails, an I²C bus, and two
interrupt outputs.

## Usage

```ato
import I2C, ElectricPower
from "atopile/st-lis3dh/lis3dh.ato" import LIS3DH_driver

module MyBoard:
    i2c = new I2C
    power_core = new ElectricPower  # 1.8-3.6 V core supply
    power_io   = new ElectricPower  # 1.8-3.6 V I/O supply

    sensor = new LIS3DH_driver

    # Power connections
    power_core ~ sensor.power_core
    power_io   ~ sensor.power_io

    # I2C connections
    i2c ~ sensor.i2c
```

## Contributing

Contributions are welcome! Please open pull requests or issues on the
GitHub repository.

## License

This package is distributed under the [MIT License](https://opensource.org/license/mit/).
