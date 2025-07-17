# Microchip ATSAMD51J19A

This is the Microchip ATSAMD51J19A microcontroller. Arduino and CircuitPython compatible.
Used in the Adafruit Feather M4 Express.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")
import ElectricPower
import I2C
import USB2_0
import Resistor

from "atopile/microchip-atsamd51j19a/microchip-atsamd51j19a.ato" import Microchip_ATSAMD51J19A
from "parts/SHOU_HAN_TYPE_C_16PIN_2MD_073/SHOU_HAN_TYPE_C_16PIN_2MD_073.ato" import SHOU_HAN_TYPE_C_16PIN_2MD_073_package

module Sensor:
    """Sensor with I²C interface"""

    power = new ElectricPower
    i2c = new I2C

module USBCConnector:
    """USB-C connector"""
    package = new SHOU_HAN_TYPE_C_16PIN_2MD_073_package
    usb = new USB2_0

    cc_resistor = new Resistor[2]
    for resistor in cc_resistor:
        resistor.resistance = 51kohm +/- 1%
        resistor.package = "0402"

    usb.usb_if.buspower.hv ~ package.VBUS
    usb.usb_if.buspower.lv ~ package.GND
    usb.usb_if.buspower.lv ~ package.SHELL
    usb.usb_if.d.p.line ~ package.DP1
    usb.usb_if.d.p.line ~ package.DP2
    usb.usb_if.d.n.line ~ package.DN1
    usb.usb_if.d.n.line ~ package.DN2

    usb.usb_if.buspower.lv ~> cc_resistor[0] ~> package.CC1
    usb.usb_if.buspower.lv ~> cc_resistor[1] ~> package.CC2

module Usage:
    """Minimal example for the Microchip ATSAMD51 microcontroller"""

    # MCU & sensor
    mcu = new Microchip_ATSAMD51J19A
    sensor = new Sensor
    usb = new USBCConnector

    # usb data and power
    usb.usb ~ mcu.usb

    # Steal power from the MCU 3V3 rail
    mcu.power_3v3 ~ sensor.power

    # I²C connection
    mcu.i2c ~ sensor.i2c
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
