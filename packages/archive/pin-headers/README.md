# Pin Headers

A collection of standard 2.54mm pitch pin headers for through-hole mounting.

## Available Components

### Single Row (1xN)

| Size | Female | Male |
| ---- | ------ | ---- |
| 1x2  | ✅     | ✅   |
| 1x3  | ✅     | ✅   |
| 1x4  | ✅     | ✅   |
| 1x5  | ✅     | ✅   |
| 1x6  | ✅     | ✅   |
| 1x8  | ✅     | ❌   |
| 1x10 | ✅     | ✅   |

### Dual Row (2xN)

| Size | Female | Male |
| ---- | ------ | ---- |
| 2x2  | ❌     | ✅   |
| 2x7  | ✅     | ❌   |
| 2x8  | ✅     | ❌   |

## Usage

```ato
import "pin-headers"

// Example usage in your design
module MyModule:
    // Create a 1x4 female header
    header = new Female_2_54mm_1x4P_TH

    // Connect signals to the pins
    my_signal ~ header.p1
    another_signal ~ header.p2
```

## Package Contents

- Footprint and symbol definitions for all pin header variants
- Test module with examples of all available components

## License

This package is released under the MIT License.
