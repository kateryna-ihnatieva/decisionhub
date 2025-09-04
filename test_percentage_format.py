#!/usr/bin/env python3
"""
Test Excel export with percentage formatting for consistency ratio
"""

from mymodules.excel_export import HierarchyExcelExporter


def test_percentage_formatting():
    """Test percentage formatting for consistency ratio"""

    # Sample analysis data with realistic consistency values
    analysis_data = {
        "method_id": 123,
        "task_description": "Тест процентного форматування",
        "criteria_names": ["Якість", "Ціна"],
        "alternatives_names": ["Варіант А", "Варіант Б"],
        "criteria_weights": [0.6, 0.4],
        "global_priorities": [0.7, 0.3],
        "criteria_matrix": [["1", "3"], ["1/3", "1"]],
        "alternatives_matrices": [
            [["1", "2"], ["1/2", "1"]],
            [["1", "1/2"], ["2", "1"]],
        ],
        "criteria_eigenvector": [1.0, 1.0],
        "alternatives_eigenvectors": [[1.414, 0.707], [0.707, 1.414]],
        "alternatives_weights": [[0.667, 0.333], [0.333, 0.667]],
        "criteria_consistency": {"ci": 0.0, "cr": 0.04623},  # 4.623%
        "alternatives_consistency": {
            "ci": [0.0, 0.0],
            "cr": [0.04623, 0.01234],
        },  # 4.623%, 1.234%
    }

    print("🧪 Testing percentage formatting...")

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

        # Test percentage conversion
        test_values = [0.04623, 0.01234, 0.1, 0.05]
        print("\n🔢 Testing percentage conversion:")
        for val in test_values:
            # Create a test cell to check formatting
            from openpyxl import Workbook

            wb = Workbook()
            ws = wb.active
            test_cell = ws.cell(row=1, column=1)
            exporter.set_percentage_style(test_cell, val)
            print(f"  {val} -> {test_cell.value} ({test_cell.number_format})")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_percentage_formatting()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")
