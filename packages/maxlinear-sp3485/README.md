# MaxLinear SP3485 3.3V Half-Duplex RS-485 Transceiver

Low-power, 10 Mbps RS-485/RS-422 half-duplex transceiver (SP3485EN-L/TR). Exposes UART-side logic (TX, RX), driver/receiver enables (DE, RE), and the RS-485 A/B differential bus. Designed for a 3.3 V supply.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import ElectricLogic
import DifferentialPair

from "atopile/maxlinear-sp3485/maxlinear-sp3485.ato" import MaxLinear_SP3485
from "atopile/validation-pogo/validation-pogo.ato" import DUTPogoPoint
from "atopile/validation-pogo/validation-pogo.ato" import DUTDatumHole
from "atopile/validation-pogo/validation-pogo.ato" import DUTMountingHole
from "atopile/logos/logos.ato" import atopile_logo_4x4mm


module Usage:
  """
  Minimal usage example for MaxLinear SP3485 (RS-485 transceiver).
  Connects a 3.3V rail, MCU UART lines, enables, and the RS-485 bus.
  """

  transceiver = new MaxLinear_SP3485

  # Power (3.3V)
  power_3v3 = new ElectricPower
  power_3v3.required = True
  assert power_3v3.voltage within 3.3V +/- 10%
  power_3v3 ~ transceiver.power

  # MCU-side UART and control signals
  mcu_tx = new ElectricLogic
  mcu_rx = new ElectricLogic
  ctrl_de = new ElectricLogic
  ctrl_re_n = new ElectricLogic

  mcu_tx.reference ~ power_3v3
  mcu_rx.reference ~ power_3v3
  ctrl_de.reference ~ power_3v3
  ctrl_re_n.reference ~ power_3v3

  mcu_tx ~ transceiver.uart_tx
  mcu_rx ~ transceiver.uart_rx
  ctrl_de ~ transceiver.driver_enable
  ctrl_re_n ~ transceiver.n_receiver_enable

  # RS-485 bus
  rs485_bus = new DifferentialPair
  rs485_bus ~ transceiver.rs485_bus

  # Test points
  pogos = new DUTPogoPoint[8]
  # Power rails
  pogos[0].net ~ power_3v3.hv
  pogos[1].net ~ power_3v3.lv
  # MCU-side UART and control
  pogos[2].net ~ mcu_tx.line
  pogos[3].net ~ mcu_rx.line
  pogos[4].net ~ ctrl_de.line
  pogos[5].net ~ ctrl_re_n.line
  # RS-485 differential bus
  pogos[6].net ~ rs485_bus.p.line
  pogos[7].net ~ rs485_bus.n.line

  M3_mounting_holes = new DUTMountingHole[4]
  datum_holes = new DUTDatumHole[2]

  logo = new atopile_logo_4x4mm
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the MIT License.
