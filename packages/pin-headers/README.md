# TI TPS54560x Buck Converter

A high-efficiency, wide input voltage range buck converter with integrated high-side MOSFET.

## Overview

The TPS54560 is a 60V, 5A step-down regulator with an integrated high-side MOSFET. It's designed for industrial, automotive, and communications power systems requiring a robust, efficient power solution.

## Key Features

- **Wide Input Voltage Range**: Survives load dump pulses up to 65V (ISO 7637 compliant)
- **High Efficiency**: 92-mΩ high-side MOSFET with pulse skipping Eco-mode™ for light load efficiency
- **Low Power Consumption**:
  - 146 μA operating quiescent current
  - 2 μA shutdown current
- **Flexible Switching Frequency**: 100 kHz to 2.5 MHz fixed frequency with external clock synchronization
- **Integrated Protection**:
  - Adjustable UVLO voltage and hysteresis
  - Cycle-by-cycle current limiting
  - Frequency foldback and thermal shutdown
- **Controlled Startup**: Internal output voltage ramp control to eliminate overshoot
- **Compact Package**: 8-terminal HSOP with PowerPAD™ for enhanced thermal performance
- **Wide Temperature Range**: -40°C to 150°C operating range

## Applications

- Industrial Automation and Motor Control
- Vehicle Accessories (GPS, Entertainment Systems)
- USB Dedicated Charging Ports and Battery Chargers
- 12V, 24V, and 48V Industrial, Automotive, and Communications Power Systems

## Package Contents

This package provides:

- Reference design for the TPS54560 buck converter
- Footprint and symbol definitions
- Example configurations for common applications

## Usage

To use this package in your design:

```python
from "atopile/ti-tps54560x/ti-tps54560x.ato" import TPS54560x

// Example usage in your design
module Test5V:
    regulator = new TPS54560x
    regulator.v_in = 24V +/- 10%
    regulator.v_out = 5V +/- 5%

    enable = new ElectricLogic
    enable.line ~ regulator.power_in.vcc
    regulator.enable ~ enable
```

## Design Resources

- [TI TPS54560 Datasheet](https://www.ti.com/lit/ds/symlink/tps54560.pdf)
- [WEBENCH® Power Designer](https://webench.ti.com/power-designer/) - Create a custom design using the TPS54560

## License

This package is released under the MIT License.

## Author

Created by Narayan Powderly <narayan@atopile.io>
