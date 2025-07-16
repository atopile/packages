# Texas Instruments TCA9548A I2C Multiplexer

8-channel I2C multiplexer/switch with reset functionality for expanding I2C buses.

**Features:**
- 8 bidirectional I2C channels
- Wide voltage range: 1.65V to 5.5V
- 3-bit address selection (8 possible addresses: 0x70-0x77)
- Active-low reset pin
- Built-in channel isolation
- Up to 400kHz I2C speed
- Low power consumption

## Usage

```ato
import I2C
import ElectricPower

from "atopile/ti-tca9548a/ti-tca9548a.ato" import TI_TCA9548A

module MyProject:
    # Power supply
    power_supply = new ElectricPower
    power_supply.voltage = 3.3V +/- 5%

    # Main I2C bus
    main_i2c = new I2C
    main_i2c.frequency = 400kHz

    # I2C multiplexer
    mux = new TI_TCA9548A

    # Connections
    power_supply ~ mux.power
    main_i2c ~ mux.i2c

    # Configure address (tie A0, A1, A2 to GND for 0x70 address)
    mux.addressor.address_lines[0].line ~ power_supply.lv
    mux.addressor.address_lines[1].line ~ power_supply.lv
    mux.addressor.address_lines[2].line ~ power_supply.lv

    # Connect to I2C channels as needed
    channel_0 = new I2C
    channel_1 = new I2C

    channel_0 ~ mux.i2cs[0]
    channel_1 ~ mux.i2cs[1]
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
