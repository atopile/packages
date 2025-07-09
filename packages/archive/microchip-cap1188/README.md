# Microchip CAP1188 Capacitive Touch Sensor

## Interfaces

- power
- i2c
- spi

## Usage

```ato
    from "atopile/microchip-cap1188/microchip_cap1188.ato" import Microchip_Tech_CAP1188_1_CP_TR_driver

    import ElectricPower

module App:

    touch_sensor = new Microchip_Tech_CAP1188_1_CP_TR_driver

    power_3v3 = new ElectricPower
    power_3v3 ~ touch_sensor.power

    # Select address
    touch_sensor.address_select.resistance = 82kohm +/- 2%

```

## Overview

This package contains a driver for the Microchip CAP1188 capacitive touch sensor.

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
