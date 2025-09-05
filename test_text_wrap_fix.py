#!/usr/bin/env python3
"""
Test script for text wrapping and lambda sum fixes
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mymodules.experts_excel_export import ExpertsExcelExporter


def test_text_wrap_and_lambda_fix():
    """Test text wrapping and lambda sum fixes"""

    print("🧪 Testing Text Wrap and Lambda Sum Fixes...")

    # Sample analysis data with long text
    analysis_data = {
        "method_id": 123,
        "experts_task": "Дуже довга задача для експертних оцінок, яка містить багато тексту і повинна переноситися на кілька рядків в Excel файлі для кращої читабельності та розуміння контексту аналізу",
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
        "name_research": ["Критерій 1", "Критерій 2", "Критерій 3"],
        "experts_data_table": [[0.8, 0.7, 0.9], [0.9, 0.8, 0.7], [0.7, 0.9, 0.8]],
        "m_i": [0.8, 0.8, 0.8],
        "r_i": [0.8, 0.8, 0.8],
        "l_value": [0.8, 0.8, 0.8],
        "l_value_sum": 2,  # Integer value
        "rank_str": "Дуже довгий висновок аналізу, який містить детальну інформацію про результати дослідження та рекомендації щодо подальших дій, які повинні бути впроваджені для покращення ефективності системи",
    }

    try:
        # Test 1: Create exporter
        print("  ✅ Creating ExpertsExcelExporter...")
        exporter = ExpertsExcelExporter()

        # Test 2: Generate workbook
        print("  ✅ Generating workbook...")
        workbook = exporter.generate_experts_analysis_excel(analysis_data)

        # Test 3: Check task description row height
        print("  ✅ Checking task description row height...")
        general_ws = workbook["Загальна інформація"]

        task_row_height = general_ws.row_dimensions[7].height
        if task_row_height and task_row_height > 30:  # Should be higher than default
            print(f"    ✅ Task description row height: {task_row_height}")
        else:
            print(f"    ❌ Task description row height too small: {task_row_height}")
            return False

        # Test 4: Check conclusion row height
        print("  ✅ Checking conclusion row height...")
        conclusion_ws = workbook["Висновки"]

        conclusion_row_height = conclusion_ws.row_dimensions[4].height
        if (
            conclusion_row_height and conclusion_row_height > 30
        ):  # Should be higher than default
            print(f"    ✅ Conclusion row height: {conclusion_row_height}")
        else:
            print(f"    ❌ Conclusion row height too small: {conclusion_row_height}")
            return False

        # Test 5: Check text wrapping is enabled
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

        # Test 6: Check l_value_sum is integer
        print("  ✅ Checking l_value_sum formatting...")
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
                if cell_value == analysis_data["l_value_sum"]:
                    sum_cell = data_ws.cell(row=lambda_row, column=col)
                    break

            if sum_cell and isinstance(sum_cell.value, int):
                print("    ✅ l_value_sum is formatted as integer")
            else:
                print("    ❌ l_value_sum is not formatted as integer")
                print(f"    Value: {sum_cell.value if sum_cell else 'Not found'}")
                print(f"    Type: {type(sum_cell.value) if sum_cell else 'N/A'}")
                return False
        else:
            print("    ❌ Could not find lambda row")
            return False

        # Test 7: Save to bytes
        print("  ✅ Testing save to bytes...")
        excel_bytes = exporter.save_to_bytes()

        if len(excel_bytes) > 1000:
            print(f"    ✅ File size: {len(excel_bytes)} bytes")
        else:
            print(f"    ❌ File too small: {len(excel_bytes)} bytes")
            return False

        print("\n🎉 All text wrap and lambda fixes passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_text_wrap_and_lambda_fix()
    if success:
        print("\n✅ Text wrap and lambda fixes are working!")
    else:
        print("\n❌ Text wrap and lambda fixes have issues!")
        sys.exit(1)
