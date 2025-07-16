# Microchip MCP4728 4-channel DAC

## Usage

```ato

import I2C
import Power

from "atopile/microchip-mcp4728/microchip-mcp4728.ato" import Microchip_MCP4728_driver


module Test:
    # Create DAC
    dac = new Microchip_MCP4728_driver

    # Create power and I2C interfaces
    power = new ElectricPower
    i2c = new I2C

    # Connect power and I2C to DAC
    power ~ dac.power
    i2c ~ dac.i2c

    # Create example electric logics
    outputs = new ElectricSignal[4]

    # Connect outputs to DAC
    outputs[0] ~ dac.outputs[0]
    outputs[1] ~ dac.outputs[1]
    outputs[2] ~ dac.outputs[2]
    outputs[3] ~ dac.outputs[3]



```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
