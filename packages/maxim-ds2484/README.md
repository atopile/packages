# Maxim DS2484 Single-Channel 1-Wire Master

The DS2484 is a single-channel 1-Wire master with an I2C interface from Maxim Integrated. This device provides an I2C to 1-Wire bridge, allowing microcontrollers without native 1-Wire support to communicate with Dallas/Maxim 1-Wire devices easily.

## Features

- **Single-channel 1-Wire master**
- **Supply voltage range**: 2.97V to 5.25V
- **I2C interface** with configurable address (0x18-0x1B)
- **Integrated 1-Wire timing and protocol** handling
- **Sleep mode** for low power operation
- **Strong pullup capability** for parasite-powered devices
- **Operating temperature**: -40°C to +85°C
- **Supply current**: 3mA active, 1µA sleep mode
- **Automatic 1-Wire bus recovery**
- **Supports all 1-Wire device families**
- **Compact package**: TDFN-6 (2.0mm × 2.0mm)

## Usage

```ato
#pragma experiment("TRAITS")

import ElectricPower
import I2C

from "maxim-ds2484.ato" import Maxim_DS2484, OneWire

module TemperatureSensor:
    """
    Mock 1-Wire temperature sensor for testing
    """
    onewire = new OneWire

module Usage:
    """
    Minimal usage example for Maxim DS2484 1-Wire to I2C bridge.
    Shows how to connect power supply, I2C bus, and 1-Wire devices.
    """

    # Create bridge instance
    bridge = new Maxim_DS2484

    # Main power supply for the bridge (3.3V or 5V)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # External I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz

    # 1-Wire temperature sensor
    temp_sensor = new TemperatureSensor

    # Connect interfaces
    power_3v3 ~ bridge.power
    i2c_bus ~ bridge.i2c
    bridge.onewire ~ temp_sensor.onewire

    # Set I2C address (default 0x18)
    bridge.i2c.address = 0x18
```

## Technical Specifications

- **Supply Voltage (VDD)**: 2.97V to 5.25V
- **I2C Address**: 0x18 (default), 0x19, 0x1A, 0x1B (selectable)
- **Supply Current**: 3mA active, 1µA sleep mode
- **1-Wire Speed**: Standard (15.4kbps) and Overdrive (125kbps)
- **1-Wire Pullup**: Internal strong pullup capability
- **Operating Temperature**: -40°C to +85°C
- **I2C Speed**: Up to 400kHz (Fast Mode)
- **Package**: TDFN-6 (2.0mm × 2.0mm × 0.75mm)

## I2C Address Configuration

The DS2484 supports four different I2C addresses that can be selected using external components:

| Configuration | I2C Address | Method |
|---------------|-------------|--------|
| Default       | 0x18        | No external components |
| Option 1      | 0x19        | External resistor configuration |
| Option 2      | 0x1A        | External resistor configuration |
| Option 3      | 0x1B        | External resistor configuration |

Note: This package implementation defaults to 0x18 for simplicity.

## Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| 1   | IO   | 1-Wire Bus I/O |
| 2   | GND  | Ground |
| 3   | SCL  | I2C Serial Clock |
| 4   | SDA  | I2C Serial Data |
| 5   | SLPZ | Sleep Control (active low) |
| 6   | VDD  | Supply Voltage |

## 1-Wire Interface

The DS2484 provides a complete 1-Wire master interface with the following capabilities:

### Supported 1-Wire Operations
- **Reset and Presence Detect**: Automatic 1-Wire bus reset and slave detection
- **Byte Read/Write**: 8-bit data transactions
- **Bit Read/Write**: Single-bit operations for precise control
- **Search ROM**: Device discovery and enumeration
- **Strong Pullup**: For parasite-powered devices during EEPROM operations

### 1-Wire Bus Characteristics
- **Standard Speed**: 15.4kbps (default)
- **Overdrive Speed**: 125kbps (optional)
- **Bus Recovery**: Automatic recovery from bus faults
- **Parasite Power**: Strong pullup support for parasite-powered devices

## I2C Register Map

The DS2484 provides several I2C registers for configuration and operation:

### Status Registers
- **Status Register**: Device and 1-Wire bus status
- **Data Register**: Read/write data buffer
- **Configuration Register**: Device configuration settings

### Command Set
- **Device Reset**: Software reset of the DS2484
- **Set Read Pointer**: Select register for reading
- **Write Configuration**: Configure device parameters
- **1-Wire Commands**: Reset, read, write, search operations

## Applications

- **Temperature Monitoring**: DS18B20, DS18S20 temperature sensors
- **Memory Devices**: DS24xx EEPROM and DS28xx NVRAM
- **Real-Time Clocks**: DS1921, DS1922 temperature loggers
- **Authentication**: DS2432, DS28E01 secure memory devices
- **Identification**: DS2401, DS2411 silicon serial numbers
- **Battery Monitoring**: DS2438 smart battery monitor
- **Industrial Automation**: Sensor networks and data logging
- **HVAC Systems**: Temperature and humidity monitoring
- **Medical Devices**: Patient monitoring and data collection
- **Automotive**: Engine temperature and diagnostic systems

## Sleep Mode

The DS2484 features a low-power sleep mode for battery-powered applications:

- **Sleep Entry**: Pull SLPZ pin low or send sleep command via I2C
- **Sleep Current**: Less than 1µA typical
- **Wake-up**: Release SLPZ pin or any I2C activity
- **Context Preservation**: Configuration settings maintained during sleep

## Example 1-Wire Devices

### Temperature Sensors
- **DS18B20**: Programmable resolution digital thermometer
- **DS18S20**: High-precision digital thermometer
- **DS1822**: Econo digital thermometer

### Memory Devices
- **DS24B33**: 4kb EEPROM with SHA-1 authentication
- **DS28E01**: 1kb EEPROM with SHA-1 engine
- **DS2431**: 1kb EEPROM

### Real-Time Clocks
- **DS1921**: Thermochron temperature logger
- **DS1922**: Hygrochron temperature/humidity logger

## Design Considerations

### PCB Layout
- Keep 1-Wire traces as short as possible
- Use adequate pullup resistor (typically 2.2kΩ)
- Place decoupling capacitors close to VDD pin
- Avoid routing 1-Wire signals near high-speed digital lines

### Power Supply
- Ensure stable power supply within specified range
- Use both bulk (1µF) and high-frequency (100nF) decoupling
- Consider power supply noise in sensitive applications

### 1-Wire Bus Length
- Maximum cable length depends on cable characteristics
- Typical installations support 100-300 meters
- Use twisted pair cable for longer distances
- Consider cable capacitance and resistance effects

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
