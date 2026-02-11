# Texas Instruments DRV8210 — Low Power DC Motor Driver

The DRV8210 is a compact, versatile motor driver from Texas Instruments featuring a low-resistance N-channel H-bridge, integrated charge pump, ultra-low sleep current, and multiple control modes (PWM, PH/EN, and independent half-bridge). It supports a wide 1.65–11 V motor supply and up to 1.76 A peak output current, with comprehensive protection features suitable for space-constrained motor, solenoid, valve, and relay applications.

## Key Features

- **Full H-bridge driver** for brushed DC motors, solenoids, valves, and relays
- **1.65 V to 11 V motor supply (VM)**
- **1.76 A peak output**, 1 Ω total RDS(on) (HS + LS)
- **Multiple interface modes**:
  - PWM (IN1/IN2)
  - PH/EN
  - Independent half-bridge
  - Parallel half-bridge (higher current capability)
- **Integrated charge pump** enabling 100% duty-cycle operation
- **Ultra-low power sleep mode**: <85 nA typical
- **Protection features**:
  - Undervoltage lockout (UVLO)
  - Overcurrent protection (OCP)
  - Thermal shutdown (TSD)
- **Logic supply (DSG only)**: 1.65–5.5 V
- **Small packages**:
  - WSON-8 (2×2 mm)
  - SOT563-6

## Applications

- Robotics and consumer devices
- Smart locks and appliances
- Solenoid / valve / latch-relay drivers
- Camera IR-cut filters
- Medical devices (pumps, actuators)
- Battery-powered portable systems
- Toys, handheld devices

---

# Usage

Below are Atopile usage patterns for common DRV8210 operating modes.

```ato
import ElectricPower
import ElectricSignal

from "atopile/ti-drv8210p/ti-drv8210p.ato" import Texas_Instruments_DRV8210PDSGR

module Usage:
    # Instantiate driver
    driver = new Texas_Instruments_DRV8210PDSGR

    # Power rails
    logic_power = new ElectricPower
    logic_power.voltage = 3.3V +/- 5%
    logic_power ~ driver.logic_power

    motor_power = new ElectricPower
    motor_power.voltage = 10V +/- 5%
    # assert motor_power.voltage within 10V +/- 5%
    motor_power ~ driver.motor_power

    current_sense = new ElectricSignal
    current_sense ~ driver.current_sense_voltage

```
