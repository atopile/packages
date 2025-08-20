# Lite-On LTR-329ALS-01 Ambient Light Sensor

Digital ALS with 16-bit resolution and I²C interface. This package wraps the
hardware connections so you can drop it into your design effortlessly.

## Usage

```ato
import ElectricPower
import I2C

from "atopile/liteon-ltr329/liteon-ltr329.ato" import Liteon_LTR329

module Usage:
    """Minimal example for the Liteon_LTR329 ambient light sensor."""

    # Ambient light sensor
    ambient_light_sensor = new Liteon_LTR329

    # Power supply
    power = new ElectricPower
    assert power.voltage within 3.3V +/- 5%
    power ~ ambient_light_sensor.power

    # I²C bus (would connect to your MCU)
    i2c = new I2C
    i2c ~ ambient_light_sensor.i2c
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
