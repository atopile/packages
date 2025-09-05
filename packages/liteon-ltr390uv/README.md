# Lite-On LTR-329ALS-01 Ambient Light Sensor

Digital ALS with 16-bit resolution and I²C interface. This package wraps the
hardware connections so you can drop it into your design effortlessly.

## Usage

```ato
import ElectricPower
import I2C

from "atopile/liteon-ltr390uv/liteon-ltr390uv.ato" import Liteon_LTR390UV

module MCU:
    """Host MCU providing I²C bus and power rail."""

    power = new ElectricPower
    i2c = new I2C


module Usage:
    """Minimal example for the Liteon_LTR390UV UV sensor."""

    # MCU & sensor
    mcu = new MCU
    uv_sensor = new Liteon_LTR390UV

    # Shared 3V3 rail
    power = new ElectricPower
    power.voltage = 3.3V
    power ~ mcu.power
    power ~ uv_sensor.power

    # I²C connection
    mcu.i2c ~ uv_sensor.i2c

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
