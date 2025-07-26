# STMicroelectronics LIS3MDL 3-Axis Magnetometer

The **LIS3MDL** from **STMicroelectronics** is a high-performance 3-axis magnetometer sensor with digital I²C/SPI interface. It's designed for electronic compass applications and provides ultra-low power consumption with excellent temperature stability.

This package provides an ato driver that models the device for use in Atopile projects. It handles power-rail definitions, I²C/SPI wiring, address selection via the `SA1` pin, and adds basic decoupling capacitors.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import I2C
from "st-lis3mdl.ato" import ST_LIS3MDL

module Usage:
    """Minimal usage example for `st-lis3mdl`.
    Shows how to wire the magnetometer to a shared 3V3 power rail and I²C bus.
    """

    # Shared rails / busses
    power_3v3 = new ElectricPower
    i2c_bus = new I2C

    # Magnetometer instance
    magnetometer = new ST_LIS3MDL

    # Connections
    magnetometer.power_core ~ power_3v3
    magnetometer.power_io ~ power_3v3
    magnetometer.i2c ~ i2c_bus

    # Configure I²C address (SA1 pulled low => 0x1C)
    # SA1 pulled high => 0x1E
    assert i2c_bus.address is 0x1C
```

## PCB footprints & symbol

The footprint, symbol and 3-D model are auto-generated from LCSC part **C478483** and come bundled with this package.

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
