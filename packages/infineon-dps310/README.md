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

from "atopile/infineon-dps310/infineon-dps310.ato" import Infineon_DPS310

module MCU:
    """Host MCU providing I²C bus and power rail."""

    power = new ElectricPower
    i2c = new I2C


module Usage:
    """Minimal example for the Infineon_DPS310 barometric pressure and altitude sensor."""

    # MCU & sensor
    mcu = new MCU
    pressure_sensor = new Infineon_DPS310

    # Shared 3V3 rail
    power = new ElectricPower
    power.voltage = 3.3V
    power ~ mcu.power
    power ~ pressure_sensor.power

    # I²C connection
    mcu.i2c ~ pressure_sensor.i2c

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
