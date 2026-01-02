#!/bin/bash
# Build script for Motor Fader Firmware
# Usage: ./build.sh [clean|build|flash|monitor|shell|chip-id]

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_IMAGE="zephyrprojectrtos/ci:v0.26.13"
BOARD="esp32s3_devkitm"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Activate venv if present
activate_venv() {
    if [ -d "$PROJECT_DIR/.venv" ]; then
        source "$PROJECT_DIR/.venv/bin/activate"
    fi
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_warn "Docker is not running."
        log_info "To start Docker on macOS: open -a Docker"
        log_info "Or install via: brew install --cask docker"
        return 1
    fi
    return 0
}

# Pull the Docker image if not present
pull_image() {
    if ! docker image inspect "$DOCKER_IMAGE" > /dev/null 2>&1; then
        log_info "Pulling Docker image: $DOCKER_IMAGE"
        docker pull "$DOCKER_IMAGE"
    fi
}

# Run command in Docker container
docker_run() {
    docker run --rm -it \
        -v "$PROJECT_DIR:/workdir" \
        -v motor-fader-zephyr-cache:/root/.cache \
        -w /workdir \
        "$DOCKER_IMAGE" \
        "$@"
}

# Initialize Zephyr workspace (run once)
init() {
    log_info "Initializing Zephyr workspace..."
    docker_run bash -c "
        if [ ! -d '.west' ]; then
            west init -l .
            west update
        else
            echo 'Workspace already initialized'
        fi
    "
}

# Clean build artifacts
clean() {
    log_info "Cleaning build artifacts..."
    rm -rf "$PROJECT_DIR/build"
    log_info "Clean complete"
}

# Build the firmware
build() {
    log_info "Building firmware for $BOARD..."
    docker_run bash -c "
        if [ ! -d '.west' ]; then
            west init -l .
            west update
        fi
        west build -b $BOARD -p auto
    "
    log_info "Build complete! Firmware at: build/zephyr/zephyr.bin"
}

# Find ESP32 serial port
find_port() {
    if ls /dev/cu.usbmodem* 2>/dev/null | head -n1; then
        return 0
    elif ls /dev/tty.usbmodem* 2>/dev/null | head -n1; then
        return 0
    elif [ -e /dev/ttyACM0 ]; then
        echo "/dev/ttyACM0"
        return 0
    fi
    return 1
}

# Check chip ID (verify ESP32 connection)
chip_id() {
    activate_venv
    log_info "Checking ESP32-S3 connection..."
    
    PORT=$(find_port)
    if [ -z "$PORT" ]; then
        log_error "No ESP32-S3 USB device found!"
        log_info "Make sure the board is connected via USB"
        exit 1
    fi
    
    log_info "Using port: $PORT"
    log_info "Put ESP32-S3 in download mode: Hold BOOT, press RESET, release BOOT"
    read -p "Press Enter when ready..."
    
    esptool --chip esp32s3 --port "$PORT" chip-id
}

# Flash the firmware (run on host with esptool)
flash() {
    activate_venv
    log_info "Flashing firmware to ESP32-S3..."
    
    PORT=$(find_port)
    if [ -z "$PORT" ]; then
        log_error "No ESP32-S3 USB device found!"
        log_info "Put ESP32 in download mode: Hold BOOT, press RESET, release BOOT"
        exit 1
    fi
    
    log_info "Using port: $PORT"
    log_info "Put ESP32-S3 in download mode: Hold BOOT, press RESET, release BOOT"
    read -p "Press Enter when ready..."
    
    # Use esptool to flash
    esptool --chip esp32s3 --port "$PORT" --baud 921600 \
        --before default_reset --after hard_reset \
        write_flash -z --flash_mode dio --flash_freq 80m --flash_size 16MB \
        0x0 build/zephyr/zephyr.bin
    
    log_info "Flash complete!"
}

# Monitor serial output
monitor() {
    activate_venv
    log_info "Starting serial monitor..."
    
    PORT=$(find_port)
    if [ -z "$PORT" ]; then
        log_error "No ESP32-S3 USB device found!"
        exit 1
    fi
    
    log_info "Monitoring $PORT (Ctrl+C to exit)"
    
    # Use screen or minicom or pyserial
    if command -v screen &> /dev/null; then
        screen "$PORT" 115200
    elif command -v minicom &> /dev/null; then
        minicom -D "$PORT" -b 115200
    else
        # Fallback to python serial
        python3 -c "
import serial
import sys
try:
    with serial.Serial('$PORT', 115200, timeout=0.1) as ser:
        print('Connected to $PORT at 115200 baud. Press Ctrl+C to exit.')
        while True:
            data = ser.read(1024)
            if data:
                sys.stdout.write(data.decode('utf-8', errors='replace'))
                sys.stdout.flush()
except KeyboardInterrupt:
    print('\nDisconnected.')
"
    fi
}

# Open interactive shell in Docker
shell() {
    log_info "Opening interactive shell in Docker..."
    docker_run bash
}

# Main
case "${1:-help}" in
    init)
        check_docker && pull_image && init
        ;;
    clean)
        clean
        ;;
    build)
        check_docker && pull_image && build
        ;;
    flash)
        flash
        ;;
    monitor)
        monitor
        ;;
    shell)
        check_docker && pull_image && shell
        ;;
    chip-id)
        chip_id
        ;;
    all)
        check_docker && pull_image && clean && build && flash
        ;;
    help|*)
        echo "Motor Fader Firmware Build Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Build Commands (require Docker):"
        echo "  init    - Initialize Zephyr workspace (run once)"
        echo "  build   - Build the firmware"
        echo "  shell   - Open interactive Docker shell"
        echo "  all     - Clean, build, and flash"
        echo ""
        echo "Device Commands (no Docker needed):"
        echo "  chip-id - Verify ESP32-S3 connection"
        echo "  flash   - Flash firmware to ESP32-S3"
        echo "  monitor - Open serial monitor"
        echo "  clean   - Remove build artifacts"
        echo ""
        echo "Prerequisites:"
        echo "  1. Start Docker: open -a Docker"
        echo "  2. For flashing: pip install esptool (or use .venv)"
        echo ""
        echo "To flash, put ESP32-S3 in download mode:"
        echo "  Hold BOOT button, press RESET, release BOOT"
        exit 0
        ;;
esac

