# YLPTEC BYYXX Isolated DC-DC Converters

YLPTEC isolated 2W DC-DC converter modules with multiple input/output voltage options. These modules provide galvanic isolation and include input/output capacitors and status LED.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("TRAITS")

import ElectricPower
from "atopile/ylptech-byyxx/ylptech-byyxx.ato" import BYYXXS_2WR2

module Usage:
    """
    Minimal usage example for ylptech-byyxx.
    Shows how to use the YLPTEC isolated DC-DC converter.
    """

    # Create the regulator
    regulator = new BYYXXS_2WR2

    # Create power rails
    power_24v = new ElectricPower
    power_5v = new ElectricPower

    # Connect the regulator between the rails
    power_24v ~> regulator ~> power_5v
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
