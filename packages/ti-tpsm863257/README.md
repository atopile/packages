# TI TPSM863257 Synchronous Buck Module

TI TPSM863257 is a high-efficiency synchronous buck converter module with integrated inductor and MOSFETs. It provides 3V to 17V input voltage range with 0.6V to 5.5V adjustable output voltage and up to 3A continuous current. Features FCCM (Forced Continuous Conduction Mode) for low output ripple and 1.2MHz switching frequency.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("TRAITS")

import ElectricPower
import ElectricLogic

from "atopile/ti-tpsm863257/ti-tpsm863257.ato" import TPSM863257

module Usage:
    """
    Minimal usage example for ti-tpsm863257.
    Shows how to create a 12V to 3.3V buck converter.
    """

    # Create the buck converter instance
    buck_converter = new TPSM863257

    # Input power supply (12V)
    power_12v = new ElectricPower
    power_12v.voltage = 12V +/- 3%

    # Output power rail (3.3V)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 3%

    # Power good indicator (optional)
    power_good_signal = new ElectricLogic
    power_good_signal.reference ~ power_3v3

    # Connect power rails
    power_12v ~ buck_converter.power_in
    power_3v3 ~ buck_converter.power_out

    # Connect control signals (enable has internal pullup, so it's optional)
    power_good_signal ~ buck_converter.power_good
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
