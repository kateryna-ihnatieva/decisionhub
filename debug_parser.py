#!/usr/bin/env python3
"""
Debug script for file parser
"""

import os
import sys
import tempfile
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mymodules.file_parser import FileParser


def debug_hierarchy_parsing():
    """Debug hierarchy file parsing"""
    print("Debugging hierarchy file parsing...")

    # Create test file
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "debug_hierarchy.xlsx")

    # Create test data
    data = []
    data.append(["", "Quality", "Price", "Service"])
    data.append(["Quality", 1, 2, 3])
    data.append(["Price", 0.5, 1, 4])
    data.append(["Service", 0.33, 0.25, 1])
    data.append([""])  # Empty row to separate matrices

    # Add alternative matrices
    for i in range(3):  # 3 criteria
        data.append(["", "Option A", "Option B", "Option C", "Option D"])
        data.append(["Option A", 1, 5, 1, 1])
        data.append(["Option B", 0.2, 1, 1, 1])
        data.append(["Option C", 1, 1, 1, 1])
        data.append(["Option D", 1, 1, 1, 1])
        if i < 2:  # Add empty row between matrices except for the last one
            data.append([""])

    # Create DataFrame and save
    df = pd.DataFrame(data)
    df.to_excel(file_path, header=False, index=False)

    print("Created test file with data:")
    print(df.to_string())

    try:
        # Test parsing
        parser = FileParser()
        result = parser.parse_file(file_path, "hierarchy", 3, 4)

        print(f"\nParsing result:")
        print(f"Success: {result['success']}")
        print(f"Error: {result.get('error', 'None')}")
        print(f"Criteria names: {result.get('criteria_names', [])}")
        print(f"Alternative names: {result.get('alternative_names', [])}")
        print(f"Number of matrices: {len(result.get('matrices', []))}")

        # Debug the parsing process
        print("\nDebugging parsing process...")
        df_read = pd.read_excel(file_path, header=None)
        print("Read DataFrame:")
        print(df_read.to_string())

        # Check each row
        for idx, row in df_read.iterrows():
            row_values = [
                str(val).strip()
                for val in row.values
                if str(val).strip() != "" and str(val).strip().lower() != "nan"
            ]
            print(f"Row {idx}: {row_values}")
            if row_values:
                has_names = any(not parser._is_numeric(val) for val in row_values)
                all_names = all(not parser._is_numeric(val) for val in row_values)
                print(f"  Has names: {has_names}, All names: {all_names}")
                if has_names:
                    print(
                        f"  Names: {[val for val in row_values if not parser._is_numeric(val)]}"
                    )

    finally:
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rmdir(os.path.dirname(file_path))


if __name__ == "__main__":
    debug_hierarchy_parsing()
