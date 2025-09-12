# ROHM BH1750 Digital Ambient Light Sensor

The BH1750 is a digital ambient light sensor with I²C interface that provides accurate lux measurements for ambient light sensing applications.

## Features

- **Digital I²C Interface**: Simple 2-wire communication
- **High Resolution**: 16-bit resolution for accurate measurements
- **Wide Range**: 1 to 65535 lux measurement range
- **Low Power**: 0.12 mA active current consumption
- **Fixed Address**: 0x23 (7-bit addressing)
- **Wide Supply Range**: 2.4V to 3.6V operation
- **Built-in 10kΩ I²C pull-up resistors**

## Usage

```ato
#pragma experiment("TRAITS")

import ElectricPower
import I2C
import has_part_removed

from "atopile/rohm-bh1750/rohm-bh1750.ato" import ROHM_BH1750

module MCU:
    """Host MCU providing I²C bus and power rail."""

    trait has_part_removed

    power = new ElectricPower
    i2c = new I2C

    trait has_part_removed

module Usage:
    """Minimal example for the ROHM_BH1750 lux sensor."""

    # MCU & sensor
    mcu = new MCU
    lux_sensor = new ROHM_BH1750

    # Shared 3V3 rail
    power = new ElectricPower
    power.voltage = 3.3V
    power ~ mcu.power
    power ~ lux_sensor.power

    # I²C connection
    mcu.i2c ~ lux_sensor.i2c

```

## Interface Details

### I²C Communication

- **Fixed Address**: 0x23 (7-bit addressing)
- **Bus Speed**: Standard mode (100 kHz) and Fast mode (400 kHz)
- **Built-in Pull-ups**: 10kΩ resistors on SCL and SDA lines
- **Address Pin**: ADDR pin connected to GND through 10kΩ resistor

### Power Supply

- **Operating Voltage**: 2.4V to 3.6V
- **Current Consumption**: 0.12 mA active, 0.01 mA standby
- **Decoupling**: Built-in 100nF capacitor for stable operation

### Light Measurement

- **Measurement Range**: 1 to 65535 lux
- **Resolution**: 16-bit digital output
- **Accuracy**: ±20% typical
- **Response Time**: Fast ambient light detection

### DVI Pin

- **Low-pass Filter**: Built-in RC filter for DVI pin
- **Filter Components**: 1kΩ resistor and 0.1µF capacitor
- **Purpose**: Noise reduction for stable operation

## Applications

- Automatic backlight control
- Display brightness adjustment
- Outdoor lighting systems
- Smart home automation
- Camera exposure control
- Energy-efficient lighting systems

## Technical Specifications

- **Resolution**: 16-bit
- **Measurement Range**: 1 to 65535 lux
- **Accuracy**: ±20% typical
- **Temperature Range**: -40°C to +85°C
- **Package**: SOP-8

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
