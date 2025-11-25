#!/usr/bin/env python3
"""compare_features.py

Compare flow feature names defined in `packet_sniffer.py` with the columns
present in a CSE-CIC-IDS2018 CSV file and report which dataset columns are
not covered by the feature list.

Usage:
  python compare_features.py --packet-file packet_sniffer.py --csv CSE-CIC-IDS2018/02-15-2018.csv

The script reads only the header of the CSV (fast) and extracts the feature
keys by parsing the `features = { ... }` literal inside `packet_sniffer.py`.
"""

import argparse
import ast
import re
import pandas as pd
import os
import sys


def extract_feature_keys_from_file(packet_file_path):
    """Parse the `features = { ... }` dict in packet_sniffer.py and return its keys."""
    text = open(packet_file_path, "r", encoding="utf-8").read()

    # Find the features = { ... } block inside extract_features. We'll search for "features\s*=\s*{"
    m = re.search(r"features\s*=\s*\{", text)
    if not m:
        raise RuntimeError("Couldn't find a 'features = {' block in the packet file")

    start = m.start()

    # Extract a balanced-brace chunk starting at the first '{' after the match
    brace_start = text.find('{', start)
    i = brace_start
    depth = 0
    while i < len(text):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                block = text[brace_start:i+1]
                break
        i += 1
    else:
        raise RuntimeError("Couldn't extract the features dict block (unbalanced braces)")

    # Use ast literal_eval on a transformed dict: convert any trailing commas and
    # keep only string keys. We'll attempt to parse the block as Python code.
    try:
        # Wrap the block into a variable assignment so ast can parse it safely
        parsed = ast.literal_eval(block)
        if isinstance(parsed, dict):
            return list(parsed.keys())
    except Exception:
        # If literal_eval fails (e.g., because values contain expressions),
        # fall back to a regex that extracts quoted keys.
        keys = re.findall(r"['\"]([A-Za-z0-9_ \-/]+?)['\"]\s*:\", block)
        return keys

    raise RuntimeError("Failed to parse feature keys from packet file")


def read_csv_columns(csv_path):
    # Read only header using pandas (fast and memory-efficient)
    try:
        df = pd.read_csv(csv_path, nrows=0)
        return list(df.columns)
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV header: {e}")


def main():
    p = argparse.ArgumentParser(description="Compare feature names against CSE-CIC-IDS2018 CSV columns")
    p.add_argument("--packet-file", default="packet_sniffer.py", help="Path to packet_sniffer.py (default: packet_sniffer.py)")
    p.add_argument("--csv", required=True, help="Path to one CSV file from CSE-CIC-IDS2018 to inspect")
    p.add_argument("--out", help="Optional output file to write missing features (one per line)")
    args = p.parse_args()

    if not os.path.exists(args.packet_file):
        print(f"Packet file not found: {args.packet_file}")
        sys.exit(1)
    if not os.path.exists(args.csv):
        print(f"CSV file not found: {args.csv}")
        sys.exit(1)

    print("Extracting feature keys from:", args.packet_file)
    feature_keys = extract_feature_keys_from_file(args.packet_file)
    print(f"Found {len(feature_keys)} feature keys in packet file")

    print("Reading CSV header:", args.csv)
    csv_cols = read_csv_columns(args.csv)
    print(f"CSV contains {len(csv_cols)} columns")

    set_features = set(k.strip() for k in feature_keys)
    set_csv = set(c.strip() for c in csv_cols)

    missing = sorted(list(set_csv - set_features))

    if missing:
        print("\nColumns in dataset but not in your feature list (sample):")
        for c in missing:
            print(" -", c)
    else:
        print("No missing columns: your feature list covers the CSV columns")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            for c in missing:
                f.write(c + "\n")
        print(f"Wrote {len(missing)} missing column names to {args.out}")


if __name__ == "__main__":
    main()
