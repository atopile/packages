# Sensirion SCD40 CO₂ Sensor

The SCD4x is Sensirion’s next generation miniature CO2
sensor. This sensor builds on the photoacoustic sensing
principle and Sensirion’s patented PAsens® and
CMOSens® technology to offer high accuracy at an
unmatched price and smallest form factor. SMD assembly
allows cost- and space-effective integration of the sensor
combined with maximal freedom of design. On-chip signal
compensation is realized with the build-in SHT4x humidity
and temperature sensor.

## Usage

```ato
import ElectricPower
import I2C

from "atopile/sensirion-scd40/sensirion-scd40.ato" import Sensirion_SCD40

module Usage:
    """Minimal example for the Sensirion_SCD40 CO₂ sensor."""

    # MCU & sensor
    power = new ElectricPower
    i2c = new I2C

    co2_sensor = new Sensirion_SCD40

    # Shared 3V3 rail
    power.voltage = 3.3V +/- 5%
    power ~ power
    power ~ co2_sensor.power

    # I²C connection
    i2c ~ co2_sensor.i2c

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
