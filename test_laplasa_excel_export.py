#!/usr/bin/env python3
"""
Test script for Laplasa Excel export
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mymodules.laplasa_excel_export import LaplasaExcelExporter


def test_laplasa_excel_export():
    """Test Laplasa Excel export functionality"""

    print("🧪 Testing Laplasa Excel Export...")

    # Sample analysis data
    analysis_data = {
        "method_id": 123,
        "laplasa_task": "Тестова задача для критерію Лапласа з довгим описом, який повинен переноситися на кілька рядків в Excel файлі",
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

        # Test 3: Check all sheets exist
        print("  ✅ Checking all sheets exist...")
        expected_sheets = [
            "Загальна інформація",
            "Матриця витрат",
            "Оптимальні варіанти",
            "Графіки",
            "Висновки",
        ]

        for sheet_name in expected_sheets:
            if sheet_name in workbook.sheetnames:
                print(f"    ✅ Sheet '{sheet_name}' exists")
            else:
                print(f"    ❌ Sheet '{sheet_name}' missing")
                return False

        # Test 4: Check general info sheet
        print("  ✅ Checking general info sheet...")
        general_ws = workbook["Загальна інформація"]

        if general_ws["A1"].value == "Звіт аналізу Критерію Лапласа":
            print("    ✅ General info header is correct")
        else:
            print("    ❌ General info header is incorrect")
            return False

        # Test 5: Check cost matrix sheet
        print("  ✅ Checking cost matrix sheet...")
        matrix_ws = workbook["Матриця витрат"]

        if matrix_ws["A3"].value == "Альтернативи":
            print("    ✅ Cost matrix header is correct")
        else:
            print("    ❌ Cost matrix header is incorrect")
            return False

        # Test 6: Check optimal variants sheet
        print("  ✅ Checking optimal variants sheet...")
        optimal_ws = workbook["Оптимальні варіанти"]

        if optimal_ws["A3"].value == "Альтернативи":
            print("    ✅ Optimal variants header is correct")
        else:
            print("    ❌ Optimal variants header is incorrect")
            return False

        # Test 7: Check conclusion sheet
        print("  ✅ Checking conclusion sheet...")
        conclusion_ws = workbook["Висновки"]

        if conclusion_ws["A4"].value == analysis_data["optimal_message"]:
            print("    ✅ Conclusion has proper optimal_message")
        else:
            print("    ❌ Conclusion optimal_message is incorrect")
            print(f"    Expected: {analysis_data['optimal_message']}")
            print(f"    Actual: {conclusion_ws['A4'].value}")
            return False

        # Test 8: Check text wrapping for long text
        print("  ✅ Checking text wrapping...")

        # Check task description cell
        task_cell = general_ws["A7"]
        if hasattr(task_cell.alignment, "wrap_text") and task_cell.alignment.wrap_text:
            print("    ✅ Task description has text wrapping")
        else:
            print("    ❌ Task description doesn't have text wrapping")
            return False

        # Check conclusion cell
        conclusion_cell = conclusion_ws["A4"]
        if (
            hasattr(conclusion_cell.alignment, "wrap_text")
            and conclusion_cell.alignment.wrap_text
        ):
            print("    ✅ Conclusion has text wrapping")
        else:
            print("    ❌ Conclusion doesn't have text wrapping")
            return False

        # Test 9: Check chart sheet
        print("  ✅ Checking chart sheet...")
        chart_ws = workbook["Графіки"]

        if chart_ws["A1"].value == "Графік оптимальних варіантів":
            print("    ✅ Chart sheet header is correct")
        else:
            print("    ❌ Chart sheet header is incorrect")
            return False

        # Test 10: Save to bytes
        print("  ✅ Testing save to bytes...")
        excel_bytes = exporter.save_to_bytes()

        if len(excel_bytes) > 1000:
            print(f"    ✅ File size: {len(excel_bytes)} bytes")
        else:
            print(f"    ❌ File too small: {len(excel_bytes)} bytes")
            return False

        print("\n🎉 All Laplasa Excel export tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_laplasa_excel_export()
    if success:
        print("\n✅ Laplasa Excel export is working!")
    else:
        print("\n❌ Laplasa Excel export has issues!")
        sys.exit(1)
