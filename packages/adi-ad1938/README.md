# AD1938 - Audio DAC/ADC

This package provides a driver for the AD1938 audio DAC/ADC (CODEC) with 4 differential inputs
(2x stereo) and 8 unipolar outputs (4x stereo).

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")

import I2S
import ElectricPower
import ElectricLogic
import ElectricSignal
import SPI
import has_part_removed

from "atopile/adi-ad1938/adi-ad1938.ato" import Analog_Devices_AD1938_driver

module Microcontroller:
    spi = new SPI
    i2s = new I2S[2]
    gpio = new ElectricLogic

    trait has_part_removed

module Amplifier:
    analog_input_left = new ElectricSignal
    analog_input_right = new ElectricSignal

    trait has_part_removed

module ClockSource:
    clock_out = new ElectricLogic

    trait has_part_removed

module Usage:
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
    clock_source.clock_out.line ~ dac_adc.model.pll_clock_in

    # override net names
    dac_adc.model.dac_channels[0].analog_left.line.override_net_name = "dac_0_left"
    dac_adc.model.dac_channels[0].analog_right.line.override_net_name = "dac_0_right"
    dac_adc.model.dac_channels[1].analog_left.line.override_net_name = "dac_1_left"
    dac_adc.model.dac_channels[1].analog_right.line.override_net_name = "dac_1_right"
    dac_adc.model.dac_channels[2].analog_left.line.override_net_name = "dac_2_left"
    dac_adc.model.dac_channels[2].analog_right.line.override_net_name = "dac_2_right"
    dac_adc.model.dac_channels[3].analog_left.line.override_net_name = "dac_3_left"
    dac_adc.model.dac_channels[3].analog_right.line.override_net_name = "dac_3_right"

    dac_adc.model.adc_channels[0].analog_left.p.line.override_net_name = "adc_0_left_P"
    dac_adc.model.adc_channels[0].analog_left.n.line.override_net_name = "adc_0_left_N"
    dac_adc.model.adc_channels[0].analog_right.p.line.override_net_name = "adc_0_right_P"
    dac_adc.model.adc_channels[0].analog_right.n.line.override_net_name = "adc_0_right_N"
    dac_adc.model.adc_channels[1].analog_left.p.line.override_net_name = "adc_1_left_P"
    dac_adc.model.adc_channels[1].analog_left.n.line.override_net_name = "adc_1_left_N"
    dac_adc.model.adc_channels[1].analog_right.p.line.override_net_name = "adc_1_right_P"
    dac_adc.model.adc_channels[1].analog_right.n.line.override_net_name = "adc_1_right_N"

```

## Development notes

See [Development notes](../development_notes.md) for information about this codec.

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
