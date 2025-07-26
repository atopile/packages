# Diodes Incorporated 74LVC1T45DW-7 Single-Bit Dual-Supply Bus Transceiver

The 74LVC1T45DW-7 is a single-bit, dual-supply bus transceiver that provides bidirectional voltage level translation between different logic levels. It features a direction control pin and supports voltage levels from 1.65V to 5.5V on both sides, making it ideal for interfacing between different voltage domains.

## Key Features

- **Single-bit bidirectional transceiver**: Translates one signal between two voltage domains
- **Dual supply operation**: Independent power supplies for each side (1.65V - 5.5V)
- **Direction control**: Programmable signal direction via DIR pin
- **High speed**: 3.6ns typical propagation delay
- **Low power**: Ultra-low quiescent current
- **Wide voltage range**: 1.65V to 5.5V on both A and B sides
- **Auto-direction sensing**: Can be configured for automatic direction detection
- **SOT-363 package**: Compact SC-70-6 package (2.0mm × 1.25mm)
- **Industrial temperature**: -40°C to +85°C operating range

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import ElectricLogic

from "diodes-inc-74lvc1t45dw-7.ato" import Diodes_Inc_74LVC1T45DW_7, Level_Shifter_3V3_to_5V, Bidirectional_Level_Shifter

module Usage:
    """
    Usage examples for Diodes Inc 74LVC1T45DW-7 level shifter.

    This example demonstrates:
    - Basic level shifter configuration
    - Pre-configured 3.3V to 5V shifter
    - Bidirectional shifter with external control
    - Multiple level shifter chaining
    - Common interface scenarios
    """

    # --- Basic Level Shifter Example ---
    basic_shifter = new Diodes_Inc_74LVC1T45DW_7

    # Power supplies
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    power_5v = new ElectricPower
    power_5v.voltage = 5V +/- 5%

    # Connect power supplies
    power_3v3 ~ basic_shifter.power_a
    power_5v ~ basic_shifter.power_b

    # Signal interfaces
    mcu_signal = new ElectricLogic
    """3.3V signal from microcontroller"""
    mcu_signal ~ basic_shifter.signal_a
    power_3v3 ~ mcu_signal.reference

    peripheral_signal = new ElectricLogic
    """5V signal to peripheral device"""
    peripheral_signal ~ basic_shifter.signal_b
    power_5v ~ peripheral_signal.reference

    # --- Pre-configured 3.3V to 5V Shifter Example ---
    preconfigured_shifter = new Level_Shifter_3V3_to_5V

    # Connect same power supplies
    power_3v3 ~ preconfigured_shifter.power_3v3
    power_5v ~ preconfigured_shifter.power_5v

    # Connect signals
    mcu_spi_clock = new ElectricLogic
    """SPI clock from 3.3V MCU"""
    mcu_spi_clock ~ preconfigured_shifter.signal_3v3
    power_3v3 ~ mcu_spi_clock.reference

    display_spi_clock = new ElectricLogic
    """SPI clock to 5V display"""
    display_spi_clock ~ preconfigured_shifter.signal_5v
    power_5v ~ display_spi_clock.reference
