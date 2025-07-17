# Sensirion SGP40 VOC Gas Sensor

A comprehensive atopile package for the Sensirion SGP40 digital VOC (Volatile Organic Compounds) gas sensor with I2C interface.

## Features

- **VOC detection**: High-accuracy volatile organic compounds measurement
- **VOC index output**: 0-500 index for indoor air quality assessment
- **Humidity compensation**: Optional humidity input for improved accuracy
- **I2C interface**: Fixed I2C address 0x59
- **Low power consumption**: 2.8mA average during measurement, <1μA in idle
- **Fast response**: <1s response time (τ63%)
- **Long-term stability**: <10% signal drift over 10 years
- **Wide operating range**: -10°C to +50°C, 10% to 95% RH
- **Small package**: 2.4mm × 2.4mm × 0.8mm DFN package

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "sensirion-sgp40.ato" import Sensirion_SGP40

module Usage:
    """
    Minimal usage example for Sensirion SGP40 VOC gas sensor.
    Shows basic I2C connection with 3.3V power supply for both core and heater.
    """

    # Power rail (3.3V for both core and heater)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    # I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400000Hz  # Fast mode I2C

    # VOC gas sensor instance
    voc_sensor = new Sensirion_SGP40

    # Connect power (both core and heater to same 3.3V rail)
    power_3v3 ~ voc_sensor.power_core
    power_3v3 ~ voc_sensor.power_heater

    # Connect I2C bus
    i2c_bus ~ voc_sensor.i2c

    # The SGP40 has a fixed I2C address of 0x59
    assert voc_sensor.i2c.address is 0x59
```

## Hardware Features

### Power Supply
- **VDD (Core)**: 1.7V to 3.6V - Digital core supply
- **VDDH (Heater)**: 1.7V to 3.6V - Heater supply (can be same as VDD)
- **Current consumption**: 2.8mA average (measurement), <1μA (idle)
- Integrated decoupling capacitors (100nF on both rails)

### Communication
- **I2C Interface**: Fixed 7-bit address 0x59
- **I2C Speed**: Up to 400 kHz (Fast mode)
- Built-in I2C pull-up resistors (4.7kΩ)

### Measurements
- **VOC Index**: 0-500 scale for indoor air quality
- **Response time**: <1s (τ63%)
- **Baseline**: Self-calibrating over 24h
- **Accuracy**: Optimized for indoor air quality applications
- **Humidity compensation**: Improves accuracy when humidity data available

### Package
- **Dimensions**: 2.4mm × 2.4mm × 0.8mm
- **Package type**: DFN-6 with exposed pad
- **Pin count**: 6 pins + exposed pad

## Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| 1   | VDD  | Digital core supply (1.7V-3.6V) |
| 2   | VSS  | Ground for digital core |
| 3   | SDA  | I2C serial data |
| 4   | N/A  | Not connected |
| 5   | VDDH | Heater supply (1.7V-3.6V) |
| 6   | SCL  | I2C serial clock |
| 7   | GND  | Ground for heater |

## Application Notes

### Power Supply Design
- VDD and VDDH can be connected to the same supply rail
- For lowest power consumption, use separate supplies and power down VDDH when not measuring
- Ensure adequate decoupling capacitors on both supply rails

### I2C Communication
- SGP40 supports standard (100kHz) and fast mode (400kHz) I2C
- Fixed address 0x59 - no address selection pins
- Pull-up resistors on SDA and SCL lines required

### VOC Algorithm
- Provides VOC index from 0-500 (0=good air, 500=poor air)
- Self-calibrating baseline over 24 hours
- Humidity compensation improves accuracy - provide RH% via software
- Designed for indoor air quality monitoring

### Measurement Cycle
- Typical measurement interval: 1 second
- Heater automatically controlled during measurement
- Fast response to VOC changes: <1s (τ63%)

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
