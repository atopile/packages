# ST STM32F072 Black Magic Probe

Embeddable Black Magic Probe (BMP) debug probe based on the STM32F072CBT6. Provides a built-in GDB server over USB -- no OpenOCD or other debug software required.

Two modules are provided:

- **`BMP_STM32F072`** (core): The probe circuit without connectors. Embed directly into your design.
- **`Usage`** (example): Core + USB-C connector + LDO + 10-pin ARM Cortex debug header. Standalone probe.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")
#pragma experiment("TRAITS")

import ElectricPower
import SWD

from "atopile/st-stm32f072-bmp/st-stm32f072-bmp.ato" import BMP_STM32F072

module MyDesign:
    # Instantiate BMP core (provide your own 3.3V and USB connection)
    bmp = new BMP_STM32F072

    # Connect 3.3V power
    power_3v3 = new ElectricPower
    power_3v3 ~ bmp.power_3v3

    # Connect SWD to your target MCU
    bmp.swd ~ my_mcu.swd

    # Route USB to your connector or edge fingers
    bmp.usb ~ my_usb_connector.usb
```

## Firmware

Flash the [Black Magic Probe firmware](https://github.com/blackmagic-debug/blackmagic) for the `stm32f072` platform via USB DFU:

1. Hold BOOT0 high and reset the STM32F072 to enter DFU bootloader
2. Flash: `dfu-util -d 1d50:6018,:6017 -s 0x08000000:leave -D blackmagic.bin`

## Interfaces

| Interface | Description |
|-----------|-------------|
| `power_3v3` | 3.3V input supply (2.0V -- 3.6V) |
| `swd` | SWD debug output (DIO, CLK, SWO, RESET) |
| `jtag` | JTAG debug output (TDI, TMS, TCK, TDO, nRESET) |
| `uart` | Serial console to target (TX, RX) |
| `usb` | USB 2.0 FS for GDB server |

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
