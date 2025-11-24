#!/usr/bin/env python3
"""sample_csvs.py

Reads CSV files from a directory, randomly samples a portion of each file,
and writes sampled files (or a combined CSV) to an output directory.

Usage examples:
  python sample_csvs.py --input-dir CSE-CIC-IDS2018 --pattern "*.csv" --frac 0.1 --seed 42 --output-dir sampled
  python sample_csvs.py -i CSE-CIC-IDS2018 -p "*.csv" -n 1000 --combine
"""

import argparse
import glob
import os
import sys
import pandas as pd
from sklearn.model_selection import train_test_split


def sample_df(df, frac=None, n=None, stratify_col=None, random_state=None):
    if frac is None and n is None:
        raise ValueError("Either frac or n must be provided")

    if stratify_col is not None and stratify_col in df.columns:
        try:
            # Use train_test_split to obtain a stratified sample
            test_size = frac if frac is not None else (float(n) / len(df))
            _, sampled = train_test_split(df, test_size=test_size, stratify=df[stratify_col], random_state=random_state)
            return sampled
        except Exception:
            # Fall back to plain sampling if stratified sampling fails
            pass

    if frac is not None:
        return df.sample(frac=frac, random_state=random_state)
    else:
        return df.sample(n=n, random_state=random_state)


def process_files(input_dir, pattern, frac, n, stratify_col, seed, output_dir, combine):
    pattern_path = os.path.join(input_dir, pattern)
    files = sorted(glob.glob(pattern_path))
    if not files:
        print(f"No files match {pattern_path}")
        return

    os.makedirs(output_dir, exist_ok=True)
    combined = []

    for path in files:
        fname = os.path.basename(path)
        print(f"Reading {fname}...")
        try:
            df = pd.read_csv(path, low_memory=False)
        except Exception as e:
            print(f"  Skipping {fname}: failed to read ({e})")
            continue

        try:
            sampled = sample_df(df, frac=frac, n=n, stratify_col=stratify_col, random_state=seed)
        except Exception as e:
            print(f"  Sampling failed for {fname}: {e}")
            continue

        if combine:
            combined.append(sampled)
        else:
            out_name = f"sampled_{fname}"
            out_path = os.path.join(output_dir, out_name)
            sampled.to_csv(out_path, index=False)
            print(f"  Wrote {out_path} ({len(sampled)} rows)")

    if combine and combined:
        combined_df = pd.concat(combined, ignore_index=True)
        out_path = os.path.join(output_dir, "sampled_combined.csv")
        combined_df.to_csv(out_path, index=False)
        print(f"Wrote combined file {out_path} ({len(combined_df)} rows)")


def parse_args():
    p = argparse.ArgumentParser(description="Sample multiple CSV files and save sampled outputs.")
    p.add_argument("--input-dir", "-i", required=True, help="Directory containing CSV files")
    p.add_argument("--pattern", "-p", default="*.csv", help="Glob pattern for CSV files (default: '*.csv')")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--frac", type=float, help="Fraction to sample from each file (0 < frac < 1)")
    group.add_argument("--n", type=int, help="Number of rows to sample from each file")
    p.add_argument("--stratify", help="Column name to use for stratified sampling (optional)")
    p.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    p.add_argument("--output-dir", "-o", default="sampled_output", help="Directory to write sampled files")
    p.add_argument("--combine", action="store_true", help="Combine all sampled results into a single CSV")
    return p.parse_args()


def main():
    args = parse_args()

    if args.frac is not None and not (0 < args.frac < 1):
        print("--frac must be between 0 and 1")
        sys.exit(1)

    process_files(
        input_dir=args.input_dir,
        pattern=args.pattern,
        frac=args.frac,
        n=args.n,
        stratify_col=args.stratify,
        seed=args.seed,
        output_dir=args.output_dir,
        combine=args.combine,
    )


if __name__ == "__main__":
    main()
