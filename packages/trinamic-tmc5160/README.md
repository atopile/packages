# Trinamic TMC5160 High-Performance Stepper Motor Driver

Advanced stepper motor controller IC with integrated MOSFET drivers, SPI interface, and comprehensive motion control features. The TMC5160 combines high-performance motor control with advanced features like stallGuard, coolStep, and dcStep for optimal motor performance.

## Features

- **Integrated MOSFET drivers**: Up to 1.4A RMS motor current (3A peak)
- **SPI interface**: High-speed communication and configuration
- **Advanced motion control**: stallGuard, coolStep, dcStep, and spreadCycle
- **Voltage supply range**: 8V to 60V motor supply, 3.0V to 5.5V logic supply
- **Microstepping**: Up to 256 microsteps per full step
- **Diagnostic outputs**: Real-time status and error reporting
- **Current sensing**: Integrated current sense for closed-loop control
- **Thermal protection**: Overtemperature protection and thermal shutdown

## Package Information

- **Manufacturer**: Trinamic Motion Control GmbH
- **Part Number**: TMC5160A-TA-T
- **JLCPCB Part**: C516354
- **Package**: TQFP-48-EP (7x7mm)
- **Operating Temperature**: -40°C to +125°C

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import Electrical
import ElectricPower
import ElectricLogic
import ElectricSignal
import SPI
import Capacitor
import Resistor
import DifferentialPair
import MOSFET
import has_part_removed

from "atopile/trinamic-tmc5160/trinamic-tmc5160.ato" import Trinamic_TMC5160
from "parts/TECH_PUBLIC_AO4882/TECH_PUBLIC_AO4882.ato" import TECH_PUBLIC_AO4882_package

