# ADI ADBMS6822 Dual isoSPI Transceiver

The ADI ADBMS6822 is a dual isoSPI transceiver IC designed for isolated SPI communication in battery management systems and other high-voltage applications. This package provides a complete driver module with configurable SPI modes, power management, and dual differential isoSPI interfaces.

For a guide on getting started with this transceiver checkout: https://blog.atopile.io/p/getting-started-with-adbms6830

## Key Features

- Dual SPI interfaces (configurable as controller or peripheral)
- Dual isoSPI differential interfaces for isolated communication
- Multiple power rails with wide voltage ranges (1.7V-30V depending on rail)
- Configurable SPI clock phase/polarity, transceiver modes, and timeout settings
- Low Power Communication Mode (LPCM) with wake-up and interrupt signaling
- Built-in bypass capacitors and power decoupling

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")
#pragma experiment("TRAITS")

import DifferentialPair
import ElectricPower
import Resistor
import has_part_removed

from "atopile/pjrc-teensy-4-1/pjrc-teensy_4_1.ato" import PJRC_Teensy_4_1

module TeensyWithoutPart from PJRC_Teensy_4_1:
    """Teensy 4.1 module without a physical part for usage examples."""
    trait has_part_removed
from "atopile/usb-connectors/usb-connectors.ato" import USBCConn
from "atopile/saleae-header/saleae-header.ato" import SaleaeHeaderRightAngle_2
from "atopile/adi-adbms6822/adi-adbms6822.ato" import ADI_ADBMS6822
from "atopile/adi-adbms6830/usage.ato" import StackableBMBInterface
from "atopile/ti-dac6578/ti-dac6578.ato" import TI_DAC6578
from "atopile/indicator-leds/indicator-leds.ato" import LEDIndicatorBlue
from "atopile/indicator-leds/indicator-leds.ato" import LEDIndicatorGreen
from "atopile/diodes-inc-74lvc1t45dw-7/diodes-inc-74lvc1t45dw-7.ato" import Diodes_Inc_74LVC1T45DW_7
from "atopile/ti-ads1115/ti-ads1115.ato" import TI_ADS1115

from "parts/Nextron_Z_231012820106/Nextron_Z_231012820106.ato" import Nextron_Z_231012820106_package
from "parts/DIBO_DB125_3_81_2P_BK_S/DIBO_DB125_3_81_2P_BK_S.ato" import DIBO_DB125_3_81_2P_BK_S_package
from "parts/XKB_Connectivity_SK_3245S_L1_B/XKB_Connectivity_SK_3245S_L1_B.ato" import XKB_Connectivity_SK_3245S_L1_B_package



