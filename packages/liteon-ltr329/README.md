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

    # Sensor
    ambient_light_sensor = new Liteon_LTR329

    # Shared 3V3 rail
    power = new ElectricPower
    power.voltage = 3.3V
    power ~ ambient_light_sensor.power

    # I²C connection
    i2c_bus = new I2C
    i2c_bus ~ ambient_light_sensor.i2c
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
