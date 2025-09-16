# Nuvoton NAU7802 Differential ADC
24 bit, 2-channel differential ADC with onboard PGA

The Nuvoton NAU7802 is a precision low-power 24-bit analog-to-digital converter (ADC), with an
onboard low-noise programmable gain amplifier (PGA), onboard RC or Crystal oscillator, and a
precision 24-bit sigma-delta (Σ-Δ) analog to digital converter (ADC). The NAU7802 device is capable of
up to 23-bit ENOB (Effective Number Of Bits) performance. This device provides a complete front-end
solution for bridge/sensor measurement such as in weigh scales, strain gauges, and many other high
resolution, low sample rate applications.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("TRAITS")

# --- Standard Library ---
import DifferentialPair
import ElectricPower
import I2C
import has_part_removed

# --- Package Import ---
from "atopile/nuvoton-nau7802/nuvoton-nau7802.ato" import Nuvoton_Tech_NAU7802_Single
from "atopile/nuvoton-nau7802/nuvoton-nau7802.ato" import Nuvoton_Tech_NAU7802_Dual

module Microcontroller:
    """Microcontroller"""
    i2c = new I2C[2]
    power_3v3 = new ElectricPower
    trait has_part_removed

module Usage:
    """
    Example of a Nuvoton Tech NAU7802 ADC in a single-channel configuration
    """
    # Power
    power_digital = new ElectricPower
    power_digital.voltage = 3.3V

    # Component
    adc_single_channel = new Nuvoton_Tech_NAU7802_Single
    micro = new Microcontroller

    # Power Connection
    adc_single_channel.power_digital ~ power_digital

    # Analog Input
    input = new DifferentialPair
    input ~ adc_single_channel.sense_input

    # I2C Data Connection
    micro.i2c[0] ~ adc_single_channel.i2c


    """
    Example of a Nuvoton Tech NAU7802 ADC in a dual-channel configuration
    """

    # Component
    adc_dual_channel = new Nuvoton_Tech_NAU7802_Dual

    # Power Connection
    adc_dual_channel.power_digital ~ power_digital

    # Analog Inputs
    inputs = new DifferentialPair[2]
    inputs[0] ~ adc_dual_channel.sense_inputs[0]
    inputs[1] ~ adc_dual_channel.sense_inputs[1]

    # # I2C Data Connection
    micro.i2c[1] ~ adc_dual_channel.i2c

```

## Contributing

Contributions are welcome! Please open an issue or pull request and ensure the `usage` build target passes (`ato build usage`).

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
