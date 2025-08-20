# Texas Instruments HDC3022 Temperature & Humidity Sensor

The HDC3022 is a digital temperature and humidity sensor from Texas Instruments that provides high-accuracy measurements with low power consumption. This ultra-low power sensor is ideal for battery-powered applications.

## Features

- **Wide supply voltage range**: 1.62V to 5.5V
- **High accuracy**: ±0.1°C temperature, ±0.5% RH humidity (typical)
- **Low power consumption**: 0.4 µA average supply current
- **Wide operating temperature range**: -40°C to +125°C
- **I2C interface** with configurable address (0x44-0x47)
- **Integrated heater** for condensation removal
- **Alert/interrupt functionality**
- **Reset functionality**
- **Compact package**: 2.5mm × 2.5mm WSON-8

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import I2C

from "atopile/ti-hdc3022/ti-hdc3022.ato" import TI_HDC3022

module Usage:
    """
    Minimal usage example for TI HDC3022 temperature and humidity sensor.
    Shows how to connect power supply and I2C bus to the sensor.
    """

    # Create sensor instance
    temp_humidity_sensor = new TI_HDC3022

    # External power supply (3.3V typical)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # External I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz

    # Connect interfaces
    power_3v3 ~ temp_humidity_sensor.power
    i2c_bus ~ temp_humidity_sensor.i2c

    # Set I2C address (default 0x44 with both address pins low)
    temp_humidity_sensor.i2c.address = 0x44

```

## Technical Specifications

- **Supply Voltage**: 1.62V to 5.5V
- **I2C Address**: 0x44 (default), 0x45, 0x46, 0x47 (configurable via address pins)
- **Temperature Range**: -40°C to +125°C
- **Humidity Range**: 0% to 100% RH
- **Temperature Accuracy**: ±0.1°C (typical)
- **Humidity Accuracy**: ±0.5% RH (typical)
- **Supply Current**: 0.4 µA (average)
- **I2C Speed**: Up to 1 MHz
- **Package**: WSON-8 (2.5mm × 2.5mm)

## I2C Address Configuration

The HDC3022 supports four different I2C addresses controlled by two address pins:

| ADDR1 | ADDR0 | I2C Address |
|-------|-------|-------------|
| Low   | Low   | 0x44 (default) |
| Low   | High  | 0x45 |
| High  | Low   | 0x46 |
| High  | High  | 0x47 |

## Pin Configuration

| Pin | Name    | Description |
|-----|---------|-------------|
| 1   | SDA     | I2C Serial Data |
| 2   | ADDR    | Address Select Pin 0 |
| 3   | ALERT   | Alert/Interrupt Output |
| 4   | SCL     | I2C Serial Clock |
| 5   | VDD     | Power Supply |
| 6   | nRESET  | Reset Input (Active Low) |
| 7   | ADDR1   | Address Select Pin 1 |
| 8   | GND     | Ground |
| 9   | EP      | Exposed Pad (Ground) |

## Applications

- Battery-powered IoT devices
- HVAC systems
- Weather stations
- Industrial process monitoring
- Smart home automation
- Portable instruments
- Medical devices
- Data loggers

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
