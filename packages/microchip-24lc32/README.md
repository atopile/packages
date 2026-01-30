# Microchip 24LC32 – 32-Kbit I²C Serial EEPROM

The **Microchip 24LC32** is a 32-Kbit (4 K × 8) serial EEPROM with an I²C interface
and wide operating-voltage range (1.8 V – 5.5 V)

## Usage

```ato
import ElectricPower
import I2C

from "atopile/microchip-24lc32/microchip-24lc32.ato" import Microchip_24LC32

module Usage:
    """Minimal example for the Microchip 24LC32 EEPROM."""

    # EEPROM instance
    eeprom = new Microchip_24LC32

    # Power rail
    power = new ElectricPower
    power.voltage = 3.3V
    power ~ eeprom.power

    # I²C bus
    i2c = new I2C
    i2c ~ eeprom.i2c
```

## Contributing

Issues and pull-requests are welcome — please open them on the [atopile/packages](https://github.com/atopile/packages) repository.

## License

This package is provided under the MIT License. See the `LICENSE` file for details.
