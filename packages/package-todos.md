Packages:
adi-ad5693r - Reviewed
adi-adbms6822
adi-adbms6830 - Reviewed
adi-adxl345 - Reviewed
adi-adxl375
adi-ds2482s-800 - Reviewed
adi-ltc4311 - Reviewed
adi-ltc4316 - Reviewed
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
indicator-leds - Reviewed
infineon-dps310 - Reviewed (version warning)
invensense-icm20948 - Reviewed (version warning)
invensense-mpu6050 - Reviewed
issi-is31fl3731 - Reviewed
liteon-ltr303 - Reviewed
liteon-ltr329 - Reviewed
liteon-ltr390uv - Reviewed
logos
macroblock-mbi5043 - Reviewed
maxim-ds1841 - Reviewed
maxim-ds18b20 - Reviewed
maxim-ds2484 - Reviewed (shadowing warnings)
maxim-ds3231 - Reviewed
maxim-ds3502 - Reviewed
maxim-max17048 - Failed Review (warning logs)
memsic-mmc5603 - Reviewed
microchip-24lc32 - Reviewed
microchip-cap1188 - Reviewed
microchip-emc2101 - Reviewed
microchip-mcp23017 - Reviewed
microchip-mcp3421 - Reviewed
microchip-mcp4725 - Reviewed
microchip-mcp4728 - Reviewed
microchip-mcp9601 - Reviewed
microchip-mcp9808 - Reviewed
rohm-bh1750 - Failed Review (README mismatch)
microphones - In Progress
mounting_holes
netties
nxp-pcf8574 - Reviewed
nxp-pcf8575 - Reviewed
nxp-pct2075 - Reviewed
nxp-pn5321 - Reviewed
opsco-sk6805-ec15 - Reviewed
st-h3lis331
st-ldk220
st-lsm303agr
st-lsm6ds3
st-vl53l4cd
st-vl53l4cx
opsco-sk6805-ec20 - Reviewed
opsco-sk6805-side - Reviewed
pjrc-teensy-4-1 - Reviewed
ti-dac6578
usb-connectors - Reviewed
raspberry-rp2040
realtek-rtl8305nb

Failing in CI:

build-verify-publish (packages/rohm-bh1750)
build-verify-publish (packages/st-h3lis331)
build-verify-publish (packages/st-ldk220)
build-verify-publish (packages/st-lsm303agr)
build-verify-publish (packages/st-lsm6ds3)
build-verify-publish (packages/st-vl53l4cd)
build-verify-publish (packages/st-vl53l4cx)
build-verify-publish (packages/ti-dac6578)

Pipeline:
Started -> Done -> In Review -> Reviewed

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
