# Texas Instruments DAC6578 8-Channel 10-Bit DAC

Texas Instruments DAC6578 8-Channel 10-Bit Digital-to-Analog Converter with I2C Interface.

## Features

- 8 x 10-bit DAC channels accessible via outputs[0-7]
- I²C interface (address 0x4C, up to 3.4MHz)
- Supply voltage: 2.7V to 5.5V (3.3V typical)
- Resolution: 10-bit (0-1023 range)
- Reference voltage input for full-scale output control
- Low power consumption: 0.12mA per channel at 5V
- Power consumption: 2.9mW typical
- Operating temperature: -40°C to +125°C
- Ultra-low glitch energy: 0.15nV-s
- Clock rates up to 3.4MHz
- Simultaneous update capability via LDAC pin
- Clear function via CLR pin
- Built-in 4.7kΩ I²C pull-up resistors

## Usage

```ato
#pragma experiment("TRAITS")

import ElectricPower
import I2C
import Electrical
import has_part_removed

from "atopile/ti-dac6578/ti-dac6578.ato" import TI_DAC6578

module MCU:
    """Host MCU providing I²C bus and power rail."""
    trait has_part_removed

    trait has_part_removed

    power = new ElectricPower
    i2c = new I2C


module Usage:
    """Complete usage example for TI_DAC6578 DAC."""

    # MCU & DAC
    mcu = new MCU
    dac = new TI_DAC6578

    # Shared 3V3 rail
    power = new ElectricPower
    power.voltage = 3.3V +/- 5%
    power ~ mcu.power
    power ~ dac.power

    # I²C connection
    mcu.i2c ~ dac.i2c

    # Note: DAC module includes 4.7k I2C pull-ups internally

    # Reference voltage (using power supply)
    dac.vref ~ power.hv

    # DAC outputs can be connected to external circuits
    # Example: connecting to test points or analog circuits
    # dac.outputs[0] ~ analog_circuit_input_a  # Channel A
    # dac.outputs[1] ~ analog_circuit_input_b  # Channel B
    # ... etc for channels 2-7 (C through H)

    # Control signals can be connected to microcontroller pins:
    # dac.clear_n ~ mcu.gpio_clear
    # dac.ldac_n ~ mcu.gpio_ldac

```

## Pin Configuration

- **ADDR0**: Address selection pin (fixed at 0x4C in this implementation)
- **SCL/SDA**: I²C clock and data lines
- **VOUTA-VOUTH**: 8 DAC output channels
- **VREFIN**: Reference voltage input (configurable via vref interface)
- **nCLR**: Clear signal (active low)
- **nLDAC**: Load DAC signal (active low)
- **AVDD**: Analog supply voltage (2.7V to 5.5V)
- **GND**: Ground

## I²C Addressing

The DAC6578 I²C address is fixed at **0x4C** in this implementation.

## Design Philosophy

This package follows these design principles:

- **Integrated I²C pull-ups**: 4.7kΩ pull-up resistors are included in the module for convenience.
- **External reference voltage**: The `vref` interface allows connection to external precision voltage references for better accuracy.
- **Array-based outputs**: All 8 DAC channels are accessible via a single `outputs[8]` array for cleaner code.
- **Minimal dependencies**: Only essential components are included.

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
