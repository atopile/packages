#!/usr/bin/env python3
"""
PID Tuning Tool using Ziegler-Nichols Method

Step 1: Find ultimate gain (Ku) - P-only control until oscillation
Step 2: Measure oscillation period (Tu)  
Step 3: Calculate PID gains

Usage: uv run --with pyserial python tune_pid.py
"""
import serial
import time
import sys

PORT = '/dev/cu.usbmodem2101'
BAUD = 115200

def connect():
    ser = serial.Serial(PORT, BAUD, timeout=0.1)
    ser.setDTR(False); time.sleep(0.1); ser.setDTR(True); time.sleep(0.1); ser.setDTR(False)
    time.sleep(1.5)
    ser.read(4096)
    return ser

def set_pid(ser, kp, ki, kd):
    """Set PID gains on device"""
    cmd = f'pid {kp} {ki} {kd}\n'
    ser.write(cmd.encode())
    time.sleep(0.1)
    ser.read(1024)  # Clear response

def get_position(ser):
    """Get current position as float 0-100"""
    ser.write(b'status\n')
    time.sleep(0.05)
    data = ser.read(2048).decode()
    for line in data.split('\n'):
        if 'normalized=' in line:
            try:
                return float(line.split('normalized=')[1].split('%')[0])
            except:
                pass
    return None

def step_response(ser, target, duration=4.0):
    """Record step response data at high frequency using device logging"""
    # Move to starting position first (opposite of target)
    start_pos = 5 if target > 50 else 95
    ser.write(f'motor {200 if start_pos < 50 else -200}\n'.encode())
    time.sleep(1.5)
    ser.write(b'stop\n')
    time.sleep(0.3)
    ser.read(4096)  # Clear buffer
    
    data = []
    start_time = time.time()
    
    # Send target position command
    ser.write(f'pos {target}\n'.encode())
    
    # High frequency polling - as fast as possible
    while time.time() - start_time < duration:
        ser.write(b'status\n')
        time.sleep(0.015)  # ~66Hz
        
        response = ser.read(4096).decode(errors='ignore')
        for line in response.split('\n'):
            if 'normalized=' in line:
                try:
                    pos = float(line.split('normalized=')[1].split('%')[0])
                    t = time.time() - start_time
                    data.append((t, pos))
                except:
                    pass
    
    ser.write(b'stop\n')
    return data

def analyze_response(data, target):
    """Analyze step response for oscillation"""
    if len(data) < 20:
        return None
    
    positions = [d[1] for d in data]
    times = [d[0] for d in data]
    
    # Smooth data slightly to reduce noise (3-point moving average)
    smoothed = positions[:1]
    for i in range(1, len(positions) - 1):
        smoothed.append((positions[i-1] + positions[i] + positions[i+1]) / 3)
    smoothed.append(positions[-1])
    
    # Find peaks with hysteresis (need >2% change to count as peak)
    peaks = []
    last_peak_val = smoothed[0]
    last_peak_type = None
    
    for i in range(1, len(smoothed) - 1):
        # Local maximum
        if smoothed[i] > smoothed[i-1] and smoothed[i] > smoothed[i+1]:
            if last_peak_type != 'max' and smoothed[i] - last_peak_val > 2:
                peaks.append((times[i], smoothed[i], 'max'))
                last_peak_val = smoothed[i]
                last_peak_type = 'max'
        # Local minimum
        elif smoothed[i] < smoothed[i-1] and smoothed[i] < smoothed[i+1]:
            if last_peak_type != 'min' and last_peak_val - smoothed[i] > 2:
                peaks.append((times[i], smoothed[i], 'min'))
                last_peak_val = smoothed[i]
                last_peak_type = 'min'
    
    # Count direction changes (more reliable than target crossings)
    direction_changes = 0
    if len(smoothed) > 2:
        going_up = smoothed[1] > smoothed[0]
        for i in range(2, len(smoothed)):
            new_going_up = smoothed[i] > smoothed[i-1]
            if new_going_up != going_up and abs(smoothed[i] - smoothed[i-1]) > 1:
                direction_changes += 1
                going_up = new_going_up
    
    # Count target crossings
    crossings = 0
    above_target = positions[0] > target
    for pos in positions[1:]:
        if (pos > target) != above_target:
            crossings += 1
            above_target = pos > target
    
    # Calculate overshoot
    final_pos = positions[-1]
    start_pos = positions[0]
    if target > start_pos:
        max_pos = max(positions)
        overshoot = max(0, (max_pos - target) / (target - start_pos) * 100) if abs(target - start_pos) > 1 else 0
    else:
        min_pos = min(positions)
        overshoot = max(0, (target - min_pos) / (start_pos - target) * 100) if abs(target - start_pos) > 1 else 0
    
    # Estimate oscillation period from peaks
    period = None
    max_peaks = [p for p in peaks if p[2] == 'max']
    if len(max_peaks) >= 2:
        period = max_peaks[1][0] - max_peaks[0][0]
    
    return {
        'crossings': crossings,
        'direction_changes': direction_changes,
        'peaks': len(peaks),
        'overshoot': overshoot,
        'final_error': abs(final_pos - target),
        'period': period,
        'settled': abs(final_pos - target) < 3,
        'samples': len(data)
    }

