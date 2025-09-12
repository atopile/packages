# Texas Instruments PCM1789 2-CH I2S Audio DAC

High-performance stereo audio DAC with I2S input and differential outputs. The PCM1789 is a monolithic CMOS integrated circuit that includes stereo digital-to-analog converters and support circuitry in a small TSSOP-24 package.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import I2S
import I2C
import ElectricLogic
import ElectricPower
import DifferentialPair

from "atopile/ti-pcm1789/ti-pcm1789.ato" import Texas_Instruments_PCM1789_driver


module Usage:
    """
    Minimal usage example for ti-pcm1789.
    Shows how to connect the PCM1789 DAC to a microcontroller with I2S and I2C interfaces.
    """

    dac = new Texas_Instruments_PCM1789_driver

    # Power supplies
    power_5v = new ElectricPower
    power_5v.voltage = 5V +/- 5%
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # Connect power
    dac.power_5v ~ power_5v
    dac.power_3v3 ~ power_3v3

    # I2C interface
    i2c = new I2C
    i2c ~ dac.i2c

    # I2S interface
    i2s = new I2S
    i2s ~ dac.i2s

    # Master clock
    master_clock = new ElectricLogic
    master_clock ~ dac.master_clock

    # Audio outputs (differential pairs)
    audio_outputs = new DifferentialPair[2]
    audio_outputs[0] ~ dac.outputs[0]
    audio_outputs[1] ~ dac.outputs[1]
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
