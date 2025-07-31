# Texas Instruments TAS5825MRHBR Stereo Class-D Audio Amplifier

A 2-channel I2S audio amplifier with I2C control interface, capable of delivering 25W per channel at 4Ω with 1% THD+N.

## Features

- 2-channel stereo Class-D amplifier
- I2S audio input interface
- I2C control interface with programmable address
- Wide supply voltage range: 4.5V to 26.5V (PVDD)
- Digital supply: 2.7V to 5.5V (DVDD)
- Built-in output filters and bootstrap capacitors
- GPIO pins for fault detection, mute control, and warnings
- Integrated protection features: over-temperature, over-current, under-voltage

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import I2C
import I2S
import DifferentialPair

from "atopile/ti-tas5825mrhbr/ti_tas5825mrhbr.ato" import Texas_Instruments_TAS5825MRHBR_driver

module AudioAmplifier:
    """
    Stereo audio amplifier for speaker output
    """

    # Power supplies
    power_3v3 = new ElectricPower
    power_20v = new ElectricPower

    assert power_3v3.voltage within 3.3V +/- 5%
    assert power_20v.voltage within 20V +/- 5%

    # I2S audio interface
    i2s = new I2S

    # I2C control interface
    i2c = new I2C
    i2c.frequency = 400kHz

    # Amplifier instance
    amp = new Texas_Instruments_TAS5825MRHBR_driver

    # Power connections
    amp.power_pvdd ~ power_20v  # Main amplifier power
    amp.power_dvdd ~ power_3v3  # Digital power

    # Interface connections
    amp.i2s ~ i2s
    amp.i2c ~ i2c

    # Set I2C address (0x4C base + resistor-selected offset)
    assert amp.i2c.address is 0x50

    # Audio outputs (differential pairs for Class-D amplifier)
    speaker_left = new DifferentialPair
    speaker_right = new DifferentialPair

    amp.output_a ~ speaker_left
    amp.output_b ~ speaker_right
```

## Control Signals

The module provides several control signals with built-in pull-up resistors:

- `fault`: Fault detection output (active low)
- `mute`: Mute control input
- `warn`: Warning output
- `pdn`: Power down control (active low)

All control signals are referenced to DVDD and include 10kΩ pull-up resistors.

## I2C Address Configuration

The I2C address is set using an external resistor on the ADR pin. The module includes a 4.7kΩ resistor by default, setting the address to 0x50. Different resistor values can be used to select other addresses according to the datasheet.

## Output Stage

The module includes complete output stages for both channels with:
- Output inductors (10µH)
- Bootstrap capacitors (470nF)
- Output capacitors (680nF)

These components are already integrated into the module, so no external output components are required.

## Power Supply Decoupling

The module includes comprehensive power supply decoupling:
- PVDD: 6x 10µF + 3x 100nF capacitors
- DVDD: 1x 4.7µF + 1x 100nF capacitors
- Internal supplies: 3x 1µF capacitors

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