module Usage:

    tmc5160 = new Trinamic_TMC5160

    # --- Power supplies ---
    power_motor = new ElectricPower
    assert power_motor.voltage within 9V to 36V  # Based on FET selection

    power_vccio = new ElectricPower
    assert power_vccio.voltage within 3.0V to 5.25V

    # --- Power Connections ---
    power_motor ~ tmc5160.power_motor
    power_motor ~ tmc5160.power_vsa
    power_vccio ~ tmc5160.power_vccio

    # --- Stepper Connections ---
    motor_a1 = new ElectricSignal
    motor_a2 = new ElectricSignal
    motor_b1 = new ElectricSignal
    motor_b2 = new ElectricSignal

    # --- Communication ---
    spi = new SPI
    chip_select = new ElectricLogic
    clk = new ElectricLogic
    refl_step = new ElectricLogic
    refr_dir = new ElectricLogic
    enca_dcin_cfg5 = new ElectricLogic
    encb_dcen_cfg4 = new ElectricLogic
    encn_dco_cfg6 = new ElectricLogic
    diag0_swn = new ElectricLogic
    drive_enable = new ElectricLogic

    spi ~ tmc5160.spi
    chip_select ~ tmc5160.chip_select
    clk ~ tmc5160.clk
    refl_step ~ tmc5160.refl_step
    refr_dir ~ tmc5160.refr_dir
    enca_dcin_cfg5 ~ tmc5160.enca_dcin_cfg5
    encb_dcen_cfg4 ~ tmc5160.encb_dcen_cfg4
    encn_dco_cfg6 ~ tmc5160.encn_dco_cfg6
    diag0_swn ~ tmc5160.diag0_swn
    drive_enable ~ tmc5160.drive_enable
    motor_a1 ~ tmc5160.motor_a_bm1
    motor_a2 ~ tmc5160.motor_a_bm2
    motor_b1 ~ tmc5160.motor_b_bm1
    motor_b2 ~ tmc5160.motor_b_bm2

    # --- External Interfaces ---
    power_vccio.hv.override_net_name = "power-vccio"
    power_vccio.lv.override_net_name = "gnd"
    chip_select.line.override_net_name = "chip-select"
    spi.sclk.line.override_net_name = "spi-sclk"
    spi.mosi.line.override_net_name = "spi-mosi"
    spi.miso.line.override_net_name = "spi-miso"
    clk.line.override_net_name = "clk"
    drive_enable.line.override_net_name = "n-drive-enable"
    refl_step.line.override_net_name = "refl_step"
    refr_dir.line.override_net_name = "refr_dir"

    power_motor.hv.override_net_name = "power-motor"
    power_motor.lv.override_net_name = "gnd"
    motor_a1.line.override_net_name = "motor-a1"
    motor_a2.line.override_net_name = "motor-a2"
    motor_b1.line.override_net_name = "motor-b1"
    motor_b2.line.override_net_name = "motor-b2"
    diag0_swn.line.override_net_name = "diag0_swn"
    enca_dcin_cfg5.line.override_net_name = "enca_dcin_cfg5"
    encb_dcen_cfg4.line.override_net_name = "encb_dcen_cfg4"
    encn_dco_cfg6.line.override_net_name = "encn_dco_cfg6"

    # --- Bulk Decoupling Capacitors ---
    bulk_decoupling_capacitor_1 = new Capacitor
    bulk_decoupling_capacitor_1.lcsc_id = "C72523"
    power_motor ~ bulk_decoupling_capacitor_1.power
    bulk_decoupling_capacitor_2 = new Capacitor
    bulk_decoupling_capacitor_2.lcsc_id = "C72523"
    power_motor ~ bulk_decoupling_capacitor_2.power

    # --- Gate Drive Resistors ---
    gate_drive_resistors = new Resistor[8]
    for resistor in gate_drive_resistors:
        resistor.resistance = 22ohm +/- 5%
        resistor.package = "0603"

    # --- Bootstrap Capacitors ---
    bootstrap_capacitors = new Capacitor[4]
    for capacitor in bootstrap_capacitors:
        capacitor.capacitance = 220nF +/- 20%
        capacitor.package = "0603"
        capacitor.lcsc_id = "C344195"

    # --- Shunt ----
    shunt_resistors = new Resistor[2]
    for shunt_resistor in shunt_resistors:
        shunt_resistor.resistance = 75mohm +/- 1%
        shunt_resistor.package = "R1206"
        shunt_resistor.max_power = 1W
        shunt_resistor.lcsc_id = "C2904225"

    shunt_sense_resistors = new Resistor[4]
    for resistor in shunt_sense_resistors:
        resistor.resistance = 47ohm +/- 0.1%
        resistor.package = "0402"

    full_bridge_decoupling_capacitors = new Capacitor[2]
    for capacitor in full_bridge_decoupling_capacitors:
        capacitor.capacitance = 470nF +/- 20%
        capacitor.package = "0603"
        capacitor.lcsc_id = "C513577"

    # --- Full Bridges ---
    full_bridge_a = new FullBridge
    full_bridge_a.bridge_power.hv ~ power_motor.hv
    full_bridge_a.bridge_power.hv ~> full_bridge_decoupling_capacitors[0] ~> power_motor.lv
    tmc5160.motor_a_high1.line ~> gate_drive_resistors[0] ~> full_bridge_a.high_gate_1.line
    tmc5160.motor_a_high2.line ~> gate_drive_resistors[1] ~> full_bridge_a.high_gate_2.line
    tmc5160.motor_a_low1.line ~> gate_drive_resistors[2] ~> full_bridge_a.low_gate_1.line
    tmc5160.motor_a_low2.line ~> gate_drive_resistors[3] ~> full_bridge_a.low_gate_2.line
    tmc5160.motor_a_cap1.line ~> bootstrap_capacitors[0] ~> full_bridge_a.bridge_middle_1
    tmc5160.motor_a_cap2.line ~> bootstrap_capacitors[1] ~> full_bridge_a.bridge_middle_2
    tmc5160.motor_a_bm1.line ~ full_bridge_a.bridge_middle_1
    tmc5160.motor_a_bm2.line ~ full_bridge_a.bridge_middle_2
    full_bridge_a.bridge_power.lv ~> shunt_resistors[0] ~> power_motor.lv
    tmc5160.motor_a_current_sense.p.line ~> shunt_sense_resistors[0] ~> full_bridge_a.bridge_power.lv
    tmc5160.motor_a_current_sense.n.line ~> shunt_sense_resistors[1] ~> power_motor.lv

    full_bridge_b = new FullBridge
    full_bridge_b.bridge_power.hv ~ power_motor.hv
    full_bridge_b.bridge_power.hv ~> full_bridge_decoupling_capacitors[1] ~> power_motor.lv
    tmc5160.motor_b_high1.line ~> gate_drive_resistors[4] ~> full_bridge_b.high_gate_1.line
    tmc5160.motor_b_high2.line ~> gate_drive_resistors[5] ~> full_bridge_b.high_gate_2.line
    tmc5160.motor_b_low1.line ~> gate_drive_resistors[6] ~> full_bridge_b.low_gate_1.line
    tmc5160.motor_b_low2.line ~> gate_drive_resistors[7] ~> full_bridge_b.low_gate_2.line
    tmc5160.motor_b_cap1.line ~> bootstrap_capacitors[2] ~> full_bridge_b.bridge_middle_1
    tmc5160.motor_b_cap2.line ~> bootstrap_capacitors[3] ~> full_bridge_b.bridge_middle_2
    tmc5160.motor_b_bm1.line ~ full_bridge_b.bridge_middle_1
    tmc5160.motor_b_bm2.line ~ full_bridge_b.bridge_middle_2
    full_bridge_b.bridge_power.lv ~> shunt_resistors[1] ~> power_motor.lv
    tmc5160.motor_b_current_sense.p.line ~> shunt_sense_resistors[2] ~> full_bridge_b.bridge_power.lv
    tmc5160.motor_b_current_sense.n.line ~> shunt_sense_resistors[3] ~> power_motor.lv

    # --- Configuration pins ---
    # SPI Mode Configuration - Enable SPI interface
    spi_mode_pullup = new Resistor
    spi_mode_pullup.resistance = 10kohm +/- 5%
    spi_mode_pullup.package = "0603"
    tmc5160.spi_mode.line ~> spi_mode_pullup ~> power_vccio.hv

    # SD Mode Configuration - Use internal ramp generator (low)
    sd_mode_pulldown = new Resistor
    sd_mode_pulldown.resistance = 10kohm +/- 5%
    sd_mode_pulldown.package = "0603"
    tmc5160.sd_mode.line ~> sd_mode_pulldown ~> power_vccio.lv

    # Test Mode Configuration - Normal operation (low)
    test_mode_pulldown = new Resistor
    test_mode_pulldown.resistance = 0ohm +/- 0.1ohm
    test_mode_pulldown.package = "0402"
    tmc5160.test_mode.line ~> test_mode_pulldown ~> power_vccio.lv

