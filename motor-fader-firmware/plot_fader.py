#!/usr/bin/env python3
"""
Motor Fader Data Capture and Plotting Tool

Usage:
    python plot_fader.py steps   - Run step demo and plot results
    python plot_fader.py log     - Log sensor data while you move fader manually
    python plot_fader.py plot <file.csv>  - Plot previously saved CSV data
"""

import serial
import time
import sys
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

PORT = '/dev/cu.usbmodem2101'
BAUD = 115200

def find_port():
    """Find ESP32 serial port"""
    import glob
    ports = glob.glob('/dev/cu.usbmodem*') + glob.glob('/dev/ttyACM*')
    if ports:
        return ports[0]
    return PORT

def capture_data(command, timeout=90):
    """Send command and capture CSV data"""
    port = find_port()
    print(f"Connecting to {port}...")
    
    ser = serial.Serial(port, BAUD, timeout=0.5)
    
    # Reset
    ser.setDTR(False)
    time.sleep(0.1)
    ser.setDTR(True)
    time.sleep(0.1)
    ser.setDTR(False)
    time.sleep(2)
    ser.read(4096)  # Clear buffer
    
    print(f"Sending '{command}' command...")
    ser.write(f'{command}\n'.encode())
    
    # Capture data
    lines = []
    start = time.time()
    
    while time.time() - start < timeout:
        data = ser.read(4096)
        if data:
            text = data.decode('utf-8', errors='replace')
            for line in text.split('\n'):
                line = line.strip()
                if line:
                    print(line)
                    lines.append(line)
            if 'complete' in text.lower():
                time.sleep(0.5)
                break
        time.sleep(0.05)
    
    ser.close()
    return lines

def parse_step_data(lines):
    """Parse step demo CSV data"""
    data = {
        'time': [],
        'target': [],
        'actual': [],
        'error': [],
        'motor': [],
        'current': []
    }
    
    for line in lines:
        if line.startswith('#') or ',' not in line:
            continue
        try:
            parts = line.split(',')
            if len(parts) >= 6:
                data['time'].append(int(parts[0]))
                data['target'].append(float(parts[1]))
                data['actual'].append(float(parts[2]))
                data['error'].append(float(parts[3]))
                data['motor'].append(int(parts[4]))
                data['current'].append(int(parts[5]))
        except (ValueError, IndexError):
            continue
    
    return data

def parse_log_data(lines):
    """Parse log command CSV data"""
    data = {
        'time': [],
        'raw_adc': [],
        'position': [],
        'current': []
    }
    
    for line in lines:
        if line.startswith('#') or ',' not in line:
            continue
        try:
            parts = line.split(',')
            if len(parts) >= 4:
                data['time'].append(int(parts[0]))
                data['raw_adc'].append(int(parts[1]))
                data['position'].append(float(parts[2]))
                data['current'].append(int(parts[3]))
        except (ValueError, IndexError):
            continue
    
    return data

def plot_step_data(data):
    """Plot step demo data"""
    if not data['time']:
        print("No data to plot!")
        return
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle('Motor Fader Step Response', fontsize=14, fontweight='bold')
    
    t = np.array(data['time']) / 1000  # Convert to seconds
    
    # Position plot
    ax1 = axes[0]
    ax1.plot(t, data['target'], 'r--', linewidth=2, label='Target', alpha=0.8)
    ax1.plot(t, data['actual'], 'b-', linewidth=1.5, label='Actual')
    ax1.fill_between(t, data['actual'], data['target'], alpha=0.3, color='orange')
    ax1.set_ylabel('Position (%)')
    ax1.set_ylim(0, 105)
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('Target vs Actual Position')
    
    # Error plot
    ax2 = axes[1]
    ax2.plot(t, data['error'], 'g-', linewidth=1)
    ax2.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    ax2.axhline(y=3, color='r', linestyle='--', linewidth=0.5, alpha=0.5)
    ax2.axhline(y=-3, color='r', linestyle='--', linewidth=0.5, alpha=0.5)
    ax2.set_ylabel('Error (%)')
    ax2.grid(True, alpha=0.3)
    ax2.set_title('Position Error')
    
    # Motor command and current
    ax3 = axes[2]
    ax3.plot(t, data['motor'], 'purple', linewidth=1, label='Motor Cmd')
    ax3_twin = ax3.twinx()
    ax3_twin.plot(t, data['current'], 'orange', linewidth=1, alpha=0.7, label='Current')
    ax3.set_ylabel('Motor Command', color='purple')
    ax3_twin.set_ylabel('Current (ADC)', color='orange')
    ax3.set_xlabel('Time (seconds)')
    ax3.grid(True, alpha=0.3)
    ax3.set_title('Motor Command & Current Draw')
    
    plt.tight_layout()
    
    # Save figure
    filename = f"fader_step_{datetime.now().strftime('%H%M%S')}.png"
    plt.savefig(filename, dpi=150)
    print(f"\nPlot saved to: {filename}")
    
    plt.show()

def plot_log_data(data):
    """Plot log data"""
    if not data['time']:
        print("No data to plot!")
        return
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    fig.suptitle('Motor Fader Sensor Log', fontsize=14, fontweight='bold')
    
    t = np.array(data['time']) / 1000
    
    # Position
    ax1 = axes[0]
    ax1.plot(t, data['position'], 'b-', linewidth=1)
    ax1.set_ylabel('Position (%)')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('Fader Position')
    
    # Raw ADC and current
    ax2 = axes[1]
    ax2.plot(t, data['raw_adc'], 'g-', linewidth=1, label='Raw ADC')
    ax2_twin = ax2.twinx()
    ax2_twin.plot(t, data['current'], 'orange', linewidth=1, alpha=0.7, label='Current')
    ax2.set_ylabel('Raw ADC', color='green')
    ax2_twin.set_ylabel('Current (ADC)', color='orange')
    ax2.set_xlabel('Time (seconds)')
    ax2.grid(True, alpha=0.3)
    ax2.set_title('Raw Sensor Values')
    
    plt.tight_layout()
    
    filename = f"fader_log_{datetime.now().strftime('%H%M%S')}.png"
    plt.savefig(filename, dpi=150)
    print(f"\nPlot saved to: {filename}")
    
    plt.show()

def save_csv(lines, prefix):
    """Save raw data to CSV file"""
    filename = f"{prefix}_{datetime.now().strftime('%H%M%S')}.csv"
    with open(filename, 'w') as f:
        for line in lines:
            f.write(line + '\n')
    print(f"Data saved to: {filename}")
    return filename

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'steps':
        print("Running step demo...")
        lines = capture_data('steps', timeout=90)
        save_csv(lines, 'step_data')
        data = parse_step_data(lines)
        print(f"\nCaptured {len(data['time'])} data points")
        plot_step_data(data)
        
    elif cmd == 'log':
        print("Logging sensor data for 5 seconds...")
        print("Move the fader by hand to see response!")
        lines = capture_data('log', timeout=10)
        save_csv(lines, 'log_data')
        data = parse_log_data(lines)
        print(f"\nCaptured {len(data['time'])} data points")
        plot_log_data(data)
        
    elif cmd == 'plot' and len(sys.argv) > 2:
        filename = sys.argv[2]
        print(f"Loading {filename}...")
        with open(filename) as f:
            lines = [l.strip() for l in f.readlines()]
        
        if 'step' in filename.lower():
            data = parse_step_data(lines)
            plot_step_data(data)
        else:
            data = parse_log_data(lines)
            plot_log_data(data)
    else:
        print(__doc__)

if __name__ == '__main__':
    main()

