# AMS TSL2591 High Dynamic Range Digital Light Sensor

Advanced digital light sensor with ultra-high sensitivity and 600M:1 dynamic range. The TSL2591 combines one broadband photodiode (visible plus infrared) and one infrared-responding photodiode on a single CMOS integrated circuit, making it ideal for precise lux calculations in a wide range of lighting conditions.

## Key Features

- **600M:1 Dynamic Range** - Handles everything from dim moonlight to bright sunlight
- **Dual Photodiodes** - Broadband (visible + IR) and infrared-responding sensors
- **I2C Interface** - Simple digital communication (fixed address 0x29)
- **Low Power** - ~0.4mA active sensing, <5mA in power down mode
- **Wide Supply Range** - 3.0V to 5.5V operation
- **Interrupt Output** - Configurable threshold-based interrupt

## Usage

```ato
#pragma experiment("TRAITS")
import I2C
import ElectricPower

from "atopile/ams-tsl2591/ams-tsl2591.ato" import AMS_TSL2591

module Usage:
    """
    Minimal usage example for AMS TSL2591 High Dynamic Range Digital Light Sensor.
    Shows how to connect the sensor to power and I2C bus.
    """

    # Light sensor instance
    light_sensor = new AMS_TSL2591

    # Power supply (3.3V typical)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz

    # Connect sensor to power and I2C
    power_3v3 ~ light_sensor.power
    i2c_bus ~ light_sensor.i2c

```

## Technical Specifications

- **Supply Voltage**: 3.0V to 5.5V
- **I2C Address**: 0x29 (7-bit, fixed)
- **Current Consumption**: ~0.4mA active, <5mA power down
- **Dynamic Range**: 600,000,000:1
- **Package**: DFN-6 (2.0mm x 2.2mm)
- **Operating Temperature**: -30°C to +70°C

## Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| 1   | SCL  | I2C Clock |
| 2   | INT  | Interrupt Output (active low) |
| 3   | GND  | Ground |
| 5   | VDD  | Power Supply |
| 6   | SDA  | I2C Data |

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
