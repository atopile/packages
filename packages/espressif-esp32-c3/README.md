# ESP32-C3 family

## Usage

```ato
from "atopile/espressif-esp32-c3/esp32_c3_mini.ato" import ESP32_C3_MINI_1_driver

module App:
    """
    Example of how to use the driver for ESP32-C3-MINI-1 modules
    """
    mcu = new ESP32_C3_MINI_1_driver
    # mcu.esp32_module -> ESP32_C3_MINI_1_model # choose another variant if you want

    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 10%
    power_3v3 ~ mcu.power

    # below are some sensible defaults. These interfaces can be muxed to any GPIO.
    i2c = new I2C
    mcu.esp32_module.i2c ~ i2c
    mcu.esp32_module.gpio[6] ~ mcu.esp32_module.i2c.scl
    mcu.esp32_module.gpio[5] ~ mcu.esp32_module.i2c.sda
    # I2C pull-up resistors
    pullup_resistors = new Resistor[2]
    for res in pullup_resistors:
        res.resistance = 10kohm +/- 1%
        res.package = "R0402"
    i2c.sda.reference.hv ~> pullup_resistors[0] ~> i2c.sda.line
    i2c.scl.reference.hv ~> pullup_resistors[1] ~> i2c.scl.line

    spi = new SPI
    mcu.esp32_module.spi ~ spi
    mcu.esp32_module.gpio[10] ~ mcu.esp32_module.spi.sclk
    mcu.esp32_module.gpio[7] ~ mcu.esp32_module.spi.mosi
    mcu.esp32_module.gpio[8] ~ mcu.esp32_module.spi.miso

    i2s = new I2S
    mcu.esp32_module.i2s ~ i2s
    mcu.esp32_module.gpio[18] ~ mcu.esp32_module.i2s.ws
    mcu.esp32_module.gpio[1] ~ mcu.esp32_module.i2s.sd
    mcu.esp32_module.gpio[0] ~ mcu.esp32_module.i2s.sck
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
