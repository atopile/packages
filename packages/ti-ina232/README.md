# TI INA232 I2C Power Monitor

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import I2C
import Power

from "atopile/ti-ina232/ti-ina232.ato" import Texas_Instruments_INA232x_driver

module Test:
    current_sensors = new Texas_Instruments_INA232x_driver[4]

    current_sensors[0].i2c.address = 0x48
    current_sensors[1].i2c.address = 0x49
    current_sensors[2].i2c.address = 0x4A
    current_sensors[3].i2c.address = 0x4B

    # Configure current
    current_sensors[0].max_current = 0.1A
    current_sensors[1].max_current = 1A
    current_sensors[2].max_current = 3A
    current_sensors[3].max_current = 10A

    power = new ElectricPower
    i2c = new I2C

    for sensor in current_sensors:
        sensor.power ~ power
        sensor.i2c ~ i2c

    # Power to sense
    power_source = new ElectricPower
    power_sink = new ElectricPower

    # High side sense (also able to sense voltage)
    power_source.vcc ~> current_sensors[0].shunt ~> power_sink.vcc

    # Low side sense
    power_source.gnd ~> current_sensors[1].shunt ~> power_sink.gnd


```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
