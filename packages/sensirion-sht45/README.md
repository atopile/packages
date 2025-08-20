# Sensirion SHT45 Temperature and Humidity Sensor

A comprehensive atopile package for the Sensirion SHT45 high-accuracy digital temperature and humidity sensor with I2C interface.

## Features

- **Temperature measurement**: -40°C to +125°C range with ±0.1°C accuracy
- **Humidity measurement**: 0% to 100% RH range with ±1.0% RH accuracy
- **High precision**: 16-bit resolution for both temperature and humidity
- **I2C interface**: Fixed I2C address 0x44 (SHT45-AD1F variant)
- **Ultra-low power**: 0.4μA in sleep mode, 1.5μA average measurement
- **Fast response**: 8s (humidity), 30s (temperature)
- **Excellent stability**: Long-term drift <0.25% RH per year
- **Wide operating voltage**: 1.08V to 3.6V
- **Ultra-small package**: 1.5mm × 1.5mm × 0.5mm DFN

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "atopile/sensirion-sht45/sensirion-sht45.ato" import Sensirion_SHT45

module Usage:
    """
    Minimal usage example for Sensirion SHT45 temperature and humidity sensor.
    Shows basic I2C connection with 3.3V power supply.
    """

    # Power rail (3.3V for sensor)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    # I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz  # Fast mode I2C

    # Temperature/humidity sensor instance
    temp_humidity_sensor = new Sensirion_SHT45

    # Connect power
    power_3v3 ~ temp_humidity_sensor.power

    # Connect I2C bus
    i2c_bus ~ temp_humidity_sensor.i2c

    # The SHT45-AD1F has a default I2C address of 0x44
    assert temp_humidity_sensor.i2c.address is 0x44

```

## Hardware Features

### Power Supply
- **Operating voltage**: 1.08V to 3.6V
- **Current consumption**: 0.4μA (sleep), 1.5μA (measurement average)
- **Peak current**: 750μA during measurement
- Integrated decoupling capacitor (100nF)

### Communication
- **I2C Interface**: Fixed 7-bit address 0x44 (SHT45-AD1F)
- **I2C Speed**: Up to 1 MHz (Fast mode+)
- Built-in I2C pull-up resistors (4.7kΩ)

### Measurements
- **Temperature**: -40°C to +125°C, ±0.1°C accuracy (typical)
- **Humidity**: 0% to 100% RH, ±1.0% RH accuracy (typical)
- **Resolution**: 16-bit for both temperature and humidity
- **Response time**: 8s (humidity), 30s (temperature to 63% of step change)
- **Repeatability**: ±0.08°C (temperature), ±0.1% RH (humidity)

### Package
- **Dimensions**: 1.5mm × 1.5mm × 0.5mm
- **Package type**: DFN-4 with exposed pad
- **Pin count**: 4 pins + exposed pad

## Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| 1   | SDA  | I2C serial data |
| 2   | SCL  | I2C serial clock |
| 3   | VDD  | Power supply (1.08V-3.6V) |
| 4   | GND  | Ground |
| 5   | EP   | Exposed pad (connect to GND) |

## Application Notes

### Power Supply Design
- Wide operating voltage range from 1.08V to 3.6V
- Ultra-low power consumption ideal for battery applications
- Connect exposed pad to ground for optimal thermal performance

### I2C Communication
- SHT45-AD1F has fixed address 0x44 (ADDR pin internally tied)
- Supports up to 1 MHz I2C clock frequency
- Pull-up resistors on SDA and SCL lines required

### Measurement Performance
- Industry-leading accuracy: ±0.1°C (temperature), ±1.0% RH (humidity)
- Excellent long-term stability with minimal drift
- Fast response times suitable for real-time monitoring

### Environmental Considerations
- Wide operating temperature range: -40°C to +125°C
- Full humidity range: 0% to 100% RH
- Excellent chemical resistance and long-term stability

### Calibration
- Factory calibrated with traceable references
- No field calibration required
- Maintains accuracy over entire operating range

## Comparison with Other SHT Series

| Feature | SHT45 | SHT40 | SHT30 |
|---------|-------|-------|-------|
| Temperature Accuracy | ±0.1°C | ±0.2°C | ±0.2°C |
| Humidity Accuracy | ±1.0% RH | ±1.8% RH | ±2.0% RH |
| Package Size | 1.5×1.5mm | 1.5×1.5mm | 2.5×2.5mm |
| Power Consumption | 0.4μA | 0.4μA | 0.6μA |
| I2C Address | 0x44 | 0x44 | 0x44/0x45 |

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
