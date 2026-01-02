#!/usr/bin/env python3
"""
Simple step response test - records position at high frequency
Usage: uv run --with pyserial python step_test.py [target_percent]
"""
import serial
import time
import sys

PORT = '/dev/cu.usbmodem2101'
BAUD = 115200

# Target position (default 50%)
target = int(sys.argv[1]) if len(sys.argv) > 1 else 50

print(f"Step Response Test - Target: {target}%")
print("=" * 50)

ser = serial.Serial(PORT, BAUD, timeout=0.05)
ser.setDTR(False); time.sleep(0.1); ser.setDTR(True); time.sleep(0.1); ser.setDTR(False)
time.sleep(1.5)
ser.read(4096)  # Clear buffer

# Get starting position
ser.write(b'status\n')
time.sleep(0.1)
start_data = ser.read(2048).decode()
start_pos = "?"
for line in start_data.split('\n'):
    if 'normalized=' in line:
        start_pos = line.split('normalized=')[1].split('%')[0]
        break

print(f"Starting position: {start_pos}%")
print(f"Sending: pos {target}")
print()
print("time_ms,position")

# Send target position
ser.write(f'pos {target}\n'.encode())

# Record data at high frequency for 3 seconds
data = []
start_time = time.time()

while time.time() - start_time < 3.0:
    ser.write(b'status\n')
    time.sleep(0.02)  # 50Hz sampling
    
    response = ser.read(2048).decode()
    for line in response.split('\n'):
        if 'normalized=' in line:
            try:
                pos = float(line.split('normalized=')[1].split('%')[0])
                t_ms = int((time.time() - start_time) * 1000)
                data.append((t_ms, pos))
                print(f"{t_ms},{pos:.1f}")
            except:
                pass
            break

# Stop motor
ser.write(b'stop\n')
ser.close()

print()
print("=" * 50)
print(f"Captured {len(data)} samples")
if data:
    final_pos = data[-1][1]
    print(f"Final position: {final_pos:.1f}%")
    print(f"Error: {abs(target - final_pos):.1f}%")

