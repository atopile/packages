# ADS1115 4ch 16-bit ADC

Sample Rate: 860sps
Communication: I2C
Input Voltage: 1.8-5.5V

## Usage

```ato

import I2C
import Power

from "atopile/ti-ads1115/ti-ads1115.ato" import Texas_Instruments_ADS1115_driver


module Test:
    """Test component"""
    # ADCs
    adcs = new Texas_Instruments_ADS1115_driver[4]

    power = new ElectricPower
    i2c = new I2C

    # Configure power
    power.voltage = 5V

    adcs[0].i2c.address = 0x48
    adcs[1].i2c.address = 0x49
    adcs[2].i2c.address = 0x4A
    adcs[3].i2c.address = 0x4B

    # Power and I2c
    for adc in adcs:
        adc.power ~ power
        adc.i2c ~ i2c


```

## Overview

This package provides the necessary components and interfaces to integrate the Raspberry Pi Compute Module 5 into your hardware designs using atopile.

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
