# Texas Instruments ADS1015 12-bit I2C ADC

Driver for the [TI ADS1015](https://www.ti.com/product/ADS1015), a 12-bit, 4-channel ADC with I2C interface. Faster and lower-power sibling of the ADS1115 (16-bit), same pinout and protocol.

## Features

- 12-bit resolution, up to 3300 SPS
- 4 single-ended or 2 differential inputs
- Supply: 2V to 5.5V
- Programmable gain amplifier (±256mV to ±6.144V)
- Comparator with ALERT/RDY output
- 4 selectable I2C addresses (0x48–0x4B)
- VSSOP-10 package

## Usage

```ato
import ElectricPower
import I2C
from "atopile/ti-ads1015/ti-ads1015.ato" import TI_ADS1015

module MyDesign:
    power = new ElectricPower
    i2c = new I2C

    adc = new TI_ADS1015
    power ~ adc.power
    i2c ~ adc.i2c

    # ADDR to GND gives 0x48 (default)
    adc.addressor.address_lines[0].line ~ power.lv
```

## I2C Address

| ADDR pin | Address |
|----------|---------|
| GND      | 0x48    |
| VDD      | 0x49    |
| SDA      | 0x4A    |
| SCL      | 0x4B    |

## Contributing

Pull requests welcome.

## License

MIT
