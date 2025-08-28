# Texas Instruments TS5A22362 — Dual SPDT Analog Switch (Atopile package)

atopile package for TI’s TS5A22362, a dual single‑pole double‑throw (SPDT) analog switch. This package exposes two switch channels with `COM`, `NO`, and `NC` nodes, includes a 100 nF bypass capacitor on the supply, and presents clean interfaces for power and control.

## Features

- Dual SPDT analog switches (two independent channels)
- Exposed `NO` and `NC` paths for each channel via bridgeable interfaces
- Two digital control inputs (`IN1`, `IN2`) exposed as `enables[2]`
- Single supply `power` interface with onboard 100 nF decoupling
- Simple bridging model for wiring signals through `NO` or `NC` paths

## Interfaces

- **power**: `ElectricPower` — connect to your logic/signal domain supply and ground
- **enables[2]**: `ElectricLogic` — drive `enables[i].line` to select `NO` vs `NC` to `COM` per channel (see datasheet truth table)
- **switches_no[2] / switches_nc[2]**: bridgeable switch paths for each channel to `COM`
  - Use `switches_no[i]` to bridge `NOi ↔ COMi`
  - Use `switches_nc[i]` to bridge `NCi ↔ COMi`

## Usage

Example usage:

```ato
#pragma experiment("BRIDGE_CONNECT")

import Electrical
import ElectricPower
import ElectricLogic

from "atopile/ti-ts5a22362/ti-ts5a22362.ato" import Texas_Instruments_TS5A22362DGSR

module Usage:
    """
    Usage example for Texas Instruments TS5A22362DGSR
    """

    power = new ElectricPower
    power.voltage = 3.3V +/- 5%

    analog_switch = new Texas_Instruments_TS5A22362DGSR
    power ~ analog_switch.power

    input_signals = new Electrical[2]
    output_signals = new Electrical[2]

    # Connect signals via switches
    input_signals[0] ~> analog_switch.switches_no[0] ~> output_signals[0]
    input_signals[1] ~> analog_switch.switches_no[1] ~> output_signals[1]

    # Enable control - active high
    enables = new ElectricLogic[2]
    enables[0] ~ analog_switch.enables[0]
    enables[1] ~ analog_switch.enables[1]
```

## Notes

- Be sure to connect `analog_switch.power` to your rail (e.g. 3.3 V) and ground.
- Drive `analog_switch.enables[i].line` per the datasheet truth table to select `NO` vs `NC` for channel `i`.
- The included 100 nF bypass capacitor is already connected across the supply pins.

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

MIT License. See `LICENSE.txt` for details.
