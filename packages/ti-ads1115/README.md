# Texas Instruments ADS1115 16-bit ADC

16-bit analog-to-digital converter with integrated multiplexer, programmable gain amplifier (PGA), comparator, oscillator, and reference.

**Features:**
- 16-bit resolution
- 4 single-ended or 2 differential inputs
- Sample rate: up to 860 SPS
- I2C interface
- Programmable gain amplifier (PGA)
- Integrated voltage reference
- Comparator with alert function
- Operating voltage: 1.8V to 5.5V

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import I2C
import ElectricSignal

from "atopile/ti-ads1115/ti-ads1115.ato" import TI_ADS1115

module Usage:
    """
    Minimal usage example for `ti-ads1115`.
    Demonstrates basic connections for the ADS1115 16-bit ADC.
    """

    # Power supply
    power_supply = new ElectricPower
    power_supply.voltage = 3.3V +/- 5%

    # I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz

    # ADC instance
    adc = new TI_ADS1115

    # Connections
    power_supply ~ adc.power
    i2c_bus ~ adc.i2c

    # Configure address (tie ADDR to GND for 0x48 address)
    adc.addressor.address_lines[0].line ~ power_supply.lv

    # Connect ADC inputs
    analog_inputs = new ElectricSignal[4]
    analog_inputs[0] ~ adc.inputs[0]
    analog_inputs[1] ~ adc.inputs[1]
    analog_inputs[2] ~ adc.inputs[2]
    analog_inputs[3] ~ adc.inputs[3]

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
