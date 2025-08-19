# ST VL53L0X Time-of-Flight Distance Sensor

The ST VL53L0X is a Time-of-Flight (ToF) ranging sensor that provides accurate distance measurements up to 2 meters with 1mm resolution. This sensor uses a VCSEL (Vertical Cavity Surface Emitting Laser) and SPAD (Single Photon Avalanche Diode) array to measure distance by calculating the time it takes for infrared light to travel to an object and back.

## Key Features

- **Range**: Up to 2 meters (6.6 feet)
- **Resolution**: 1mm
- **Interface**: I²C (up to 400 kHz)
- **Operating Voltage**: 2.6V to 5.5V (regulated to 2.8V internally)
- **Current Consumption**: <10µA standby, 19mA during ranging
- **Package**: 12-pin optical SMD package
- **Default I²C Address**: 0x29 (7-bit)

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C
import ElectricLogic

from "atopile/st-vl53l0x/st-vl53l0x.ato" import ST_VL53L0X

module Usage:
    """
    Minimal usage example for st-vl53l0x.
    Demonstrates basic connections for ToF distance sensor operation.
    """

    # --- Distance sensor ---
    tof_sensor = new ST_VL53L0X

    # --- Power supply (3.3V typical) ---
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.2V to 3.4V

    # --- I2C bus ---
    i2c_bus = new I2C
    assert i2c_bus.frequency <= 400kHz
    assert i2c_bus.address is 0x29

    # --- Optional control signals ---
    shutdown_control = new ElectricLogic
    interrupt_pin = new ElectricLogic

    # --- Connections ---
    power_3v3 ~ tof_sensor.power
    i2c_bus ~ tof_sensor.i2c
    shutdown_control ~ tof_sensor.xshut
    interrupt_pin ~ tof_sensor.gpio1

```

## Interfaces

### Required
- **power**: ElectricPower interface (2.6V to 5.5V)
- **i2c**: I²C interface for configuration and data readout

### Optional
- **xshut**: Shutdown control pin (active low)
- **gpio1**: Interrupt/GPIO pin for advanced features

## Pin Configuration

- **VDD/AVDD**: Power supply pins (2.6V to 5.5V)
- **VSS/GND**: Ground pins
- **SCL/SDA**: I²C clock and data lines
- **SHT**: Shutdown pin (XSHUT)
- **GP1**: GPIO1/Interrupt pin

## Applications

- Proximity detection
- User detection for displays and user interfaces
- Gesture recognition
- Laser assisted autofocus for cameras
- Industrial distance measurement
- Robotics obstacle detection

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
