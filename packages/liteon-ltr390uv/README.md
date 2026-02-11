# Lite-On LTR-390UV UV Light Sensor

Digital UV sensor with 16-bit resolution and I²C interface. This package wraps the
hardware connections so you can drop it into your design effortlessly.

## Usage

```ato
import ElectricPower
import I2C

from "atopile/liteon-ltr390uv/liteon-ltr390uv.ato" import Liteon_LTR390UV

module Usage:
    """Minimal example for the Liteon_LTR390UV UV sensor."""

    # UV sensor
    uv_sensor = new Liteon_LTR390UV

    # Power supply
    power = new ElectricPower
    assert power.voltage within 3.3V +/- 5%
    power ~ uv_sensor.power

    # I²C bus (would connect to your MCU)
    i2c = new I2C
    i2c ~ uv_sensor.i2c

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
