Packages:
adi-ad5693r - Done
adi-adbms6822 - Failed Review
adi-adbms6830 - Needs Work (package verify failed - warning logs not empty)
adi-adxl345 - Reviewed
adi-adxl375 - Needs Work (package verify failed - missing usage build target)
adi-ds2482s-800 - Reviewed
adi-ltc4311 - Done
adi-ltc4316 - Done
allvision-oled128x32 - Reviewed
ams-tsl2591 - Reviewed
aosong-aht20 - Reviewed
audio - In Progress
awinic-aw9523 - Reviewed
bosch-bme280 - Reviewed
bosch-bme680 - Reviewed
bosch-bme688 - Reviewed
bosch-bmp280 - Reviewed
bosch-bmp388 - Reviewed
diodes-inc-74lvc1t45dw-7 - Reviewed
espressif-esp32-c3 - In Review
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
microchip-emc2101 - Done
microchip-mcp23017 - Done
microchip-mcp3421 - Done
microchip-mcp4725 - Done
microchip-mcp4728 - Done
microchip-mcp9601 - Done
microchip-mcp9808 - Done
rohm-bh1750 - Done
microphones - In Progress
mounting_holes
netties
nxp-pcf8574 - Done
nxp-pcf8575 - Done
nxp-pct2075 - Done
nxp-pn5321 - Done
opsco-sk6805-ec15 - Done
st-h3lis331 - Done
st-ldk220 - Done
st-lsm303agr - Done
st-lsm6ds3 - Done
st-vl53l4cd - Done
st-vl53l4cx - Done
opsco-sk6805-ec20 - Done
opsco-sk6805-side - Done
pjrc-teensy_4_1 - Done
ti-dac6578 - Done
usb-connectors - Done
raspberry-rp2040 - Done
realtek-rtl8305nb - Done

# Process - Worker

0. Find a package that has not been started above, then mark it as started
1. Run `ato build --frozen`, if no warnings and passes, skip to 4.
2. If failed, investigate warnings and fix
3. Run `ato build` and ensure clean build
4. Run `ato package verify -s`
5. If there are changes, commit them
6. If there are changes, bump the version by +0.0.1
7. Mark as done above

# Process - Reviewer

0. Find a package that has not been marked 'Done', then mark it as In Review
1. Run `ato build --frozen`
2. Run `ato package verify -s`
3. If both pass, marks 'Reviewed' - if it fails, mark as 'Failed Review'

# Notes

For picker warnings you may need to add:

trait has_part_removed

eg for an example MCU model that doesnt actually have a footprint
