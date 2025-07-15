# Texas Instruments INA238 Current, Voltage & Power Monitor

`ti-ina238` provides a ready-to-use atopile driver for the [INA238](https://www.ti.com/product/INA238) precision digital power monitor.

The module exposes an I²C interface and bridges a high-side shunt resistor to measure the current flowing from **power_in** to **power_out** while reporting shunt/bus voltage and calculated power.

## Features

- **High-accuracy, bidirectional current sensing**: ±80 mV shunt drop full-scale
- **16-bit Δ-Σ ADC**: Programmable conversion time and averaging
- **Wide operating range**: 2.7 V – 5.5 V supply, common-mode up to 85 V
- **ALERT interrupt pin**: Over-limit events notification
- **I²C addressing**: Two address pins → 4 selectable addresses (0x40–0x43)
- **Integrated components**: On-board decoupling and configurable external shunt
- **Bridge capability**: Can be inserted inline in power path using `~>` operator
- **Built-in 10kΩ I²C pull-up resistors**

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import I2C

from "ti-ina238.ato" import TI_INA238

module Usage:
    """
    Minimal usage example for ti-ina238 current monitor.
    Measures load current/power on a 12 V rail.
    """

    # Power rails
    supply = new ElectricPower
    load = new ElectricPower
    supply.voltage = 5V +/- 5%

    # I2C bus
    i2c = new I2C

    # Device instance
    sensor = new TI_INA238
    sensor.max_current = 5A
    sensor.power ~ supply

    # Wiring
    supply ~> sensor ~> load
    sensor.i2c ~ i2c

    # Address automatically set by addressor (0x40 base address when A0=A1=0)
    # Pull-up resistors are built into the module
```

## Interface Details

### I²C Communication
- **Address Range**: 0x40 to 0x43 (4 possible addresses)
- **Address Selection**: Two address pins (A0, A1) control the address
- **Address Configuration**: Automatically handled by addressor system
- **Bus Speed**: Up to 3.4 MHz I²C-compatible interface
- **Built-in Pull-ups**: 10kΩ resistors on SCL and SDA lines

### Power Supply
- **Operating Voltage**: 2.7V to 5.5V
- **Common-mode Range**: Up to 85V
- **Decoupling**: Built-in 100nF capacitor for stable operation

### Current Sensing
- **Method**: High-side bidirectional current sensing
- **Shunt Voltage**: ±80mV full-scale range
- **Shunt Resistor**: Automatically sized based on max_current parameter
- **Bridge Mode**: Can be inserted inline in power path

### Alert Function
- **ALERT Pin**: Open-drain output for programmable alerts
- **Configurable Limits**: Overcurrent, undervoltage, and other conditions
- **Interrupt Support**: Real-time notification of limit violations

## Applications

- Battery monitoring and management
- Power supply monitoring
- Motor current sensing
- Solar panel monitoring
- DC/DC converter efficiency measurement
- Load monitoring in embedded systems

## Technical Specifications

- **Resolution**: 16-bit Δ-Σ ADC
- **Conversion Time**: Programmable from 50 µs to 4.156 ms
- **Accuracy**: High precision measurements
- **Temperature Range**: -40°C to +125°C
- **Package**: VSSOP-10

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
