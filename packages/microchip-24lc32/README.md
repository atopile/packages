# Microchip 24LC32 – 32-Kbit I²C Serial EEPROM

The **Microchip 24LC32** is a 32-Kbit (4 K × 8) serial EEPROM with an I²C interface
and wide operating-voltage range (1.8 V – 5.5 V)

## Usage

```ato
import ElectricPower
import I2C

from "atopile/microchip-24lc32/microchip-24lc32.ato" import Microchip_24LC32

module MCU:
    """Host MCU providing I²C bus and power rail."""

    power = new ElectricPower
    i2c = new I2C


module Usage:
    """Minimal example for the Microchip 24LC32 EEPROM."""

    # MCU & sensor
    mcu = new MCU
    eeprom = new Microchip_24LC32

    # Shared 3V3 rail
    power = new ElectricPower
    power.voltage = 3.3V
    power ~ mcu.power
    power ~ eeprom.power

    # I²C connection
    mcu.i2c ~ eeprom.i2c

```

## Contributing

Issues and pull-requests are welcome — please open them on the [atopile/packages](https://github.com/atopile/packages) repository.

## License

This package is provided under the MIT License. See the `LICENSE` file for details.
