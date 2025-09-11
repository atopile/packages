# XLR Audio Connectors

A collection of XLR 3-pin connectors for professional audio applications.

This package includes:

- **Male PCB mount connector** (Neutrik NC3MAAH) - 3-pin male XLR connector for direct PCB mounting
- **Female PCB mount connector** (Neutrik NCJ6FA-H) - 3-pin female XLR connector for direct PCB mounting

Both connectors follow standard XLR audio pinout conventions:

- Pin 1: Ground/Shield
- Pin 2: Hot (positive phase)
- Pin 3: Cold (negative phase)

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")
#pragma experiment("TRAITS")

import ElectricPower, DifferentialPair, Electrical

from "xlr-connectors.ato" import XLR_Male_PC_Mount, XLR_Female_PC_Mount

module Usage:
    """
    Usage examples for XLR connectors package.

    Shows how to use both male and female PCB-mounted XLR connectors
    for balanced audio applications.
    """

    # --- Power supply for differential pair references ---
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.3V +/- 5%

    # --- Example 1: Male XLR connector ---
    xlr_male = new XLR_Male_PC_Mount

    # Connect differential pair reference to power
    xlr_male.audio.p.reference ~ power_3v3
    xlr_male.audio.n.reference ~ power_3v3

    # Connect ground to power ground
    xlr_male.ground ~ power_3v3.lv

    # --- Example 2: Female XLR connector ---
    xlr_female = new XLR_Female_PC_Mount

    # Connect differential pair reference to power
    xlr_female.audio.p.reference ~ power_3v3
    xlr_female.audio.n.reference ~ power_3v3

    # Connect ground to power ground
    xlr_female.ground ~ power_3v3.lv

    # --- Example connection: XLR cable simulation ---
    # Connect male to female to simulate an XLR cable
    xlr_male.audio ~ xlr_female.audio
    xlr_male.ground ~ xlr_female.ground

    # --- Example connections to external circuits ---
    # For audio input/output, you can connect to:
    # audio_codec.balanced_input ~ xlr_female.audio
    # audio_amplifier.balanced_output ~ xlr_male.audio
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
