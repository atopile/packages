# Batteries - Power Storage Components

Base battery modules providing common battery characteristics for primary and secondary batteries.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("TRAITS")

import ElectricPower
import has_part_removed

from "atopile/batteries/batteries.ato" import EMB_BATTERY_LP402535

module Load:
    """Example load that draws power from battery"""
    power = new ElectricPower
    trait has_part_removed

module Usage:
    """
    Minimal usage example for batteries.
    Shows how to use different battery types with their characteristics.
    """

    # Example secondary battery (rechargeable LP402535)
    secondary_battery = new EMB_BATTERY_LP402535

    # Example loads
    load1 = new Load

    # Connect batteries to loads
    secondary_battery.power ~ load1.power
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
