# Texas Instruments TMAG5273 3D Hall-Effect Sensor

Low-power linear 3D Hall-effect sensor with I2C interface

## Features

- 3-axis Hall-effect sensing (X, Y, Z)
- 12-bit ADC resolution
- I2C interface up to 1MHz
- Configurable power modes
- Built-in temperature sensor
- CORDIC angle calculation engine
- Interrupt capability
- Supply voltage: 1.7V to 3.6V
- Operating temperature: -40°C to +125°C

## Usage

```ato
from "ti-tmag5273/tmag5273.ato" import TMAG5273_driver

module MySystem:
    # Power supply
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.3V +/- 5%

    # I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz
    i2c_bus.address = 0x22  # Default address

    # Hall sensor
    hall_sensor = new TMAG5273_driver

    # Connections
    power_3v3 ~ hall_sensor.power
    i2c_bus ~ hall_sensor.i2c
```

## I2C Address Configuration

The TMAG5273 supports configurable I2C addresses from 0x22 to 0x79. The default address is 0x22.

## Power Modes

- Active mode: 2.3mA typical
- Wake-up/Sleep mode: 1µA typical
- Sleep mode: 5nA typical

## Variants

This package uses the TMAG5273A1 variant (±40mT/±80mT range). Other variants available:
- TMAG5273A2: ±133mT/±266mT range
- TMAG5273B1: ±40mT/±80mT with different features
- TMAG5273C1: ±40mT/±80mT with different features

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
