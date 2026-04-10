#!/usr/bin/env python3
import os
import sys
import argparse

BOM = b'\xef\xbb\xbf'

def check_and_fix_bom(directory, fix=False):
    files_to_check = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.csv'):
                files_to_check.append(os.path.join(root, file))

    missing_bom = []
    for file_path in files_to_check:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        if not content.startswith(BOM):
            missing_bom.append(file_path)
            if fix:
                print(f"Adding BOM to {file_path}")
                with open(file_path, 'wb') as f:
                    f.write(BOM + content)
            else:
                print(f"Missing BOM: {file_path}")

    return missing_bom

def main():
    parser = argparse.ArgumentParser(description="Enforce UTF-8 BOM on CSV files.")
    parser.add_argument("--fix", action="store_true", help="Automatically add BOM if missing.")
    parser.add_argument("--dir", default="data", help="Directory to search for CSV files.")
    args = parser.parse_args()

    missing_bom = check_and_fix_bom(args.dir, args.fix)

    if missing_bom and not args.fix:
        print(f"\nError: {len(missing_bom)} CSV files are missing the UTF-8 BOM.")
        print("Please run this script with --fix or manually add the BOM to ensure Excel compatibility.")
        sys.exit(1)
    
    if not missing_bom:
        print("All CSV files have the correct UTF-8 BOM.")
    elif args.fix:
        print(f"\nSuccessfully added BOM to {len(missing_bom)} files.")

if __name__ == "__main__":
    main()
