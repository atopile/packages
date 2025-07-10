# NXP PCT2075 Temperature Sensor

Driver for the NXP PCT2075 I²C temperature sensor and thermal watchdog. This digital temperature sensor provides 1°C accuracy and features a thermal watchdog with open-drain output.

## Features

- Digital temperature sensor with 1°C accuracy
- I²C-bus Fm+ interface (up to 1 MHz)
- Thermal watchdog with programmable temperature limit
- Open-drain overtemperature output
- Configurable I²C address via address pins (0x48-0x4F)
- Low power consumption
- Wide operating temperature range

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "nxp-pct2075.ato" import NXP_PCT2075

module Usage:
    """
    Minimal usage example for NXP PCT2075 temperature sensor.
    Demonstrates basic I²C connection and power supply.
    """

    sensor = new NXP_PCT2075

    # Power supply
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%
    power_3v3 ~ sensor.power

    # I²C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz
    i2c_bus ~ sensor.i2c

    # Set I²C address (default 0x48 with all address pins low)
    sensor.i2c.address = 0x48
```

## I²C Address Configuration

The PCT2075 supports 8 different I²C addresses (0x48-0x4F) configured via the A0, A1, and A2 pins:

| A2 | A1 | A0 | I²C Address |
|----|----|----|-------------|
| 0  | 0  | 0  | 0x48        |
| 0  | 0  | 1  | 0x49        |
| 0  | 1  | 0  | 0x4A        |
| 0  | 1  | 1  | 0x4B        |
| 1  | 0  | 0  | 0x4C        |
| 1  | 0  | 1  | 0x4D        |
| 1  | 1  | 0  | 0x4E        |
| 1  | 1  | 1  | 0x4F        |

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
