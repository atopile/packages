# Maxim MAX17048 LiPoly/LiIon Fuel Gauge and Battery Monitor

Low cost Lithium Polymer batteries have revolutionized electronics - they're thin, light, can be regulated down to 3.3V and they're easy to charge. The MAX17048 is a simple-to-use fuel gauge IC that provides accurate battery monitoring for single-cell lithium-ion/polymer batteries.

This fuel gauge decodes the non-linear battery voltage to calculate accurate charge percentage, eliminating the guesswork in battery monitoring applications.

## Features

- Compatible with 1S 3.7-4.2V Lithium Ion or Polymer batteries
- I2C interface for easy communication
- Accurate battery percentage calculation from voltage
- Low power consumption
- Operating voltage: 1.8V to 5.5V
- Alert functionality for low battery conditions
- Compatible with 3.3V and 5.0V logic levels

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("TRAITS")

import ElectricPower
import I2C
import has_part_removed
from "atopile/maxim-max17048/maxim-max17048.ato" import Maxim_MAX17048

module Battery:
    """
    Conceptual battery module for usage examples.
    In real applications, this would represent the actual LiPoly/LiIon battery.
    """
    trait has_part_removed
    power = new ElectricPower

module Usage:
    """
    Minimal usage example for Maxim MAX17048 LiPoly/LiIon Fuel Gauge.
    Shows how to connect power, I2C bus, and battery monitoring.
    """

    # Create fuel gauge instance
    fuel_gauge = new Maxim_MAX17048

    # Power supply (3.3V typical)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%
    power_3v3 ~ fuel_gauge.power

    # I2C bus
    i2c_bus = new I2C
    i2c_bus.address = 0x36
    i2c_bus.frequency = 400kHz
    i2c_bus ~ fuel_gauge.i2c

    # Battery connections (would connect to actual battery terminals)
    # Note: In real application, these would connect to your LiPoly/LiIon battery
    battery = new Battery
    battery.power ~ fuel_gauge.battery_interface
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
