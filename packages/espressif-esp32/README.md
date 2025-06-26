# ESP32 Modules

## Usage

```ato
from "atopile/espressif-esp32/esp32_s3.ato" import ESP32_S3_WROOM_1_N16R8
from "atopile/usb-connectors/usb-connectors.ato" import USBCConn
from "atopile/ti-ina232/ti-ina232.ato" import Texas_Instruments_INA232x_driver
from "atopile/ti-tlv75901/ti-tlv75901.ato" import TLV75901_driver
from "atopile/addressable-leds/sk6805-ec20.ato" import SK6805EC20_driver


module App:
    # Components
    micro = new ESP32_S3_WROOM
    usb_c = new USBCConn
    current_sensor = new Texas_Instruments_INA232x_driver
    ldo_3V3 = new TLV75901_driver
    leds = new SK6805EC20_driver[5]

    # Power
    power_3v3 = new ElectricPower
    usb_c.usb2.usb_if.buspower ~> ldo_3V3 ~> current_sensor ~> power_3v3
    power_3v3 ~ micro.power
    power_3v3 ~ current_sensor.power

    # Configure LDO
    ldo_3V3.v_in = 5V +/- 5%
    ldo_3V3.v_out = 3.3V +/- 3%

    # Configure and Connect I2C Current Sensor
    current_sensor.i2c.address = 0x48
    current_sensor.max_current = 355mA * 1.2#20% margin on max active current
    micro.i2c[0] ~ current_sensor.i2c

    pullups = new Resistor[2]
    for pullup in pullups:
        pullup.package = "R0402"
        pullup.resistance = 4.7kohm +/- 10%

    micro.i2c[0].sda.line ~> pullups[0] ~> micro.power.vcc
    micro.i2c[0].scl.line ~> pullups[1] ~> micro.power.vcc

    # Connect USB
    usb_c.usb2 ~ micro.usb2

    # Connect Addressable LEDs
    for led in leds:
        led.power ~ power_3v3

    micro.gpios[10] ~> leds[0] ~> leds[1] ~> leds[2] ~> leds[3] ~> leds[4]



```

## Overview

This package provides a set of modules for the ESP32 microcontroller family from Espressif.

To select the right module for your application, visit: https://www.espressif.com/en/products/modules

## Currently supported modules

| Series   | Package   | Flash/PSRAM | Module Name            |
| -------- | --------- | ----------- | ---------------------- |
| ESP32-S3 | WROOM-1   | N8R2        | ESP32_S3_WROOM_1_N8R2  |
|          |           | N8R8        | ESP32_S3_WROOM_1_N8R8  |
|          |           | N16R2       | ESP32_S3_WROOM_1_N16R2 |
|          |           | N16R8       | ESP32_S3_WROOM_1_N16R8 |
| ESP32-C3 | WROOM-02U | N4          | ESP32_C3_WROOM_02U_N4  |
|          | WROOM-02  | N4          | ESP32_C3_WROOM_02_N4   |
|          |           | H4          | ESP32_C3_WROOM_02_H4   |

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
