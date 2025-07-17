# TI DRV2605L Haptic Driver

Advanced haptic driver IC for Linear Resonant Actuators (LRA) and Eccentric Rotating Mass (ERM) motors with built-in haptic effect library and I2C interface.

## Features

- **Haptic Effect Library**: 123 built-in waveforms for various tactile feedback effects
- **Actuator Support**: Compatible with both LRA and ERM haptic motors
- **Smart Control**: Closed-loop actuator control system for consistent performance
- **I2C Interface**: Fixed address 0x5A for easy integration
- **PWM Input Mode**: Real-time waveform control bypass
- **Wide Voltage Range**: 2.0V to 5.2V supply voltage
- **Built-in Regulator**: 1.8V internal rail with external capacitor
- **Low Power**: Standby mode for battery-powered applications

## Applications

- Smartphones and tablets
- Gaming controllers
- Wearable devices
- Industrial HMI
- Automotive touchscreens
- Medical devices

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "ti-drv2605l.ato" import TI_DRV2605L

module Usage:
    """
    Minimal usage example for TI DRV2605L haptic driver.
    Shows basic I2C connection and power supply for haptic feedback applications.
    """

    # Create haptic driver instance
    haptic_driver = new TI_DRV2605L

    # External power supply (3.3V typical)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # External I2C bus (from microcontroller)
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz  # Standard I2C speed
    i2c_bus.address = 0x5A      # DRV2605L fixed address

    # External haptic motor connection
    haptic_motor = new ElectricPower

    # Connect power supply
    power_3v3 ~ haptic_driver.power

    # Connect I2C bus
    i2c_bus ~ haptic_driver.i2c

    # Connect haptic motor/actuator
    haptic_motor ~ haptic_driver.haptic_output
```

## External Interfaces

### Required Connections

- **power**: Main power supply (2.0V to 5.2V)
- **i2c**: I2C bus interface (fixed address 0x5A)
- **haptic_output**: Differential output for haptic motor (OUT+/OUT-)

### Optional Connections

- **enable**: Enable control input (pulled high by default)
- **trigger**: Hardware trigger for PWM mode (pulled low by default)

## Technical Specifications

- **Supply Voltage**: 2.0V to 5.2V
- **I2C Address**: 0x5A (fixed, 7-bit)
- **I2C Speed**: Up to 400kHz
- **Output Voltage**: Up to 5.5V peak
- **Output Current**: Up to 250mA (depending on load)
- **Package**: VSSOP-10
- **Temperature Range**: -40°C to +85°C

## Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| 1 | REG | 1.8V regulator output (requires 1µF capacitor) |
| 2 | SCL | I2C clock |
| 3 | SDA | I2C data |
| 4 | IN/TRIG | PWM input/trigger |
| 5 | EN | Enable (active high) |
| 6 | VDD/NC | No connect |
| 7 | OUT+ | Positive haptic output |
| 8 | GND | Ground |
| 9 | OUT- | Negative haptic output |
| 10 | VDD | Power supply input |

## Haptic Effect Library

The DRV2605L includes 123 built-in haptic effects organized into categories:

- **Strong Click Effects**: Sharp, defined clicks
- **Soft Bump Effects**: Gentle tactile feedback
- **Double/Triple Click**: Multi-tap sequences
- **Soft Fuzz Effects**: Buzzing sensations
- **Strong Buzz Effects**: Intense vibrations
- **Alert Effects**: Attention-getting patterns
- **Pulsing Effects**: Rhythmic feedback
- **Transition Effects**: Smooth ramps and fades

## Hardware Setup

### Required External Components

1. **REG Pin Capacitor**: 1µF ceramic capacitor from REG to GND
2. **VDD Decoupling**: 100nF ceramic + 10µF bulk capacitors
3. **I2C Pull-ups**: 10kΩ resistors on SCL/SDA (integrated in driver)
4. **Enable Pull-up**: 10kΩ resistor (for default enabled state)
5. **Trigger Pull-down**: 10kΩ resistor (for default inactive state)

### Haptic Motor Connection

Connect your LRA or ERM motor between OUT+ and OUT- pins. Typical motors:

- **LRA**: Linear resonant actuators (recommended)
- **ERM**: Small vibration motors (coin cell type)
- **Load Impedance**: 8Ω minimum recommended

## Software Integration

The device communicates via I2C with these key registers:

- **0x00**: Status register
- **0x01**: Mode register (select operation mode)
- **0x02**: Real-time playback input
- **0x03**: Library selection
- **0x04**: Waveform sequencer
- **0x07**: Go register (trigger playback)

### Basic Initialization Sequence

1. Set standby bit to exit standby mode
2. Configure actuator type (LRA/ERM)
3. Set library selection
4. Auto-calibrate actuator (recommended)
5. Load waveform effects
6. Trigger playback

## JLCPCB Part Number

- **LCSC**: C527464
- **Manufacturer**: Texas Instruments
- **Part Number**: DRV2605LDGSR
- **Package**: VSSOP-10
- **Stock**: Available

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
