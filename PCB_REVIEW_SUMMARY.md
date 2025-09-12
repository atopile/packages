# PCB Review Summary

## Changed KiCad PCB Files in PR

This document summarizes the KiCad PCB files that have been modified in the current PR and need manual review.

### Files Changed: 16 PCB files

| #   | Package          | File                                                                            | Changes      | Description                        |
| --- | ---------------- | ------------------------------------------------------------------------------- | ------------ | ---------------------------------- |
| 1   | adi-adbms6822    | `layouts/usage/usage.kicad_pcb`                                                 | +1848 -10    | Restored to main branch state      |
| 2   | maxim-max17048   | `layouts/default/default.kicad_pcb`                                             | +2498 -2460  | Max17048 fixes                     |
| 3   | maxim-max17048   | `layouts/usage/usage.kicad_pcb`                                                 | +2586 -2570  | Max17048 fixes                     |
| 4   | microphones      | `layouts/default/default.kicad_pcb`                                             | +87 -0       | New default build target           |
| 5   | microphones      | `layouts/knowles_sph0641lu4h_1/knowles_sph0641lu4h_1.kicad_pcb`                 | +727 -1233   | Package structure fixes            |
| 6   | microphones      | `layouts/linkmems_lma3722t421_oa5/linkmems_lma3722t421_oa5.kicad_pcb`           | +58 -716     | Package structure fixes            |
| 7   | microphones      | `layouts/linkmems_lmd2718t261_oa1/linkmems_lmd2718t261_oa1.kicad_pcb`           | +62 -391     | Package structure fixes            |
| 8   | microphones      | `layouts/tdk_invensense_ics_43434/tdk_invensense_ics_43434.kicad_pcb`           | +143 -765    | Package structure fixes            |
| 9   | microphones      | `layouts/tdk_invensense_mmict390200012/tdk_invensense_mmict390200012.kicad_pcb` | +78 -355     | Package structure fixes            |
| 10  | microphones      | `layouts/usage/usage.kicad_pcb`                                                 | +1140 -3566  | Package structure fixes            |
| 11  | nxp-pn5321       | `layouts/default/default.kicad_pcb`                                             | +9828 -9682  | Layout files updated after build   |
| 12  | nxp-pn5321       | `layouts/usage/usage.kicad_pcb`                                                 | +10024 -9990 | Layout files updated after build   |
| 13  | raspberry-rp2040 | `layouts/default/default.kicad_pcb`                                             | +9832 -9795  | Automated build and verify updates |
| 14  | raspberry-rp2040 | `layouts/usage/usage.kicad_pcb`                                                 | +50 -50      | Automated build and verify updates |
| 15  | st-vl53l4cd      | `layouts/default/default.kicad_pcb`                                             | +2411 -2367  | Build and verify fixes             |
| 16  | st-vl53l4cd      | `layouts/usage/usage.kicad_pcb`                                                 | +2539 -2509  | Build and verify fixes             |

## Review Scripts Available

Three scripts have been created to help with manual review:

### 1. `open_changed_pcbs.py` (Basic Python Script)

- Opens all changed PCB files in KiCad
- Simple confirmation dialog
- Basic error handling

### 2. `review_pcb_changes.py` (Advanced Python Script)

- Shows detailed change statistics for each file
- Displays related commit messages
- Interactive selection (open all or select specific files)
- Comprehensive review checklist

### 3. `open_changed_pcbs.sh` (Shell Script)

- Quick shell script alternative
- Simple and fast execution
- Minimal dependencies

## Usage Instructions

### Option 1: Run the advanced Python script (recommended)

```bash
./review_pcb_changes.py
```

### Option 2: Run the basic Python script

```bash
./open_changed_pcbs.py
```

### Option 3: Run the shell script

```bash
./open_changed_pcbs.sh
```

## Manual Review Checklist

For each opened PCB file, verify:

### Layout Integrity

- ✅ Component placement and orientation
- ✅ Routing and trace integrity
- ✅ Via placement and sizes
- ✅ Copper pour and ground planes

### Design Quality

- ✅ Silkscreen and component references
- ✅ Design rule compliance
- ✅ Layer stackup consistency
- ✅ Manufacturing requirements

### Package-Specific Concerns

- ✅ **microphones package**: Check that component removals didn't break layouts
- ✅ **maxim-max17048**: Verify fixes are correctly applied
- ✅ **nxp-pn5321**: Large changes - verify layout integrity
- ✅ **raspberry-rp2040**: Check automated updates are correct
- ✅ **st-vl53l4cd**: Verify build fixes maintained layout quality
- ✅ **adi-adbms6822**: Check restoration to main branch state

### High-Priority Reviews

Files with the most significant changes that need extra attention:

1. **nxp-pn5321** layouts (>9000 line changes each)
2. **raspberry-rp2040** default layout (>9000 line changes)
3. **maxim-max17048** layouts (~2500 line changes each)
4. **st-vl53l4cd** layouts (~2400-2500 line changes each)

## Notes

- All scripts require KiCad to be installed and accessible
- Files will open in separate KiCad windows
- Review should focus on unexpected changes or layout degradation
- Pay special attention to packages with large line count changes
