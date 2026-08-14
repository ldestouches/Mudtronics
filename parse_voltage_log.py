#!/usr/bin/env python3
"""Parse Shewa plantarum voltage log into CSV format."""
import csv
import re
from pathlib import Path


def parse_voltage_log(input_path, output_path):
    """
    Read voltage log file and convert to CSV.
    
    Input format:
        voltage0 = -0.25
        voltage1 = 9.5
        voltage2 = -3.375
        voltage3 = -19.5
        02-03-2026 08:39:26
        voltage0 = ...
        ...
    
    Output CSV:
        timestamp,voltage0,voltage1,voltage2,voltage3
        02-03-2026 08:39:26,-0.25,9.5,-3.375,-19.5
        ...
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    rows = []
    
    with input_path.open('r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Parse in groups: 4 voltage lines + 1 timestamp line
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Try to match voltage line
        voltage_match = re.match(r'voltage(\d)\s*=\s*([\d\.\-]+)', line)
        
        if voltage_match:
            # Start of a voltage block
            voltages = {}
            
            # Read up to 4 voltage lines
            for v in range(4):
                if i + v >= len(lines):
                    break
                v_line = lines[i + v].strip()
                v_match = re.match(r'voltage(\d)\s*=\s*([\d\.\-]+)', v_line)
                if v_match:
                    ch = int(v_match.group(1))
                    val = float(v_match.group(2))
                    voltages[ch] = val
                else:
                    break
            
            # Next line should be timestamp
            if i + 4 < len(lines):
                ts_line = lines[i + 4].strip()
                # Try to match timestamp (DD-MM-YYYY HH:MM:SS)
                ts_match = re.match(r'(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})', ts_line)
                if ts_match and len(voltages) == 4:
                    timestamp = ts_match.group(1)
                    row = [
                        timestamp,
                        voltages.get(0, ''),
                        voltages.get(1, ''),
                        voltages.get(2, ''),
                        voltages.get(3, '')
                    ]
                    rows.append(row)
                    i += 5
                else:
                    i += 1
            else:
                i += 1
        else:
            i += 1
    
    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'voltage0', 'voltage1', 'voltage2', 'voltage3'])
        writer.writerows(rows)
    
    print(f'Parsed {len(rows)} readings from {input_path}')
    print(f'Wrote CSV to {output_path}')
    return output_path


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Parse Shewa plantarum voltage log to CSV')
    parser.add_argument('input', help='Input voltage log file')
    parser.add_argument('--output', '-o', default='shewa_plantarum_log.csv', 
                        help='Output CSV file (default: shewa_plantarum_log.csv)')
    
    args = parser.parse_args()
    parse_voltage_log(args.input, args.output)
