#!/usr/bin/env python3
"""
Test Excel export with fraction strings (like '1/3', '1/5')
"""

from mymodules.excel_export import HierarchyExcelExporter


def test_fraction_conversion():
    """Test Excel export with fraction strings"""

    # Sample analysis data with fraction strings (like real data)
    analysis_data = {
        "method_id": 123,
        "task_description": "Test AHP Analysis with Fractions",
        "criteria_names": ["Quality", "Price"],
        "alternatives_names": ["Option A", "Option B"],
        "criteria_weights": [0.6, 0.4],
        "global_priorities": [0.7, 0.3],
        "criteria_matrix": [["1", "3"], ["1/3", "1"]],  # Contains fraction
        "alternatives_matrices": [
            [["1", "2"], ["1/2", "1"]],  # Contains fraction
            [["1", "1/2"], ["2", "1"]],  # Contains fraction
        ],
        "criteria_eigenvector": [1.0, 1.0],
        "alternatives_eigenvectors": [[1.414, 0.707], [0.707, 1.414]],
        "alternatives_weights": [[0.667, 0.333], [0.333, 0.667]],
        "criteria_consistency": {"ci": 0.0, "cr": 0.0},
        "alternatives_consistency": {"ci": [0.0, 0.0], "cr": [0.0, 0.0]},
    }

    print("🧪 Testing Excel export with fraction strings...")

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

        # Test fraction conversion
        test_fractions = ["1/3", "1/5", "2/3", "5/2", "1", "0.5"]
        print("\n🔢 Testing fraction conversion:")
        for frac in test_fractions:
            converted = exporter.convert_fraction_to_float(frac)
            print(f"  {frac} -> {converted}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_fraction_conversion()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")
