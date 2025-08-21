# Vishay VCNL4200 High Resolution Long Distance Proximity and Ambient Light Sensor

The VCNL4200 is a high-resolution, long-distance proximity and ambient light sensor with infrared emitter, I2C interface, and interrupt function from Vishay. This sensor offers superior performance with extended detection range and enhanced sunlight immunity, making it ideal for demanding applications.

## Features

- **High-resolution proximity and ambient light sensor**
- **Supply voltage range**: 2.5V to 3.6V
- **Long-range proximity detection**: Up to 1.5m (target dependent)
- **Enhanced sunlight immunity** and crosstalk cancellation
- **High resolution**: 16-bit proximity and ambient light data
- **I2C interface** with configurable address (0x51-0x54)
- **Interrupt functionality** for proximity and ambient light thresholds
- **Low power consumption**: 150µA typical (proximity mode)
- **Operating temperature**: -40°C to +85°C
- **Built-in IR LED** with adjustable current (up to 200mA)
- **Smart persistence** to avoid false triggers
- **Compact package**: SMD-10 (5.6mm × 3.0mm)

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("MODULE_TEMPLATING")

import ElectricPower
import I2C

from "atopile/vishay-vcnl4200/vishay-vcnl4200.ato" import Vishay_VCNL4200

module Usage:
    """
    Minimal usage example for Vishay VCNL4200 proximity and ambient light sensor.
    Shows how to connect power supply and I2C bus.
    """

    # Create sensor instance
    sensor = new Vishay_VCNL4200

    # Main power supply for the sensor (3.3V)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # External I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz

    # Connect interfaces
    power_3v3 ~ sensor.power
    i2c_bus ~ sensor.i2c

    # Set I2C address (fixed for VCNL4200)
    sensor.i2c.address = 0x51

    # LED control is optional - leave unconnected for always-on LED
    # Connect to microcontroller GPIO to control LED programmatically

```

## Technical Specifications

- **Supply Voltage (VDD)**: 2.5V to 3.6V
- **I2C Address**: 0x51-0x54 (configurable via LED_CATHODE pin)
- **Supply Current**: 150µA typical (proximity mode), 200µA typical (ambient light mode)
- **IR LED Current**: Up to 200mA (adjustable via I2C)
- **Proximity Range**: Up to 1.5m (target dependent)
- **Ambient Light Range**: 0.01 lux to 120k lux
- **ADC Resolution**: 16-bit for both proximity and ambient light
- **Conversion Time**: 8.4ms (proximity), 100ms (ambient light)
- **I2C Speed**: Up to 1 MHz (Fast Mode Plus)
- **Package**: SMD-10 (5.6mm × 3.0mm × 1.5mm)

## I2C Address Configuration

The VCNL4200 supports four different I2C addresses controlled by the LED_CATHODE pin:

| LED_CATHODE Connection | I2C Address | Description |
|------------------------|-------------|-------------|
| GND                    | 0x51        | Default configuration |
| VDD                    | 0x52        | Connected to supply voltage |
| SDA                    | 0x53        | Connected to I2C data line |
| SCL                    | 0x54        | Connected to I2C clock line |

## Pin Configuration

| Pin | Name         | Description |
|-----|--------------|-------------|
| 1   | GND          | Ground |
| 2   | LED_CATHODE  | Address Select / IR LED Cathode |
| 3   | VDD          | Supply Voltage |
| 4   | NC           | No Connection |
| 5   | LEDneg       | IR LED Negative (internal) |
| 6   | LEDpos       | IR LED Positive (internal) |
| 7   | NC           | No Connection |
| 8   | INT          | Interrupt Output (active low) |
| 9   | SDAT         | I2C Serial Data |
| 10  | SCLK         | I2C Serial Clock |

## Enhanced Features

### Long-Range Proximity Detection
- **Extended detection range**: Up to 1.5m with optimized IR LED drive
- **Improved signal-to-noise ratio**: Better performance in challenging environments
- **Smart persistence**: Configurable integration time to avoid false triggers
- **Crosstalk cancellation**: Automatic compensation for ambient light interference

### Advanced Ambient Light Sensing
- **High dynamic range**: 0.01 lux to 120k lux measurement capability
- **Sunlight immunity**: Excellent performance under direct sunlight
- **White light response**: Optimized for human eye sensitivity
- **Programmable integration time**: Adjustable from 50ms to 800ms

### Interrupt System
- **Dual threshold interrupts**: Separate high and low thresholds
- **Persistence filter**: Configurable number of consecutive readings
- **Interrupt modes**: Proximity, ambient light, or both
- **Logic output**: Active-low open-drain output

## Applications

- **Long-range object detection** and counting
- **Touchless user interfaces** and gesture recognition
- **Automotive interior sensing** and dashboard controls
- **Industrial automation** and safety systems
- **Smart lighting control** with ambient light compensation
- **Security systems** and motion detection
- **Consumer electronics** proximity sensing
- **Gaming controllers** and interactive devices
- **Medical devices** and contactless interfaces
- **Robotics** obstacle detection and navigation

## Register Map

The VCNL4200 provides comprehensive I2C registers for configuration and data reading:

### Configuration Registers
- **ALS_CONF (0x00)**: Ambient light sensor configuration
- **PS_CONF1 (0x03)**: Proximity sensor configuration 1
- **PS_CONF2 (0x03)**: Proximity sensor configuration 2
- **PS_CONF3 (0x04)**: Proximity sensor configuration 3

### Data Registers
- **ALS_DATA (0x09)**: 16-bit ambient light data
- **PS_DATA (0x08)**: 16-bit proximity data
- **WHITE_DATA (0x0A)**: 16-bit white light data
- **INT_FLAG (0x0D)**: Interrupt status flags

### Threshold Registers
- **PS_THDL (0x06)**: Proximity low threshold
- **PS_THDH (0x07)**: Proximity high threshold
- **ALS_THDL (0x01)**: Ambient light low threshold
- **ALS_THDH (0x02)**: Ambient light high threshold

## Performance Advantages

### Compared to VCNL4020
- **5x longer detection range**: 1.5m vs 300mm
- **Better sunlight immunity**: Enhanced optical design
- **Higher resolution**: Improved 16-bit ADC performance
- **Faster response time**: Optimized conversion timing
- **Lower power consumption**: More efficient operation

### Environmental Robustness
- **Temperature stability**: -40°C to +85°C operation
- **Humidity resistance**: Suitable for harsh environments
- **EMI immunity**: Robust against electromagnetic interference
- **Optical isolation**: Reduced crosstalk between channels

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
