# Networked Logic Analyzer — Specification

## Overview

100+ channel, 50 MHz, network-streaming logic analyzer with FPGA-based transition compression and deep DDR3 capture buffer. Designed for continuous capture with software-defined triggering — the instrument streams everything, and analysis/triggering happens on the backend.

## Block Diagram

```
                                    ┌─────────────┐
                                    │  SPI Flash   │
                                    │  (Bitstream) │
                                    └──────┬───────┘
                                           │ SPI (shared)
  ┌──────────────┐    FMC 8-bit    ┌───────┴───────┐
  │              │◄───────────────►│               │
  │   STM32H723  │    SPI ctrl     │   ECP5 FPGA   │
  │              │◄───────────────►│  (LFE5U-25F)  │
  │              │                 │               │
  └──┬──┬──┬──┬──┘                 └──┬─────────┬──┘
     │  │  │  │                       │         │
     │  │  │  │                   ┌───┴──┐  ┌───┴──────────┐
     │  │  │  │                   │ DDR3 │  │  Card-Edge   │
     │  │  │  │                   │512 MB│  │  100+ ch     │
     │  │  │  │                   └──────┘  │  50 MHz      │
     │  │  │  │                             └──────────────┘
     │  │  │  └── SWD (debug header)
     │  │  └───── USB-C (power + USB 2.0 FS)
     │  └──────── MDIO
     └─────────── RMII ──► LAN8742A PHY ──► RJ45 (100 Mbit)
```

## Power Architecture

| Rail   | Voltage       | Source        | Load                              |
|--------|---------------|---------------|-----------------------------------|
| 5V0    | 5.0V ± 5%    | USB-C VBUS    | Input, bulk cap                   |
| 3V3    | 3.3V ± 5%    | LDO from 5V0  | STM32, FPGA IO Banks 0-3/8, PHY  |
| 2V5    | 2.5V ± 5%    | LDO from 5V0  | FPGA VCCAUX                       |
| 1V35   | 1.35V ± 5%   | LDO from 3V3  | DDR3 VDDQ, FPGA IO Banks 6-7     |
| 1V35int| 1.35V ± 5%   | Ferrite from 1V35 | DDR3 VTT (internal termination)|
| 1V1    | 1.1V ± 5%    | LDO from 3V3  | FPGA core (VCC)                   |

All rails share common ground. Bulk capacitors on each rail. Ferrite bead filters VCCAUX and DDR3 internal termination.

## Channel Specification

- **Channel count:** 100+ (target ~108 usable FPGA IOs)
- **Logic levels:** 3.3V LVCMOS (FPGA IO bank voltage)
- **Max sample rate:** 50 MHz (all channels simultaneously)
- **Connector:** Card-edge (PCIe-style or high-density board-to-board)
- **Pin budget:**

| FPGA Bank | Total IOs | Allocation            | Probe Channels |
|-----------|-----------|-----------------------|----------------|
| 0         | 24        | Probe channels        | 24             |
| 1         | 32        | Probe channels        | 32             |
| 2         | 32        | STM32 FMC bus (~12)   | ~20            |
| 3         | 32        | SPI ctrl (~4), probes | ~28            |
| 6         | 32        | DDR3 address/ctrl     | 0              |
| 7         | 32        | DDR3 data             | 0              |
| 8         | 13        | JTAG/config/SPI flash | 0              |
| **Total** |           |                       | **~104**       |

## Data Path

```
Raw: 100 ch × 50 MHz = 625 MB/s
  → FPGA transition compression (~20:1 to 100:1 typical)
  → DDR3 ring buffer (512 MB continuous)
  → 8-bit FMC readout to STM32
  → Optional LZ4 second-stage compression
  → TCP over 100 Mbit Ethernet → Backend
```

## Capture Mode

**Continuous streaming only.** The instrument captures and streams all data continuously. There is no hardware trigger engine — all triggering, filtering, and analysis is performed in software on the backend. The DDR3 ring buffer provides deep buffering to absorb network latency and bandwidth variations.

## Interfaces

### Ethernet (100 Mbit)
- LAN8742A PHY connected to STM32 via RMII + MDIO
- RJ45 connector with integrated magnetics
- TCP streaming protocol with custom framing

### USB-C
- Power input (5V VBUS)
- USB 2.0 Full-Speed device (CDC serial for config/debug/initial bring-up)

### FPGA ↔ STM32 Communication
- **FMC 8-bit parallel bus:** High-bandwidth data path for captured samples
  - D[0:7] data lines + NOE (read) + NWE (write) + NE1 (chip select) + FIFO_READY (IRQ)
  - STM32 FMC peripheral in async SRAM mode
  - MDMA for zero-copy transfers to network stack
- **SPI control bus:** Low-bandwidth register interface
  - Sample rate config, arm/disarm, status readback, DDR3 test commands
  - STM32 SPI master → FPGA SPI slave

### SPI Flash
- W25Q32 or W25Q128 (4-16 MB)
- Connected to ECP5 sysCONFIG pins for native FPGA boot
- STM32 can write bitstream for OTA FPGA updates (shared SPI bus or dedicated)

### Debug
- STM32 SWD via TC2050 pogo-pin header
- ECP5 JTAG pins exposed (on-board JTAG adapter TBD)

## Self-Test Architecture

### FPGA → FPGA Loopback
- 4-8 FPGA output pins routed back to input channel pins
- FPGA generates known patterns, captures them, verifies in DDR3
- Tests: input buffers, capture engine, compression, DDR3 write/read

### FPGA → STM32 Loopback
- A few FPGA outputs routed to STM32 GPIO inputs (separate from FMC)
- STM32 commands pattern generation via SPI, reads back on GPIO
- Tests: SPI control path, FPGA fabric, STM32 GPIO

### STM32 Self-Test
- ADC reads voltage dividers on each power rail (5V0, 3V3, 2V5, 1V35, 1V1)
- Ethernet link status via MDIO
- USB enumeration check
- SPI flash JEDEC ID read

## Status Indicators
- Power LED (3.3V rail)
- Ethernet link LED (directly from PHY/RJ45)
- Capture active LED (STM32 GPIO)
- FPGA DONE LED (ECP5 DONE pin)

## OTA Updates
- **STM32 firmware:** Network-triggered, dual-bank flash update
- **FPGA bitstream:** STM32 writes new bitstream to SPI flash, asserts PROGRAMN to reload

## Firmware Architecture (future)

### STM32
- FMC DMA reception (MDMA → AXI SRAM double-buffer)
- lwIP TCP stack with custom framing protocol
- USB CDC serial console
- OTA bootloader
- Self-test suite

### FPGA Gateware
- Transition-only compression (XOR change detect → timestamp + channel values)
- DDR3 circular ring buffer with write/read pointers
- FMC slave interface (8-bit async SRAM emulation)
- SPI slave control registers
- Self-test pattern generator on loopback pins

## Backend + Viewer (future)

### Backend
- Rust TCP ingest service with LZ4 decompression
- TimescaleDB for transition storage
- mDNS device discovery

### Viewer
- Tauri + React + WebGL cross-platform app
- GPU-accelerated waveform rendering
- Protocol analyzer plugins (UART, SPI, I2C, JTAG/SWD)
- Zoomable timeline, measurement cursors, search, bookmarks, VCD/CSV export
