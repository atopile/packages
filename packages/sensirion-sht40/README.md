# Sensirion SHT40 Digital Temperature & Humidity Sensor

The SHT40 is a digital temperature and humidity sensor with high accuracy and low power consumption. It provides calibrated, linearized sensor signals in digital I2C format with a wide supply voltage range from 1.08V to 3.6V, making it ideal for mobile and battery-driven applications.

## Key Features

- **High accuracy**: ±1.8% RH, ±0.2°C
- **Wide supply voltage**: 1.08V to 3.6V
- **Low power consumption**: 0.4 µA sleep current
- **I2C interface**: Fixed address 0x44
- **Small package**: DFN-4-EP (1.5mm × 1.5mm)
- **Operating range**: -40°C to 125°C, 0 to 100% RH
- **Fast response**: 8s (tau63%)

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

# --- Standard library imports ---
import ElectricPower
import I2C

# --- Package import ---
from "atopile/sensirion-sht40/sensirion-sht40.ato" import Sensirion_SHT40

module Usage:
    """
    Minimal usage example for `sensirion-sht40`.
    Powers the SHT40 from a 3.3V rail and places it on an I²C bus at the
    fixed address **0x44**.
    """

    # Power rail (3.3 V)
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.2V to 3.4V

    # I²C bus
    i2c_bus = new I2C

    # Sensor instance
    sensor = new Sensirion_SHT40

    # Connect required power rail
    power_3v3 ~ sensor.power

    # Provide logic reference for the bus
    power_3v3 ~ i2c_bus.scl.reference
    power_3v3 ~ i2c_bus.sda.reference

    # Connect I²C bus
    i2c_bus ~ sensor.i2c

    # Address is fixed at 0x44 (no configuration needed)
    assert sensor.i2c.address within 0x44

```

## Interface Details

### I2C Communication
- **Fixed address**: 0x44 (7-bit)
- **Clock frequency**: Up to 1 MHz
- **No address selection pins** - address is factory programmed

### Power Supply
- **Operating voltage**: 1.08V to 3.6V
- **Supply current**:
  - Active: 600 µA (typical)
  - Sleep: 0.4 µA (typical)

### Package Information
- **Package type**: DFN-4-EP (1.5mm × 1.5mm)
- **Exposed pad**: Connected to VSS for thermal performance
- **Pin configuration**:
  - Pin 1: SDA (I2C data)
  - Pin 2: SCL (I2C clock)
  - Pin 3: VDD (power supply)
  - Pin 4: VSS (ground)
  - Pin 5 (EP): Exposed pad (ground)

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
