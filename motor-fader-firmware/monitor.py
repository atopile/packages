#!/usr/bin/env python3
"""ADC channel monitor - move the fader and see which channel changes!"""
import serial
import time
import sys

PORT = '/dev/cu.usbmodem2101'

ser = serial.Serial(PORT, 115200, timeout=0.1)
ser.setDTR(False); time.sleep(0.1); ser.setDTR(True); time.sleep(0.1); ser.setDTR(False)
time.sleep(2)
ser.read(4096)

print('Move the fader and watch which GPIO changes!')
print('Press Ctrl+C to stop\n')

try:
    while True:
        ser.write(b'scan\n')
        time.sleep(0.3)
        data = ser.read(4096).decode()
        
        # Parse GPIO values
        vals = {}
        for line in data.split('\n'):
            if 'GPIO' in line and ':' in line:
                parts = line.strip().split(':')
                gpio = parts[0].strip()
                val = parts[1].strip()
                vals[gpio] = val
        
        # Print on one line
        out = '  '.join([f'{k}:{v:>4}' for k,v in sorted(vals.items())])
        print(f'\r{out}', end='', flush=True)
        time.sleep(0.2)
except KeyboardInterrupt:
    print('\nDone!')
finally:
    ser.close()

