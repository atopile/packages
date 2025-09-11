# ST LSM303AGR – 3-Axis Accelerometer + 3-Axis Magnetometer (eCompass)

The **LSM303AGR** is a miniature system-in-package from STMicroelectronics that combines a high-precision 3-axis accelerometer with a 3-axis magnetometer, providing a complete *eCompass* solution in a single 3 mm × 3 mm LGA-12 package.

This package exposes a fully-connected `ST_LSM303AGR` driver module that bundles the bare IC together with the required decoupling capacitors, I²C pull-ups and address-selection resistor.  It can be dropped straight into your design; just connect an `I2C` bus and an `ElectricPower` rail.

## Usage

```ato
#pragma experiment("TRAITS")

import ElectricPower
import I2C
import has_part_removed

from "atopile/st-lsm303agr/st-lsm303agr.ato" import ST_LSM303AGR

module MCU:
    """Host MCU providing I²C bus and power rail."""

    trait has_part_removed

    power = new ElectricPower
    i2c = new I2C


module Usage:
    """Minimal example for the ST_LSM303AGR accelerometer."""

    # MCU & sensor
    mcu = new MCU
    imu = new ST_LSM303AGR

    # Shared 3V3 rail
    power = new ElectricPower
    power.voltage = 3.3V
    power ~ mcu.power
    power ~ imu.power

    # I²C connection
    mcu.i2c ~ imu.i2c
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
