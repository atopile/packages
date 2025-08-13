# Indicator LEDs (0603) – Red/Green/Blue/Yellow/Yellow-Green/White

Convenience modules for single indicator LEDs with a correctly sized series resistor and bridgeable interface.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import ElectricSignal
import ElectricPower

from "indicator-leds.ato" import LEDIndicatorRed
from "indicator-leds.ato" import LEDIndicatorGreen

module Usage:
    red_led = new LEDIndicatorRed
    green_led = new LEDIndicatorGreen

    power = new ElectricPower
    power.voltage = 5V
    power ~ red_led.power

    gpio = new ElectricSignal
    gpio.line ~> green_led ~> gpio.reference.lv
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
