# ST VL53L1X Time-of-Flight Distance Sensor

The VL53L1X is a state-of-the-art, Time-of-Flight (ToF), laser-ranging sensor based on ST's FlightSense™ technology. It is the fastest miniature ToF sensor on the market with accurate ranging up to 4 m and fast ranging frequency up to 50 Hz.

## Key Features

- **Long distance ranging**: Up to 4 m (13 ft) under favorable conditions
- **High accuracy**: 1 mm resolution with accurate distance measurement
- **Fast ranging**: Up to 50 Hz measurement frequency
- **Compact size**: LGA-12 package (2.5mm × 4.9mm)
- **I2C interface**: Standard I2C digital interface
- **Low power**: Optimized for battery-powered applications
- **Ambient light immunity**: Works in various lighting conditions
- **Multiple distance modes**: Short, medium, and long distance modes
- **Wide supply voltage**: 2.6V to 3.5V

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

# --- Standard library imports ---
import ElectricPower
import I2C
import ElectricLogic

# --- Package import ---
from "atopile/st-vl53l1x/st-vl53l1x.ato" import ST_VL53L1X


module Usage:
    """
    Minimal usage example for `st-vl53l1x`.
    Powers the VL53L1X from a 3.3V rail and places it on an I²C bus at the
    default address **0x29**.
    """

    # Power rail (3.3 V for both analog supplies)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    # I²C bus
    i2c_bus = new I2C

    # Sensor instance
    sensor = new ST_VL53L1X

    # Connect required power rail
    power_3v3 ~ sensor.power

    # Provide logic reference for the bus
    power_3v3 ~ i2c_bus.scl.reference
    power_3v3 ~ i2c_bus.sda.reference

    # Connect I²C bus
    i2c_bus ~ sensor.i2c

    # Default I2C address is 0x29
    sensor.i2c.address = 0x29

    # Optional: Connect shutdown pin (pull high to enable)
    # power_3v3.hv ~ sensor.xshut.line

    # Optional: Connect interrupt pin
    # interrupt_line = new ElectricLogic
    # interrupt_line ~ sensor.gpio1

```

## Interface Details

### I2C Communication
- **Default address**: 0x29 (7-bit)
- **Clock frequency**: Up to 400 kHz (Fast mode)
- **Data format**: 16-bit distance measurements

### Power Supply
- **AVDD**: Analog supply voltage (2.6V to 3.5V)
- **AVDDVCSEL**: VCSEL (laser) supply voltage (2.6V to 3.5V)
- **Current consumption**:
  - Active: ~20 mA (typical during ranging)
  - Standby: ~5 µA (typical)

### Control Pins
- **XSHUT**: Hardware shutdown pin (active low)
  - Pull low to put device in shutdown mode
  - Pull high or leave floating for normal operation
- **GPIO1**: Interrupt output pin
  - Configurable interrupt for new data ready
  - Can be used for event-driven measurements

### Distance Measurement
- **Range**: 4 cm to 4 m (depending on conditions)
- **Resolution**: 1 mm
- **Accuracy**: ±3% (typical) under good conditions
- **Field of View**: 27° typical
- **Measurement time**: 20ms to 200ms (depending on mode)

## Package Information

- **LCSC Part Number**: C190004
- **Package**: LGA-12 (2.5mm × 4.9mm × 1.6mm)
- **Operating Temperature**: -20°C to +70°C
- **Storage Temperature**: -40°C to +85°C
- **Manufacturer**: STMicroelectronics
- **Part Number**: VL53L1CXV0FY/1

### Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| 1 | AVDDVCSEL | VCSEL supply voltage (2.6V - 3.5V) |
| 2 | AVSSVCSEL | VCSEL ground |
| 3 | GND | Ground |
| 4 | GND2 | Ground |
| 5 | XSHUT | Hardware shutdown (active low) |
| 6 | GND3 | Ground |
| 7 | GPIO1 | Interrupt output |
| 8 | DNC | Do not connect |
| 9 | SDA | I²C data line |
| 10 | SCL | I²C clock line |
| 11 | AVDD | Analog supply voltage (2.6V - 3.5V) |
| 12 | GND4 | Ground |

## Distance Modes

The VL53L1X offers three distance modes that can be configured via software:

1. **Short Distance Mode**: Optimized for distances up to 1.3m with high ambient light immunity
2. **Medium Distance Mode**: Balanced performance for distances up to 3m
3. **Long Distance Mode**: Maximum range up to 4m with lower ambient light immunity

## Applications

- **Robotics**: Obstacle detection and navigation
- **Drones**: Altitude sensing and collision avoidance
- **IoT devices**: Presence detection and proximity sensing
- **Industrial automation**: Level measurement and object detection
- **Consumer electronics**: Gesture recognition and user presence
- **Smart home**: Room occupancy detection and automated lighting
- **Security systems**: Motion detection and perimeter monitoring
- **Automotive**: Parking assistance and blind spot detection
- **Medical devices**: Non-contact distance measurement
- **Smart agriculture**: Crop height monitoring and irrigation control

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
