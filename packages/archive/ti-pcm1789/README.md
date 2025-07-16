# TI PCM1789 2-CH I2S Audio DAC

## Usage

```ato

import I2S
import I2C
import ElectricPower
import DifferentialPair

from "atopile/ti-pcm1789/ti-pcm1789.ato" import Texas_Instruments_PCM1789_driver


module Micro:
    power_3v3 = new ElectricPower
    i2s = new I2S
    i2c = new I2C

module XLR:
    balanced = new DifferentialPair

module Example:
    dac = new Texas_Instruments_PCM1789_driver
    micro = new Micro
    xlrs = new XLR[2]

    # Power
    power_5v = new ElectricPower
    power_5v.voltage = 5V
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    micro.power_3v3 ~ power_3v3
    dac.power_5v ~ power_5v
    dac.power_3v3 ~ power_3v3

    # Connect data
    micro.i2c ~ dac.i2c
    micro.i2s ~ dac.i2s
    micro.clock_out ~ dac.master_clock

    # Connect outputs
    dac.outputs[0] ~ xlrs[0].balanced
    dac.outputs[1] ~ xlrs[1].balanced


```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
