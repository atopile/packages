# Texas Instruments MAX3243 3V to 5.5V Multichannel RS-232 Line Driver/Receiver

Texas Instruments MAX3243 is a 3V to 5.5V multichannel RS-232 line driver and receiver with ±15kV ESD protection. It features 3 drivers and 5 receivers, making it ideal for DE-9 DTE interface applications.

## Features

- **3 drivers and 5 receivers** - Perfect for DE-9 DTE interface
- **3V to 5.5V supply voltage** - Compatible with 3.3V and 5V systems
- **250kbps data rate** - High-speed RS-232 communication
- **±15kV ESD protection** - Robust protection for RS-232 lines
- **Auto-powerdown feature** - Automatically powers down when no valid RS-232 signal is detected
- **Low power consumption** - 300µA typical active current, 1µA standby
- **External capacitors** - Requires 4 × 1µF capacitors for charge pump operation
- **Always-active output** - ROUT5 is always enabled for ring indicator detection
- **UART pullup resistors** - Automatic pullup resistors on DTR, TXD, and RTS inputs

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import Capacitor
import ElectricLogic
import ElectricPower
import Resistor
import RS232
import UART

from "atopile/ti-max3243/ti-max3243.ato" import TI_MAX3243

from "parts/Ckmtw_D_DMR009PF_D002/Ckmtw_D_DMR009PF_D002.ato" import Ckmtw_D_DMR009PF_D002_package
from "parts/Ckmtw_D_DMR009PM_D002/Ckmtw_D_DMR009PM_D002.ato" import Ckmtw_D_DMR009PM_D002_package
from "parts/Hanbo_Electronic_HB_PH3_254112PB2GOP/Hanbo_Electronic_HB_PH3_254112PB2GOP.ato" import Hanbo_Electronic_HB_PH3_254112PB2GOP_package

module Usage:
    """
    Minimal usage example for ti-max3243.
    Shows how to connect the TI MAX3243 RS-232 transceiver to a microcontroller UART
    and external RS-232 connector.
    """

    # Power supply
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # MAX3243 transceiver
    rs232_transceiver = new TI_MAX3243
    rs232_transceiver.power ~ power_3v3

    # Microcontroller UART interface
    mcu_uart = new UART
    mcu_uart.base_uart.tx.reference ~ power_3v3
    mcu_uart.base_uart.rx.reference ~ power_3v3
    mcu_uart.rts.reference ~ power_3v3
    mcu_uart.cts.reference ~ power_3v3
    mcu_uart.dtr.reference ~ power_3v3
    mcu_uart.dsr.reference ~ power_3v3
    mcu_uart.dcd.reference ~ power_3v3
    mcu_uart.ri.reference ~ power_3v3
    mcu_uart ~ rs232_transceiver.uart

    # External RS-232 connector
    external_rs232 = new RS232
    external_rs232.reference_shim ~ power_3v3

    # Optional: Control signals (can be left floating for auto-powerdown)
    # Force ON signal (normally low for auto-powerdown)
    forceon_control = new ElectricLogic
    forceon_control.reference ~ power_3v3
    forceon_control ~ rs232_transceiver.forceon

    # Force OFF signal (normally high for normal operation)
    nforceoff_control = new ElectricLogic
    nforceoff_control.reference ~ power_3v3
    nforceoff_control ~ rs232_transceiver.nforceoff

    # Invalid signal indicator
    invalid_indicator = new ElectricLogic
    invalid_indicator.reference ~ power_3v3
    invalid_indicator ~ rs232_transceiver.ninvalid

    de9_rs232_male = new DE9RS232Male
    de9_rs232_male.rs232 ~ rs232_transceiver.rs232

    power_3v3.hv.override_net_name = "Vin"
    power_3v3.lv.override_net_name = "VGND"

module DE9RS232Female:
    package = new Ckmtw_D_DMR009PF_D002_package
    rs232 = new RS232

    package.1 ~ rs232.dcd.line
    package.2 ~ rs232.rx.line
    package.3 ~ rs232.tx.line
    package.4 ~ rs232.dtr.line
    package.5 ~ rs232.reference_shim.lv
    package.6 ~ rs232.dsr.line
    package.7 ~ rs232.rts.line
    package.8 ~ rs232.cts.line
    package.9 ~ rs232.ri.line

    package.MH1 ~ rs232.reference_shim.lv
    package.MH2 ~ rs232.reference_shim.lv


module DE9RS232Male:
    package = new Ckmtw_D_DMR009PM_D002_package
    rs232 = new RS232

    package.1 ~ rs232.dcd.line
    package.2 ~ rs232.rx.line
    package.3 ~ rs232.tx.line
    package.4 ~ rs232.dtr.line
    package.5 ~ rs232.reference_shim.lv
    package.6 ~ rs232.dsr.line
    package.7 ~ rs232.rts.line
    package.8 ~ rs232.cts.line
    package.9 ~ rs232.ri.line

    package.MH1 ~ rs232.reference_shim.lv
    package.MH2 ~ rs232.reference_shim.lv

```

## Interfaces

- **power** - Main power supply (3.0V to 5.5V)
- **uart** - UART interface for microcontroller connection
- **rs232** - RS-232 interface for external connections
- **forceon** - Force ON control signal (active high)
- **nforceoff** - Force OFF control signal (active low)
- **ninvalid** - Invalid signal indicator (active low)

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