module Usage:
    teensy = new TeensyWithoutPart
    adbms6822 = new ADI_ADBMS6822
    usb_c_connector = new USBCConn
    gpio_dac = new TI_DAC6578
    sbi = new StackableBMBInterface
    adcs = new TI_ADS1115[2]

    # --- External Interfaces ---
    power_5v = new ElectricPower
    """
    Main power rail for the Teensy.
    """

    power_3v3 = new ElectricPower
    """
    Logic level power rail, supplied by teensy onboard LDO
    """

    stack_power = new ElectricPower
    cells = new ElectricPower[16]
    # adbms6822.isospi_ports[0]
    # adbms6822.isospi_ports[1]

    # --- Power Connections ---
    power_5v ~ usb_c_connector.usb2.usb_if.buspower
    adbms6822.vp_power ~ power_5v
    adbms6822.vdd_iso_spi_power ~ power_3v3
    adbms6822.vdds_spi_power ~ power_3v3
    gpio_dac.power ~ power_3v3
    gpio_dac.vref ~ power_3v3.hv

    teensy.power ~ power_5v
    teensy.power_3v3 ~ power_3v3
    stack_power.lv ~ power_3v3.lv
    adcs[0].power ~ power_5v
    adcs[1].power ~ power_5v

    # --- Comms Connections ---
    teensy.spi[0] ~ adbms6822.spi[0]
    teensy.chip_select[0] ~ adbms6822.spi_cs[0]
    teensy.spi[1] ~ adbms6822.spi[1]
    teensy.chip_select[1] ~ adbms6822.spi_cs[1]
    teensy.usb_device ~ usb_c_connector.usb2
    teensy.i2c[0] ~ adcs[0].i2c
    teensy.i2c[0] ~ adcs[1].i2c

    # --- I2C Pullups ---
    # I2C pullups are provided by the TI DAC6578 module (4.7kohm +/- 1%)
    # Adding explicit pullups to satisfy design checks
    i2c_pullups = new Resistor[2]
    for pullup in i2c_pullups:
        pullup.resistance = 4.7kohm +/- 1%
        pullup.package = "0402"

    teensy.i2c[0].scl.line ~> i2c_pullups[0] ~> power_3v3.hv
    teensy.i2c[0].sda.line ~> i2c_pullups[1] ~> power_3v3.hv

    # --- I2C Addresses ---
    adcs[0].i2c.address = 0x48
    adcs[1].i2c.address = 0x49


    # --- GPIO DAC Connections ---
    gpio_dac.i2c ~ teensy.i2c[0]
    gpio_dac.clear_n ~ teensy.gpio[2]
    gpio_dac.ldac_n ~ teensy.gpio[3]

    gpio_dac.outputs[0] ~ sbi.signals_up.10
    gpio_dac.outputs[1] ~ sbi.signals_up.11
    gpio_dac.outputs[2] ~ sbi.signals_up.12
    gpio_dac.outputs[3] ~ sbi.signals_up.13
    gpio_dac.outputs[4] ~ sbi.signals_up.14
    gpio_dac.outputs[5] ~ sbi.signals_up.15
    gpio_dac.outputs[6] ~ sbi.signals_up.16
    gpio_dac.outputs[7] ~ sbi.signals_up.17

    # --- LED Connections ---
    led_blue = new LEDIndicatorBlue
    led_blue.current = 0.5mA to 1mA
    power_5v.hv ~> led_blue ~> power_5v.lv
    led_green = new LEDIndicatorGreen
    led_green.current = 0.5mA to 1mA
    power_3v3.hv ~> led_green ~> power_3v3.lv

    # --- Saleae Debug Header Connections ---
    saleae_spi_interface = new SaleaeHeaderRightAngle_2

    # Spi 0
    saleae_spi_interface.headers[0].spi ~ adbms6822.spi[0]
    saleae_spi_interface.headers[0].spi_cs ~ adbms6822.spi_cs[0]

    # Spi 1
    saleae_spi_interface.headers[1].spi ~ adbms6822.spi[1]
    saleae_spi_interface.headers[1].spi_cs ~ adbms6822.spi_cs[1]

    # External isoSPI connectors
    external_isoSPI_connectors = new DIBO_DB125_3_81_2P_BK_S_package[2]
    external_isoSPI_connectors[0].1 ~ adbms6822.isospi_ports[0].p.line
    external_isoSPI_connectors[0].2 ~ adbms6822.isospi_ports[0].n.line
    external_isoSPI_connectors[1].1 ~ adbms6822.isospi_ports[1].p.line
    external_isoSPI_connectors[1].2 ~ adbms6822.isospi_ports[1].n.line
    adbms6822.isospi_ports[0].p.line.override_net_name = "ISO0_P"
    adbms6822.isospi_ports[0].n.line.override_net_name = "ISO0_N"
    adbms6822.isospi_ports[1].p.line.override_net_name = "ISO1_P"
    adbms6822.isospi_ports[1].n.line.override_net_name = "ISO1_N"

    # IDC Cellsim connector
    sbi.isoSPI_up ~ adbms6822.isospi_ports[0]
    sbi.isoSPI_down ~ adbms6822.isospi_ports[1]
    sbi.isoSPI_passthru ~ adbms6822.isospi_ports[1]

    # --- ADC Connections ---
    sbi.signals_up.6 ~ adcs[0].inputs[0].line # ADBMS6830 VREG
    sbi.signals_up.7 ~ adcs[0].inputs[1].line # ADBMS6830 VREF2
    sbi.signals_up.8 ~ adcs[0].inputs[2].line # ADBMS6830 ISOMD
    sbi.signals_up.9 ~ adcs[0].inputs[3].line # ADBMS6830 VREG_DRIVE

    sbi.signals_up.10 ~ adcs[1].inputs[0].line # ADBMS6830 GPIO0
    sbi.signals_up.11 ~ adcs[1].inputs[1].line # ADBMS6830 GPIO1
    sbi.signals_up.12 ~ adcs[1].inputs[2].line # ADBMS6830 GPIO2
    sbi.signals_up.13 ~ adcs[1].inputs[3].line # ADBMS6830 GPIO3

    cellsim_connector = new Nextron_Z_231012820106_package
    stack_power.lv ~ cellsim_connector.19
    cells[0].lv ~ cellsim_connector.18
    cells[0].hv ~ cellsim_connector.17
    cells[1].lv ~ cellsim_connector.17
    cells[1].hv ~ cellsim_connector.16
    cells[2].lv ~ cellsim_connector.16
    cells[2].hv ~ cellsim_connector.15
    cells[3].lv ~ cellsim_connector.15
    cells[3].hv ~ cellsim_connector.14
    cells[4].lv ~ cellsim_connector.14
    cells[4].hv ~ cellsim_connector.13
    cells[5].lv ~ cellsim_connector.13
    cells[5].hv ~ cellsim_connector.12
    cells[6].lv ~ cellsim_connector.12
    cells[6].hv ~ cellsim_connector.11
    cells[7].lv ~ cellsim_connector.11
    cells[7].hv ~ cellsim_connector.10
    cells[8].lv ~ cellsim_connector.10
    cells[8].hv ~ cellsim_connector.9
    cells[9].lv ~ cellsim_connector.9
    cells[9].hv ~ cellsim_connector.8
    cells[10].lv ~ cellsim_connector.8
    cells[10].hv ~ cellsim_connector.7
    cells[11].lv ~ cellsim_connector.7
    cells[11].hv ~ cellsim_connector.6
    cells[12].lv ~ cellsim_connector.6
    cells[12].hv ~ cellsim_connector.5
    cells[13].lv ~ cellsim_connector.5
    cells[13].hv ~ cellsim_connector.4
    cells[14].lv ~ cellsim_connector.4
    cells[14].hv ~ cellsim_connector.3
    cells[15].lv ~ cellsim_connector.3
    cells[15].hv ~ cellsim_connector.2
    stack_power.hv ~ cellsim_connector.1


    stack_power.lv ~ sbi.cell_power_down.1
    cells[0].lv ~ sbi.cell_power_down.2
    cells[0].hv ~ sbi.cell_power_down.3
    cells[1].lv ~ sbi.cell_power_down.3
    cells[1].hv ~ sbi.cell_power_down.4
    cells[2].lv ~ sbi.cell_power_down.4
    cells[2].hv ~ sbi.cell_power_down.5
    cells[3].lv ~ sbi.cell_power_down.5
    cells[3].hv ~ sbi.cell_power_down.6
    cells[4].lv ~ sbi.cell_power_down.6
    cells[4].hv ~ sbi.cell_power_down.7
    cells[5].lv ~ sbi.cell_power_down.7
    cells[5].hv ~ sbi.cell_power_down.8
    cells[6].lv ~ sbi.cell_power_down.8
    cells[6].hv ~ sbi.cell_power_down.9
    cells[7].lv ~ sbi.cell_power_down.9
    cells[7].hv ~ sbi.cell_power_down.10
    cells[8].lv ~ sbi.cell_power_down.10
    cells[8].hv ~ sbi.cell_power_down.11
    cells[9].lv ~ sbi.cell_power_down.11
    cells[9].hv ~ sbi.cell_power_down.12
    cells[10].lv ~ sbi.cell_power_down.12
    cells[10].hv ~ sbi.cell_power_down.13
    cells[11].lv ~ sbi.cell_power_down.13
    cells[11].hv ~ sbi.cell_power_down.14
    cells[12].lv ~ sbi.cell_power_down.14
    cells[12].hv ~ sbi.cell_power_down.15
    cells[13].lv ~ sbi.cell_power_down.15
    cells[13].hv ~ sbi.cell_power_down.16
    cells[14].lv ~ sbi.cell_power_down.16
    cells[14].hv ~ sbi.cell_power_down.17
    cells[15].lv ~ sbi.cell_power_down.17
    cells[15].hv ~ sbi.cell_power_down.18
    stack_power.hv ~ sbi.cell_power_down.30

    stack_power.lv ~ sbi.cell_sense_down.1
    cells[0].lv ~ sbi.cell_sense_down.2
    cells[0].hv ~ sbi.cell_sense_down.3
    cells[1].lv ~ sbi.cell_sense_down.3
    cells[1].hv ~ sbi.cell_sense_down.4
    cells[2].lv ~ sbi.cell_sense_down.4
    cells[2].hv ~ sbi.cell_sense_down.5
    cells[3].lv ~ sbi.cell_sense_down.5
    cells[3].hv ~ sbi.cell_sense_down.6
    cells[4].lv ~ sbi.cell_sense_down.6
    cells[4].hv ~ sbi.cell_sense_down.7
    cells[5].lv ~ sbi.cell_sense_down.7
    cells[5].hv ~ sbi.cell_sense_down.8
    cells[6].lv ~ sbi.cell_sense_down.8
    cells[6].hv ~ sbi.cell_sense_down.9
    cells[7].lv ~ sbi.cell_sense_down.9
    cells[7].hv ~ sbi.cell_sense_down.10
    cells[8].lv ~ sbi.cell_sense_down.10
    cells[8].hv ~ sbi.cell_sense_down.11
    cells[9].lv ~ sbi.cell_sense_down.11
    cells[9].hv ~ sbi.cell_sense_down.12
    cells[10].lv ~ sbi.cell_sense_down.12
    cells[10].hv ~ sbi.cell_sense_down.13
    cells[11].lv ~ sbi.cell_sense_down.13
    cells[11].hv ~ sbi.cell_sense_down.14
    cells[12].lv ~ sbi.cell_sense_down.14
    cells[12].hv ~ sbi.cell_sense_down.15
    cells[13].lv ~ sbi.cell_sense_down.15
    cells[13].hv ~ sbi.cell_sense_down.16
    cells[14].lv ~ sbi.cell_sense_down.16
    cells[14].hv ~ sbi.cell_sense_down.17
    cells[15].lv ~ sbi.cell_sense_down.17
    cells[15].hv ~ sbi.cell_sense_down.18
    stack_power.hv ~ sbi.cell_sense_down.30

    cells[0].lv.override_net_name = "CELL0"
    cells[0].hv.override_net_name = "CELL1"
    cells[1].hv.override_net_name = "CELL2"
    cells[2].hv.override_net_name = "CELL3"
    cells[3].hv.override_net_name = "CELL4"
    cells[4].hv.override_net_name = "CELL5"
    cells[5].hv.override_net_name = "CELL6"
    cells[6].hv.override_net_name = "CELL7"
    cells[7].hv.override_net_name = "CELL8"
    cells[8].hv.override_net_name = "CELL9"
    cells[9].hv.override_net_name = "CELL10"
    cells[10].hv.override_net_name = "CELL11"
    cells[11].hv.override_net_name = "CELL12"
    cells[12].hv.override_net_name = "CELL13"
    cells[13].hv.override_net_name = "CELL14"
    cells[14].hv.override_net_name = "CELL15"
    cells[15].hv.override_net_name = "CELL16"
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
