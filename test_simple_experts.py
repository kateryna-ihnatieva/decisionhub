#!/usr/bin/env python3
"""
Simple test for Experts Excel export fixes
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mymodules.experts_excel_export import ExpertsExcelExporter


def test_simple_experts():
    """Simple test for Experts Excel export"""

    print("🧪 Simple Experts Excel Test...")

    # Sample analysis data
    analysis_data = {
        "method_id": 123,
        "experts_task": "Тестова задача",
        "table_competency": [[0.8, 0.7, 0.9], [0.9, 0.8, 0.7]],
        "k_k": [0.76, 0.82],
        "k_a": [0.8, 0.85],
        "name_arguments": ["Ступінь знайомства", "Теоретичний аналіз"],
        "name_research": ["Критерій 1", "Критерій 2"],
        "experts_data_table": [[0.8, 0.7], [0.9, 0.8]],
        "m_i": [0.8, 0.8],
        "r_i": [0.8, 0.8],
        "l_value": [0.8, 0.8],
        "l_value_sum": 1,  # Integer value
        "rank_str": "Критерій 1 має найвищий пріоритет",
    }

    try:
        # Test 1: Create exporter
        print("  ✅ Creating exporter...")
        exporter = ExpertsExcelExporter()

        # Test 2: Check font colors
        print("  ✅ Checking font colors...")
        print(f"    Data font color: {exporter.data_font.color}")
        print(f"    Sum font color: {exporter.sum_font.color}")
        if (
            str(exporter.data_font.color.rgb)[2:] == "000000"
            and str(exporter.sum_font.color.rgb)[2:] == "000000"
        ):
            print("    ✅ Font colors are correct (black)")
        else:
            print("    ❌ Font colors are incorrect")
            return False

        # Test 3: Generate workbook
        print("  ✅ Generating workbook...")
        workbook = exporter.generate_experts_analysis_excel(analysis_data)

        # Test 4: Check conclusion sheet
        print("  ✅ Checking conclusion sheet...")
        conclusion_ws = workbook["Висновки"]

        if conclusion_ws["A4"].value == analysis_data["rank_str"]:
            print("    ✅ Conclusion has proper rank_str")
        else:
            print("    ❌ Conclusion doesn't have proper rank_str")
            return False

        # Test 5: Save to bytes
        print("  ✅ Testing save to bytes...")
        excel_bytes = exporter.save_to_bytes()

        if len(excel_bytes) > 1000:
            print(f"    ✅ File size: {len(excel_bytes)} bytes")
        else:
            print(f"    ❌ File too small: {len(excel_bytes)} bytes")
            return False

        print("\n🎉 All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_simple_experts()
    if success:
        print("\n✅ Experts Excel fixes are working!")
    else:
        print("\n❌ Experts Excel fixes have issues!")
        sys.exit(1)
