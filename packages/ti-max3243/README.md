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

import ElectricPower, ElectricLogic
import RS232, UART
import Resistor, Capacitor

from "ti-max3243.ato" import TI_MAX3243

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
    external_rs232.tx.reference ~ power_3v3
    external_rs232.rx.reference ~ power_3v3
    external_rs232.rts.reference ~ power_3v3
    external_rs232.cts.reference ~ power_3v3
    external_rs232.dtr.reference ~ power_3v3
    external_rs232.dsr.reference ~ power_3v3
    external_rs232.dcd.reference ~ power_3v3
    external_rs232.ri.reference ~ power_3v3
    external_rs232 ~ rs232_transceiver.rs232

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
```

## Interfaces

- **power** - Main power supply (3.0V to 5.5V)
- **uart** - UART interface for microcontroller connection
- **rs232** - RS-232 interface for external connections
- **forceon** - Force ON control signal (active high)
- **nforceoff** - Force OFF control signal (active low)
- **ninvalid** - Invalid signal indicator (active low)

## Pin Mapping

### UART Side (Logic Levels)
- **DIN1** → DTR (Data Terminal Ready)
- **DIN2** → TXD (Transmit Data)
- **DIN3** → RTS (Request To Send)
- **ROUT1** → CTS (Clear To Send)
- **ROUT2** → RI (Ring Indicator)
- **ROUT3** → DSR (Data Set Ready)
- **ROUT4** → RXD (Receive Data)
- **ROUT5** → DCD (Data Carrier Detect) - Always active

### RS-232 Side (±12V Levels)
- **RIN1** → CTS (Clear To Send)
- **RIN2** → RI (Ring Indicator)
- **RIN3** → DSR (Data Set Ready)
- **RIN4** → RXD (Receive Data)
- **RIN5** → DCD (Data Carrier Detect)
- **DOUT1** → DTR (Data Terminal Ready)
- **DOUT2** → TXD (Transmit Data)
- **DOUT3** → RTS (Request To Send)

## External Components

The package automatically includes:
- 4 × 1µF capacitors for charge pump operation
- Pullup resistors on UART inputs (DTR, TXD, RTS) for proper logic levels
- Pull-up resistor on FORCEON for always-on operation
- Pull-up resistor on nFORCEOFF for normal operation

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
