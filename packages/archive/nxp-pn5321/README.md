# NXP PN5321 NFC Reader

## Usage

```ato
import ElectricPower
import DifferentialPair
import Resistor

from "atopile/nxp-pn5321/nxp-pn5321.ato" import NXP_PN5321_driver
from "atopile/esp32/esp32_c3.ato" import ESP32_C3_WROOM

module Antenna:
    input = new DifferentialPair

module Example:
    esp32 = new ESP32_C3_WROOM
    nfc = new NXP_PN5321_driver
    antenna = new Antenna

    # Power
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V
    power_3v3 ~ esp32.power
    power_3v3 ~ nfc.power_3v3

    # I2C pullups
    pullups = new Resistor[2]
    for pullup in pullups:
        pullup.package = "R0402"
        pullup.resistance = 4.7kohm +/- 10%

    esp32.i2c[0].sda.line ~> pullups[0] ~> power_3v3.vcc
    esp32.i2c[0].scl.line ~> pullups[1] ~> power_3v3.vcc

    # Connect comms to nfc
    esp32.i2c[0] ~ nfc.i2c
    esp32.gpios[10] ~ nfc.reset
    esp32.gpios[11] ~ nfc.interrupt

    nfc.antenna_output ~ antenna.input

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
