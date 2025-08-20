# ST LSM303AGR – 3-Axis Accelerometer + 3-Axis Magnetometer (eCompass)

The **LSM303AGR** is a miniature system-in-package from STMicroelectronics that combines a high-precision 3-axis accelerometer with a 3-axis magnetometer, providing a complete *eCompass* solution in a single 3 mm × 3 mm LGA-12 package.

This package exposes a fully-connected `ST_LSM303AGR` driver module that bundles the bare IC together with the required decoupling capacitors, I²C pull-ups and address-selection resistor.  It can be dropped straight into your design; just connect an `I2C` bus and an `ElectricPower` rail.

## Usage

```ato
import ElectricPower
import I2C

from "atopile/st-lsm303agr/st-lsm303agr.ato" import ST_LSM303AGR

module Usage:
    """Minimal example for the ST_LSM303AGR accelerometer."""

    # Sensor
    imu = new ST_LSM303AGR

    # Power supply (3.3V typical)
    power = new ElectricPower
    assert power.voltage within 3.3V +/- 5%
    power ~ imu.power

    # I²C bus (would connect to your MCU)
    i2c = new I2C
    i2c ~ imu.i2c

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
