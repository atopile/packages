# Texas Instruments TPS563201 3A Buck Converter

The TPS563201 is a synchronous buck converter with integrated MOSFETs capable of delivering up to 3A of continuous output current.

## Specifications

- **Input Voltage**: 4.5V to 17V
- **Output Voltage**: 0.76V to 7V (adjustable)
- **Output Current**: Up to 3A continuous
- **Switching Frequency**: Fixed 580kHz
- **Package**: SOT-23-6
- **Features**:
  - Integrated MOSFETs
  - Current mode control
  - Internal compensation
  - Power good output
  - Enable pin

## Usage

```ato
from "atopile/ti-tps563201/ti-tps563201.ato" import TPS563201
import ElectricPower

module MyProject:
    # Power rails
    power_12v = new ElectricPower
    power_3v3 = new ElectricPower

    # Buck converter
    regulator = new TPS563201

    # Configure voltages
    assert power_12v.voltage is 12V +/- 10%
    assert regulator.output_voltage is 3.3V +/- 2%

    # Connect power
    power_12v ~ regulator.power_in
    regulator.power_out ~ power_3v3

    # Optional: control enable (defaults to always enabled)
    # enable = new ElectricLogic
    # enable ~ regulator.enable
```

## Example Configurations

### 1.8V Output
```ato
regulator = new TPS563201
assert regulator.input_voltage is 5V +/- 10%
assert regulator.output_voltage is 1.8V +/- 3%
```

### 5V Output from 12V Input
```ato
regulator = new TPS563201
assert regulator.input_voltage is 12V +/- 10%
assert regulator.output_voltage is 5V +/- 3%
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
