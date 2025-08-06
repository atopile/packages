# Shenzhen Allvision Tech N087 2832TSWYG02 H14 128x32 OLED Display

A 0.91" 128x32 OLED display with I²C interface.

## Usage

```ato
import ElectricPower
import I2C

from "atopile/allvision-oled128x32/allvision_oled128x32.ato" import OLED12832

module MCU:
    """Host MCU providing I²C bus and power rail."""

    power = new ElectricPower
    i2c = new I2C


module Usage:
    """Minimal example for the OLED12832."""

    # MCU & sensor
    mcu = new MCU
    display = new OLED12832

    # Shared 3V3 rail
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V
    power_5v = new ElectricPower
    power_5v.voltage = 5V
    power_3v3 ~ mcu.power
    power_5v ~ display.power_5v
    power_3v3 ~ display.power_3v3

    # I²C connection
    mcu.i2c ~ display.i2c
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
