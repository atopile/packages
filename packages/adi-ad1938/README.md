# AD1938 - Audio DAC/ADC

This package provides a driver for the AD1938 audio DAC/ADC (CODEC) with 4 differential inputs
(2x stereo) and 8 unipolar outputs (4x stereo).

## Usage

```ato
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")
import I2S
import ElectricPower
import ElectricLogic
import ElectricSignal
import SPI

from "ad1938.ato" import Analog_Devices_AD1938_driver

module Microcontroller:
    spi = new SPI
    i2s = new I2S[2]
    gpio = new ElectricLogic

module Amplifier:
    analog_input_left = new ElectricSignal
    analog_input_right = new ElectricSignal

module ClockSource:
    clock_out = new ElectricLogic

module Example:
    """
    AD1938 Example
    """
    dac_adc = new Analog_Devices_AD1938_driver
    mcu = new Microcontroller
    amp = new Amplifier
    clock_source = new ClockSource

    # Power
    power = new ElectricPower
    power.required = True
    assert power.voltage within 3.3V
    power ~ dac_adc.power

    # Reset
    dac_adc.reset_disable ~ mcu.gpio

    # dac/adc configuration


    # SPI - for configuration
    mcu.spi ~ dac_adc.model.spi

    # I2S - for audio
    mcu.i2s[0] ~ dac_adc.model.i2s_ins[0]
    mcu.i2s[1] ~ dac_adc.model.i2s_outs[0]
    amp.analog_input_left ~ dac_adc.model.dac_channels[0].analog_left
    amp.analog_input_right ~ dac_adc.model.dac_channels[0].analog_right

    # clock
    clock_source.clock_out ~ dac_adc.model.pll_clock_in
```

## Development notes

See [Development notes](../development_notes.md) for information about this codec.

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
