# Realtek RTL8305NB 5-Port Ethernet Switch

A comprehensive atopile package for the **Realtek RTL8305NB** 5-port 10/100 Ethernet switch IC with integrated PHY transceivers. This package provides both a basic driver module and a complete managed switch reference design.

## Features

### RTL8305NB Switch IC

- **5-port 10/100 Ethernet switch** with integrated PHYs
- **Auto-negotiation** on all ports (10Base-T/100Base-TX)
- **Internal 1.2V regulator** (3.3V input)
- **MDIO management interface** for configuration
- **Per-port LED indicators** for status
- **Loop detection** with automatic port disable
- **Energy Efficient Ethernet (EEE)** support (disabled by default)
- **25MHz crystal oscillator** with ±50ppm tolerance
- **QFN-48 package** (LCSC C3010343)

### Complete Usage Example

The included usage example demonstrates a **professional managed switch** with:

- **ESP32-C3 Management**: WiFi-enabled microcontroller for remote management
- **W5500 SPI Bridge**: Connects ESP32-C3 to switch as network node
- **4x External RJ-45 Ports**: With integrated magnetics for user connections
- **USB-C Power**: 5V input with efficient buck converter regulation
- **Comprehensive Status LEDs**: Power, link, activity, and programmable indicators
- **Debug Headers**: Saleae logic analyzer connections for protocol analysis
- **Level Shifting**: 3.3V↔5V translation for mixed-voltage operation

## Quick Start

### Basic Switch Usage

```ato
from "atopile/realtek-rtl8305nb/realtek-rtl8305nb.ato" import Realtek_RTL8305NB

module MySwitch:
    switch = new Realtek_RTL8305NB

    # Connect 3.3V power
    power_3v3 = new ElectricPower
    switch.power_3v3 ~ power_3v3

    # Connect Ethernet ports
    # switch.ethernets[0-4] available for connections

    # Optional: Connect management interface
    # switch.i2c_mdio for MDIO configuration
    # switch.reset for external reset control
```

### Complete Managed Switch

