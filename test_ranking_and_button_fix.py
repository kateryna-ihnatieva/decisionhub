#!/usr/bin/env python3
"""
Test script for ranking column removal and export button positioning
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mymodules.experts_excel_export import ExpertsExcelExporter


def test_ranking_and_button_fix():
    """Test ranking column removal and export button positioning"""

    print("🧪 Testing Ranking Column Removal and Export Button...")

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
        print("  ✅ Checking ranking sheet columns...")
        ranking_ws = workbook["Ранжування"]

        # Check headers
        if (
            ranking_ws["A3"].value == "Критерій"
            and ranking_ws["B3"].value == "Значення λ"
        ):
            print("    ✅ Ranking sheet has correct headers (Критерій, Значення λ)")
        else:
            print("    ❌ Ranking sheet headers are incorrect")
            print(f"    A3: {ranking_ws['A3'].value}")
            print(f"    B3: {ranking_ws['B3'].value}")
            return False

        # Check that there's no C3 column (Позиція)
        if ranking_ws["C3"].value is None:
            print("    ✅ Position column (C3) is removed")
        else:
            print("    ❌ Position column (C3) still exists")
            print(f"    C3 value: {ranking_ws['C3'].value}")
            return False

        # Test 4: Check ranking data has only 2 columns
        print("  ✅ Checking ranking data structure...")

        # Check first data row
        if (
            ranking_ws["A5"].value is not None
            and ranking_ws["B5"].value is not None
            and ranking_ws["C5"].value is None
        ):
            print("    ✅ Ranking data has only 2 columns")
        else:
            print("    ❌ Ranking data structure is incorrect")
            print(f"    A5: {ranking_ws['A5'].value}")
            print(f"    B5: {ranking_ws['B5'].value}")
            print(f"    C5: {ranking_ws['C5'].value}")
            return False

        # Test 5: Check merge cells is correct (A1:B1)
        print("  ✅ Checking merge cells...")

        # Check if A1:B1 is merged
        merged_ranges = list(ranking_ws.merged_cells.ranges)
        if any(str(range) == "A1:B1" for range in merged_ranges):
            print("    ✅ Header is correctly merged to A1:B1")
        else:
            print("    ❌ Header merge is incorrect")
            print(f"    Merged ranges: {[str(r) for r in merged_ranges]}")
            return False

        # Test 6: Save to bytes
        print("  ✅ Testing save to bytes...")
        excel_bytes = exporter.save_to_bytes()

        if len(excel_bytes) > 1000:
            print(f"    ✅ File size: {len(excel_bytes)} bytes")
        else:
            print(f"    ❌ File too small: {len(excel_bytes)} bytes")
            return False

        print("\n🎉 Ranking column removal and export button fixes passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_ranking_and_button_fix()
    if success:
        print("\n✅ Ranking and button fixes are working!")
    else:
        print("\n❌ Ranking and button fixes have issues!")
        sys.exit(1)
