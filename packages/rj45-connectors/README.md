# RJ45 Ethernet Connectors

A collection of RJ45 (8P8C) Ethernet connectors for different mounting styles and applications.

This package includes:

- **Vertical SMD connector** (HCTL HC-RJ45-055-7) - Compact surface-mount design without magnetics
- **Horizontal through-hole connector with magnetics** (HANRUN HR911130A) - Through-hole design with integrated transformers and LED support

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")
#pragma experiment("TRAITS")

import Ethernet, ElectricPower, ElectricLogic, Electrical

from "rj45-connectors.ato" import RJ45_Vertical_SMD, RJ45_Horizontal_TH_Magnetics

module Usage:
    """
    Usage examples for RJ45 connectors package.

    Shows how to use both the vertical SMD connector (without magnetics)
    and the horizontal through-hole connector (with integrated magnetics).
    """

    # --- Power supply for logic references ---
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.3V +/- 5%

    # --- Example 1: Vertical SMD connector (no magnetics) ---
    rj45_vertical = new RJ45_Vertical_SMD

    # Connect Ethernet interface power reference
    rj45_vertical.ethernet.led_link.reference ~ power_3v3
    rj45_vertical.ethernet.led_speed.reference ~ power_3v3

    # Connect shield to ground
    rj45_vertical.shield ~ power_3v3.lv

    # --- Example 2: Horizontal TH connector with magnetics ---
    rj45_horizontal = new RJ45_Horizontal_TH_Magnetics

    # Connect Ethernet interface power reference
    rj45_horizontal.ethernet.led_link.reference ~ power_3v3
    rj45_horizontal.ethernet.led_speed.reference ~ power_3v3

    # Connect shield to ground
    rj45_horizontal.shield ~ power_3v3.lv

    # --- Example connections to external circuits ---
    # For the magnetics connector, you can connect directly to an Ethernet PHY:
    # phy.ethernet ~ rj45_horizontal.ethernet
    # For the vertical SMD, you would typically need external transformers
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
