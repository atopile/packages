# TLV75901 LDO

TLV75901 LDO Regulator with adjustable output voltage

## Usage

```ato

import ElectricPower

from "atopile/ti-tlv75901/ti-tlv75901.ato" import TLV75901_driver
from "atopile/buttons/buttons.ato" import ButtonPulldown
from "atopile/buttons/buttons.ato" import VerticalButton

module Test:
    # Create LDO
    ldo = new TLV75901_driver

    # Configure voltages
    ldo.v_in = 5V +/- 1%
    ldo.v_out = 3.3V +/- 3%

    # Create example power interfaces
    power_in = new ElectricPower
    power_out = new ElectricPower

    # Connect to regulator (bridge connect)
    power_in ~> ldo ~> power_out

    # Connect to regulator (Interfaces)
    power_in ~ ldo.power_in
    power_out ~ ldo.power_out

    # Disable button
    disable_button = new ButtonPulldown
    disable_button.button.button -> VerticalButton
    disable_button.output ~ ldo.enable
    disable_button.pulldown.resistance = 1kohms +/- 20%

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
