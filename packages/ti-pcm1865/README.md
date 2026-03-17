# TI PCM1865 Audio ADC

24-bit, 192kHz, 4-channel audio ADC

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")
#pragma experiment("TRAITS")

# --- Standard library imports ---
import ElectricPower
import I2C
import I2S
import DifferentialPair
import has_part_removed

# --- Package import ---
from "atopile/ti-pcm1865/ti-pcm1865.ato" import Texas_Instruments_PCM1865

module XLR:
    """XLR connector"""
    balanced = new DifferentialPair
    trait has_part_removed

module Microcontroller:
    """Microcontroller"""
    i2c = new I2C
    i2s = new I2S
    power_3v3 = new ElectricPower
    trait has_part_removed

module Usage:
    """
    Example of a Texas Instruments PCM1865 audio ADC
    """
    # Power
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    # Components
    adc = new Texas_Instruments_PCM1865
    micro = new Microcontroller
    xlrs = new XLR[4]

    # Power connections
    power_3v3 ~ adc.power_3v3
    power_3v3 ~ micro.power_3v3

    # Data connections
    micro.i2c ~ adc.i2c
    micro.i2s ~ adc.i2s

    # Connect inputs
    xlrs[0].balanced ~ adc.balanced_inputs[0]
    xlrs[1].balanced ~ adc.balanced_inputs[1]
    xlrs[2].balanced ~ adc.balanced_inputs[2]
    xlrs[3].balanced ~ adc.balanced_inputs[3]

```

## Contributing

Contributions are welcome! Please open an issue or pull request and ensure the `usage` build target passes (`ato build usage`).

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
