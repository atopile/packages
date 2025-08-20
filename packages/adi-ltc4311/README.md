# ADI LTC4311 Low Voltage I2C/SMBus Accelerator

The LTC4311 is a rise-time accelerator that provides buffered connections for I2C bus lines with active pull-up currents to extend I2C bus capacitance beyond normal limits and improve signal integrity. This package provides an atopile interface for the ADI LTC4311 dual bidirectional buffer.

## Features

- **Wide Supply Voltage Range**: 1.6V to 5.5V operation
- **High Speed Operation**: Up to 400kHz I2C/SMBus support
- **Dual Bidirectional Buffers**: Two independent signal buffers for SDA and SCL
- **Active Pull-Up**: Provides slew-limited pull-up currents for improved signal integrity
- **Low Power**: Auto-detect standby mode and low current shutdown (<5μA)
- **ESD Protection**: ±8kV Human Body Model ESD ruggedness
- **Extended Bus Capacitance**: Handles bus loading well beyond 400pF specification

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import ElectricLogic
import I2C
from "atopile/adi-ltc4311/adi-ltc4311.ato" import ADI_LTC4311

module Usage:
    """
    Minimal usage example for adi-ltc4311.

    This example demonstrates how to use the LTC4311 I2C accelerator/buffer
    to improve signal integrity on I2C bus lines.

    The LTC4311 provides two independent bidirectional buffers that can be
    used to buffer SDA and SCL lines separately.
    """

    # Create power supply
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # Create I2C bus
    i2c = new I2C

    # Instantiate the LTC4311 I2C accelerator
    i2c_buffer = new ADI_LTC4311

    # Connect power
    power_3v3 ~ i2c_buffer.power

    # Connect I2C bus
    i2c ~ i2c_buffer.i2c

```

## How It Works

The LTC4311 provides two independent bidirectional signal buffers (BUS1 and BUS2) that can be used to:

- **Buffer I2C Lines**: Each bus connection can handle one I2C signal line (SDA or SCL)
- **Extend Bus Capacity**: Allows I2C operation with much higher capacitance loads
- **Improve Signal Integrity**: Active pull-up provides better signal edges and rise times
- **Isolate Bus Segments**: Prevents loading on one segment from affecting the other
- **Enable/Disable Operation**: Optional enable control for power management

## Applications

- **I2C Bus Extension**: Extend I2C communication over longer distances
- **Signal Integrity Improvement**: Enhance signal quality in noisy environments
- **Level Shifting**: Bridge I2C devices operating at different voltage levels (1.6V-5.5V)
- **Bus Buffering**: Isolate I2C segments to prevent loading issues
- **Cable Driving**: Drive I2C signals through cables up to 4000pF capacitance
- **Multi-Master Systems**: Improve signal integrity in complex I2C topologies

## Package Information

- **JLCPCB Part Number**: C580856
- **Package**: SC-70-6 (2.1mm × 1.3mm)
- **Operating Temperature**: Commercial grade (0°C to 70°C typical)
- **Manufacturer**: Analog Devices (ADI)
- **Part Number**: LTC4311CSC6#TRPBF

## Pin Configuration

| Pin | Name   | Description |
|-----|--------|-------------|
| 1   | VCC    | Power supply (1.6V to 5.5V) |
| 2   | GND    | Ground |
| 3   | ENABLE | Enable pin (active high) |
| 4   | BUS2   | Bidirectional buffer 2 |
| 5   | GND    | Ground |
| 6   | BUS1   | Bidirectional buffer 1 |

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
