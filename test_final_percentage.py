#!/usr/bin/env python3
"""
Test final Excel export with correct percentage formatting
"""

from mymodules.excel_export import HierarchyExcelExporter


def test_final_percentage_formatting():
    """Test final percentage formatting"""

    # Sample analysis data with realistic consistency values
    analysis_data = {
        "method_id": 123,
        "task_description": "Фінальний тест процентного форматування",
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
        "criteria_consistency": {"ci": 0.0, "cr": 8.959},  # Already in percentage
        "alternatives_consistency": {
            "ci": [0.0, 0.0],
            "cr": [4.623, 1.234],  # Already in percentage
        },
    }

    print("🧪 Testing final percentage formatting...")

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

        # Test percentage conversion with realistic values
        test_values = [
            (0.04623, "Decimal format"),
            (8.959, "Already in percentage"),
            (0.1, "Decimal format"),
            (10.0, "Already in percentage"),
        ]
        print("\n🔢 Testing percentage conversion:")
        for val, description in test_values:
            from openpyxl import Workbook

            wb = Workbook()
            ws = wb.active
            test_cell = ws.cell(row=1, column=1)
            exporter.set_percentage_style(test_cell, val)
            print(
                f"  {val} ({description}) -> {test_cell.value} ({test_cell.number_format})"
            )

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_final_percentage_formatting()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")