```ato
"Complete 5-port Ethernet switch using Realtek RTL8305NB"
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import Resistor

from "realtek-rtl8305nb.ato" import Realtek_RTL8305NB
from "atopile/rj45-connectors/rj45-connectors.ato" import RJ45_Horizontal_TH_Magnetics
from "atopile/espressif-esp32-c3/esp32_c3_mini.ato" import ESP32_C3_MINI_1_driver
from "atopile/wiznet-w5500/wiznet-w5500.ato" import Wiznet_W5500
from "atopile/usb-connectors/usb-connectors.ato" import USB2_0TypeCHorizontalConnector
from "atopile/ti-tpsm863257/ti-tpsm863257.ato" import TPSM863257
from "atopile/opsco-sk6805-side/opsco-sk6805-side.ato" import OPSCO_SK6805_SIDE
from "atopile/diodes-inc-74lvc1t45dw-7/diodes-inc-74lvc1t45dw-7.ato" import Diodes_Inc_74LVC1T45DW_7
from "atopile/saleae-header/saleae-header.ato" import SaleaeHeaderRightAngle_2
from "atopile/logos/logos.ato" import atopile_logo_25x6mm
from "atopile/indicator-leds/indicator-leds.ato" import LEDIndicatorGreen, LEDIndicatorYellow, LEDIndicatorRed, LEDIndicatorBlue

module Usage:
    """
    Complete 5-port Ethernet switch example using RTL8305NB
    Creates a managed switch with 4 external RJ-45 ports and ESP32-C3 connected via W5500
    """

    # --- Main switch IC ---
    switch = new Realtek_RTL8305NB

    # --- Management microcontroller ---
    esp32 = new ESP32_C3_MINI_1_driver
    """
    ESP32-C3 for switch management, configuration, and monitoring
    Can implement web interface, SNMP, or custom management protocols
    """

    # --- SPI-to-Ethernet bridge ---
    w5500 = new Wiznet_W5500
    """
    W5500 SPI-to-Ethernet controller
    Connects ESP32-C3 to the switch as a network node
    """

    # --- Power supply system ---
    # USB-C input connector
    usb_connector = new USB2_0TypeCHorizontalConnector
    """
    USB-C connector for 5V power input
    """

    # 3.3V Buck converter (more efficient than LDO)
    buck = new TPSM863257
    """
    TI TPSM863257 synchronous buck converter
    Converts 5V USB input to 3.3V with ~90% efficiency
    Much more efficient than LDO for high current applications
    """

    # Power rails
    power_5v = new ElectricPower
    power_3v3 = new ElectricPower
    """
    5V from USB-C and regulated 3.3V for all components
    """
    power_5v.required = True
    power_3v3.required = True
    assert power_5v.voltage within 5V +/- 5%
    assert power_3v3.voltage within 3.3V +/- 5%

    atopile_logo = new atopile_logo_25x6mm

    # Net name overrides for cleaner PCB layout
    power_5v.hv.override_net_name = "+5V"
    power_5v.lv.override_net_name = "GND"
    power_3v3.hv.override_net_name = "+3V3"
    esp32.i2c.scl.line.override_net_name = "I2C_SCL"
    esp32.i2c.sda.line.override_net_name = "I2C_SDA"
    esp32.spi.sclk.line.override_net_name = "SPI_SCLK"
    esp32.spi.mosi.line.override_net_name = "SPI_MOSI"
    esp32.spi.miso.line.override_net_name = "SPI_MISO"
    w5500.spi_cs.line.override_net_name = "SPI_CS"

    # --- RJ-45 Ethernet connectors with integrated magnetics ---
    ethernet_ports = new RJ45_Horizontal_TH_Magnetics[4]
    """
    4 x RJ-45 connectors with integrated magnetics for external ports
    Each connector includes transformer isolation and common-mode filtering
    Port 0 is used internally for ESP32-C3 via W5500
    """

    # --- Ethernet status LEDs ---
    link_led = new LEDIndicatorGreen
    """
    Green link status LED for W5500-Switch connection
    Shows when Ethernet link is established
    """

    activity_led = new LEDIndicatorYellow
    """
    Yellow activity LED for W5500-Switch connection
    Shows network traffic activity
    """

    # --- Power indicator LEDs ---
    power_5v_led = new LEDIndicatorRed
    """
    Red power indicator LED for 5V rail
    Shows when 5V power is present and active
    """

    power_3v3_led = new LEDIndicatorBlue
    """
    Blue power indicator LED for 3.3V rail
    Shows when 3.3V regulator output is active
    """

    # --- Status LED with level shifter ---
    status_led = new OPSCO_SK6805_SIDE
    """
    Addressable RGB LED for system status indication
    Can show power, network activity, error states, etc.
    """

    level_shifter = new Diodes_Inc_74LVC1T45DW_7
    """
    3.3V to 5V level shifter for LED data signal
    Translates ESP32-C3 3.3V GPIO to 5V logic for SK6805
    """

    # --- Debug header ---
    debug_header = new SaleaeHeaderRightAngle_2
    """
    Saleae logic analyzer debug header
    Monitors: SPI (SCLK, MOSI, MISO, CS), I2C (SCL, SDA), Reset, Loop indication
    """

    # --- Connections ---
    # Power supply chain: USB-C → 5V → Buck Converter → 3.3V
    usb_connector.usb.usb_if.buspower ~ power_5v
    power_5v ~> buck ~> power_3v3

    # Power all components
    switch.power_3v3 ~ power_3v3
    esp32.power ~ power_3v3
    w5500.power ~ power_3v3
    status_led.power ~ power_5v              # SK6805 Addressable LED requires 5V
    level_shifter.power_a ~ power_3v3        # 3.3V side (ESP32)
    level_shifter.power_b ~ power_5v         # 5V side (LED)


    # USB data connection for ESP32-C3 programming and communication
    esp32.usb_if ~ usb_connector.usb.usb_if

    # External Ethernet ports (4 ports for users)
    switch.ethernets[1] ~ ethernet_ports[0].ethernet  # External port 1
    switch.ethernets[2] ~ ethernet_ports[1].ethernet  # External port 2
    switch.ethernets[3] ~ ethernet_ports[2].ethernet  # External port 3
    switch.ethernets[4] ~ ethernet_ports[3].ethernet  # External port 4

    # Internal management network (ESP32-C3 connected as network node)
    switch.ethernets[0] ~ w5500.ethernet              # W5500 connects to switch port 0
    esp32.spi ~ w5500.spi                             # ESP32-C3 controls W5500 via SPI

    # Status LEDs using bridge connect across power rails
    w5500.ethernet.led_link.line ~> link_led ~> power_3v3.lv      # Green link status LED
    w5500.ethernet.led_speed.line ~> activity_led ~> power_3v3.lv # Yellow activity LED
    power_5v.hv ~> power_5v_led ~> power_5v.lv               # Red 5V power indicator LED
    power_3v3.hv ~> power_3v3_led ~> power_3v3.lv            # Blue 3.3V power indicator LED
    # GPIO assignments (avoiding conflicts with peripherals and strapping pins)
    esp32.gpio[3] ~ w5500.spi_cs                      # GPIO3: W5500 SPI chip select
    esp32.gpio[0] ~ w5500.interrupt                   # GPIO0: W5500 interrupt (ADC capable)
    esp32.gpio[1] ~ w5500.reset                       # GPIO1: W5500 reset (ADC capable)

    # Switch management via MDIO (optional - for advanced configuration)
    switch.i2c_mdio ~ esp32.i2c       # ESP32 can also manage switch directly via MDIO (uses GPIO5/GPIO6)
    switch.reset ~ esp32.gpio[4]      # GPIO4: Switch reset control
    switch.loop_indication ~ esp32.gpio[20]  # GPIO20: Switch loop detection monitor

    # Status LED connection via level shifter (3.3V → 5V)
    esp32.gpio[21] ~> level_shifter ~> status_led.data_in  # GPIO21: LED data
    level_shifter.dir.line ~ power_3v3.hv                  # DIR = HIGH for A→B transmission

    # I2C/MDIO pull-up resistors (required for proper signaling)
    i2c_pullups = new Resistor[2]
    for r in i2c_pullups:
        r.resistance = 4.7kohm +/- 5%
        r.package = "0402"

    esp32.i2c.scl.line ~> i2c_pullups[0] ~> power_3v3.hv
    esp32.i2c.sda.line ~> i2c_pullups[1] ~> power_3v3.hv

    # Debug header connections (for logic analyzer monitoring)
    # Header 0: SPI signals
    debug_header.headers[0].channels[0] ~ esp32.spi.sclk      # SPI Clock (GPIO10)
    debug_header.headers[0].channels[1] ~ esp32.spi.mosi      # SPI MOSI (GPIO7)
    debug_header.headers[0].channels[2] ~ esp32.spi.miso      # SPI MISO (GPIO8)
    debug_header.headers[0].channels[3] ~ esp32.gpio[3]       # SPI CS (GPIO3)

    # Header 1: I2C and control signals
    debug_header.headers[1].channels[0] ~ esp32.i2c.scl       # I2C SCL (GPIO6)
    debug_header.headers[1].channels[1] ~ esp32.i2c.sda       # I2C SDA (GPIO5)
    debug_header.headers[1].channels[2] ~ esp32.gpio[4]       # Switch reset (GPIO4)
    debug_header.headers[1].channels[3] ~ esp32.gpio[20]      # Loop detection (GPIO20)
```

