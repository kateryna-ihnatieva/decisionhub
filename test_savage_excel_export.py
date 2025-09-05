#!/usr/bin/env python3
"""
Test script for Savage Excel export functionality
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mymodules.savage_excel_export import SavageExcelExporter


def test_savage_excel_export():
    """Test Savage Excel export functionality"""

    print("🧪 Testing Savage Excel Export...")

    # Sample analysis data
    analysis_data = {
        "method_id": 123,
        "savage_task": "Тестова задача для критерію Севіджа з дуже довгим описом завдання, який повинен переноситися на наступні рядки для перевірки функціональності переносу тексту",
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
        "loss_matrix": [
            [8, 8, 8],
            [3, 3, 3],
            [6, 6, 6],
            [0, 0, 0],
        ],
        "max_losses": [8, 3, 6, 0],
        "optimal_message": "Оптимальною за критерієм Севіджа є альтернатива Альтернатива 4 (мінімальні втрати 0).",
    }

    try:
        # Test 1: Create exporter
        print("  ✅ Creating SavageExcelExporter...")
        exporter = SavageExcelExporter()

        # Test 2: Generate workbook
        print("  ✅ Generating workbook...")
        workbook = exporter.generate_savage_analysis_excel(analysis_data)

        # Test 3: Check all sheets exist
        print("  ✅ Checking all sheets exist...")
        expected_sheets = [
            "Загальна інформація",
            "Матриця витрат",
            "Матриця втрат",
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

        if general_ws["A1"].value == "Звіт аналізу Критерію Севіджа":
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

        # Test 6: Check loss matrix sheet
        print("  ✅ Checking loss matrix sheet...")
        loss_ws = workbook["Матриця втрат"]

        if loss_ws["A3"].value == "Альтернативи":
            print("    ✅ Loss matrix header is correct")
        else:
            print("    ❌ Loss matrix header is incorrect")
            return False

        # Test 7: Check max losses column
        print("  ✅ Checking max losses column...")
        last_col = chr(66 + len(analysis_data["name_conditions"]))  # E for 3 conditions
        if loss_ws[f"{last_col}3"].value == "Макс. втрати":
            print("    ✅ Max losses column header is correct")
        else:
            print(
                f"    ❌ Max losses column header is incorrect: {loss_ws[f'{last_col}3'].value}"
            )
            return False

        # Test 8: Check max losses values
        print("  ✅ Checking max losses values...")
        for i in range(len(analysis_data["name_alternatives"])):
            row = i + 4
            expected_value = analysis_data["max_losses"][i]
            actual_value = loss_ws[f"{last_col}{row}"].value

            if actual_value == expected_value:
                print(f"    ✅ Row {i+1} max loss value is correct: {actual_value}")
            else:
                print(
                    f"    ❌ Row {i+1} max loss value is incorrect: expected {expected_value}, got {actual_value}"
                )
                return False

        # Test 9: Check optimal variants sheet
        print("  ✅ Checking optimal variants sheet...")
        optimal_ws = workbook["Оптимальні варіанти"]

        if (
            optimal_ws["A3"].value == "Альтернативи"
            and optimal_ws["B3"].value == "Максимальні втрати"
            and optimal_ws["C3"].value is None
        ):
            print("    ✅ Optimal variants has correct 2-column structure")
        else:
            print("    ❌ Optimal variants structure is incorrect")
            print(f"    A3: {optimal_ws['A3'].value}")
            print(f"    B3: {optimal_ws['B3'].value}")
            print(f"    C3: {optimal_ws['C3'].value}")
            return False

        # Test 10: Check optimal variants are sorted by max losses (ascending)
        print("  ✅ Checking optimal variants sorting...")
        # Should be sorted: D(0), B(3), C(6), A(8)
        expected_sorted_order = [
            "Альтернатива 4",
            "Альтернатива 2",
            "Альтернатива 3",
            "Альтернатива 1",
        ]
        expected_sorted_values = [0, 3, 6, 8]

        for i in range(len(expected_sorted_order)):
            row = i + 5
            actual_alternative = optimal_ws[f"A{row}"].value
            actual_value = optimal_ws[f"B{row}"].value

            if actual_alternative == expected_sorted_order[i]:
                print(
                    f"    ✅ Sorted row {i+1} alternative is correct: {actual_alternative}"
                )
            else:
                print(
                    f"    ❌ Sorted row {i+1} alternative is incorrect: expected {expected_sorted_order[i]}, got {actual_alternative}"
                )
                return False

            if actual_value == expected_sorted_values[i]:
                print(f"    ✅ Sorted row {i+1} value is correct: {actual_value}")
            else:
                print(
                    f"    ❌ Sorted row {i+1} value is incorrect: expected {expected_sorted_values[i]}, got {actual_value}"
                )
                return False

        # Test 11: Check chart preserves original order
        print("  ✅ Checking chart preserves original order...")
        chart_ws = workbook["Графіки"]

        # Chart should preserve original order: A1, A2, A3, A4
        expected_chart_order = [
            "Альтернатива 1",
            "Альтернатива 2",
            "Альтернатива 3",
            "Альтернатива 4",
        ]
        expected_chart_values = [8, 3, 6, 0]

        for i in range(len(expected_chart_order)):
            row = i + 4
            actual_alternative = chart_ws[f"A{row}"].value
            actual_value = chart_ws[f"B{row}"].value

            if actual_alternative == expected_chart_order[i]:
                print(
                    f"    ✅ Chart row {i+1} alternative is correct: {actual_alternative}"
                )
            else:
                print(
                    f"    ❌ Chart row {i+1} alternative is incorrect: expected {expected_chart_order[i]}, got {actual_alternative}"
                )
                return False

            if actual_value == expected_chart_values[i]:
                print(f"    ✅ Chart row {i+1} value is correct: {actual_value}")
            else:
                print(
                    f"    ❌ Chart row {i+1} value is incorrect: expected {expected_chart_values[i]}, got {actual_value}"
                )
                return False

        # Test 12: Check conclusion matches exactly
        print("  ✅ Checking conclusion...")
        conclusion_ws = workbook["Висновки"]

        if conclusion_ws["A4"].value == analysis_data["optimal_message"]:
            print("    ✅ Conclusion matches exactly")
        else:
            print("    ❌ Conclusion doesn't match")
            print(f"    Expected: {analysis_data['optimal_message']}")
            print(f"    Actual: {conclusion_ws['A4'].value}")
            return False

        # Test 13: Check text wrapping
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

        # Test 14: Save to bytes
        print("  ✅ Testing save to bytes...")
        excel_bytes = exporter.save_to_bytes()

        if len(excel_bytes) > 1000:
            print(f"    ✅ File size: {len(excel_bytes)} bytes")
        else:
            print(f"    ❌ File too small: {len(excel_bytes)} bytes")
            return False

        print("\n🎉 All Savage Excel export tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_savage_excel_export()
    if success:
        print("\n✅ Savage Excel export is working!")
    else:
        print("\n❌ Savage Excel export has issues!")
        sys.exit(1)
