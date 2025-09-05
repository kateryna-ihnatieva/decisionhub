#!/usr/bin/env python3
"""
Test script for Laplasa Excel export fixes
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mymodules.laplasa_excel_export import LaplasaExcelExporter


def test_laplasa_fixes():
    """Test Laplasa Excel export fixes"""

    print("🧪 Testing Laplasa Excel Export Fixes...")

    # Sample analysis data
    analysis_data = {
        "method_id": 123,
        "laplasa_task": "Тестова задача для критерію Лапласа",
        "name_alternatives": [
            "Альтернатива 1",
            "Альтернатива 2",
            "Альтернатива 3",
            "Альтернатива 4",
        ],
        "name_conditions": [
            "Умова 1",
            "Умова 2",
            "Умова 3",
        ],
        "cost_matrix": [
            [10, 20, 30],
            [15, 25, 35],
            [12, 22, 32],
            [18, 28, 38],
        ],
        "optimal_variants": [20.0, 25.0, 22.0, 28.0],
        "optimal_message": "Оптимальна альтернатива Альтернатива 4, має максимальне значення очікуваної вигоди ('28.0').",
    }

    try:
        # Test 1: Create exporter
        print("  ✅ Creating LaplasaExcelExporter...")
        exporter = LaplasaExcelExporter()

        # Test 2: Generate workbook
        print("  ✅ Generating workbook...")
        workbook = exporter.generate_laplasa_analysis_excel(analysis_data)

        # Test 3: Check cost matrix has M column instead of Sum
        print("  ✅ Checking cost matrix column header...")
        matrix_ws = workbook["Матриця витрат"]

        # Check that last column header is "M" not "Сума"
        last_col = chr(66 + len(analysis_data["name_conditions"]))  # E for 3 conditions
        if matrix_ws[f"{last_col}3"].value == "M":
            print("    ✅ Last column header is 'M'")
        else:
            print(
                f"    ❌ Last column header is not 'M': {matrix_ws[f'{last_col}3'].value}"
            )
            return False

        # Test 4: Check M column has optimal variants values
        print("  ✅ Checking M column values...")
        for i in range(len(analysis_data["name_alternatives"])):
            row = i + 4
            expected_value = analysis_data["optimal_variants"][i]
            actual_value = matrix_ws[f"{last_col}{row}"].value

            if (
                abs(actual_value - expected_value) < 0.001
            ):  # Allow for floating point precision
                print(f"    ✅ Row {i+1} M value is correct: {actual_value}")
            else:
                print(
                    f"    ❌ Row {i+1} M value is incorrect: expected {expected_value}, got {actual_value}"
                )
                return False

        # Test 5: Check optimal variants sheet has only 2 columns
        print("  ✅ Checking optimal variants sheet structure...")
        optimal_ws = workbook["Оптимальні варіанти"]

        # Check headers
        if (
            optimal_ws["A3"].value == "Альтернативи"
            and optimal_ws["B3"].value == "Очікувана вигода"
            and optimal_ws["C3"].value is None
        ):
            print("    ✅ Optimal variants has correct 2-column structure")
        else:
            print("    ❌ Optimal variants structure is incorrect")
            print(f"    A3: {optimal_ws['A3'].value}")
            print(f"    B3: {optimal_ws['B3'].value}")
            print(f"    C3: {optimal_ws['C3'].value}")
            return False

        # Test 6: Check merge cells is correct (A1:B1)
        print("  ✅ Checking merge cells...")
        merged_ranges = list(optimal_ws.merged_cells.ranges)
        if any(str(range) == "A1:B1" for range in merged_ranges):
            print("    ✅ Header is correctly merged to A1:B1")
        else:
            print("    ❌ Header merge is incorrect")
            return False

        # Test 7: Check conclusion matches exactly
        print("  ✅ Checking conclusion...")
        conclusion_ws = workbook["Висновки"]

        if conclusion_ws["A4"].value == analysis_data["optimal_message"]:
            print("    ✅ Conclusion matches exactly")
        else:
            print("    ❌ Conclusion doesn't match")
            print(f"    Expected: {analysis_data['optimal_message']}")
            print(f"    Actual: {conclusion_ws['A4'].value}")
            return False

        # Test 8: Save to bytes
        print("  ✅ Testing save to bytes...")
        excel_bytes = exporter.save_to_bytes()

        if len(excel_bytes) > 1000:
            print(f"    ✅ File size: {len(excel_bytes)} bytes")
        else:
            print(f"    ❌ File too small: {len(excel_bytes)} bytes")
            return False

        print("\n🎉 All Laplasa fixes passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_laplasa_fixes()
    if success:
        print("\n✅ Laplasa fixes are working!")
    else:
        print("\n❌ Laplasa fixes have issues!")
        sys.exit(1)
