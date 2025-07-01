# Buttons

Implements vertical and horizontal momentary switches as well as a pullup and pulldown module.

## Usage

```ato
from "atopile/buttons/buttons.ato" import ButtonPullup
from "atopile/buttons/buttons.ato" import ButtonDown
from "atopile/buttons/buttons.ato" import VerticalButton
from "atopile/buttons/buttons.ato" import HorizontalButton

module TestPullupPulldownButtons:
    """
    Test module for pullup/pulldown buttons
    """
    # Create example signals
    config_pins = new ElectricSignal[2]
    power = new ElectricPower
    for config_pin in config_pins:
        config_pin.reference ~ power # Typically done inside a driver

    # Make and configure pullup and pulldown buttons
    btn_pullup_vertical = new ButtonPullup
    btn_pullup_vertical.button.button -> VerticalButton
    config_pins[0] ~ btn_pullup_vertical.output

    btn_pulldown_horizontal = new ButtonPulldown
    btn_pulldown_horizontal.button.button -> HorizontalButton
    config_pins[1] ~ btn_pulldown_horizontal.output

module TestButtons:
    """
    Test module for direct use of horizontal and vertical buttons
    """
    config_pins = new ElectricSignal[2]
    power = new ElectricPower
    for config_pin in config_pins:
        config_pin.reference ~ power # Typically done inside a driver

    # When button is pressed, enable will be pulled HIGH via a 10k resistor
    pull_resistors = new Resistor[2]
    for pr in pull_resistors:
        pr.resistance = 10kohms +/- 20%
        pr.package = "R0402"

    btn_horizontal = new HorizontalButton
    btn_vertical = new VerticalButton

    # Connect first button to pull config_pins[0] to gnd through 10k
    config_pins[0].line ~> btn_horizontal ~> pull_resistors[0] ~> power.lv

    # Connect second button to pull config_pins[1] to hv through 10k
    config_pins[1].line ~> btn_vertical ~> pull_resistors[1] ~> power.hv
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
