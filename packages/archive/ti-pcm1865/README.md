# TI PCM1865 Audio ADC

24-bit, 192kHz, 4-channel audio ADC

```ato
import ElectricPower
import Electrical
from "atopile/ti-pcm1865/ti-pcm1865.ato" import Texas_Instruments_PCM1865_driver

module XLR:
    """XLR connector"""
    balanced = new DifferentialPair

module Microcontroller:
    """Microcontroller"""
    i2c = new I2C
    i2s = new I2S
    power_3v3 = new ElectricPower

module Example:
    """
    Example of a Texas Instruments PCM1865 audio ADC
    """
    # Power
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    # Components
    adc = new Texas_Instruments_PCM1865_driver
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

Created by Narayan Powderly <narayan@atopile.io>
