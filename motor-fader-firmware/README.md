# Motor Fader Firmware

Zephyr RTOS firmware for ESP32-S3 based motorized fader controller using the DRV8210P H-bridge driver.

## Hardware

- **MCU**: ESP32-S3-WROOM-1 (N16R8)
- **Motor Driver**: Texas Instruments DRV8210PDSGR
- **Fader**: ALPS ALPINE RS60N11M9A0F motor fader

### Pin Assignments

| Signal | GPIO | Function |
|--------|------|----------|
| IN1 | GPIO4 | Motor direction control (PWM) |
| IN2 | GPIO5 | Motor direction control (PWM) |
| nSLEEP | GPIO6 | Driver enable (active high) |
| POT_SENSE | GPIO2 | Position ADC (0-3.3V) |
| CURRENT_SENSE | GPIO3 | Motor current ADC |
| TOUCH_SENSE | GPIO1 | Capacitive touch detection |

### Motor Control Logic (DRV8210P)

| IN1 | IN2 | Result |
|-----|-----|--------|
| H | L | Forward |
| L | H | Reverse |
| L | L | Coast (stop) |
| H | H | Brake |

## Building

### Prerequisites

- Docker installed and running
- Python 3 with `esptool` (`pip install esptool`)

### Quick Start

```bash
# Make build script executable
chmod +x build.sh

# Initialize workspace (first time only)
./build.sh init

# Build firmware
./build.sh build

# Flash to ESP32-S3 (put in download mode first)
./build.sh flash

# Monitor serial output
./build.sh monitor
```

### Manual Docker Build

```bash
# Pull Docker image
docker pull zephyrprojectrtos/ci:v0.26.13

# Build
docker run --rm -v $(pwd):/workdir -w /workdir \
    zephyrprojectrtos/ci:v0.26.13 \
    bash -c "west init -l . && west update && west build -b esp32s3_devkitm"
```

### Flashing

Put ESP32-S3 in download mode:
1. Hold **BOOT** button
2. Press and release **RESET** button
3. Release **BOOT** button

Then flash:
```bash
python3 -m esptool --chip esp32s3 --port /dev/tty.usbmodem* \
    --baud 921600 write_flash 0x0 build/zephyr/zephyr.bin
```

## Usage

Connect via USB serial (115200 baud) to access the shell.

### Shell Commands

```
fader demo      - Start back-and-forth demo
fader stop      - Stop motor
fader cal       - Run endstop calibration
fader pos <%%>  - Set target position (0-100)
fader pid <Kp> <Ki> <Kd> - Set PID gains
fader motor <-100..100>  - Manual motor control
fader status    - Show system status
fader ff <mode> - Set force feedback mode
```

### Force Feedback Modes

| Mode | Value | Behavior |
|------|-------|----------|
| Disabled | 0 | No force feedback |
| Hold | 1 | Hold position, yield to user force |
| Spring | 2 | Spring back to target after release |
| Follow | 3 | Follow user movement |

## Features

### Closed-Loop Position Control

PID controller maintains fader position with:
- 100Hz control loop
- Anti-windup on integral term
- Configurable deadband
- Derivative-on-measurement to avoid kick

Default PID gains: `Kp=2.0, Ki=0.5, Kd=0.1`

### Endstop Calibration

Automatic calibration finds mechanical travel limits:
1. Drives motor slowly toward minimum
2. Detects stall via current sensing
3. Records min position
4. Repeats for maximum
5. Saves to NVS (non-volatile storage)

### Touch Detection & Force Feedback

- Capacitive touch sensing on fader knob
- Current-based force detection (backup)
- Multiple force feedback modes
- Smooth user override without fighting motor

## Project Structure

```
motor-fader-firmware/
├── CMakeLists.txt          # Build configuration
├── prj.conf                # Zephyr config
├── west.yml                # West manifest
├── Dockerfile              # Build environment
├── docker-compose.yml      # Docker services
├── build.sh                # Build helper script
├── boards/
│   └── esp32s3_devkitm.overlay  # Device tree overlay
└── src/
    ├── main.c              # Application entry point
    ├── motor_control.c/h   # H-bridge control
    ├── pid.c/h             # PID controller
    ├── calibration.c/h     # Endstop calibration
    └── touch_detect.c/h    # Touch & force feedback
```

## Tuning Guide

### PID Tuning

1. Start with `Kp` only, `Ki=0`, `Kd=0`
2. Increase `Kp` until oscillation begins
3. Reduce `Kp` by ~30%
4. Add small `Ki` for steady-state error
5. Add `Kd` if needed for faster response

```
fader pid 3.0 0.0 0.0   # Start with P only
fader pos 50            # Go to 50%
fader pid 3.0 0.3 0.0   # Add integral
fader pid 3.0 0.3 0.1   # Add derivative
```

### Calibration Tuning

If calibration fails or is inaccurate:
- Increase `CAL_MOTOR_SPEED` if motor stalls too easily
- Decrease `CAL_STALL_THRESHOLD` if not detecting stalls
- Increase `CAL_STALL_SAMPLES` for more robust detection

## License

MIT License - See LICENSE file

