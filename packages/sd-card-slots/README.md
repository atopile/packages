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

```atoxx
from "atopile/sd-card-slots/sd-card-slots.ato" import MicroSD_SPI
from "atopile/sd-card-slots/sd-card-slots.ato" import FullSD_SPI
from "atopile/sd-card-slots/parts/SOFNG_SD_006M/SOFNG_SD_006M.ato" import SOFNG_SD_006M_model
from "atopile/espressif-esp32-s3/espressif-esp32-s3.ato" import Espressif_ESP32_S3

module Usage:
    mcu = new Espressif_ESP32_S3

    # MicroSD slot via SPI (default slot: Korean Hroparts TF-01A)
    micro_sd = new MicroSD_SPI
    micro_sd.spi ~ mcu.spi
    micro_sd.spi_cs ~ mcu.spi_cs
    micro_sd.power ~ mcu.power

    # MicroSD slot via SPI with SOFNG SD-006M push-push slot
    micro_sd_alt = new MicroSD_SPI
    micro_sd_alt.slot -> SOFNG_SD_006M_model
    micro_sd_alt.power ~ mcu.power

    # Full-size SD slot via SPI (default slot: XUNPU SD-102)
    full_sd = new FullSD_SPI
    full_sd.power ~ mcu.power

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
from "atopile/sd-card-slots/sd-card-slots.ato" import MicroSD_SPI
from "atopile/sd-card-slots/sd-card-slots.ato" import MicroSD_SDBus
from "atopile/sd-card-slots/sd-card-slots.ato" import FullSD_SPI
from "atopile/sd-card-slots/sd-card-slots.ato" import FullSD_SDBus
from "atopile/espressif-esp32-s3/espressif-esp32-s3.ato" import Espressif_ESP32_S3

module Usage:
    mcu = new Espressif_ESP32_S3

    # MicroSD slot via SPI (default slot: Korean Hroparts TF-01A)
    micro_sd_spi = new MicroSD_SPI
    micro_sd_spi.spi ~ mcu.spi
    micro_sd_spi.spi_cs ~ mcu.spi_cs
    micro_sd_spi.power ~ mcu.power

    # MicroSD slot via SD Bus
    micro_sd_sdbus = new MicroSD_SDBus
    micro_sd_sdbus.power ~ mcu.power

    # Full-size SD slot via SPI (default slot: XUNPU SD-102)
    full_sd_spi = new FullSD_SPI
    full_sd_spi.power ~ mcu.power

    # Full-size SD slot via SD Bus
    full_sd_sdbus = new FullSD_SDBus
    full_sd_sdbus.power ~ mcu.power

```

3. Use it: `sd_card.slot -> My_New_Slot_model`

## Contributing

Contributions welcome via pull requests on the [GitHub repository](https://github.com/atopile/packages).

## License

[MIT License](https://opensource.org/license/mit/)
