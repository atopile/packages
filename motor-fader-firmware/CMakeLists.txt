# SPDX-License-Identifier: Apache-2.0
# Motor Fader Firmware - Zephyr Project

cmake_minimum_required(VERSION 3.20.0)

# Find Zephyr package
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

project(motor_fader_firmware)

# Source files
target_sources(app PRIVATE
    src/main.c
    src/motor_control.c
    src/pid.c
    src/calibration.c
    src/touch_detect.c
)

# Include directories
target_include_directories(app PRIVATE
    src
)

