# NXP PN5321 NFC Reader

## Usage

```ato
import ElectricPower
import DifferentialPair
import I2C

from "atopile/nxp-pn5321/nxp-pn5321.ato" import NXP_PN5321_driver

module Antenna:
    input = new DifferentialPair

module Usage:
    nfc = new NXP_PN5321_driver
    antenna = new Antenna

    # Power
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 10%
    power_3v3 ~ nfc.power_3v3

    # I2C interface
    i2c = new I2C
    i2c ~ nfc.i2c

    # Antenna connection
    nfc.antenna_output ~ antenna.input

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
