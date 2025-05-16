# Microchip MCP4725 DAC

## Usage

```ato

import I2C
import Power

from "atopile/microchip-mcp4725/microchip-mcp4725.ato" import Microchip_Tech_MCP4725_driver


module Test:
    # Create 2 DACs
    dacs = new Microchip_Tech_MCP4725_driver[2]

    # Create power and I2C interfaces
    power = new ElectricPower
    i2c = new I2C

    # Connect DACs to power and I2C
    for dac in dacs:
        dac.power ~ power
        dac.i2c ~ i2c

    # Set DAC addresses
    dacs[0].i2c.address = 0x60
    dacs[1].i2c.address = 0x61

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
