# Infineon DPS310 Barometric Pressure Sensor

The DPS310 is a miniaturized digital barometric air pressure sensor with ultra-high precision (±0.002 hPa or ±0.02 m) and low current consumption. The sensor provides temperature measurements as well. Both pressure and temperature measurements are available via I²C/SPI interfaces.

## Usage

```ato
import ElectricPower
import I2C

from "atopile/infineon-dps310/infineon-dps310.ato" import Infineon_DPS310

module Usage:
    """Minimal example for the Infineon_DPS310 barometric pressure and altitude sensor."""

    # Pressure sensor
    pressure_sensor = new Infineon_DPS310

    # Power supply (3.3V typical)
    power = new ElectricPower
    assert power.voltage within 3.3V +/- 5%
    power ~ pressure_sensor.power

    # I²C bus (would connect to your MCU)
    i2c = new I2C
    i2c ~ pressure_sensor.i2c

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