module FullBridge:
    """
        bridge_power.hv
                |
            +---+---+
            | |
        high_fet1 high_fet2
            | |
            | |
    bridge_middle1 bridge_middle2
            | |
            | |
        low_fet1 low_fet2
            | |
            +---+---+
                |
            bridge_power.lv
    """
    bridge_power = new ElectricPower

    high_gate_1 = new ElectricLogic
    high_gate_2 = new ElectricLogic
    low_gate_1 = new ElectricLogic
    low_gate_2 = new ElectricLogic
    bridge_middle_1 = new Electrical
    bridge_middle_2 = new Electrical

    high_gate_1.reference.lv ~ bridge_middle_1
    high_gate_2.reference.lv ~ bridge_middle_2
    low_gate_1.reference.lv ~ bridge_middle_2
    low_gate_2.reference.lv ~ bridge_middle_1

    high_fets = new TECH_PUBLIC_AO4882
    high_fets.mosfets[0].drain ~ bridge_power.hv
    high_fets.mosfets[0].gate ~ high_gate_1.line
    high_fets.mosfets[0].source ~ bridge_middle_1
    high_fets.mosfets[1].drain ~ bridge_power.hv
    high_fets.mosfets[1].gate ~ high_gate_2.line
    high_fets.mosfets[1].source ~ bridge_middle_2

    low_fets = new TECH_PUBLIC_AO4882
    low_fets.mosfets[0].drain ~ bridge_middle_1
    low_fets.mosfets[0].gate ~ low_gate_1.line
    low_fets.mosfets[0].source ~ bridge_power.lv
    low_fets.mosfets[1].drain ~ bridge_middle_2
    low_fets.mosfets[1].gate ~ low_gate_2.line
    low_fets.mosfets[1].source ~ bridge_power.lv

module TECH_PUBLIC_AO4882:
    package = new TECH_PUBLIC_AO4882_package
    mosfets = new Theoretical_MOSFET[2]

    for mosfet in mosfets:
        mosfet.channel_type = "N_CHANNEL"
        mosfet.max_drain_source_voltage = 40V
        mosfet.on_resistance = 25mohm

    mosfets[0].gate ~ package.G1
    mosfets[0].drain ~ package.D1
    mosfets[0].source ~ package.S1
    mosfets[1].gate ~ package.G2
    mosfets[1].drain ~ package.D2
    mosfets[1].source ~ package.S2

module Theoretical_MOSFET from MOSFET:
    trait has_part_removed
    """
    This theoretical MOSFET is used to avoid picking the MOSFET part.
    The TECH_PUBLIC_AO4882 package has two MOSFETs, so we can connect
    theoretical mosfets to the package to capture indended behavior.
    """
```

## Power Supply Requirements

The TMC5160 requires multiple power supplies:

- **power**: Main logic supply (3.0V to 5.5V, typically 3.3V)
- **power_io**: I/O supply (3.0V to 5.5V, typically 3.3V)
- **power_analog**: Analog supply (3.0V to 5.5V, typically 3.3V)
- **power_motor**: Motor supply (8V to 60V, typically 12V or 24V)

## Interfaces

### SPI Communication
- **spi**: Standard SPI interface for register access and configuration
- **chip_select**: Active-low chip select signal

### Motor Outputs
- **motor_a_high/motor_a_low**: Phase A motor connections
- **motor_b_high/motor_b_low**: Phase B motor connections

### Control Signals
- **enable**: Driver enable (active low)
- **clk**: Clock input for microstepping
- **diag0/diag1**: Diagnostic outputs

### Current Sensing
- **sense_a/sense_b**: Current sense outputs for each phase

## Advanced Features

- **stallGuard**: Sensorless stall detection
- **coolStep**: Automatic current reduction based on load
- **dcStep**: Automatic speed control
- **spreadCycle**: High-precision chopper algorithm
- **Integrated charge pump**: For high-side gate driver supply

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
