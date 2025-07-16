# Texas Instruments ADS1115 16-bit ADC

16-bit analog-to-digital converter with integrated multiplexer, programmable gain amplifier (PGA), comparator, oscillator, and reference.

**Features:**
- 16-bit resolution
- 4 single-ended or 2 differential inputs
- Sample rate: up to 860 SPS
- I2C interface
- Programmable gain amplifier (PGA)
- Integrated voltage reference
- Comparator with alert function
- Operating voltage: 1.8V to 5.5V

## Usage

```ato
import I2C
import ElectricPower

from "atopile/ti-ads1115/ti-ads1115.ato" import TI_ADS1115

module MyProject:
    # Power and I2C bus
    power_supply = new ElectricPower
    i2c_bus = new I2C

    # ADC instance
    adc = new TI_ADS1115

    # Configure power
    power_supply.voltage = 3.3V +/- 5%

    # Connect interfaces
    power_supply ~ adc.power
    i2c_bus ~ adc.i2c

    # Configure address (tie ADDR to GND for 0x48 address)
    adc.addressor.address_lines[0].line ~ power_supply.lv
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
