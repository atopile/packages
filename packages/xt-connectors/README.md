# XT Connectors (XT30 series)

Atopile package providing XT30 power connectors in common variants: male/female and right‑angle/vertical. Useful for battery and high‑current power connections.

## Usage

```ato
import ElectricPower

from "atopile/xt-connectors/xt-connectors.ato" import XT30_Male_Right_Angle
from "atopile/xt-connectors/xt-connectors.ato" import XT30_Male_Vertical
from "atopile/xt-connectors/xt-connectors.ato" import XT30_Female_Right_Angle
from "atopile/xt-connectors/xt-connectors.ato" import XT30_Female_Vertical

module Usage:
    """Test module for XT30 connectors"""
    right_angle_male = new XT30_Male_Right_Angle
    vertical_male = new XT30_Male_Vertical
    right_angle_female = new XT30_Female_Right_Angle
    vertical_female = new XT30_Female_Vertical

    # Connect power together
    power = new ElectricPower
    power ~ right_angle_male.power
    power ~ vertical_male.power
    power ~ right_angle_female.power
    power ~ vertical_female.power
```

## Contributing

Contributions are welcome! Please open an issue or pull request, and ensure the `usage` build target passes (`ato build usage`).

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
