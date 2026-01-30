# Banana Plugs

Atopile driver for various banana plugs.
The simple banana plugs are a bit smaller in size and don't support the safety plugs.
The premium banana plugs are a bit larger in size and support the safety plugs.

## Usage

```ato
#pragma experiment("FOR_LOOP")

# --- Standard library imports ---
import ElectricPower

# --- Package import ---
from "atopile/banana-plugs/banana-plugs.ato" import SimpleBananaPlugPower
from "atopile/banana-plugs/banana-plugs.ato" import PremiumBananaPlugPower

from "atopile/banana-plugs/banana-plugs.ato" import SimpleBananaPlugBlack
from "atopile/banana-plugs/banana-plugs.ato" import SimpleBananaPlugRed
from "atopile/banana-plugs/banana-plugs.ato" import SimpleBananaPlugYellow
from "atopile/banana-plugs/banana-plugs.ato" import SimpleBananaPlugGreen
from "atopile/banana-plugs/banana-plugs.ato" import SimpleBananaPlugBlue
from "atopile/banana-plugs/banana-plugs.ato" import PremiumBananaPlugBlack
from "atopile/banana-plugs/banana-plugs.ato" import PremiumBananaPlugRed

module Usage:
    """
    Minimal usage example for `banana-plugs`.
    """

    # Standard spacing (3/4inch (19.05mm)) with power
    power_rail = new ElectricPower

    simple_banana_plug_power = new SimpleBananaPlugPower
    premium_banana_plug_power = new PremiumBananaPlugPower

    simple_banana_plug_power.power ~ power_rail
    premium_banana_plug_power.power ~ power_rail

    # seperate connectors
    simple_banana_plug_black = new SimpleBananaPlugBlack
    simple_banana_plug_red = new SimpleBananaPlugRed
    simple_banana_plug_yellow = new SimpleBananaPlugYellow
    simple_banana_plug_green = new SimpleBananaPlugGreen
    simple_banana_plug_blue = new SimpleBananaPlugBlue
    premium_banana_plug_black = new PremiumBananaPlugBlack
    premium_banana_plug_red = new PremiumBananaPlugRed

    for plug in [simple_banana_plug_black, simple_banana_plug_red, simple_banana_plug_yellow, simple_banana_plug_green, simple_banana_plug_blue, premium_banana_plug_black, premium_banana_plug_red]:
        plug.contact ~ power_rail.hv

```

## Contributing

Contributions are welcome! Please open an issue or pull request and ensure the `usage` build target passes (`ato build usage`).

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
