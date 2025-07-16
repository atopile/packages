# SH1107 128x128 OLED display

This is a 128x128 pixel OLED display with SH1107 controller and I²C interface.

## Usage

```ato
import ElectricPower
import I2C

from "atopile/oled_sh1107/oled_sh1107.ato" import SH1107_128x128

module MCU:
    """Host MCU providing I²C bus and power rail."""

    power = new ElectricPower
    i2c = new I2C


module Usage:
    """Minimal example for the OLED12832."""

    # MCU & sensor
    mcu = new MCU
    display = new SH1107_128x128

    # Shared 3V3 rail
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V
    power_3v3 ~ mcu.power
    power_3v3 ~ display.power_3v3

    # I²C connection
    mcu.i2c ~ display.i2c
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
