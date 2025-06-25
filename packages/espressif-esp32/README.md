# ESP32 Modules

## Usage

```ato
from "atopile/espressif-esp32/esp32_s3.ato" import ESP32_S3_WROOM_1_N16R8
from "atopile/usb-connectors/usb-connectors.ato" import USBCConn
from "atopile/ti-ina232/ti-ina232.ato" import Texas_Instruments_INA232x_driver
from "atopile/ti-tlv75901/ti-tlv75901.ato" import TLV75901_driver


module App:
    # Components
    esp32_s3 = new ESP32_S3_WROOM
    usb_c = new USBCConn
    current_sensor = new Texas_Instruments_INA232x_driver
    ldo_3V3 = new TLV75901_driver

    # Configure LDO
    ldo_3V3.v_in = 5V +/- 5%
    ldo_3V3.v_out = 3.3V +/- 3%

    # Connect USB power thru shunt to ESP32
    usb_c.usb2.usb_if.buspower ~ ldo_3V3.power_in
    ldo_3V3.power_out ~> current_sensor.shunt ~> esp32_s3.power
    ldo_3V3.power_out.gnd ~ esp32_s3.power.gnd

    # Configure and Connect I2C Current Sensor
    current_sensor.i2c.address = 0x48
    current_sensor.max_current = 0.355*1.2A #20% margin on max active current
    current_sensor.power ~ usb_c.usb2.usb_if.buspower
    esp32_s3.i2c[0] ~ current_sensor.i2c

    pullups = new Resistor[2]
    for pullup in pullups:
        pullup.package = "R0402"
        pullup.resistance = 4.7kohm +/- 10%

    esp32_s3.i2c[0].sda.line ~> pullups[0] ~> esp32_s3.power.vcc
    esp32_s3.i2c[0].scl.line ~> pullups[1] ~> esp32_s3.power.vcc

    # Connect USB
    usb_c.usb2 ~ esp32_s3.usb2
```

## Overview
This package provides a set of modules for the ESP32 microcontroller family from Espressif.

To select the right module for your application, visit: https://www.espressif.com/en/products/modules

## Currently supported modules

| Series   | Package    | Flash/PSRAM | Module Name             |
|----------|------------|-------------|-------------------------|
| ESP32-S3 | WROOM-1    | N8R2        | ESP32_S3_WROOM_1_N8R2   |
|          |            | N8R8        | ESP32_S3_WROOM_1_N8R8   |
|          |            | N16R2       | ESP32_S3_WROOM_1_N16R2  |
|          |            | N16R8       | ESP32_S3_WROOM_1_N16R8  |
| ESP32-C3 | WROOM-02U  | N4          | ESP32_C3_WROOM_02U_N4   |
|          | WROOM-02   | N4          | ESP32_C3_WROOM_02_N4    |
|          |            | H4          | ESP32_C3_WROOM_02_H4    |

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).