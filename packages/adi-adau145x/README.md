# ADAU145x - Audio DSP

This package provides a driver for the ADAU145x family of audio DSPs.

## Usage

```ato

import I2C
import I2S
import ElectricPower
import ElectricLogic
import Resistor

from "atopile/adi-adau145x/adau145x.ato" import Analog_Devices_ADAU145x_driver

module Microcontroller:
    i2c = new I2C
    i2s = new I2S
    gpio = new ElectricLogic

module Amplifier:
    i2s = new I2S

module Example:
    """
    ADAU145x Example
    """
    dsp = new Analog_Devices_ADAU145x_driver
    mcu = new Microcontroller
    amp = new Amplifier

    # Power
    power = new ElectricPower
    power.required = True
    assert power.voltage within 3.3V
    power ~ dsp.power

    # Reset
    dsp.reset_disable ~ mcu.gpio

    # I2C - for configuration
    mcu.i2c ~ dsp.model.i2c

    # Pullups on I2C
    pullups = new Resistor[2]
    for pullup in pullups:
        pullup.resistance = 4.7kohm +/- 10%
        pullup.package = "R0402"

    mcu.i2c.sda.line ~> pullups[0] ~> power.vcc
    mcu.i2c.scl.line ~> pullups[1] ~> power.vcc

    # I2S - for audio
    mcu.i2s ~ dsp.model.i2s_ins[0]
    amp.i2s ~ dsp.model.i2s_outs[0]
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
