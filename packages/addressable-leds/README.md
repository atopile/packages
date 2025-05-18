# Addressable LEDs

## Usage

```ato

import ElectricPower
import ElectricLogic

from "atopile/addressable-leds/sk6805-ec20.ato" import SK6805EC20_driver

module Test:
    leds = new SK6805EC20_driver[10]

    # Create ElectricPower
    power = new ElectricPower

    # Connect power to each LED
    for led in leds:
        power ~ led.power

    # Create ElectricLogic
    data_in = new ElectricLogic

    data_in ~> leds[0] ~> leds[1] ~> leds[2] ~> leds[3] ~> leds[4] ~> leds[5] ~> leds[6] ~> leds[7] ~> leds[8] ~> leds[9]


```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
