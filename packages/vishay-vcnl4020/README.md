# Vishay VCNL4020 Fully Integrated Proximity and Ambient Light Sensor

The VCNL4020 is a fully integrated proximity and ambient light sensor with infrared emitter, I2C interface, and interrupt function from Vishay. This sensor is ideal for applications requiring both proximity detection and ambient light measurement in a single compact package.

## Features

- **Fully integrated proximity and ambient light sensor**
- **Supply voltage range**: 2.5V to 3.6V
- **Built-in IR LED** with adjustable current (up to 200mA)
- **High resolution**: 16-bit proximity and ambient light data
- **I2C interface** with fixed address 0x13
- **Interrupt functionality** for proximity and ambient light thresholds
- **Low power consumption**: 90µA typical (proximity mode)
- **Operating temperature**: -40°C to +85°C
- **Proximity detection range**: Up to 200mm (depending on target)
- **Ambient light range**: 0.25 lux to 16k lux
- **Compact package**: VDFN-10 (3.0mm × 3.0mm)

## Usage

```ato
#pragma experiment("TRAITS")

import ElectricPower
import I2C

from "atopile/vishay-vcnl4020/vishay-vcnl4020.ato" import Vishay_VCNL4020

module Usage:
    """
    Minimal usage example for Vishay VCNL4020 proximity and ambient light sensor.
    Shows how to connect power supply and I2C bus.
    """

    # Create sensor instance
    sensor = new Vishay_VCNL4020

    # Main power supply for the sensor (3.3V)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # External I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz

    # Connect interfaces
    power_3v3 ~ sensor.power
    i2c_bus ~ sensor.i2c

    # Set I2C address (fixed for VCNL4020)
    sensor.i2c.address = 0x13

```

## Technical Specifications

- **Supply Voltage (VDD)**: 2.5V to 3.6V
- **I2C Address**: 0x13 (fixed, not configurable)
- **Supply Current**: 90µA typical (proximity mode), 150µA typical (ambient light mode)
- **IR LED Current**: Up to 200mA (adjustable via I2C)
- **Proximity Range**: Up to 200mm (target dependent)
- **Ambient Light Range**: 0.25 lux to 16k lux
- **ADC Resolution**: 16-bit for both proximity and ambient light
- **Conversion Time**: 1.95ms (proximity), 100ms (ambient light)
- **I2C Speed**: Up to 3.4 MHz (High Speed mode)
- **Package**: VDFN-10 (3.0mm × 3.0mm × 0.9mm)

## I2C Communication

The VCNL4020 uses a fixed I2C address of **0x13** (7-bit addressing). This address cannot be changed, so only one VCNL4020 can be used per I2C bus without additional hardware.

## Pin Configuration

| Pin | Name      | Description |
|-----|-----------|-------------|
| 1   | IRanode   | IR LED Anode (internal) |
| 2   | SDA       | I2C Serial Data |
| 3   | INT       | Interrupt Output (active low) |
| 4   | SCL       | I2C Serial Clock |
| 5   | VDD       | Supply Voltage |
| 6-7 | NC        | No Connection |
| 8-9 | GND       | Ground |
| 10  | IRcathode | IR LED Cathode (internal) |

## Functionality

### Proximity Sensing
- Uses built-in IR LED and photodiode for proximity detection
- Adjustable IR LED current (0-200mA) for different sensing ranges
- 16-bit proximity data with programmable interrupt thresholds
- Ideal for touchless switching, object detection, and user presence sensing

### Ambient Light Sensing
- Photodiode measures ambient light levels
- 16-bit ambient light data with lux conversion
- Programmable interrupt thresholds for light level detection
- Useful for automatic backlight control and light-sensitive applications

### Interrupt Function
- Configurable interrupt thresholds for both proximity and ambient light
- Active-low interrupt output
- Reduces microcontroller polling requirements
- Supports both high and low threshold interrupts

## Applications

- Touchless switches and buttons
- Object detection and counting
- User presence sensing
- Automatic backlight control
- Light level monitoring
- Proximity-based device wake-up
- Industrial automation sensors
- Mobile device proximity sensing
- Gaming controllers
- Automotive interior sensing

## Register Map

The VCNL4020 provides several I2C registers for configuration and data reading:

- **Command Register (0x80)**: Controls operational modes
- **Proximity Rate Register (0x82)**: Sets proximity measurement rate
- **IR LED Current Register (0x83)**: Controls IR LED current
- **Ambient Light Parameter Register (0x84)**: Configures ambient light measurement
- **Proximity Data Registers (0x87-0x88)**: 16-bit proximity data
- **Ambient Light Data Registers (0x85-0x86)**: 16-bit ambient light data
- **Interrupt Control Register (0x89)**: Configures interrupt behavior
- **Threshold Registers (0x8A-0x8F)**: Sets interrupt thresholds

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
