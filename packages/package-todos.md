Packages to fix
build-verify-publish (packages/adi-adbms6822) - Done
build-verify-publish (packages/adi-adxl375) - Done
build-verify-publish (packages/maxim-ds2484) - Started
build-verify-publish (packages/maxim-max17048) - Done
build-verify-publish (packages/rohm-bh1750)
build-verify-publish (packages/st-h3lis331) - Started
build-verify-publish (packages/st-ldk220) - Done
build-verify-publish (packages/st-lsm303agr) - Done
build-verify-publish (packages/st-lsm6ds3) - Started
build-verify-publish (packages/st-vl53l4cd) - Done
build-verify-publish (packages/st-vl53l4cx) - Done
build-verify-publish (packages/ti-dac6578) - Done

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