def print_response(data, target):
    """Print step response as simple ASCII plot"""
    if not data:
        return
    
    positions = [d[1] for d in data]
    min_p, max_p = min(positions), max(positions)
    range_p = max(max_p - min_p, 1)
    
    print(f"\nStep Response (target={target}%, range={min_p:.1f}-{max_p:.1f}%):")
    print("-" * 65)
    
    # Sample points for display (show ~25 lines)
    step = max(1, len(data) // 25)
    for i in range(0, len(data), step):
        t, pos = data[i]
        bar_len = int((pos - min_p) / range_p * 40)
        target_mark = int((target - min_p) / range_p * 40)
        bar = '=' * bar_len
        
        # Build the line
        graph = [' '] * 41
        for j in range(bar_len):
            graph[j] = '='
        if 0 <= target_mark <= 40:
            graph[target_mark] = '|'
        
        print(f"{t:5.2f}s {pos:5.1f}% |{''.join(graph)}|")
    
    print("-" * 65)
    print(f"  Range: {max_p - min_p:.1f}%  Target line marked with |")

def main():
    print("=" * 60)
    print("PID Tuning Tool - Ziegler-Nichols Method")
    print("=" * 60)
    print()
    print("Step 1: Find Ultimate Gain (Ku)")
    print("  - Starting with P-only control (Ki=0, Kd=0)")
    print("  - Increasing Kp until sustained oscillation")
    print()
    
    ser = connect()
    
    # Ziegler-Nichols: Start with P-only
    kp_values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0]
    target = 50
    
    ku = None  # Ultimate gain
    tu = None  # Ultimate period
    
    for kp in kp_values:
        print(f"\n>>> Testing Kp={kp} (Ki=0, Kd=0)")
        set_pid(ser, kp, 0, 0)
        time.sleep(0.3)
        
        data = step_response(ser, target, duration=4.0)
        
        if data:
            analysis = analyze_response(data, target)
            print_response(data, target)
            
            if analysis:
                print(f"  Samples: {analysis['samples']}")
                print(f"  Peaks detected: {analysis['peaks']}")
                print(f"  Direction changes: {analysis['direction_changes']}")
                print(f"  Target crossings: {analysis['crossings']}")
                print(f"  Overshoot: {analysis['overshoot']:.1f}%")
                print(f"  Final error: {analysis['final_error']:.1f}%")
                if analysis['period']:
                    print(f"  Est. period: {analysis['period']:.3f}s")
                
                # Sustained oscillation = multiple peaks or direction changes
                oscillating = analysis['peaks'] >= 4 or analysis['direction_changes'] >= 6
                if oscillating:
                    ku = kp
                    tu = analysis['period'] or 0.3  # Default period
                    print(f"\n*** OSCILLATION DETECTED at Kp={kp} ***")
                    print(f"*** This is your Ultimate Gain (Ku) ***")
                    break
                elif analysis['overshoot'] > 50:
                    print(f"  >> High overshoot - getting close to Ku")
        
        resp = input("Press Enter to continue (or 'q' to quit, 's' to skip to calculations): ")
        if resp.lower() == 'q':
            ser.close()
            return
        if resp.lower() == 's':
            ku = float(input("Enter your estimated Ku: "))
            tu = float(input("Enter your estimated Tu (oscillation period in seconds): "))
            break
    
    if ku:
        print()
        print("=" * 60)
        print("Step 2: Calculate PID Gains (Ziegler-Nichols)")
        print("=" * 60)
        print(f"Ultimate Gain (Ku) = {ku}")
        print(f"Ultimate Period (Tu) = {tu:.2f}s")
        print()
        
        # Ziegler-Nichols formulas
        # Classic PID: Kp = 0.6*Ku, Ki = 2*Kp/Tu, Kd = Kp*Tu/8
        # No overshoot: Kp = 0.2*Ku, Ki = 2*Kp/Tu, Kd = Kp*Tu/3
        
        print("Classic PID (some overshoot):")
        kp_classic = 0.6 * ku
        ki_classic = 2 * kp_classic / tu
        kd_classic = kp_classic * tu / 8
        print(f"  Kp = {kp_classic:.2f}")
        print(f"  Ki = {ki_classic:.2f}")
        print(f"  Kd = {kd_classic:.2f}")
        print()
        
        print("No-Overshoot PID:")
        kp_no = 0.2 * ku
        ki_no = 2 * kp_no / tu
        kd_no = kp_no * tu / 3
        print(f"  Kp = {kp_no:.2f}")
        print(f"  Ki = {ki_no:.2f}")
        print(f"  Kd = {kd_no:.2f}")
        print()
        
        print("To apply, run:")
        print(f"  Classic: pid {kp_classic:.2f} {ki_classic:.2f} {kd_classic:.2f}")
        print(f"  No-overshoot: pid {kp_no:.2f} {ki_no:.2f} {kd_no:.2f}")
    else:
        print("\nNo sustained oscillation found. Try higher Kp values.")
    
    ser.close()

if __name__ == '__main__':
    main()

