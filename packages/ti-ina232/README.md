# Texas Instruments INA232 Current/Power Monitor

The INA232 is a high-side/low-side bidirectional current and power monitor with I2C interface. It can measure current, voltage, and power with high accuracy over a wide input voltage range.

## Features

- **Wide Input Range**: 0V to 48V common-mode voltage
- **High Resolution**: 16-bit ADC for precise measurements
- **Bidirectional Sensing**: Measures current in both directions
- **Flexible Sensing**: High-side or low-side current sensing
- **I²C Interface**: 16 programmable addresses (0x40-0x4F)
- **Shunt Voltage Range**: ±75mV full scale
- **Programmable Alerts**: Configurable overlimit detection
- **Low Power**: Ultra-low supply current
- **Small Package**: SOT-23-8 package
- **Configurable shunt resistor with current parameter**
- **Bridgable design for inline current sensing**
- **Built-in 10kΩ I²C pull-up resistors**

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")
import ElectricPower
import I2C

from "ti-ina232.ato" import TI_INA232

module Usage:
    """
    Minimal usage example for ti-ina232 current monitor.
    Measures load current/power on a 12V rail.
    """

    # Power rails
    supply = new ElectricPower
    load = new ElectricPower
    supply.voltage = 12V +/- 5%

    # I2C bus
    i2c = new I2C

    # Device instance
    sensor = new TI_INA232
    sensor.max_current = 2A
    sensor.power ~ supply

    # Wiring - using bridge functionality
    supply ~> sensor ~> load
    sensor.i2c ~ i2c

    # Address automatically set by addressor (0x40 base address when A0=0)
    # Pull-up resistors are built into the module
    # Device power supply (3.3V)
    device_power = new ElectricPower
    device_power.voltage = 3.3V +/- 5%
    device_power ~ sensor.power
```

## Hardware Features

### Power Supply
- **Sensor Supply**: 1.7V to 5.5V (VS pin)
- **Common-Mode Range**: 0V to 48V (load voltage)
- Integrated decoupling capacitor (100nF)

### Current Sensing
- **Shunt Voltage Range**: ±75mV full scale
- **Configurable Shunt Resistor**: Automatically sized based on max_current parameter
- **High-side Sensing**: Measures current in positive supply rail
- **Bidirectional**: Supports both source and sink current
- **Bridgable Design**: Can be inserted inline in power path using ~> operator

### I²C Interface
- **Address Range**: 0x40 to 0x41 (2 addresses)
- **Address Selection**: A0 pin controls address (using Addressor module)
  - A0 = GND: 0x40
  - A0 = VCC: 0x41
- **Default Address**: 0x40 (A0 tied to GND)
- **Automatic Address Management**: Uses Addressor module for clean address handling
- **Built-in Pull-ups**: 10kΩ resistors on SCL and SDA lines

### Alert Function
- **Programmable Alerts**: Overcurrent, undervoltage, etc.
- **Open-drain Output**: Active low alert signal
- **Configurable Limits**: Via I²C registers

## Applications

- Battery monitoring and management
- Power supply monitoring
- Motor current sensing
- Solar panel monitoring
- DC/DC converter efficiency measurement
- Load monitoring in embedded systems

## Technical Specifications

- **Resolution**: 16-bit ADC
- **Sample Rate**: Up to 1024 samples/second
- **Accuracy**: ±0.1% (typical)
- **Temperature Range**: -40°C to +125°C
- **Package**: SOT-23-8

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
