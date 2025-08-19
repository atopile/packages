# ST HTS221 Temperature & Humidity Sensor

The STMicroelectronics HTS221 is a compact digital humidity and temperature sensor with I2C interface. It features a capacitive sensing element for relative humidity and a band-gap temperature sensor. The sensor provides calibrated digital output and operates over a wide temperature range (-40°C to 120°C) and humidity range (0-100% RH).

## Features

- Digital humidity and temperature sensor
- I2C interface (address 0x5F)
- Operating voltage: 1.71V to 3.6V
- Temperature range: -40°C to 120°C
- Humidity range: 0-100% RH
- Data Ready (DRDY) output signal
- Chip Select (CS) for I2C/SPI mode selection
- Low power consumption
- Small HLGA-6 package (2x2mm)

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")
#pragma experiment("TRAITS")
#pragma experiment("MODULE_TEMPLATING")

import I2C
import ElectricPower
import ElectricLogic
import Resistor

from "atopile/st-hts221/st-hts221.ato" import ST_HTS221

module Usage:
    """
    Minimal usage example for st-hts221.
    Shows how to connect the HTS221 temperature and humidity sensor.
    """

    sensor = new ST_HTS221

    # Connect power supply
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%
    power_3v3 ~ sensor.power

    # Connect I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz
    i2c_bus ~ sensor.i2c

    # Set CS high for I2C mode
    cs_pullup = new Resistor
    cs_pullup.resistance = 10kohm +/- 1%
    cs_pullup.package = "0402"
    power_3v3.hv ~> cs_pullup ~> sensor.cs.line
    power_3v3 ~ sensor.power

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
