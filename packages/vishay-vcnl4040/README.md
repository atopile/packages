# Vishay VCNL4040 Proximity and Light Sensor

The VCNL4040 is a handy two-in-one sensor with a proximity sensor that works from 0 to 200mm (about 7.5 inches) and light sensor with range of 0.0125 to 6553 lux. Perfect for detecting nearby objects and measuring ambient light levels in your electronic projects.

## Features

- **Proximity Detection**: 0-200mm range with IR emitter and detector
- **Ambient Light Sensing**: 0.0125-6553 lux range with excellent linearity
- **I²C Interface**: Simple digital communication with 7-bit address 0x60
- **Interrupt Output**: Configurable interrupt pin for threshold-based alerts
- **Low Power**: Optimized for battery-powered applications
- **Integrated Solution**: Built-in IR emitter, IR detector, and ambient light sensor

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricLogic
import ElectricPower
import I2C

from "atopile/vishay-vcnl4040/vishay-vcnl4040.ato" import Vishay_VCNL4040

module Usage:
    """
    Minimal usage example for vishay-vcnl4040.
    Demonstrates basic connections for proximity and light sensing with interrupt.
    """

    # --- Sensor instance ---
    sensor = new Vishay_VCNL4040

    # --- Power supply ---
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%
    power_3v3 ~ sensor.power

    # --- I2C bus ---
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz
    i2c_bus ~ sensor.i2c

    # --- Interrupt connection (optional) ---
    interrupt_line = new ElectricLogic
    interrupt_line ~ sensor.int_pin

```

## Technical Specifications

- **Operating Voltage**: 2.5V to 3.6V
- **I²C Address**: 0x60 (7-bit)
- **Proximity Range**: 0-200mm
- **Light Range**: 0.0125-6553 lux
- **Package**: 4-pin OPIC (Optical IC) package
- **Temperature Range**: -40°C to +85°C

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
