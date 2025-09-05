#!/usr/bin/env python3
"""
Test script for lambda sum fix
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mymodules.experts_excel_export import ExpertsExcelExporter


def test_lambda_sum_fix():
    """Test lambda sum fix with floating point precision"""

    print("🧪 Testing Lambda Sum Fix...")

    # Sample analysis data with floating point precision issue
    l_value = [
        0.23809523809523808,
        0.047619047619047616,
        0.19047619047619047,
        0.2857142857142857,
        0.14285714285714285,
        0.09523809523809523,
    ]
    l_value_sum = round(sum(l_value))  # Should be 1, not 0

    print(f"  Debug - l_value: {l_value}")
    print(f"  Debug - sum(l_value): {sum(l_value)}")
    print(f"  Debug - round(sum(l_value)): {l_value_sum}")

    analysis_data = {
        "method_id": 123,
        "experts_task": "Test task",
        "table_competency": [
            [0.8, 0.7, 0.9, 0.6, 0.8],
            [0.9, 0.8, 0.7, 0.8, 0.9],
            [0.7, 0.9, 0.8, 0.7, 0.8],
        ],
        "k_k": [0.76, 0.82, 0.78],
        "k_a": [0.8, 0.85, 0.8],
        "name_arguments": [
            "Ступінь знайомства",
            "Теоретичний аналіз",
            "Досвід",
            "Література",
            "Інтуїція",
        ],
        "name_research": [
            "Критерій 1",
            "Критерій 2",
            "Критерій 3",
            "Критерій 4",
            "Критерій 5",
            "Критерій 6",
        ],
        "experts_data_table": [[0.8, 0.7, 0.9], [0.9, 0.8, 0.7], [0.7, 0.9, 0.8]],
        "m_i": [0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
        "r_i": [0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
        "l_value": l_value,
        "l_value_sum": l_value_sum,
        "rank_str": "Test conclusion",
    }

    try:
        # Test 1: Create exporter
        print("  ✅ Creating ExpertsExcelExporter...")
        exporter = ExpertsExcelExporter()

        # Test 2: Generate workbook
        print("  ✅ Generating workbook...")
        workbook = exporter.generate_experts_analysis_excel(analysis_data)

        # Test 3: Check l_value_sum is correct
        print("  ✅ Checking l_value_sum...")
        data_ws = workbook["Дані експертів"]

        # Find the sum cell (should be in the last column of lambda row)
        lambda_row = None
        for row in range(1, 20):  # Check first 20 rows
            if data_ws[f"A{row}"].value == "λ":
                lambda_row = row
                break

        if lambda_row:
            # Find the sum cell (last column)
            sum_cell = None
            for col in range(2, 10):  # Check columns B to J
                cell_value = data_ws.cell(row=lambda_row, column=col).value
                if cell_value == l_value_sum:
                    sum_cell = data_ws.cell(row=lambda_row, column=col)
                    break

            if sum_cell and sum_cell.value == 1:  # Should be 1, not 0
                print("    ✅ l_value_sum is correctly 1")
            else:
                print("    ❌ l_value_sum is not 1")
                print(f"    Value: {sum_cell.value if sum_cell else 'Not found'}")
                return False
        else:
            print("    ❌ Could not find lambda row")
            return False

        # Test 4: Save to bytes
        print("  ✅ Testing save to bytes...")
        excel_bytes = exporter.save_to_bytes()

        if len(excel_bytes) > 1000:
            print(f"    ✅ File size: {len(excel_bytes)} bytes")
        else:
            print(f"    ❌ File too small: {len(excel_bytes)} bytes")
            return False

        print("\n🎉 Lambda sum fix passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_lambda_sum_fix()
    if success:
        print("\n✅ Lambda sum fix is working!")
    else:
        print("\n❌ Lambda sum fix has issues!")
        sys.exit(1)
