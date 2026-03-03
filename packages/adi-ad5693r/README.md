# ADI AD5693R 16-Bit DAC with I2C Interface

The AD5693R is a single-channel 16-bit digital-to-analog converter (DAC) with an I2C interface. This package provides a complete atopile module for integrating the AD5693R into your electronic designs.

## Features

- 16-bit resolution
- I2C interface (400 kHz max)
- Rail-to-rail output
- Internal 2.5V reference
- Wide supply voltage range: 1.8V to 5.5V
- Configurable I2C address via A0 pin
- MSOP-10 package

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import I2C
import ElectricSignal

from "atopile/adi-ad5693r/adi-ad5693r.ato" import ADI_AD5693R

module Usage:
    """
    Minimal usage example for `adi-ad5693r`.
    Demonstrates basic connections for the AD5693R 16-bit DAC.
    """

    # Power supply
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz

    # DAC instance
    dac = new ADI_AD5693R

    # Connections
    power_3v3 ~ dac.power
    i2c_bus ~ dac.i2c

    # Configure address (tie A0 to GND for 0x0C address)
    dac.addressor.address_lines[0].line ~ power_3v3.lv

    # Connect DAC output
    dac_out = new ElectricSignal
    dac_out ~ dac.dac_out

```

## Interface Description

### Power Supply
- **power**: Main power supply (1.8V to 5.5V)
- Includes automatic decoupling capacitors (100nF + 10µF)

### I2C Interface
- **i2c**: Standard I2C interface with automatic reference shimming
- Built-in soft pull-up resistors (10kΩ)
- Address configuration via internal Addressor module
- Default address: 0x0C (when A0 is tied to GND)
- Address: 0x0D (when A0 is tied to VDD)

### DAC Output & Signals
- **dac_out**: DAC analog output signal
- **vlogic**: I2C logic level reference (connect to I2C bus voltage)
- **vref**: Reference voltage input (internal 2.5V or external) - includes 100nF filtering capacitor

### Control Pins
- **reset**: Reset pin (active low) - includes weak pullup resistor (100kΩ) to keep device active
- **ldac**: Load DAC pin (active low) - includes pulldown resistor (10kΩ) for immediate updates

## I2C Address Configuration

The AD5693R supports two I2C addresses based on the A0 pin:
- A0 = GND: Address 0x0C
- A0 = VDD: Address 0x0D

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
