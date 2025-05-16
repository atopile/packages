# Assorted Buttons

Implements a few common buttons configured as current limited pullups/pulldowns

Connected like so:

```
output.line ~> btn ~> resistor ~> output.hv/.lv (pullup/pulldown)
```

## Usage

```ato
from "atopile/buttons/buttons.ato" import ButtonPullup
from "atopile/buttons/buttons.ato" import ButtonDown
from "atopile/buttons/buttons.ato" import ButtonSKRPACE010
from "atopile/buttons/buttons.ato" import ButtonSKTDLDE010


module Test:
    """
    Test module for buttons
    """
    # Make and configure buttons
    btn_pullup_vertical = new ButtonPullup
    btn_pullup_vertical.btn -> ButtonSKRPACE010

    btn_pullup_horizontal = new ButtonPullup
    btn_pullup_horizontal.btn -> ButtonSKTDLDE010

    btn_pulldown_vertical = new ButtonPulldown
    btn_pulldown_vertical.btn -> ButtonSKRPACE010

    btn_pulldown_horizontal = new ButtonPulldown
    btn_pulldown_horizontal.btn -> ButtonSKTDLDE010

    # Create example signals
    enable = new ElectricLogic
    power = new ElectricPower
    enable.reference ~ power # Typically done inside a driver

    # Connect button
    enable ~ btn_pullup_vertical.output

    # When button is pressed, enable will be pulled HIGH via a 10k resistor
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
