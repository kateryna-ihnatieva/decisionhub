#!/usr/bin/env python3
"""
Final test for Excel export with correct data structure
"""

from mymodules.excel_export import HierarchyExcelExporter


def test_final_excel_export():
    """Test Excel export with correct data structure"""

    # Sample analysis data matching the real structure
    analysis_data = {
        "method_id": 123,
        "task_description": "Test AHP Analysis",
        "criteria_names": ["Quality", "Price"],
        "alternatives_names": ["Option A", "Option B"],
        "criteria_weights": [0.6, 0.4],
        "global_priorities": [0.7, 0.3],
        "criteria_matrix": [["1", "1.5"], ["0.67", "1"]],
        "alternatives_matrices": [
            [["1", "2"], ["0.5", "1"]],
            [["1", "0.5"], ["2", "1"]],
        ],
        "criteria_eigenvector": [1.0, 1.0],
        "alternatives_eigenvectors": [[1.414, 0.707], [0.707, 1.414]],
        "alternatives_weights": [[0.667, 0.333], [0.333, 0.667]],  # Normalized weights
        "criteria_consistency": {"ci": 0.0, "cr": 0.0},
        "alternatives_consistency": {"ci": [0.0, 0.0], "cr": [0.0, 0.0]},
    }

    print("🧪 Testing final Excel export...")

    try:
        exporter = HierarchyExcelExporter()
        workbook = exporter.generate_hierarchy_analysis_excel(analysis_data)

        # Get sheet names
        sheet_names = [sheet.title for sheet in workbook.worksheets]
        print(f"✅ Excel file generated successfully!")
        print(f"📊 Sheets created: {sheet_names}")

        # Test saving to bytes
        excel_bytes = exporter.save_to_bytes()
        print(f"💾 File size: {len(excel_bytes)} bytes")

        # Check if the order is correct
        expected_order = [
            "General Information",
            "Criteria Matrix",
            "Matrix_Quality",
            "Matrix_Price",
            "Criteria",
            "Alternatives",
            "Results",
            "Consistency",
            "Charts",
        ]

        if sheet_names == expected_order:
            print("✅ Sheet order is correct!")
        else:
            print("❌ Sheet order is incorrect!")
            print(f"Expected: {expected_order}")
            print(f"Got: {sheet_names}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_final_excel_export()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")
