# Texas Instruments TPS82130 Adjustable Regulator

The TPS82140 is a 17-V input 2-A step-down converter MicroSiP™ power module
optimized for small solution size and high efficiency. The module integrates a
synchronous step-down converter and an inductor to simplify design, reduce
external components, and save PCB area. The low-profile and compact solution is
suitable for automated assembly by standard surface-mount equipment.

## Features

- 3.0 mm × 2.8 mm × 1.5 mm MicroSiP™ package
- 3.0 V to 17 V input range
- 2 A continuous output current
- DCS-Control™ topology
- Power-save mode for light-load efficiency
- 20 µA operating quiescent current
- 0.9 V to 6 V adjustable output voltage
- 100 % duty cycle for lowest dropout
- Power-good output
- Programmable soft-startup with tracking
- Thermal shutdown protection
- Pin-to-pin compatible with TPS82130 and TPS82150
- –40 °C to 125 °C operating temperature range

## Usage

```ato
import ElectricPower
import ElectricLogic

from "atopile/ti-tps82130/ti-tps82130.ato" import Texas_Instruments_TPS82130

module Usage:
    """
    Test design
    """
    regulator12_3v3 = new Texas_Instruments_TPS82130
    regulator12_3v3.power_out.max_current = 3000mA
    regulator12_3v3.soft_start_time_ms = 1.8ms

    # --- Connections ---
    power_input = new ElectricPower
    assert power_input.voltage within 12V +/- 10%
    power_output = new ElectricPower
    assert power_output.voltage within 3.3V +/- 5%

    # TODO: enable required workaround
    enable = new ElectricLogic
    enable.line ~ power_input.hv

    regulator12_3v3.power_in ~ power_input
    regulator12_3v3.power_out ~ power_output
    regulator12_3v3.enable ~ enable
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
