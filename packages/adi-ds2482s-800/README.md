# Analog Devices DS2482S-800 8-Channel I2C to 1-Wire Bus Adapter

The DS2482S-800 is an 8-channel I2C-to-1-Wire bus adapter that allows easy connection of multiple 1-Wire devices (such as DS18B20 temperature sensors) to an I2C bus. This package provides a complete atopile module for the DS2482S-800 chip.

## Features

- 8 selectable 1-Wire channels
- I2C interface with configurable address (0x18-0x1F)
- Wide operating voltage range: 2.9V to 5.5V
- Built-in parasitic power pullups
- Self-timed operation with standard and Overdrive speeds support
- Slew-controlled 1-Wire edges to minimize line noise

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")

import ElectricPower
import I2C
from "atopile/adi-ds2482s-800/adi-ds2482s-800.ato" import ADI_DS2482S_800

module Usage:
    """
    Minimal usage example for `adi-ds2482s-800`.
    Shows how to connect the DS2482S-800 8-channel I2C to 1-Wire bus adapter.
    """

    # Create the DS2482S-800 instance
    ds2482 = new ADI_DS2482S_800

    # Power supply (3.3V typical)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%
    power_3v3 ~ ds2482.power

    # I2C bus connection
    i2c = new I2C
    i2c.frequency = 400kHz
    i2c.address = 0x18  # Base address when all address pins are low
    i2c ~ ds2482.i2c

    # The 8 1-Wire channels are now available as:
    # ds2482.onewire_channels[0] through ds2482.onewire_channels[7]
    # These can be connected to DS18B20 temperature sensors or other 1-Wire devices

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
