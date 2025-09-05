#!/usr/bin/env python3
"""
Test script for export button style and positioning fixes
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mymodules.experts_excel_export import ExpertsExcelExporter


def test_export_button_fixes():
    """Test export button style and positioning fixes"""

    print("🧪 Testing Export Button Fixes...")

    # Sample analysis data
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
        ],
        "experts_data_table": [[0.8, 0.7, 0.9], [0.9, 0.8, 0.7], [0.7, 0.9, 0.8]],
        "m_i": [0.8, 0.8, 0.8, 0.8, 0.8],
        "r_i": [0.8, 0.8, 0.8, 0.8, 0.8],
        "l_value": [0.2, 0.3, 0.25, 0.15, 0.1],
        "l_value_sum": 1,
        "rank_str": "Test conclusion",
    }

    try:
        # Test 1: Create exporter
        print("  ✅ Creating ExpertsExcelExporter...")
        exporter = ExpertsExcelExporter()

        # Test 2: Generate workbook
        print("  ✅ Generating workbook...")
        workbook = exporter.generate_experts_analysis_excel(analysis_data)

        # Test 3: Check ranking sheet has only 2 columns
        print("  ✅ Checking ranking sheet structure...")
        ranking_ws = workbook["Ранжування"]

        # Check headers
        if (
            ranking_ws["A3"].value == "Критерій"
            and ranking_ws["B3"].value == "Значення λ"
            and ranking_ws["C3"].value is None
        ):
            print("    ✅ Ranking sheet has correct 2-column structure")
        else:
            print("    ❌ Ranking sheet structure is incorrect")
            return False

        # Test 4: Check merge cells is correct (A1:B1)
        print("  ✅ Checking merge cells...")
        merged_ranges = list(ranking_ws.merged_cells.ranges)
        if any(str(range) == "A1:B1" for range in merged_ranges):
            print("    ✅ Header is correctly merged to A1:B1")
        else:
            print("    ❌ Header merge is incorrect")
            return False

        # Test 5: Check all sheets exist
        print("  ✅ Checking all sheets exist...")
        expected_sheets = [
            "Загальна інформація",
            "Компетентність експертів",
            "Дані експертів",
            "Ранжування",
            "Графіки",
            "Висновки",
        ]

        for sheet_name in expected_sheets:
            if sheet_name in workbook.sheetnames:
                print(f"    ✅ Sheet '{sheet_name}' exists")
            else:
                print(f"    ❌ Sheet '{sheet_name}' missing")
                return False

        # Test 6: Check conclusion sheet has proper rank_str
        print("  ✅ Checking conclusion sheet...")
        conclusion_ws = workbook["Висновки"]

        if conclusion_ws["A4"].value == analysis_data["rank_str"]:
            print("    ✅ Conclusion has proper rank_str")
        else:
            print("    ❌ Conclusion rank_str is incorrect")
            print(f"    Expected: {analysis_data['rank_str']}")
            print(f"    Actual: {conclusion_ws['A4'].value}")
            return False

        # Test 7: Save to bytes
        print("  ✅ Testing save to bytes...")
        excel_bytes = exporter.save_to_bytes()

        if len(excel_bytes) > 1000:
            print(f"    ✅ File size: {len(excel_bytes)} bytes")
        else:
            print(f"    ❌ File too small: {len(excel_bytes)} bytes")
            return False

        print("\n🎉 All export button fixes passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_export_button_fixes()
    if success:
        print("\n✅ Export button fixes are working!")
    else:
        print("\n❌ Export button fixes have issues!")
        sys.exit(1)
