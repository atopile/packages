# STMicroelectronics VL6180 Time-of-Flight Proximity and Ambient Light Sensor

The STMicroelectronics VL6180 is an advanced Time-of-Flight (ToF) sensor that combines precise distance ranging with ambient light sensing in a single compact package. Using infrared VCSEL (Vertical Cavity Surface Emitting Laser) technology, it provides accurate distance measurements independent of target color, size, or reflectance properties.

## Key Features

- **Time-of-Flight Ranging**: 0-100mm typical range, up to 600mm possible with reduced accuracy
- **Ambient Light Sensing**: 0-100k lux measurement range
- **Color Independence**: Accurate measurements regardless of target color or reflectance
- **I2C Interface**: Simple integration with 7-bit address 0x29 (software configurable)
- **Dual GPIO Pins**: Programmable for interrupts and chip enable
- **Low Power**: 1.7mA average consumption during ranging at 10Hz
- **Fast Measurement**: Up to 100Hz ranging rate
- **Small Package**: LGA-12 package (4.8 x 2.8 mm)

## Technical Specifications

### Distance Ranging
- **Measurement Range**: 0-100mm (typical), up to 600mm possible
- **Accuracy**: ±3mm typical at 50mm distance
- **Resolution**: 1mm
- **Field of View**: 25° typical
- **Technology**: Time-of-Flight with integrated VCSEL and photodiode

### Ambient Light Sensing
- **Range**: 0.1 to 100,000 lux
- **Resolution**: Depends on integration time and gain settings
- **Response**: Broad spectrum with IR rejection

### Electrical Characteristics
- **I/O Supply (VDD_IO)**: 2.6V to 5.5V (typically 3.3V)
- **Analog Supply (AVDD)**: 2.8V nominal (2.6V to 3.0V)
- **VCSEL Supply**: 2.8V nominal (2.6V to 3.0V)
- **I2C Address**: 0x29 (7-bit, default) - software configurable
- **I2C Frequency**: Up to 400kHz (Fast Mode)
- **Current Consumption**:
  - Standby: <1μA
  - Ranging: 1.7mA average at 10Hz
  - Peak during measurement: ~20mA

### Package and Environment
- **Package**: LGA-12 (4.8 x 2.8 x 1.0 mm)
- **Operating Temperature**: -20°C to +70°C
- **Storage Temperature**: -40°C to +85°C
- **RoHS Compliant**: Yes

## Pin Configuration

The VL6180 requires multiple power domains:
- **AVDD**: Analog power supply (2.8V)
- **AVDD_VCSEL**: VCSEL power supply (2.8V)
- **AVSS_VCSEL**: VCSEL ground
- **GND**: Main ground
- **SCL/SDA**: I2C communication
- **GPIO0_CE**: Chip enable input / Data ready output
- **GPIO1**: Programmable interrupt output

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import ElectricLogic
import I2C

from "atopile/st-vl6180/st-vl6180.ato" import ST_VL6180

module Usage:
    """
    Minimal usage example for `st-vl6180`.
    Demonstrates Time-of-Flight ranging and ambient light sensor setup with proper power supplies.
    """

    # --- Main component ---
    tof_sensor = new ST_VL6180

    # --- Power supplies ---
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.2V to 3.4V

    # Analog and VCSEL supplies (need 2.6V to 3.0V)
    power_2v8 = new ElectricPower
    assert power_2v8.voltage within 2.8V to 2.9V

    # --- I2C bus ---
    i2c_bus = new I2C
    assert i2c_bus.frequency within 100kHz to 400kHz

    # --- Connect interfaces ---
    # I/O supply can use 3.3V (2.6V-5.5V range)
    power_3v3 ~ tof_sensor.power_io
    # Analog and VCSEL supplies need 2.8V (2.6V-3.0V range)
    power_2v8 ~ tof_sensor.power_analog
    power_2v8 ~ tof_sensor.power_vcsel

    # I2C connection
    i2c_bus ~ tof_sensor.i2c

    # I2C address is fixed at 0x29 by default
    tof_sensor.i2c.address = 0x29


    # --- Optional: GPIO usage ---
    # GPIO0/CE can be used for chip enable and data ready interrupt
    chip_enable = new ElectricLogic
    chip_enable.reference ~ power_3v3
    chip_enable ~ tof_sensor.gpio0_ce

    # GPIO1 can be used for threshold interrupts
    interrupt_pin = new ElectricLogic
    interrupt_pin.reference ~ power_3v3
    interrupt_pin ~ tof_sensor.gpio1

    # --- Usage notes ---
    # The VL6180 provides:
    # - Time-of-Flight ranging: 0-100mm typical, up to 600mm possible
    # - Ambient light sensing: 0-100k lux range
    # - Independent of target color/reflectance
    # - Low power: ~1.7mA during ranging at 10Hz
    #
    # Key features:
    # - Default I2C address: 0x29 (can be changed in software)
    # - GPIO0: Chip enable input / Data ready output
    # - GPIO1: Programmable interrupt output
    # - Fast ranging: up to 100Hz measurement rate
    # - Integrated IR emitter (VCSEL) and photodiode

