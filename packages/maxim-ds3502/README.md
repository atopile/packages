# Maxim DS3502 Digital Potentiometer (10 kΩ, I²C)

The **Maxim Integrated DS3502** is a 128-step (7-bit), non-volatile 10 kΩ digital potentiometer controllable over an I²C bus. It is ideal for replacing mechanical trim-pots in calibration and biasing applications. The device integrates an EEPROM that stores the wiper position, allowing the resistance setting to be automatically restored on power-up.

## Usage

```ato
import ElectricPower
import I2C
import Electrical

from "atopile/maxim-ds3502/maxim-ds3502.ato" import Maxim_DS3502

module Usage:
    """
    Minimal usage example for maxim-ds3502.
    DS3502 used as a programmable voltage divider between 3V3 and GND.
    """

    # DS3502 instance
    pot = new Maxim_DS3502

    # Shared 3.3V rail
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # I²C bus
    i2c_bus = new I2C

    # Power and I²C connections
    power_3v3 ~ pot.power
    i2c_bus ~ pot.i2c

    # Wire potentiometer as voltage divider
    power_3v3.hv ~ pot.potentiometer_high.line  # RH to 3V3
    power_3v3.lv ~ pot.potentiometer_low.line   # RL to GND
    pot.i2c.address = 0x28  # A1=A0=0 on DS3502

    # Wiper output
    wiper_out = new Electrical
    wiper_out ~ pot.potentiometer_wiper.line   # RW output

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
