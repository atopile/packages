# Aosong AHT20 Temperature and Humidity Sensor

A comprehensive atopile package for the Aosong AHT20 digital temperature and humidity sensor with I2C interface.

## Features

- **Temperature measurement**: -40°C to +85°C range with ±0.3°C accuracy
- **Humidity measurement**: 0% to 100% RH range with ±2% RH accuracy
- **I2C interface**: Fixed I2C address 0x38
- **Low power consumption**: 0.25μA in sleep mode, 600μA during measurement
- **Fast response**: <5s (humidity), <30s (temperature)
- **Wide operating voltage**: 1.8V to 3.6V
- **Small package**: 3mm × 3mm × 1.0mm SMD package

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "aosong-aht20.ato" import Aosong_AHT20

module Usage:
    """
    Minimal usage example for Aosong AHT20 temperature and humidity sensor.
    Shows basic I2C connection with 3.3V power supply.
    """

    # Power rail (3.3V for sensor)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    # I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400000Hz  # Fast mode I2C

    # Temperature/humidity sensor instance
    sensor = new Aosong_AHT20

    # Connect power
    power_3v3 ~ sensor.power

    # Connect I2C bus
    i2c_bus ~ sensor.i2c

    # The AHT20 has a fixed I2C address of 0x38
    assert sensor.i2c.address is 0x38
```

## Hardware Features

### Power Supply
- **Operating voltage**: 1.8V to 3.6V
- **Current consumption**: 0.25μA (sleep), 600μA (measurement)
- Integrated decoupling capacitor (100nF)

### Communication
- **I2C Interface**: Fixed 7-bit address 0x38
- **I2C Speed**: Up to 400 kHz (Fast mode)
- Built-in I2C pull-up resistors (4.7kΩ)

### Measurements
- **Temperature**: -40°C to +85°C, ±0.3°C accuracy
- **Humidity**: 0% to 100% RH, ±2% RH accuracy
- **Resolution**: 16-bit for both temperature and humidity
- **Response time**: <5s (humidity), <30s (temperature)

### Package
- **Dimensions**: 3mm × 3mm × 1.0mm
- **Package type**: SMD-6P
- **Pin count**: 6 pins (including 2 NC pins)

## Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| 1   | NC   | Not connected |
| 2   | VDD  | Power supply (1.8V-3.6V) |
| 3   | SCL  | I2C serial clock |
| 4   | SDA  | I2C serial data |
| 5   | GND  | Ground |
| 6   | NC   | Not connected |

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
