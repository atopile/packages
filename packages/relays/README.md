# Relays package

A collection of commonly used relay parts and ready-to-use logic-level relay modules.

### Selector table

| Series            | Type   | Contacts | Rating | Coil | Build target/module        |
| ----------------- | ------ | -------- | ------ | ---- | -------------------------- |
| HK4100F           | Power  | SPDT     | 3 A    | 5 V  | `LogicLevelRelaySPDT3A5V`  |
| HK4100F           | Power  | SPDT     | 3 A    | 12 V | `LogicLevelRelaySPDT3A12V` |
| HK4100F           | Power  | SPDT     | 3 A    | 24 V | `LogicLevelRelaySPDT3A24V` |
| Omron G2R-2       | Power  | DPDT     | 5 A    | 5 V  | `LogicLevelRelayDPDT5A5V`  |
| Omron G2R-2       | Power  | DPDT     | 5 A    | 12 V | `LogicLevelRelayDPDT5A12V` |
| Omron G2R-2       | Power  | DPDT     | 5 A    | 24 V | `LogicLevelRelayDPDT5A24V` |
| HF115F            | Power  | DPDT     | 8 A    | 5 V  | `LogicLevelRelayDPDT8A5V`  |
| HF115F            | Power  | DPDT     | 8 A    | 12 V | `LogicLevelRelayDPDT8A12V` |
| HF115F            | Power  | DPDT     | 8 A    | 24 V | `LogicLevelRelayDPDT8A24V` |
| Omron G5V-1       | Signal | SPDT     | 1 A    | 3 V  | `LogicLevelRelaySPDT1A3V`  |
| Omron G5V-1       | Signal | SPDT     | 1 A    | 5 V  | `LogicLevelRelaySPDT1A5V`  |
| Omron G5V-1       | Signal | SPDT     | 1 A    | 12 V | `LogicLevelRelaySPDT1A12V` |
| Omron G5V-1       | Signal | SPDT     | 1 A    | 24 V | `LogicLevelRelaySPDT1A24V` |
| Omron G6K-2F-Y-TR | Signal | DPDT     | 1 A    | 3 V  | `LogicLevelRelayDPDT1A3V`  |
| Omron G6K-2F-Y-TR | Signal | DPDT     | 1 A    | 5 V  | `LogicLevelRelayDPDT1A5V`  |
| Omron G6K-2F-Y-TR | Signal | DPDT     | 1 A    | 12 V | `LogicLevelRelayDPDT1A12V` |
| Omron G6K-2F-Y-TR | Signal | DPDT     | 1 A    | 24 V | `LogicLevelRelayDPDT1A24V` |

Each series includes atomic parts and wrappers exposing typed interfaces (`RelaySPDT` / `RelayDPDT`) and logic-level driver modules for simple enable and coil-power control (with an indicator LED).

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import ElectricLogic
import Electrical

from "relays.ato" import LogicLevelRelaySPDT3A12V, LogicLevelRelayDPDT5A5V, LogicLevelRelayDPDT1A3V


module Usage:
    """
    Minimal usage example showcasing three relay series:
    - HK4100F SPDT 3A 12V
    - G2R-2 DPDT 5A 5V
    - G6K-2F-Y-TR DPDT 1A 3V
    """

    # Rails
    power_12v = new ElectricPower
    power_5v = new ElectricPower
    power_3v3 = new ElectricPower

    # Enables (one per relay)
    enables = new ElectricLogic[3]

    # Relays
    relay_SPDT_3A_12V = new LogicLevelRelaySPDT3A12V
    relay_DPDT_5A_5V = new LogicLevelRelayDPDT5A5V
    relay_DPDT_1A_3V = new LogicLevelRelayDPDT1A3V

    # Power connections
    power_12v ~ relay_SPDT_3A_12V.coil_power
    power_5v ~ relay_DPDT_5A_5V.coil_power
    power_3v3 ~ relay_DPDT_1A_3V.coil_power

    # Enable references and wiring
    for enable in enables:
        enable.reference ~ power_3v3

    # Power for coils
    relay_SPDT_3A_12V.coil_power ~ power_12v
    relay_DPDT_5A_5V.coil_power ~ power_5v
    relay_DPDT_1A_3V.coil_power ~ power_3v3

    # Enable for relays
    enables[0] ~ relay_SPDT_3A_12V.enable
    enables[1] ~ relay_DPDT_5A_5V.enable
    enables[2] ~ relay_DPDT_1A_3V.enable

    # Connecting signal through relay

    # Electrical
    input_electrical = new Electrical
    output_electrical = new Electrical
    input_electrical ~> relay_SPDT_3A_12V.relay.switch_no ~> output_electrical

    # Logic
    input_logics = new ElectricLogic[2]
    output_logic = new ElectricLogic[2]
    input_logics[0].line ~> relay_DPDT_1A_3V.relay.switch_no[0] ~> output_logic[0].line
    input_logics[1].line ~> relay_DPDT_1A_3V.relay.switch_no[1] ~> output_logic[1].line

    # Power - normally open, switching both vcc and gnd
    input_power = new ElectricPower
    output_power = new ElectricPower
    input_power.vcc ~> relay_DPDT_5A_5V.relay.switch_no[0] ~> output_power.vcc
    input_power.gnd ~> relay_DPDT_5A_5V.relay.switch_no[1] ~> output_power.gnd
```

## Builds

- Logic-level examples for each series are available in `ato.yaml` under the `builds` section.
- A `usage` build target is provided to render the example above.

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
