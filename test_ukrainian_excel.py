#!/usr/bin/env python3
"""
Test Excel export with Ukrainian language
"""

from mymodules.excel_export import HierarchyExcelExporter


def test_ukrainian_excel_export():
    """Test Excel export with Ukrainian language"""

    # Sample analysis data with fraction strings
    analysis_data = {
        "method_id": 123,
        "task_description": "Тестовий аналіз AHP з українською мовою",
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
        "criteria_consistency": {"ci": 0.0, "cr": 0.0},
        "alternatives_consistency": {"ci": [0.0, 0.0], "cr": [0.0, 0.0]},
    }

    print("🧪 Testing Ukrainian Excel export...")

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

        # Check Ukrainian sheet names
        expected_ukrainian_sheets = [
            "Загальна інформація",
            "Матриця критеріїв",
            "Матриця_Якість",
            "Матриця_Ціна",
            "Критерії",
            "Альтернативи",
            "Результати",
            "Узгодженість",
            "Графіки",
        ]

        if sheet_names == expected_ukrainian_sheets:
            print("✅ Ukrainian sheet names are correct!")
        else:
            print("❌ Ukrainian sheet names are incorrect!")
            print(f"Expected: {expected_ukrainian_sheets}")
            print(f"Got: {sheet_names}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_ukrainian_excel_export()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")
