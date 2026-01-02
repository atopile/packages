# Motor Fader Firmware Build Environment
# Uses Zephyr CI image with ESP32 support

FROM zephyrprojectrtos/ci:v0.26.13

# Install additional tools for ESP32 flashing
RUN pip3 install esptool

# Set up workspace
WORKDIR /workdir

# Environment for Zephyr
ENV ZEPHYR_TOOLCHAIN_VARIANT=zephyr
ENV ZEPHYR_SDK_INSTALL_DIR=/opt/toolchains/zephyr-sdk-0.16.5

# Default command
CMD ["/bin/bash"]

