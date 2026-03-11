# SD Card Slots

Atopile package for SD and microSD card slots with SPI and SD Bus interfaces.

## Assembly Picker

| Assembly | Form Factor | Transport | Default Slot Component |
|---|---|---|---|
| `MicroSD_SPI` | microSD | SPI | Korean Hroparts TF-01A |
| `MicroSD_SDBus` | microSD | SD Bus (4-bit) | Korean Hroparts TF-01A |
| `FullSD_SPI` | Full SD | SPI | XUNPU SD-102 |
| `FullSD_SDBus` | Full SD | SD Bus (4-bit) | XUNPU SD-102 |

## Quick Start - SPI

```ato
from "atopile/sd-card-slots/sd-card-slots.ato" import MicroSD_SPI

module MyProject:
    sd_card = new MicroSD_SPI
    sd_card.spi ~ mcu.spi
    sd_card.spi_cs ~ mcu.spi_cs
    sd_card.power ~ mcu.power
```

## Quick Start - SD Bus

```ato
from "atopile/sd-card-slots/sd-card-slots.ato" import MicroSD_SDBus

module MyProject:
    sd_card = new MicroSD_SDBus
    sd_card.data[0] ~ mcu.gpio_0
    sd_card.data[1] ~ mcu.gpio_1
    sd_card.data[2] ~ mcu.gpio_2
    sd_card.data[3] ~ mcu.gpio_3
    sd_card.cmd ~ mcu.gpio_cmd
    sd_card.clk ~ mcu.gpio_clk
    sd_card.power ~ mcu.power
```

## Swap the Slot Component

Any assembly's slot can be swapped to a different physical connector using retype (`->`):

```ato
from "atopile/sd-card-slots/sd-card-slots.ato" import MicroSD_SPI
from "atopile/sd-card-slots/parts/SOFNG_SD_006M/SOFNG_SD_006M.ato" import SOFNG_SD_006M_model

module MyProject:
    sd_card = new MicroSD_SPI
    sd_card.slot -> SOFNG_SD_006M_model
```

## SPI Interface

Applies to: `MicroSD_SPI`, `FullSD_SPI`

| Signal | Type | Description |
|---|---|---|
| `spi` | SPI | SPI bus (MISO, MOSI, SCLK) |
| `spi_cs` | ElectricLogic | Chip select |
| `power` | ElectricPower | 3.3V supply (asserted 3.3V +/- 5%) |
| `card_detect` | ElectricLogic | Card detection |
| `write_protect` | ElectricLogic | Write protection |

Included passives: 100nF VDD bypass cap, 10k pull-ups on MISO, MOSI, SCLK.

## SD Bus Interface

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

Each assembly is composed from independent layers. The package uses composition so each axis of the design space can be swapped independently.

```
Assembly (e.g. MicroSD_SPI)
  ├── slot: SDSlotMicroSS → Korean_Hroparts_Elec_TF_01A_model
  │     └── card_pins: SDCardPinsSS       Physical contact signals
  ├── driver: SDSlotDriverSS              Pin-to-logic mapping + bypass cap
  │     ├── card_pins ← slot.card_pins
  │     └── sd: SDLogicSDBus              Typed bus signals
  └── transport: SDTransportSPI           SPI mapping + pull-up resistors
        ├── sd ← driver.sd
        ├── spi → exposed
        └── spi_cs → exposed
```

### Layers

| Layer | File | Modules | Purpose |
|---|---|---|---|
| **Pins** | `pins.ato` | `SDCardPinsSS`, `SDCardPinsUHSII`, `SDCardPinsSDExpress1Lane`, `SDCardPinsSDExpress2Lane` | Physical contact definitions per SD standard (9, 17, 19, or 27 pins) |
| **Logic** | `logic.ato` | `SDLogicSDBus`, `SDLogicUHSII`, `SDLogicSDExpress1Lane`, `SDLogicSDExpress2Lane` | Typed bus interfaces with voltage constraints per protocol |
| **Slot** | `pins.ato` | `SDSlotMicroSS`, `SDSlotFullSS`, `SDSlotMicroUHSII`, `SDSlotFullUHSII`, `SDSlotFullExpress1Lane`, `SDSlotFullExpress2Lane` | Pairs a form factor (micro/full) with a pin standard |
| **Part Model** | `parts/*/` | `Korean_Hroparts_Elec_TF_01A_model`, `XUNPU_SD_102_model`, `SOFNG_SD_006M_model` | Maps physical footprint pins to the slot's `card_pins` interface |
| **Driver** | `sd-card-slots.ato` | `SDSlotDriverSS` | Bridges pin signals to typed logic + adds bypass capacitor |
| **Transport** | `sd-card-slots.ato` | `SDTransportSPI`, `SDTransportSDBus` | Maps host protocol (SPI or SD Bus) to SD logic signals + adds pull-up resistors |
| **Assembly** | `sd-card-slots.ato` | `MicroSD_SPI`, `MicroSD_SDBus`, `FullSD_SPI`, `FullSD_SDBus` | User-facing module composing slot + driver + transport |

### How layers connect

| Connection | What it does |
|---|---|
| `slot.card_pins ~ driver.card_pins` | Routes physical contacts into the driver |
| `driver.sd ~ transport.sd` | Routes typed logic signals into the transport |
| `transport.spi ~ assembly.spi` | Exposes host-side SPI to the user |
| `driver.sd.power ~ assembly.power` | Exposes the power rail to the user |

## Included Slot Components

| Component | Form Factor | Type | LCSC |
|---|---|---|---|
| Korean Hroparts TF-01A | microSD | Push-pull | C91145 |
| SOFNG SD-006M | microSD | Push-push | C125615 |
| XUNPU SD-102 | Full SD | Push-pull | C266602 |

## Adding a New Slot Component

1. Create the part in `parts/<MANUFACTURER_PART>/` using `ato create part`
2. Import the appropriate slot base (`SDSlotMicroSS` or `SDSlotFullSS`) and create a model that maps footprint pins to `card_pins`:

```ato
from "atopile/sd-card-slots/pins.ato" import SDSlotMicroSS

module My_New_Slot_model from SDSlotMicroSS:
    package = new My_New_Slot_package
    card_pins.CD_DAT3 ~ package.CD_DAT3
    card_pins.CMD ~ package.CMD
    # ... map remaining pins
```

3. Use it: `sd_card.slot -> My_New_Slot_model`

## Contributing

Contributions welcome via pull requests on the [GitHub repository](https://github.com/atopile/packages).

## License

[MIT License](https://opensource.org/license/mit/)
