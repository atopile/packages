# DL-RFM95-915M LoRa Module Atopile Package

This package provides a ready-to-use driver module and atomic part definition for the **HopeRF DL-RFM95-915M** LoRa transceiver module (LCSC `C2844473`).

## Provided files

| File | Description |
|------|-------------|
| `dl-rfm95-915m.ato` | Driver `module DL_RFM95_915M` – exposes power, SPI, chip-select, reset, 6 configurable GPIOs (DIO0-DIO5) and the RF antenna interface.  Includes decoupling capacitors and pull-up resistors on `CS` and `RESET`. |
| `parts/DL_RFM95_915M/DL_RFM95_915M.ato` | Atomic part with full pin map, LCSC link and placeholder symbol/footprint references. |

## Interfaces

* `power` – `ElectricPower` (3 V3)
* `spi` – `SPI`
* `spi_cs` – `ElectricLogic` (active-low chip-select)
* `nreset` – `ElectricLogic` (active-low reset)
* `gpios[6]` – `ElectricLogic` (DIO0…DIO5)
* `antenna` – `ElectricSignal` (RF)

## Quick usage example

```ato
from "atopile/dl-rfm95-915m/dl-rfm95-915m.ato" import DL_RFM95_915M

module MyNode:
    lora = new DL_RFM95_915M

    # Connect power (3V3 rail)
    lora.power ~ global_3v3

    # Hook up MCU SPI bus
    mcu.spi[0] ~ lora.spi
    mcu.gpios.cs0 ~ lora.spi_cs
    mcu.gpios.reset ~ lora.nreset

    # Optionally use interrupt GPIOs
    mcu.gpios[5:0] ~ lora.gpios

    # RF path to 50 Ω antenna match network
    lora.antenna ~ rf_match.antenna
```

## Footprint & symbol

The atomic part references:

* Footprint: `COMM-SMD_DL-RFM95-915M.kicad_mod`
* Symbol: `DL-RFM95-915M.kicad_sym`
* 3D Model: `DL-RFM95-915M.STEP`

These are placeholders – generate or substitute with your preferred CAD library items.

## License

MIT License © 2025 Atopile Contributors
