# Microchip CAP1188 8-Channel Capacitive Touch Sensor

The Microchip CAP1188 is an 8-channel capacitive touch sensor with integrated LED drivers and multiple communication interfaces. This sensor provides reliable touch detection with configurable sensitivity and supports both I²C and SPI communication protocols.

## Key Features

- **8 Capacitive Touch Inputs**: Independent touch sensing channels (CS1-CS8)
- **8 LED Drivers**: Built-in LED drivers for visual feedback (LED1-LED8)
- **Dual Interface**: I²C or SPI communication (software selectable)
- **Configurable I²C Address**: 5 different I²C addresses via address pin
- **Operating Voltage**: 3.0V to 3.6V
- **Low Power**: Standby current < 50µA
- **Package**: 24-pin QFN (4mm x 4mm)
- **Alert/Interrupt**: Programmable interrupt output

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("TRAITS")
#pragma experiment("FOR_LOOP")

import I2C
import ElectricPower
import ElectricLogic

from "microchip-cap1188.ato" import Microchip_CAP1188

module Usage:
    """
    Usage example for the Microchip CAP1188 8-channel capacitive touch sensor.
    Demonstrates basic connections for touch sensing with optional LED feedback.
    """

    # --- Touch sensor ---
    touch_sensor = new Microchip_CAP1188

    # --- Power supply (3.3V) ---
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.2V to 3.4V

    # --- I²C bus ---
    i2c_bus = new I2C
    assert i2c_bus.frequency <= 400kHz
    assert i2c_bus.address is 0x2B  # Default address with 100kohm resistor

    # --- Optional control signals ---
    reset_pin = new ElectricLogic
    interrupt_pin = new ElectricLogic

    # --- Touch pad connections (optional - connect as needed) ---
    touch_button_1 = new ElectricLogic
    touch_button_2 = new ElectricLogic
    touch_button_3 = new ElectricLogic
    touch_button_4 = new ElectricLogic

    # --- LED connections (optional - connect as needed) ---
    status_led_1 = new ElectricLogic
    status_led_2 = new ElectricLogic

    # --- Connections ---
    power_3v3 ~ touch_sensor.power
    i2c_bus ~ touch_sensor.i2c
    reset_pin ~ touch_sensor.reset
    interrupt_pin ~ touch_sensor.interrupt

    # Connect some touch pads (as examples)
    touch_button_1 ~ touch_sensor.touch_pads[0]
    touch_button_2 ~ touch_sensor.touch_pads[1]
    touch_button_3 ~ touch_sensor.touch_pads[2]
    touch_button_4 ~ touch_sensor.touch_pads[3]

    # Connect some LEDs (as examples)
    status_led_1 ~ touch_sensor.led_outputs[0]
    status_led_2 ~ touch_sensor.led_outputs[1]
```

## Interfaces

### Required
- **power**: ElectricPower interface (3.0V to 3.6V)
- **i2c**: I²C interface for communication

### Optional
- **reset**: Reset control pin (active low)
- **interrupt**: Interrupt/alert pin (active low, open-drain)
- **touch_pads[8]**: 8 capacitive touch sensing inputs
- **led_outputs[8]**: 8 LED driver outputs

## I²C Address Configuration

The I²C address is configured via the address resistor connected to the ADDR_COMM pin:

| Resistor Value | I²C Address | Notes |
|----------------|-------------|-------|
| 0Ω (GND) | N/A | 4-wire SPI mode |
| 82kΩ | 0x2C | I²C mode |
| 100kΩ | 0x2B | I²C mode (default) |
| 120kΩ | 0x2A | I²C mode |
| 150kΩ | 0x29 | I²C mode |
| Open (VDD) | 0x28 | I²C mode |

## Pin Configuration

- **VDD**: Power supply (3.0V to 3.6V)
- **GND**: Ground
- **SCL/SDA**: I²C clock and data lines
- **RESET**: Reset pin (active low)
- **ALERT**: Interrupt/alert pin (active low, open-drain)
- **CS1-CS8**: Capacitive touch sensing inputs
- **LED1-LED8**: LED driver outputs
- **ADDR_COMM**: Address/communication configuration pin

## Applications

- Touch buttons and sliders
- Capacitive user interfaces
- Proximity detection
- Touch-sensitive control panels
- Industrial HMI applications
- Consumer electronics interfaces
- Automotive touch controls

## Technical Specifications

- **Supply Voltage**: 3.0V to 3.6V
- **Supply Current**: 1.5mA active, <50µA standby
- **Communication**: I²C (up to 400kHz) or SPI (up to 2MHz)
- **Touch Sensitivity**: Programmable (multiple settings)
- **LED Current**: Up to 35mA per channel
- **Operating Temperature**: -40°C to +85°C
- **Package**: 24-pin QFN (4mm x 4mm)

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
