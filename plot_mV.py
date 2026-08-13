#!/usr/bin/env python3
"""
Simple script to parse soil log text files, save combined CSVs, and plot voltages V0, V1, V2
as voltage traces over time (time shown in days). The script reads files, combines them,
creates a wide CSV (one row per timestamp with V0..V3) and a long/tidy CSV (date, time, name, value),
then plots V0 (autoclaved soil), V1 (soil culture 1) and V2 (soil culture 2). The plot is saved as PNG.

Usage: python plot_mV.py

Adjust the FILE_PATHS list below if your files are in a different location.
"""

from datetime import datetime
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# --- Configuration ---
# Update these paths if your files are elsewhere
FILE_PATHS = [
    "20260802_soil_log.txt",
    "20260805_soil_log.txt",
]
OUTPUT_CSV_WIDE = "combined_soil_wide.csv"   # date,time,V0,V1,V2,V3
OUTPUT_CSV_LONG = "combined_soil_long.csv"   # date,time,name,value
OUTPUT_PNG = "soil_plot.png"

# Mapping from voltage column to human-friendly sample name
NAME_MAP = {
    'V0': 'autoclaved soil',
    'V1': 'soil culture 1',
    'V2': 'soil culture 2',
    # V3 is present in the files but not plotted; keep it in the wide CSV
}


def parse_log_file(path):
    """Parse one log file and return a list of records with datetime and V0..V3 floats.

    The file format repeats blocks of 4 voltage lines followed by a datetime line, e.g.:
      voltage0 = 108.75
      voltage1 = -113.25
      voltage2 = -90.125
      voltage3 = 529.125
      20-03-2026 14:14:34

    The function is robust to stray empty lines and will scan for voltage0 markers.
    """
    records = []
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    with p.open('r', encoding='utf-8', errors='ignore') as fh:
        # read and strip lines
        raw_lines = [ln.strip() for ln in fh if ln.strip()]

    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        # look for a voltage0 line to begin a block
        if line.lower().startswith('voltage0'):
            try:
                v0_line = raw_lines[i]
                v1_line = raw_lines[i + 1]
                v2_line = raw_lines[i + 2]
                v3_line = raw_lines[i + 3]
                dt_line = raw_lines[i + 4]
            except IndexError:
                # reached end of file with incomplete block
                break

            def parse_voltage(s):
                # expect 'voltageN = <number>'
                if '=' in s:
                    return float(s.split('=', 1)[1].strip())
                # fallback: try to parse the whole string
                return float(s)

            try:
                v0 = parse_voltage(v0_line)
                v1 = parse_voltage(v1_line)
                v2 = parse_voltage(v2_line)
                v3 = parse_voltage(v3_line)
            except ValueError:
                # If parsing fails, skip this block
                i += 1
                continue

            # parse datetime like '20-03-2026 14:14:34'
            try:
                dt = datetime.strptime(dt_line, '%d-%m-%Y %H:%M:%S')
            except ValueError:
                # try alternative common format(s) if present
                try:
                    dt = datetime.strptime(dt_line, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    i += 1
                    continue

            records.append({
                'datetime': dt,
                'date': dt.strftime('%Y-%m-%d'),
                'time': dt.strftime('%H:%M:%S'),
                'V0': v0,
                'V1': v1,
                'V2': v2,
                'V3': v3,
                'source_file': str(p.name),
            })

            i += 5
        else:
            # not the start of a block; move on
            i += 1

    return records


def build_dataframes(file_paths):
    all_records = []
    for fp in file_paths:
        recs = parse_log_file(fp)
        all_records.extend(recs)

    if not all_records:
        raise RuntimeError('No records parsed from the provided files')

    # build wide DataFrame
    df_wide = pd.DataFrame(all_records)
    df_wide.sort_values('datetime', inplace=True)
    df_wide.reset_index(drop=True, inplace=True)

    # save wide CSV with date and time columns first
    df_wide_out = df_wide[['date', 'time', 'V0', 'V1', 'V2', 'V3', 'source_file', 'datetime']]
    df_wide_out.to_csv(OUTPUT_CSV_WIDE, index=False)

    # build long/tidy DataFrame for V0..V2 (we don't need V3 for plotting)
    df_long = df_wide.melt(
        id_vars=['date', 'time', 'datetime', 'source_file'],
        value_vars=['V0', 'V1', 'V2'],
        var_name='voltage',
        value_name='value'
    )
    # map voltage column to human-friendly name
    df_long['name'] = df_long['voltage'].map(NAME_MAP)
    df_long = df_long[['date', 'time', 'name', 'value', 'datetime', 'source_file']]
    df_long.to_csv(OUTPUT_CSV_LONG, index=False)

    return df_wide, df_long


def plot_voltages(df_wide):
    # compute time in days relative to start
    t0 = df_wide['datetime'].min()
    df_wide['days'] = df_wide['datetime'].apply(lambda d: (d - t0).total_seconds() / 86400.0)

    plt.figure(figsize=(10, 5))

    # Plot V0 (autoclaved soil) in black, V1 and V2 in default colors
    plt.plot(df_wide['days'], df_wide['V0'], color='black', label='autoclaved soil')
    plt.plot(df_wide['days'], df_wide['V1'], label='soil culture 1')
    plt.plot(df_wide['days'], df_wide['V2'], label='soil culture 2')

    plt.xlabel("Time (days)")
    plt.ylabel('Voltage (mV)')
    plt.title('Soil voltages over time')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Set x-ticks every 2 days
    min_day = df_wide['days'].min()
    max_day = df_wide['days'].max()
    # create ticks starting from floor(min_day) to ceil(max_day) step 2
    import math
    start_tick = math.floor(min_day)
    end_tick = math.ceil(max_day)
    if end_tick <= start_tick:
        ticks = [start_tick]
    else:
        ticks = list(range(start_tick, end_tick + 1, 2))
    plt.xticks(ticks)

    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=200)
    print(f"Saved plot to {OUTPUT_PNG}")


def main():
    print('Parsing files...')
    df_wide, df_long = build_dataframes(FILE_PATHS)
    print(f'Wrote wide CSV: {OUTPUT_CSV_WIDE} (rows={len(df_wide)})')
    print(f'Wrote long CSV: {OUTPUT_CSV_LONG} (rows={len(df_long)})')

    print('Plotting...')
    plot_voltages(df_wide)
    print('Done.')


if __name__ == '__main__':
    main()
