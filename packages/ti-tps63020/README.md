# Texas Instruments TPS63020 High Efficiency Single Inductor Buck-boost Converter

## Overview

The TPS63020 is a high-efficiency, single-inductor buck-boost converter with 4-A switches. It provides a power supply solution with a 1.8V to 5.5V input voltage range and delivers output voltages between 1.2V to 5.5V. This makes it ideal for battery-powered applications where the input voltage can be above, below, or equal to the output voltage.

## Key Features

- Input voltage range: 1.8V to 5.5V
- Output voltage range: 1.2V to 5.5V (adjustable)
- Output current: up to 3A (buck mode), 2A (boost mode)
- Switching frequency: 2.4MHz typical
- Efficiency: up to 95%
- Small solution size with integrated switches
- Power good output

## Usage

```ato
import ElectricPower
from "ti-tps63020.ato" import TPS63020_driver

module MyDesign:
    # Power rails
    power_in = new ElectricPower
    power_3v3 = new ElectricPower

    # Configure input power (e.g., from Li-ion battery)
    assert power_in.voltage within 3.0V to 4.2V

    # Configure output power
    assert power_3v3.voltage within 3.25V to 3.35V
    assert power_3v3.max_current within 0A to 2A

    # Create buck-boost converter
    converter = new TPS63020_driver

    # Connect power
    power_in ~> converter ~> power_3v3
```

## Implementation Details

This package includes:
- Automatic calculation of feedback resistor values
- Proper decoupling capacitors on input and output
- Inductor selection with appropriate current rating
- Power good pullup resistor
- Compensation network calculations

The module automatically handles:
- Right half-plane zero frequency verification for stable operation
- Peak inductor current calculations
- Proper component sizing based on voltage and current requirements

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