```

## Technical Specifications

### Electrical Characteristics
- **Supply Voltage**: 1.65V to 5.5V (both VCC_A and VCC_B)
- **Input Voltage**: -0.5V to VCC + 0.5V
- **Output Current**: ±24mA continuous
- **Quiescent Current**: 10μA maximum (typical 0.1μA)
- **Input Capacitance**: 3.5pF typical
- **Output Capacitance**: 4.5pF typical

### Performance Characteristics
- **Propagation Delay**: 3.6ns typical (VCC = 3.3V)
- **Rise/Fall Time**: 2.0ns typical (VCC = 3.3V, CL = 15pF)
- **Maximum Toggle Rate**: 210MHz typical
- **Power Dissipation**: 500mW maximum
- **Channel-to-Channel Skew**: 0.5ns maximum

### Logic Levels
**VCC_A = VCC_B = 3.3V:**
- **VIH**: 2.0V minimum (High-level input voltage)
- **VIL**: 0.8V maximum (Low-level input voltage)
- **VOH**: 2.3V minimum (High-level output voltage)
- **VOL**: 0.4V maximum (Low-level output voltage)

**VCC_A = VCC_B = 5.0V:**
- **VIH**: 3.15V minimum
- **VIL**: 1.35V maximum
- **VOH**: 3.8V minimum
- **VOL**: 0.4V maximum

### Package Information
- **Package Type**: SOT-363 (SC-70-6)
- **Dimensions**: 2.0mm × 1.25mm × 1.1mm
- **Pin Pitch**: 0.65mm
- **Lead Count**: 6 pins
- **Moisture Sensitivity**: MSL 1

## Pin Configuration

| Pin | Name | Function |
|-----|------|----------|
| 1   | VCC_A | Supply voltage for side A |
| 2   | GND   | Ground reference |
| 3   | A     | Data input/output for side A |
| 4   | B     | Data input/output for side B |
| 5   | VCC_B | Supply voltage for side B |
| 6   | DIR   | Direction control input |

## Direction Control

The DIR pin controls the signal flow direction:

- **DIR = VCC_A (HIGH)**: Signal flows from A to B
- **DIR = GND (LOW)**: Signal flows from B to A
- **DIR pin reference**: Always referenced to VCC_A

## Circuit Design Guidelines

### Power Supply Decoupling
- **Placement**: Place 100nF ceramic capacitors close to VCC_A and VCC_B pins
- **Additional filtering**: Consider 1μF tantalum for bulk decoupling
- **Ground plane**: Solid ground connection essential for performance

### PCB Layout Recommendations
- **Trace length**: Keep signal traces as short as possible
- **Impedance control**: Match trace impedance for high-speed signals
- **Ground plane**: Continuous ground plane under the device
- **Via placement**: Minimize vias in high-speed signal paths

### Signal Integrity
- **Series termination**: Consider series resistors for long traces
- **Pull-up/pull-down**: May be required depending on application
- **Rise time**: Ensure adequate drive strength for capacitive loads

## Applications

### Common Use Cases
- **Microcontroller interfacing**: 3.3V MCU to 5V peripherals
- **Mixed-voltage systems**: Battery-powered devices with multiple voltage rails
- **Legacy system integration**: Modern 3.3V devices with older 5V systems
- **Bus translation**: I2C, SPI, UART level shifting
- **FPGA/CPLD interfacing**: Different I/O voltage standards

### Protocol-Specific Applications

#### SPI Bus Translation
```
MCU (3.3V) → Level Shifter → Peripheral (5V)
- SCLK, MOSI: A→B direction
- MISO: B→A direction
- CS: A→B direction
```

#### I2C Bus Translation
```
Requires bidirectional capability:
- SDA: Bidirectional with external direction control
- SCL: Typically A→B (master to slave)
```

#### UART Translation
```
TX Path: MCU_TX (3.3V) → Level Shifter → Device_RX (5V)
RX Path: Device_TX (5V) → Level Shifter → MCU_RX (3.3V)
```

## Design Examples

### 3.3V Microcontroller to 5V Display
```ato
display_interface = new Level_Shifter_3V3_to_5V
mcu_gpio ~ display_interface.signal_3v3
display_enable ~ display_interface.signal_5v
```

### Bidirectional I2C Level Shifting
```ato
i2c_shifter = new Bidirectional_Level_Shifter
mcu_sda ~ i2c_shifter.signal_low      # 3.3V side
sensor_sda ~ i2c_shifter.signal_high  # 5V side
direction_control ~ i2c_shifter.direction_control
```

### Multi-Channel Bus Translation
```ato
# 4-bit parallel bus level shifting
bus_shifters = new Diodes_Inc_74LVC1T45DW_7[4]
for i in range(4):
    mcu_bus[i] ~ bus_shifters[i].signal_a
    peripheral_bus[i] ~ bus_shifters[i].signal_b
```

## Performance Optimization

### Speed Optimization
- **Load capacitance**: Minimize capacitive loading
- **Drive strength**: Consider buffer amplification for heavy loads
- **Slew rate**: Adjust based on EMI requirements

### Power Optimization
- **Unused inputs**: Tie unused inputs to VCC or GND
- **Direction control**: Optimize switching to minimize power
- **Supply sequencing**: Ensure proper power-up/down sequence

## Troubleshooting

### Common Issues
1. **Signal integrity problems**: Check power supply decoupling
2. **Direction control errors**: Verify DIR pin connection and logic
3. **Voltage level issues**: Confirm supply voltages within specification
4. **Timing violations**: Check propagation delays and setup/hold times

### Debug Techniques
- **Oscilloscope analysis**: Verify signal transitions and timing
- **Logic analyzer**: Check protocol compliance
- **Power measurement**: Monitor supply current for anomalies

## Package Information
- **Part Number**: 74LVC1T45DW-7
- **JLCPCB Part**: C168855
- **Manufacturer**: Diodes Incorporated
- **Package**: SOT-363 (SC-70-6)
- **RoHS**: Compliant
- **Operating Temperature**: -40°C to +85°C
- **Storage Temperature**: -65°C to +150°C

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