## Architecture

### Network Topology

```
ESP32-C3 ←SPI→ W5500 ←Ethernet→ RTL8305NB Port 0
                                      ↓
                               Ports 1-4 → RJ-45 Connectors
```

### Power Architecture

```
USB-C 5V → TPSM863257 Buck Converter → 3.3V → All Components
    ↓
SK6805 RGB LED (5V)
```

## Hardware Specifications

### Power Requirements

- **Input**: 5V via USB-C (1.5A+ recommended)
- **Regulation**: TI TPSM863257 buck converter (~90% efficiency)
- **Consumption**: ~1A @ 3.3V (switch + ESP32 + W5500)

### Crystal Specifications

- **Frequency**: 25MHz ±10ppm (Yangxing Tech X322525MRB4SI)
- **Load Capacitance**: 18pF (included in design)
- **Temperature Range**: -40°C to +85°C

### GPIO Allocation (ESP32-C3)

| GPIO  | Function        | Description               |
| ----- | --------------- | ------------------------- |
| 0     | W5500 Interrupt | ADC capable               |
| 1     | W5500 Reset     | ADC capable               |
| 2     | RGB LED Data    | Via level shifter         |
| 3     | SPI Chip Select | W5500 CS                  |
| 4     | Switch Reset    | Control signal            |
| 5     | I2C SDA         | MDIO data                 |
| 6     | I2C SCL         | MDIO clock                |
| 7     | SPI MOSI        | Data to W5500             |
| 8     | SPI MISO        | Data from W5500           |
| 10    | SPI SCLK        | SPI clock                 |
| 18/19 | USB             | Programming/communication |
| 20    | Loop Detection  | Monitor signal            |
| 21    | RGB LED         | Via level shifter         |

