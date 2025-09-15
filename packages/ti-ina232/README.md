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
import Resistor

from "atopile/ti-ina232/ti-ina232.ato" import TI_INA232

module Usage:
    """
    Usage example for ti-ina232 current monitor showing all 4 possible addresses.
    Tests INA232A addressing scheme with different A0 pin connections.
    """

    # Power rails
    supply = new ElectricPower
    load1 = new ElectricPower
    load2 = new ElectricPower
    load3 = new ElectricPower
    load4 = new ElectricPower
    supply.voltage = 12V +/- 5%

    # Device power supply (3.3V)
    device_power = new ElectricPower
    device_power.voltage = 3.3V +/- 5%

    # I2C bus with pull-up resistors
    i2c = new I2C
    i2c.reference_shim ~ device_power

    # Four sensors with different address configurations
    sensor1 = new TI_INA232  # A0 = GND -> 0x40
    sensor2 = new TI_INA232  # A0 = VS -> 0x41
    sensor3 = new TI_INA232  # A0 = SDA -> 0x42
    sensor4 = new TI_INA232  # A0 = SCL -> 0x43

    # Configure sensors with different current ranges
    sensor1.max_current = 0.5A   # Low current monitoring
    sensor2.max_current = 1A   # Medium current monitoring
    sensor3.max_current = 5A   # High current monitoring
    sensor4.max_current = 10A  # Very high current monitoring

    # Connect power and I2C to all sensors
    for sensor in [sensor1, sensor2, sensor3, sensor4]:
        sensor.power ~ device_power
        # sensor.i2c ~ i2c

    i2c1 = new I2C
    sensor1.i2c ~ i2c1
    i2c2 = new I2C
    sensor2.i2c ~ i2c2
    i2c3 = new I2C
    sensor3.i2c ~ i2c3
    i2c4 = new I2C
    sensor4.i2c ~ i2c4

    # Address configuration via A0 pin connections:
    # Sensor 1: A0 to GND (0x40)
    sensor1.i2c.address = 0x40

    # Sensor 2: A0 to VS (0x41)
    sensor2.i2c.address = 0x41

    # Sensor 3: A0 to SDA (0x42)
    sensor3.i2c.address = 0x42

    # Sensor 4: A0 to SCL (0x43)
    sensor4.i2c.address = 0x43

    # Wiring - using bridge functionality for each sensor
    supply ~> sensor1 ~> load1
    supply ~> sensor2 ~> load2
    supply ~> sensor3 ~> load3
    supply ~> sensor4 ~> load4

    # Expected addresses and current ranges:
    # sensor1: 0x40 (A0=GND) - 1A max current
    # sensor2: 0x41 (A0=VS) - 2A max current
    # sensor3: 0x42 (A0=SDA) - 5A max current
    # sensor4: 0x43 (A0=SCL) - 10A max current

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
