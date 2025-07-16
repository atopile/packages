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

import ElectricPower
import SPI
import ElectricLogic

from "trinamic-tmc5160.ato" import Trinamic_TMC5160

module Usage:
    """
    Minimal usage example for `trinamic-tmc5160`.
    Shows how to connect the TMC5160 stepper motor driver with SPI interface,
    multiple power supplies, and motor connections.
    """

    # Create TMC5160 driver instance
    stepper_driver = new Trinamic_TMC5160

    # --- Power supplies ---
    power_3v3 = new ElectricPower
    """
    3.3V power supply for logic and I/O
    """
    power_3v3.voltage = 3.3V +/- 5%

    power_24v = new ElectricPower
    """
    24V power supply for motor drivers
    """
    power_24v.voltage = 24V +/- 10%

    # --- SPI bus ---
    spi_bus = new SPI
    """
    SPI bus for communication with TMC5160
    """
    spi_bus.sclk.reference ~ power_3v3
    spi_bus.mosi.reference ~ power_3v3
    spi_bus.miso.reference ~ power_3v3

    # --- Control signals ---
    chip_select = new ElectricLogic
    """
    SPI chip select signal (active low)
    """
    chip_select.reference_shim ~ power_3v3

    enable_signal = new ElectricLogic
    """
    Driver enable signal (active low)
    """
    enable_signal.reference_shim ~ power_3v3

    clock_signal = new ElectricLogic
    """
    Clock signal for microstepping
    """
    clock_signal.reference_shim ~ power_3v3

    # --- Motor connections ---
    motor_phase_a_pos = new ElectricLogic
    """
    Motor phase A positive connection
    """
    motor_phase_a_pos.reference_shim ~ power_24v

    motor_phase_a_neg = new ElectricLogic
    """
    Motor phase A negative connection
    """
    motor_phase_a_neg.reference_shim ~ power_24v

    motor_phase_b_pos = new ElectricLogic
    """
    Motor phase B positive connection
    """
    motor_phase_b_pos.reference_shim ~ power_24v

    motor_phase_b_neg = new ElectricLogic
    """
    Motor phase B negative connection
    """
    motor_phase_b_neg.reference_shim ~ power_24v

    # --- Connections ---

    # Connect power supplies
    power_3v3 ~ stepper_driver.power
    power_3v3 ~ stepper_driver.power_io
    power_3v3 ~ stepper_driver.power_analog
    power_24v ~ stepper_driver.power_motor

    # Connect SPI bus
    spi_bus ~ stepper_driver.spi
    chip_select ~ stepper_driver.chip_select

    # Connect control signals
    enable_signal ~ stepper_driver.enable
    clock_signal ~ stepper_driver.clk

    # Connect motor outputs
    motor_phase_a_pos ~ stepper_driver.motor_a_high
    motor_phase_a_neg ~ stepper_driver.motor_a_low
    motor_phase_b_pos ~ stepper_driver.motor_b_high
    motor_phase_b_neg ~ stepper_driver.motor_b_low

    # Optional: Connect diagnostic outputs for monitoring
    diag0_signal = new ElectricLogic
    diag1_signal = new ElectricLogic
    diag0_signal.reference_shim ~ power_3v3
    diag1_signal.reference_shim ~ power_3v3

    diag0_signal ~ stepper_driver.diag0
    diag1_signal ~ stepper_driver.diag1

    # Optional: Connect current sense outputs for monitoring
    sense_a_signal = new ElectricLogic
    sense_b_signal = new ElectricLogic
    sense_a_signal.reference_shim ~ power_3v3
    sense_b_signal.reference_shim ~ power_3v3

    sense_a_signal ~ stepper_driver.sense_a
    sense_b_signal ~ stepper_driver.sense_b
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
