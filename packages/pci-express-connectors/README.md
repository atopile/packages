# PCI Express Board Edge Connectors

Standard PCIe x1, x4, x8, and x16 board edge connectors for expansion cards. These connectors provide the physical interface for PCIe expansion cards to connect to motherboards or other host systems.

## Features

- **Complete PCIe connector family**: x1, x4, x8, and x16 configurations
- **Standard pinout**: Follows PCI Express specification
- **High-speed differential signals**: Proper impedance-controlled routing
- **Power delivery**: +12V, +3.3V, and +3.3V_aux power rails
- **Control signals**: Present detect, reset, wake, and reference clock
- **JTAG interface**: For testing and debugging
- **SMBus interface**: For system management

## Available Connectors

### PCIe_X1

- **1 lane** (2 differential pairs)
- **18 pins per side** (36 total)
- **Applications**: Network cards, sound cards, low-bandwidth peripherals

### PCIe_X4

- **4 lanes** (8 differential pairs)
- **32 pins per side** (64 total)
- **Applications**: NVMe SSDs, RAID controllers, high-speed network cards

### PCIe_X8

- **8 lanes** (16 differential pairs)
- **49 pins per side** (98 total)
- **Applications**: High-performance network cards, storage controllers

### PCIe_X16

- **16 lanes** (32 differential pairs)
- **82 pins per side** (164 total)
- **Applications**: Graphics cards, high-end accelerators, multi-port network cards

## Usage

```ato
from "atopile/pci-express-connectors/pci-express-connectors.ato" import PCIe_X1, PCIe_X4, PCIe_X8, PCIe_X16

module Usage:
    """
    Example usage of PCIe board edge connectors
    Shows how to use each connector type in a design
    """

    # Example 1: Simple PCIe x1 card
    pcie_x1_card = new PCIe_X1
    """PCIe x1 connector for single-lane expansion card"""

    # Example 2: PCIe x4 card (e.g., NVMe SSD)
    pcie_x4_card = new PCIe_X4
    """PCIe x4 connector for quad-lane expansion card"""

    # Example 3: PCIe x8 card (e.g., high-performance network card)
    pcie_x8_card = new PCIe_X8
    """PCIe x8 connector for octal-lane expansion card"""

    # Example 4: PCIe x16 card (e.g., graphics card)
    pcie_x16_card = new PCIe_X16
    """PCIe x16 connector for 16-lane expansion card"""

    # Power supply connections (example)
    main_12v = new ElectricPower
    """Main +12V power supply"""
    main_3v3 = new ElectricPower
    """Main +3.3V power supply"""
    main_3v3_aux = new ElectricPower
    """Auxiliary +3.3V power supply (always-on)"""

    # Connect power supplies to all PCIe connectors
    main_12v ~ pcie_x1_card.power.v12
    main_3v3 ~ pcie_x1_card.power.v3_3
    main_3v3_aux ~ pcie_x1_card.power.v3_3_aux

    main_12v ~ pcie_x4_card.power.v12
    main_3v3 ~ pcie_x4_card.power.v3_3
    main_3v3_aux ~ pcie_x4_card.power.v3_3_aux

    main_12v ~ pcie_x8_card.power.v12
    main_3v3 ~ pcie_x8_card.power.v3_3
    main_3v3_aux ~ pcie_x8_card.power.v3_3_aux

    main_12v ~ pcie_x16_card.power.v12
    main_3v3 ~ pcie_x16_card.power.v3_3
    main_3v3_aux ~ pcie_x16_card.power.v3_3_aux

    # Example power supply constraints
    assert main_12v.voltage within 11.4V to 12.6V  # ±5% tolerance
    assert main_3v3.voltage within 3.135V to 3.465V  # ±5% tolerance
    assert main_3v3_aux.voltage within 3.135V to 3.465V  # ±5% tolerance
```

## Interfaces

### PCIe_Power

Power supply interface with three rails:

- `v12`: +12V main power (high current)
- `v3_3`: +3.3V main power
- `v3_3_aux`: +3.3V auxiliary power (always-on)

### PCIe_Signals

Control and configuration signals:

- `prsnt1`, `prsnt2`: Present detect pins
- `perst`: PCI Express reset
- `wake`: Wake signal for power management
- `refclk_p`, `refclk_n`: Reference clock differential pair

### PCIe_Lane

Single PCIe lane with differential pairs:

- `tx_p`, `tx_n`: Transmit differential pair
- `rx_p`, `rx_n`: Receive differential pair

### PCIe_JTAG

JTAG test interface:

- `tck`: Test clock
- `tdi`: Test data in
- `tdo`: Test data out
- `tms`: Test mode select
- `trst`: Test reset

### PCIe_SMBus

System Management Bus interface:

- `smclk`: SMBus clock
- `smdat`: SMBus data

## Design Considerations

### Power Supply Design

- **+12V rail**: High current capability required (up to 75W for x16)
- **+3.3V rail**: Powers I/O and logic circuits
- **+3.3V_aux**: Always-on power for wake functionality
- **Decoupling**: Add appropriate bypass capacitors near connector

### Signal Integrity

- **Differential pairs**: Maintain 100Ω ±10% impedance
- **Length matching**: Keep differential pair lengths matched within 0.1mm
- **Layer stackup**: Use controlled impedance PCB stackup
- **Via stitching**: Provide adequate return path stitching

### Mechanical Considerations

- **Card retention**: Follow PCIe mechanical specifications
- **Connector height**: Standard vs low-profile options available
- **Bracket mounting**: Ensure proper mechanical support

## Electrical Specifications

| Parameter              | Min   | Typ   | Max    | Unit |
| ---------------------- | ----- | ----- | ------ | ---- |
| +12V Supply            | 11.4  | 12.0  | 12.6   | V    |
| +3.3V Supply           | 3.135 | 3.3   | 3.465  | V    |
| +3.3V_aux Supply       | 3.135 | 3.3   | 3.465  | V    |
| Differential Impedance | 90    | 100   | 110    | Ω    |
| Reference Clock        | 99.97 | 100.0 | 100.03 | MHz  |

## Package Contents

- PCIe x1, x4, x8, x16 connector components
- KiCad footprints and symbols
- 3D models for mechanical verification
- Complete pinout definitions
- Usage examples and documentation

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
