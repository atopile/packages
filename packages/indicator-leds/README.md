# Indicator LEDs (0603) – Red/Green/Blue/Yellow/Yellow-Green/White

Convenience modules for single indicator LEDs with a correctly sized series resistor.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")

import ElectricPower
import ElectricLogic
import ElectricSignal

from "atopile/indicator-leds/indicator-leds.ato" import LEDIndicatorRed
from "atopile/indicator-leds/indicator-leds.ato" import LEDIndicatorGreen
from "atopile/indicator-leds/indicator-leds.ato" import LEDIndicatorBlue

module Usage:
    """
    Minimal usage example for `indicator-leds`.
    Demonstrates 3 connection options and 2 active states.
    """

    red_led_active_high = new LEDIndicatorRed<active_low=False> # by default, active high, so template is optional
    green_led_active_high = new LEDIndicatorGreen
    blue_led_active_high = new LEDIndicatorBlue
    red_led_active_low = new LEDIndicatorRed<active_low=True>
    green_led_active_low = new LEDIndicatorGreen<active_low=True>
    blue_led_active_low = new LEDIndicatorBlue<active_low=True>

    # Connect to power (active high or low does not matter, always on when power is on)
    power = new ElectricPower
    power.voltage = 5V +/- 5%
    power ~ red_led_active_high.power
    power ~ red_led_active_low.power

    # Or connect to logic signal
    logic = new ElectricLogic
    logic.reference ~ power
    logic ~ green_led_active_high.logic
    logic ~ blue_led_active_low.logic

    # Or connect to analog signal
    analog_signal = new ElectricSignal
    analog_signal.reference ~ power
    analog_signal ~ green_led_active_low.analog_signal
    analog_signal ~ blue_led_active_high.analog_signal

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
