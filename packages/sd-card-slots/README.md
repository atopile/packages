# SD Card Slots

Atopile package for SD and microSD card slots with SPI and SD Bus interfaces.

## Assembly Picker

| Assembly | Form Factor | Transport | Default Slot Component |
|---|---|---|---|
| `MicroSD_SPI` | microSD | SPI | Korean Hroparts TF-01A |
| `MicroSD_SDBus` | microSD | SD Bus (4-bit) | Korean Hroparts TF-01A |
| `FullSD_SPI` | Full SD | SPI | XUNPU SD-102 |
| `FullSD_SDBus` | Full SD | SD Bus (4-bit) | XUNPU SD-102 |

## Quick Start - SPI Mode

```ato
from "atopile/sd-card-slots/sd-card-slots.ato" import MicroSD_SPI

module MyProject:
    sd_card = new MicroSD_SPI

    # Connect to host
    sd_card.spi ~ mcu.spi
    sd_card.spi_cs ~ mcu.spi_cs
    sd_card.power ~ mcu.power
```

## Quick Start - SD Bus Mode

```ato
from "atopile/sd-card-slots/sd-card-slots.ato" import MicroSD_SDBus

module MyProject:
    sd_card = new MicroSD_SDBus

    # Connect to host
    sd_card.data[0] ~ mcu.sdmmc_data[0]
    sd_card.data[1] ~ mcu.sdmmc_data[1]
    sd_card.data[2] ~ mcu.sdmmc_data[2]
    sd_card.data[3] ~ mcu.sdmmc_data[3]
    sd_card.cmd ~ mcu.sdmmc_cmd
    sd_card.clk ~ mcu.sdmmc_clk
    sd_card.power ~ mcu.power
```

## Swap the Slot Component

Any assembly's slot can be swapped to a different physical connector:

```ato
from "atopile/sd-card-slots/sd-card-slots.ato" import MicroSD_SPI
from "atopile/sd-card-slots/parts/SOFNG_SD_006M/SOFNG_SD_006M.ato" import SOFNG_SD_006M_model

module MyProject:
    sd_card = new MicroSD_SPI
    sd_card.slot -> SOFNG_SD_006M_model
```

## SPI Assembly Interface

Applies to: `MicroSD_SPI`, `FullSD_SPI`

| Signal | Type | Description |
|---|---|---|
| `spi` | SPI | SPI bus (MISO, MOSI, SCLK) |
| `spi_cs` | ElectricLogic | Chip select |
| `power` | ElectricPower | 3.3V supply (asserted 3.3V +/- 5%) |
| `card_detect` | ElectricLogic | Card detection |
| `write_protect` | ElectricLogic | Write protection |

Included passives: 100nF VDD bypass cap, 10k pull-ups on MISO, MOSI, SCLK.

## SD Bus Assembly Interface

Applies to: `MicroSD_SDBus`, `FullSD_SDBus`

| Signal | Type | Description |
|---|---|---|
| `data[0:3]` | ElectricLogic[4] | 4-bit data bus |
| `cmd` | ElectricLogic | Command line |
| `clk` | ElectricLogic | Clock line |
| `power` | ElectricPower | 3.3V supply (asserted 3.3V +/- 5%) |
| `card_detect` | ElectricLogic | Card detection |
| `write_protect` | ElectricLogic | Write protection |

Included passives: 100nF VDD bypass cap, 10k pull-ups on CMD and DAT[0:3].

## Architecture

The package is layered so each axis of the SD card design space can be independently swapped:

```
pins.ato         Physical contact pin definitions (per standard)
logic.ato        Typed electrical bus interfaces (per bus mode)
sd-card-slots.ato    Slots + drivers + transports + assemblies
```

### Layer overview

| Layer | What it represents | Swap to change... |
|---|---|---|
| **Pins** (`SDCardPinsSS`, `...UHSII`, `...Express1Lane`, `...Express2Lane`) | Which physical contacts exist on the connector | Pin standard |
| **Logic** (`SDLogicSDBus`, `...UHSII`, `...Express1Lane`, `...Express2Lane`) | Typed bus signals with voltage constraints | Bus protocol |
| **Slot** (`SDSlotMicroSS`, `SDSlotFullSS`, `...UHSII`, `...Express`) | Form factor + pin interface | Slot shape |
| **Driver** (`SDSlotDriverSS`) | Pin-to-logic wiring + bypass caps | Driver circuitry |
| **Transport** (`SDTransportSPI`, `SDTransportSDBus`) | Host-side protocol mapping + passives | Host interface |
| **Assembly** (`MicroSD_SPI`, `MicroSD_SDBus`, `FullSD_SPI`, `FullSD_SDBus`) | User-facing module combining all layers | Everything |

### How the layers compose

```
MicroSD_SPI (user-facing)
  ├── slot: SDSlotMicroSS          Form factor + pin interface
  │     └── card_pins: SDCardPinsSS    9 standard contacts
  ├── driver: SDSlotDriverSS       Pin-to-logic mapping + 100nF bypass
  │     ├── card_pins ← slot.card_pins
  │     └── sd: SDLogicSDBus       Typed bus signals
  └── transport: SDTransportSPI    SPI mapping + 3x 10k pull-ups
        ├── sd ← driver.sd
        ├── spi ← exposed
        └── spi_cs ← exposed
```

## Included Slot Components

| Component | Form Factor | Type | LCSC |
|---|---|---|---|
| Korean Hroparts TF-01A | microSD | Push-pull | C91145 |
| SOFNG SD-006M | microSD | Push-push | C125615 |
| XUNPU SD-102 | Full SD | Push-pull | C266602 |

## Adding a New Slot Component

1. Create the part in `parts/<MANUFACTURER_PART>/` using `ato create part`
2. Import the appropriate slot base and map the footprint pins:

```ato
from "atopile/sd-card-slots/pins.ato" import SDSlotMicroSS

module My_New_Slot_model from SDSlotMicroSS:
    package = new My_New_Slot_package

    card_pins.CD_DAT3 ~ package.CS
    card_pins.CMD ~ package.DI
    card_pins.VSS1 ~ package.GND
    card_pins.VDD ~ package.VDD
    card_pins.CLK ~ package.SCLK
    card_pins.VSS2 ~ package.GND
    card_pins.DAT0 ~ package.DO
    card_pins.DAT1 ~ package.DAT1
    card_pins.DAT2 ~ package.DAT2
    card_pins.CD ~ package.CD
```

3. Use it: `sd_card.slot -> My_New_Slot_model`

## Contributing

Contributions welcome via pull requests on the [GitHub repository](https://github.com/atopile/packages).

## License

[MIT License](https://opensource.org/license/mit/)
