# Texas Instruments TCA4307 Hot-Swappable I²C Bus Buffer

The TCA4307 is a hot-swappable I²C bus buffer designed for I/O card insertion into live backplane systems without corrupting data and clock bus lines. It provides bidirectional buffering with automatic bus recovery and reset pulse generation.

## Key Features

- **Hot-swappable capability**: Safe insertion/removal from live I²C bus
- **Automatic bus recovery**: Disconnects after ~40ms timeout on stuck bus
- **Reset pulse generation**: Up to 16 reset pulses for bus recovery
- **Bidirectional buffering**: Full I²C protocol support including arbitration
- **Wide supply voltage**: 2.3V to 5.5V
- **High-speed operation**: Up to 400kHz (Fast-mode I²C)
- **Pre-charging**: 1V pre-charge during insertion to minimize glitches
- **Clock stretching support**: Maintains I²C timing requirements
- **Package**: VSSOP-8 (2.3mm × 3.0mm)
- **Temperature range**: -40°C to +125°C

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "ti-tca4307.ato" import TI_TCA4307

module Usage:
    """
    Minimal usage example for ti-tca4307.
    Demonstrates basic I²C buffer configuration with 3.3V power supply.
    The buffer provides isolation and hot-swap capability between upstream
    controller and downstream I²C devices.
    """

    # Buffer instance
    buffer = new TI_TCA4307

    # External I²C busses
    i2c_host = new I2C
    """Host/controller I2C bus (upstream)"""

    i2c_devices = new I2C
    """Device I2C bus (downstream)"""

    # Bridge connect
    i2c_host ~> buffer ~> i2c_devices

    # Power supply (3.3V rail)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # Connect power supply
    power_3v3 ~ buffer.power
```

## Interface Details

### I2C Buffering
- **Upstream port**: Connects to host/controller I²C bus
- **Downstream port**: Connects to target I²C devices
- **Bidirectional**: Full duplex data and clock buffering
- **Protocol support**: Standard-mode (100kHz) and Fast-mode (400kHz)

### Control Pins
- **ENABLE**: Active-high enable input (internally pulled up)
- **READY**: Open-drain output indicating buffer readiness (active low)

### Power Supply
- **VCC**: 2.3V to 5.5V (typical 3.3V or 5.0V)
- **Current consumption**:
  - Active mode: 3.5mA (typical)
  - Standby mode: 1.5mA (typical)

### Hot-Swap Features
- **Pre-charging**: Outputs pre-charged to 1V during power-up
- **Bus timeout**: Automatic disconnect after 40ms of stuck bus condition
- **Reset generation**: Generates up to 16 reset pulses for bus recovery
- **Rise time acceleration**: 130mA current source for faster edges

## Pin Configuration (VSSOP-8)
1. **EN** - Buffer enable (active high)
2. **SCLOUT** - Downstream I²C clock (to card)
3. **SCLIN** - Upstream I²C clock (from backplane)
4. **GND** - Ground
5. **READY** - Buffer ready output (open-drain, active low)
6. **SDAIN** - Upstream I²C data (from backplane)
7. **SDAOUT** - Downstream I²C data (to card)
8. **VCC** - Power supply

## Applications
- Hot-swappable I²C modules and cards
- Backplane I²C systems
- Industrial automation with live insertion/removal
- Test equipment with changeable sensor modules
- Redundant I²C bus architectures
- I²C bus isolation and protection

## Operating Modes

### Normal Operation
- Both upstream and downstream I²C buses are connected
- Bidirectional data/clock buffering active
- READY pin indicates successful connection

### Bus Recovery Mode
- Activated when stuck bus condition detected (>40ms)
- Generates reset pulses to clear stuck devices
- Automatically reconnects when bus returns to idle

### Hot-Swap Insertion
- Pre-charges outputs to 1V to minimize disturbance
- Gradual connection to avoid bus corruption
- READY pin goes low when buffer is fully operational

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