```

## Operation Modes

### Single-Shot Mode
- On-demand measurements
- Lower power consumption
- Suitable for battery-powered applications

### Continuous Mode
- Regular periodic measurements
- Faster response time
- Configurable measurement rate up to 100Hz

### Interrupt Modes
- **Data Ready**: GPIO signals when new measurement is available
- **Threshold**: GPIO signals when distance/light crosses programmed thresholds
- **Error Detection**: GPIO signals measurement errors or invalid data

## Important Notes

### Power Supply Design
- **Multiple Rails**: Requires 2.8V for analog/VCSEL and 2.6V-5.5V for I/O
- **Clean Power**: Use low-noise supplies for best performance
- **Decoupling**: 100nF capacitors included for each supply domain
- **Current Spikes**: Plan for ~20mA peak current during measurements

### I2C Communication
- **Default Address**: 0x29 (can be changed via software, resets on power cycle)
- **Multiple Sensors**: Use GPIO0 as chip enable to share I2C bus with multiple VL6180s
- **Pull-ups**: Ensure adequate I2C pull-up resistors

### Optical Design
- **Clear Aperture**: Ensure unobstructed optical path
- **Cover Glass**: Use AR-coated cover glass if protection needed
- **Crosstalk**: Minimize optical crosstalk between emitter and detector
- **Ambient Light**: Sensor compensates for ambient light automatically

### Performance Optimization
- **Calibration**: Factory calibrated, no user calibration typically needed
- **Integration Time**: Adjustable for different ambient light conditions
- **Gain Settings**: Configurable for optimal SNR in different applications
- **Filtering**: Built-in signal processing reduces noise

## Applications

- **Proximity Detection**: Touch-free switches and presence detection
- **Gesture Recognition**: Hand tracking and gesture interfaces
- **Robotics**: Obstacle avoidance and navigation
- **Industrial Automation**: Position sensing and object detection
- **Consumer Electronics**: Camera autofocus, display brightness control
- **IoT Devices**: Smart lighting and occupancy sensing
- **Liquid Level Sensing**: Non-contact level measurement
- **Security Systems**: Intrusion detection and beam-break sensors

## Advantages

- **True Distance**: Measures actual distance, not relative intensity
- **Color Independent**: Works with any target color or reflectance
- **Eye Safe**: Class 1 laser safety rating
- **No Calibration**: Factory calibrated for immediate use
- **Fast Response**: Microsecond measurement capability
- **Low Power**: Suitable for battery-powered applications
- **Small Size**: Compact integration in space-constrained designs

## Comparison with Other Sensors

### vs. Ultrasonic Sensors
- **Faster Response**: Microsecond vs. millisecond measurements
- **Higher Resolution**: 1mm vs. several mm resolution
- **No Sound**: Silent operation
- **Smaller Size**: Much more compact

### vs. IR Proximity Sensors
- **Absolute Distance**: True distance vs. relative proximity
- **Color Independent**: No calibration needed for different targets
- **Better Accuracy**: ±3mm vs. ±10% typical for IR sensors

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
