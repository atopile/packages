# Bosch BMP388 Temperature & Pressure Sensor

High-accuracy digital temperature and pressure sensor with integrated interrupt functionality and advanced filtering.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C
import ElectricLogic

from "bosch-bmp388.ato" import Bosch_BMP388

module Usage:
    """
    Minimal usage example for bosch-bmp388.
    Shows basic I²C connection, power supply, and interrupt handling.
    """

    sensor = new Bosch_BMP388

    # Connect external I²C bus
    i2c = new I2C
    i2c ~ sensor.i2c

    # Connect power supplies
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    power_3v3 ~ sensor.power_core
    power_3v3 ~ sensor.power_io

    # Connect interrupt pin to microcontroller GPIO
    interrupt_gpio = new ElectricLogic
    interrupt_gpio ~ sensor.interrupt

    # Set I²C address to 0x76 (SDO pulled low)
    assert sensor.i2c.address is 0x76
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
