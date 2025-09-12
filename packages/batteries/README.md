# Batteries

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("TRAITS")

import ElectricPower

from "atopile/batteries/batteries.ato" import Battery, BatteryPrimary, BatterySecondary

module Usage:
    """
    Minimal usage example for batteries.
    Shows how to use the base battery modules.
    """

    # Example of a primary battery (non-rechargeable)
    primary_battery = new BatteryPrimary
    primary_battery.voltage = 3.7V +/- 5%
    primary_battery.capacity = 2000mAh +/- 10%
    primary_battery.discharge_current_max = 1A +/- 20%

    # Example of a secondary battery (rechargeable)
    secondary_battery = new BatterySecondary
    secondary_battery.voltage = 3.7V +/- 5%
    secondary_battery.capacity = 2000mAh +/- 10%
    secondary_battery.discharge_current_max = 2A +/- 20%
    secondary_battery.charge_current_max = 1A +/- 20%

    # Connect power interfaces
    power_primary = new ElectricPower
    power_primary ~ primary_battery.power

    power_secondary = new ElectricPower
    power_secondary ~ secondary_battery.power
```

## Overview

This package contains the base modules for various battery types and battery implementations. It provides:

- **Battery**: Base battery module with common parameters (voltage, capacity, discharge current)
- **BatteryPrimary**: Non-rechargeable battery module
- **BatterySecondary**: Rechargeable battery module with charging parameters
- **EMB_BATTERY_LP402535_driver**: Specific implementation for LP402535 lithium-ion battery

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
