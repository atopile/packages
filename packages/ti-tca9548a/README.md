# TCA9548APWR I2C Multiplexer

## Usage

```
import I2C
import ElectricPower

from "atopile/ti-tca9548a/tca9548a.ato" import TCA9548APWR_driver
module Test:
    # Create 8 muxes
    muxes = new TCA9548APWR_driver[8]

    # Create I2C and Power
    power = new ElectricPower
    i2c = new I2C

    # Connect I2C
    for mux in muxes:
        i2c ~ mux.i2c
        power ~ mux.power

    # Assert addresses
    assert muxes[0].i2c.address is 0x70
    assert muxes[1].i2c.address is 0x71
    assert muxes[2].i2c.address is 0x72
    assert muxes[3].i2c.address is 0x73
    assert muxes[4].i2c.address is 0x74
    assert muxes[5].i2c.address is 0x75
    assert muxes[6].i2c.address is 0x76
    assert muxes[7].i2c.address is 0x77
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
