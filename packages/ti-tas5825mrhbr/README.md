# TI TAS5825MRHBR 2-CH I2S Audio Amplifier

## Usage

```ato

import ElectricPower
import I2C
import I2S

from "atopile/ti-tas5825mrhbr/ti_tas5825mrhbr.ato" import Texas_Instruments_TAS5825MRHBR_driver

module Example:
    amp = new Texas_Instruments_TAS5825MRHBR_driver

    power_3v3 = new ElectricPower
    power_20V = new ElectricPower
    power_3v3.voltage = 3.3V
    power_20V.voltage = 20V

    i2s = new I2S
    i2c = new I2C

    amp.power_pvdd ~ power_20V
    amp.power_dvdd ~ power_3v3

    amp.i2s ~ i2s
    amp.i2c ~ i2c

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
