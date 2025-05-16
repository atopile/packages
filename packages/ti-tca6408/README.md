# TCA6408 8ch GPIO expander

## Usage

```ato

import I2C
import Power

from "atopile/ti-tca6408/ti-tca6408.ato" import Texas_Instruments_TCA6408_driver


module Test:
    """
    Test TCA6408 driver
    """
    expanders = new Texas_Instruments_TCA6408_driver[2]

    # Power and I2C
    i2c = new I2C
    power = new ElectricPower
    power.voltage = 3.3V

    # Set addresses
    expanders[0].i2c.address = 0x20
    expanders[1].i2c.address = 0x21

    # Connect power and I2C
    for expander in expanders:
        expander.power ~ power
        expander.i2c ~ i2c


```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
