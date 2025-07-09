# Analog Devices ADT7410 High-Precision Temperature Sensor

`C660048` • ±0.5°C accurate, 16-bit digital I²C temperature sensor with programmable temperature alerts.

The **ADT7410** is a high-precision temperature sensor from Analog Devices with exceptional accuracy and resolution. It communicates via I²C bus with configurable 7-bit addresses (0x48-0x4B) and operates from **2.7V – 5.5V**.

This package wraps the raw JLCPCB part into an easy-to-use Atopile module, complete with power-rail modeling, on-board I²C pull-ups, address selection via Addressor, interrupt output pull-ups, and the required 100nF decoupling capacitor.

## Features

- **High accuracy**: ±0.5°C from -40°C to +105°C
- **16-bit resolution**: 0.0078°C per LSB
- **Configurable I²C addresses**: 0x48-0x4B (via A0, A1 pins)
- **Programmable temperature alerts**: INT and CT outputs
- **Wide supply range**: 2.7V to 5.5V
- **Low power consumption**: 210µA typical at 3.3V

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower, I2C
from "adi-adt7410.ato" import ADI_ADT7410

module Example:
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    i2c = new I2C

    sensor = new ADI_ADT7410
    power_3v3 ~ sensor.power
    power_3v3 ~ i2c.scl.reference; power_3v3 ~ i2c.sda.reference
    i2c ~ sensor.i2c

    # Default address is 0x48 (A1=0, A0=0)
    # Address selection is automatic via Addressor
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
