#!/usr/bin/env python3
"""
1kHz Step Response Capture
Usage: uv run --with pyserial python step1k.py <target%> [duration_ms] [Kp] [Ki] [Kd]
"""
import serial
import time
import sys

PORT = '/dev/cu.usbmodem2101'
BAUD = 115200

target = int(sys.argv[1]) if len(sys.argv) > 1 else 50
duration = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
kp = float(sys.argv[3]) if len(sys.argv) > 3 else None
ki = float(sys.argv[4]) if len(sys.argv) > 4 else None
kd = float(sys.argv[5]) if len(sys.argv) > 5 else None

print(f"1kHz Step Response - Target: {target}%, Duration: {duration}ms")

ser = serial.Serial(PORT, BAUD, timeout=0.1)
ser.setDTR(False); time.sleep(0.1); ser.setDTR(True); time.sleep(0.1); ser.setDTR(False)
time.sleep(1.5)
ser.read(4096)

# Set PID gains if provided
if kp is not None and ki is not None and kd is not None:
    print(f"Setting PID: Kp={kp}, Ki={ki}, Kd={kd}")
    ser.write(f'pid {kp} {ki} {kd}\n'.encode())
    time.sleep(0.2)
    ser.read(1024)

# Move to opposite end first
start_pos = 5 if target > 50 else 95
print(f"Moving to start position ({start_pos}%)...")
ser.write(f'motor {200 if start_pos < 50 else -200}\n'.encode())
time.sleep(1.5)
ser.write(b'stop\n')
time.sleep(0.3)
ser.read(4096)

# Send step command
print(f"Running step response...")
ser.write(f'step {target} {duration}\n'.encode())

# Capture all output
data = []
start_time = time.time()
timeout = duration / 1000 + 3  # Extra time for serial

while time.time() - start_time < timeout:
    line = ser.readline().decode(errors='ignore').strip()
    if line:
        if line.startswith('#'):
            print(line)
        elif ',' in line:
            data.append(line)
        if 'Done' in line:
            break

ser.close()

print(f"\nCaptured {len(data)} samples")

# Parse and analyze
times = []
positions = []
targets = []
motor_cmds = []

for line in data:
    try:
        parts = line.split(',')
        times.append(int(parts[0]))
        positions.append(float(parts[1]))
        targets.append(float(parts[2]))
        motor_cmds.append(int(parts[3]))
    except:
        pass

if positions:
    # Find oscillations
    direction_changes = 0
    going_up = positions[1] > positions[0] if len(positions) > 1 else True
    for i in range(2, len(positions)):
        new_up = positions[i] > positions[i-1]
        if new_up != going_up and abs(positions[i] - positions[i-1]) > 0.5:
            direction_changes += 1
            going_up = new_up
    
    # Calculate metrics
    final_pos = positions[-1]
    overshoot = 0
    if target > positions[0]:
        max_pos = max(positions)
        if max_pos > target:
            overshoot = max_pos - target
    else:
        min_pos = min(positions)
        if min_pos < target:
            overshoot = target - min_pos
    
    print(f"\n=== Analysis ===")
    print(f"Direction changes: {direction_changes}")
    print(f"Overshoot: {overshoot:.1f}%")
    print(f"Final position: {final_pos:.1f}%")
    print(f"Final error: {abs(final_pos - target):.1f}%")
    print(f"Range: {min(positions):.1f}% - {max(positions):.1f}%")
    
    # Simple ASCII plot
    print(f"\n=== Step Response ===")
    min_p, max_p = min(positions), max(positions)
    range_p = max(max_p - min_p, 1)
    
    step = max(1, len(times) // 30)
    for i in range(0, len(times), step):
        t = times[i]
        pos = positions[i]
        bar_len = int((pos - min_p) / range_p * 50)
        target_mark = int((target - min_p) / range_p * 50)
        
        graph = ['-'] * 51
        for j in range(bar_len + 1):
            graph[j] = '='
        if 0 <= target_mark <= 50:
            graph[target_mark] = '|'
        
        print(f"{t:4d}ms {pos:5.1f}% |{''.join(graph)}|")
    
    # Save data
    filename = f"step_{target}pct_{int(time.time())}.csv"
    with open(filename, 'w') as f:
        f.write("time_ms,position,target,motor_cmd\n")
        for line in data:
            f.write(line + '\n')
    print(f"\nData saved to: {filename}")

