# Microchip CAP1188 Capacitive Touch Sensor

## Interfaces

- power
- i2c
- spi

## Usage

```ato
    # from "atopile/microchip-cap1188/microchip_cap1188.ato" import Microchip_Tech_CAP1188_1_CP_TR_driver

    import I2C
    import ElectricPower
    import Resistor

module App:

    touch_sensor = new Microchip_Tech_CAP1188_1_CP_TR_driver

    power_3v3 = new ElectricPower

    power_3v3 ~ touch_sensor.power

    address_select = new Resistor
    address_select.package = "R0402"
    address_select.resistance = 0 ohm +/- 0.05 ohm
    touch_sensor.address.line ~> address_select ~> power_3v3.lv # 4w spi



```

## Overview

This package contains a driver for the Microchip CAP1188 capacitive touch sensor.

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
