Packages:
adi-ad5693r - Done
adi-adbms6822 - Done
adi-adbms6830 - Done
adi-adxl345 - Done
adi-adxl375 - Done
adi-ds2482s-800 - Done
adi-ltc4311 - Done
adi-ltc4316 - Done
allvision-oled128x32 - Done
ams-tsl2591 - Done
aosong-aht20 - Done
archive
audio
awinic-aw9523 - Done
bosch-bme280 - Done
bosch-bme680 - Done
bosch-bme688 - Done
bosch-bmp280 - Done
bosch-bmp388 - Done
diodes-inc-74lvc1t45dw-7 - Done
espressif-esp32-c3 - Done
indicator-leds - Done
infineon-dps310 - Done
invensense-icm20948 - Done
invensense-mpu6050 - Done
issi-is31fl3731 - Done
liteon-ltr303 - Done
liteon-ltr329 - Done
liteon-ltr390uv - Done
logos
macroblock-mbi5043 - Done
maxim-ds1841 - Done
maxim-ds18b20 - Done
maxim-ds2484 - Done
maxim-ds3231 - Done
maxim-ds3502 - Done
maxim-max17048 - Done
memsic-mmc5603 - Done
microchip-24lc32 - Done
microchip-cap1188 - Done
microchip-emc2101
microchip-mcp23017
microchip-mcp3421
microchip-mcp4725
microchip-mcp4728
microchip-mcp9601
microchip-mcp9808
rohm-bh1750 - Done
microphones
mounting_holes
netties
nxp-pcf8574
nxp-pcf8575
nxp-pct2075
nxp-pn5321
opsco-sk6805-ec15
st-h3lis331 - Done
st-ldk220 - Done
st-lsm303agr - Done
st-lsm6ds3 - Done
st-vl53l4cd - Done
st-vl53l4cx - Done
opsco-sk6805-ec20
opsco-sk6805-side
pci-express-connectors
pjrc-teensy_4_1 - Done
ti-dac6578 - Done
usb-connectors - Done
raspberry-rp2040
realtek-rtl8305nb

# Process:

0. Find a package that has not been started above, then mark it as started
1. Run `ato build --frozen`, if no warnings and passes, skip to 4.
2. If failed, investigate warnings and fix
3. Run `ato build` and ensure clean build
4. Run `ato package verify -s`
5. If there are changes, commit them
6. If there are changes, bump the version by +0.0.1
7. Mark as done above

# Reviewer

If a package is d

If you get stuck, mark the package as 'need help'e,

# Notes

For picker warnings you may need to add:

trait has_part_removed

eg for an example MCU model that doesnt actually have a footprint