## Status Indicators

### LED System

- 🔴 **Red LED**: 5V power present
- 🔵 **Blue LED**: 3.3V regulator active
- 🟢 **Green LED**: W5500↔Switch link established
- 🟡 **Yellow LED**: Network activity/traffic
- 🌈 **RGB LED**: Programmable system status (ESP32 controlled)

### Debug Capabilities

- **2x Saleae Headers**: 8-channel logic analyzer connections
- **SPI Monitoring**: SCLK, MOSI, MISO, CS signals
- **I2C Monitoring**: SCL, SDA signals
- **Control Monitoring**: Reset, loop detection signals

## Configuration Options

### Default Settings

- **EEE**: Disabled (better compatibility)
- **Loop Detection**: Enabled (network protection)
- **Reset Blink**: Enabled (visual feedback)

### Optional EEPROM Support

For custom configuration, connect an **M24C02** (or compatible) I2C EEPROM to the `i2c_mdio` interface at address **0x50**. The RTL8305NB will auto-load configuration from EEPROM during power-on.

## Management Capabilities

The ESP32-C3 can provide:

- **Web Interface**: Browser-based switch configuration
- **WiFi Bridge**: Connect switch to wireless networks
- **MQTT/REST APIs**: Remote monitoring and control
- **SNMP**: Professional network management
- **Custom Logic**: Port mirroring, VLANs, QoS implementation

## Applications

- **SOHO Networking**: Small office/home office switches
- **IoT Gateways**: Managed switch with WiFi uplink
- **Industrial Ethernet**: Reliable switching with remote management
- **Development Platforms**: Protocol analysis and network testing
- **Educational**: Complete reference design for Ethernet switching

## Package Contents

- **Driver Module**: `Realtek_RTL8305NB` with all interfaces
- **Usage Example**: Complete managed switch design
- **Parts**: RTL8305NB IC (C3010343) and crystal (C70593)
- **Documentation**: Comprehensive interface descriptions
- **Build Targets**: Both driver and usage examples

## Dependencies

This package requires several atopile packages for the complete usage example:

- `atopile/espressif-esp32-c3` - ESP32-C3 management controller
- `atopile/wiznet-w5500` - SPI-to-Ethernet bridge
- `atopile/rj45-connectors` - Ethernet connectors with magnetics
- `atopile/ti-tpsm863257` - Efficient buck converter
- `atopile/usb-connectors` - USB-C power input
- `atopile/indicator-leds` - Status LED indicators
- `atopile/opsco-sk6805-side` - Addressable RGB LED
- `atopile/diodes-inc-74lvc1t45dw-7` - Level shifter
- `atopile/saleae-header` - Debug headers

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
