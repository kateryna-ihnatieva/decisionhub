import io
from datetime import datetime

import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference


class HierarchyExcelExporter:
    def __init__(self):
        self.workbook = None
        self.worksheet = None

    def create_workbook(self):
        """Create a new Excel workbook"""
        self.workbook = openpyxl.Workbook()
        # Remove default sheet
        self.workbook.remove(self.workbook.active)

    def add_worksheet(self, title):
        """Add a new worksheet to the workbook"""
        self.worksheet = self.workbook.create_sheet(title=title)
        return self.worksheet

    def set_header_style(self, cell, text, color="366092"):
        """Set header cell style"""
        cell.value = text
        cell.font = Font(name="Arial", size=14, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

    def set_subheader_style(self, cell, text, color="4F81BD"):
        """Set subheader cell style"""
        cell.value = text
        cell.font = Font(name="Arial", size=12, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

    def set_data_style(self, cell, value, bold=False):
        """Set data cell style"""
        cell.value = value
        cell.font = Font(name="Arial", size=10, bold=bold)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

    def set_number_style(self, cell, value, decimal_places=4, bold=False):
        """Set number cell style with specific decimal places"""
        if isinstance(value, (int, float)):
            cell.value = round(value, decimal_places)
        else:
            cell.value = value
        cell.font = Font(name="Arial", size=10, bold=bold)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

    def auto_adjust_columns(self, worksheet):
        """Auto-adjust column widths"""
        for column in worksheet.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    def create_general_info_sheet(self, task_description, method_id, created_date=None):
        """Create general information sheet"""
        ws = self.add_worksheet("General Information")

        # Title
        self.set_header_style(ws["A1"], "AHP Analysis Report", "366092")
        ws.merge_cells("A1:D1")

        # Method information
        ws["A3"] = "Analysis Method:"
        ws["B3"] = "Analytic Hierarchy Process (AHP)"
        ws["A4"] = "Analysis ID:"
        ws["B4"] = f"Task_{method_id}"
        ws["A5"] = "Created Date:"
        ws["B5"] = created_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Task description
        if task_description:
            ws["A7"] = "Task Description:"
            ws["A8"] = task_description
            ws.merge_cells("A8:D12")
            ws["A8"].alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True
            )

        # Style the information cells
        for row in range(3, 6):
            for col in range(1, 3):
                cell = ws.cell(row=row, column=col)
                cell.font = Font(name="Arial", size=11, bold=(col == 1))
                cell.border = Border(
                    left=Side(style="thin"),
                    right=Side(style="thin"),
                    top=Side(style="thin"),
                    bottom=Side(style="thin"),
                )

        self.auto_adjust_columns(ws)

    def create_criteria_sheet(self, criteria_names, criteria_weights):
        """Create criteria sheet with weights and ranking"""
        ws = self.add_worksheet("Criteria")

        # Headers
        self.set_header_style(ws["A1"], "Criteria Analysis", "366092")
        ws.merge_cells("A1:D1")

        self.set_subheader_style(ws["A3"], "Criteria", "4F81BD")
        self.set_subheader_style(ws["B3"], "Weight", "4F81BD")
        self.set_subheader_style(ws["C3"], "Ranking", "4F81BD")
        self.set_subheader_style(ws["D3"], "Percentage", "4F81BD")

        # Data
        for i, (name, weight) in enumerate(zip(criteria_names, criteria_weights)):
            row = i + 4
            self.set_data_style(ws.cell(row=row, column=1), name)
            self.set_number_style(ws.cell(row=row, column=2), weight)
            self.set_data_style(ws.cell(row=row, column=3), i + 1)
            self.set_number_style(ws.cell(row=row, column=4), weight * 100, 2)
            ws.cell(row=row, column=4).number_format = "0.00%"

        self.auto_adjust_columns(ws)

    def create_alternatives_sheet(self, alternatives_names, global_priorities):
        """Create alternatives sheet with global priorities"""
        ws = self.add_worksheet("Alternatives")

        # Headers
        self.set_header_style(ws["A1"], "Alternatives Analysis", "366092")
        ws.merge_cells("A1:D1")

        self.set_subheader_style(ws["A3"], "Alternative", "4F81BD")
        self.set_subheader_style(ws["B3"], "Global Priority", "4F81BD")
        self.set_subheader_style(ws["C3"], "Ranking", "4F81BD")
        self.set_subheader_style(ws["D3"], "Percentage", "4F81BD")

        # Data
        for i, (name, priority) in enumerate(
            zip(alternatives_names, global_priorities)
        ):
            row = i + 4
            self.set_data_style(ws.cell(row=row, column=1), name)
            self.set_number_style(ws.cell(row=row, column=2), priority)
            self.set_data_style(ws.cell(row=row, column=3), i + 1)
            self.set_number_style(ws.cell(row=row, column=4), priority * 100, 2)
            ws.cell(row=row, column=4).number_format = "0.00%"

        self.auto_adjust_columns(ws)

    def create_criteria_matrix_sheet(
        self, criteria_names, matrix_data, eigenvector, normalized_eigenvector
    ):
        """Create criteria comparison matrix sheet"""
        ws = self.add_worksheet("Criteria Matrix")

        # Headers
        self.set_header_style(ws["A1"], "Criteria Comparison Matrix", "366092")
        ws.merge_cells(f"A1:{get_column_letter(len(criteria_names) + 3)}1")

        # Matrix headers
        self.set_subheader_style(ws["A3"], "", "4F81BD")
        for i, name in enumerate(criteria_names):
            col = i + 2
            self.set_subheader_style(ws.cell(row=3, column=col), name, "4F81BD")
        self.set_subheader_style(
            ws.cell(row=3, column=len(criteria_names) + 2), "Eigenvector", "4F81BD"
        )
        self.set_subheader_style(
            ws.cell(row=3, column=len(criteria_names) + 3), "Normalized", "4F81BD"
        )

        # Matrix data
        for i, name in enumerate(criteria_names):
            row = i + 4
            self.set_subheader_style(ws.cell(row=row, column=1), name, "4F81BD")
            for j in range(len(criteria_names)):
                col = j + 2
                self.set_number_style(ws.cell(row=row, column=col), matrix_data[i][j])
            self.set_number_style(
                ws.cell(row=row, column=len(criteria_names) + 2), eigenvector[i]
            )
            self.set_number_style(
                ws.cell(row=row, column=len(criteria_names) + 3),
                normalized_eigenvector[i],
            )

        self.auto_adjust_columns(ws)

    def create_alternatives_matrix_sheet(
        self,
        criteria_name,
        alternatives_names,
        matrix_data,
        eigenvector,
        normalized_eigenvector,
    ):
        """Create alternatives comparison matrix sheet for a specific criteria"""
        ws = self.add_worksheet(f"Matrix_{criteria_name[:20]}")

        # Headers
        self.set_header_style(
            ws["A1"], f"Alternatives Matrix - {criteria_name}", "366092"
        )
        ws.merge_cells(f"A1:{get_column_letter(len(alternatives_names) + 3)}1")

        # Matrix headers
        self.set_subheader_style(ws["A3"], "", "4F81BD")
        for i, name in enumerate(alternatives_names):
            col = i + 2
            self.set_subheader_style(ws.cell(row=3, column=col), name, "4F81BD")
        self.set_subheader_style(
            ws.cell(row=3, column=len(alternatives_names) + 2), "Eigenvector", "4F81BD"
        )
        self.set_subheader_style(
            ws.cell(row=3, column=len(alternatives_names) + 3), "Normalized", "4F81BD"
        )

        # Matrix data
        for i, name in enumerate(alternatives_names):
            row = i + 4
            self.set_subheader_style(ws.cell(row=row, column=1), name, "4F81BD")
            for j in range(len(alternatives_names)):
                col = j + 2
                self.set_number_style(ws.cell(row=row, column=col), matrix_data[i][j])
            self.set_number_style(
                ws.cell(row=row, column=len(alternatives_names) + 2), eigenvector[i]
            )
            self.set_number_style(
                ws.cell(row=row, column=len(alternatives_names) + 3),
                normalized_eigenvector[i],
            )

        self.auto_adjust_columns(ws)

    def create_results_sheet(
        self,
        alternatives_names,
        criteria_names,
        criteria_weights,
        alternatives_weights,
        global_priorities,
    ):
        """Create final results sheet"""
        ws = self.add_worksheet("Results")

        # Headers
        self.set_header_style(ws["A1"], "Final Results", "366092")
        ws.merge_cells(f"A1:{get_column_letter(len(criteria_names) + 3)}1")

        # Table headers
        self.set_subheader_style(ws["A3"], "Alternatives", "4F81BD")
        for i, name in enumerate(criteria_names):
            col = i + 2
            self.set_subheader_style(ws.cell(row=3, column=col), name, "4F81BD")
        self.set_subheader_style(
            ws.cell(row=3, column=len(criteria_names) + 2), "Global Priority", "4F81BD"
        )
        self.set_subheader_style(
            ws.cell(row=3, column=len(criteria_names) + 3), "Ranking", "4F81BD"
        )

        # Criteria weights row
        self.set_subheader_style(ws.cell(row=4, column=1), "Criteria Weights", "4F81BD")
        for i, weight in enumerate(criteria_weights):
            col = i + 2
            self.set_number_style(ws.cell(row=4, column=col), weight)

        # Alternatives data
        for i, name in enumerate(alternatives_names):
            row = i + 5
            self.set_data_style(ws.cell(row=row, column=1), name)
            for j in range(len(criteria_names)):
                col = j + 2
                self.set_number_style(
                    ws.cell(row=row, column=col), alternatives_weights[j][i]
                )
            self.set_number_style(
                ws.cell(row=row, column=len(criteria_names) + 2),
                global_priorities[i],
                bold=True,
            )
            self.set_data_style(ws.cell(row=row, column=len(criteria_names) + 3), i + 1)

        self.auto_adjust_columns(ws)

    def create_consistency_sheet(
        self, criteria_consistency, alternatives_consistency, criteria_names
    ):
        """Create consistency indicators sheet"""
        ws = self.add_worksheet("Consistency")

        # Headers
        self.set_header_style(ws["A1"], "Consistency Indicators", "366092")
        ws.merge_cells("A1:D1")

        # Criteria consistency
        self.set_subheader_style(ws["A3"], "Criteria Matrix", "4F81BD")
        self.set_subheader_style(ws["B3"], "CI", "4F81BD")
        self.set_subheader_style(ws["C3"], "CR", "4F81BD")
        self.set_subheader_style(ws["D3"], "Status", "4F81BD")

        self.set_data_style(ws.cell(row=4, column=1), "Criteria")
        self.set_number_style(ws.cell(row=4, column=2), criteria_consistency["ci"])
        self.set_number_style(ws.cell(row=4, column=3), criteria_consistency["cr"])
        status = (
            "Acceptable" if criteria_consistency["cr"] <= 0.1 else "Review Required"
        )
        self.set_data_style(ws.cell(row=4, column=4), status)

        # Alternatives consistency
        row = 6
        self.set_subheader_style(
            ws.cell(row=row, column=1), "Alternatives Matrices", "4F81BD"
        )
        self.set_subheader_style(ws.cell(row=row, column=2), "CI", "4F81BD")
        self.set_subheader_style(ws.cell(row=row, column=3), "CR", "4F81BD")
        self.set_subheader_style(ws.cell(row=row, column=4), "Status", "4F81BD")

        for i, (ci, cr) in enumerate(
            zip(alternatives_consistency["ci"], alternatives_consistency["cr"])
        ):
            row = i + 7
            self.set_data_style(ws.cell(row=row, column=1), criteria_names[i])
            self.set_number_style(ws.cell(row=row, column=2), ci)
            self.set_number_style(ws.cell(row=row, column=3), cr)
            status = "Acceptable" if cr <= 0.1 else "Review Required"
            self.set_data_style(ws.cell(row=row, column=4), status)

        self.auto_adjust_columns(ws)

    def create_chart_sheet(self, alternatives_names, global_priorities):
        """Create chart sheet with visualization"""
        ws = self.add_worksheet("Charts")

        # Headers
        self.set_header_style(ws["A1"], "Results Visualization", "366092")
        ws.merge_cells("A1:D1")

        # Prepare data for chart
        ws["A3"] = "Alternative"
        ws["B3"] = "Global Priority"

        for i, (name, priority) in enumerate(
            zip(alternatives_names, global_priorities)
        ):
            ws.cell(row=i + 4, column=1).value = name
            ws.cell(row=i + 4, column=2).value = priority

        # Create bar chart
        chart = BarChart()
        chart.title = "Global Priorities Comparison"
        chart.x_axis.title = "Alternatives"
        chart.y_axis.title = "Priority"

        data = Reference(ws, min_col=2, min_row=3, max_row=len(alternatives_names) + 3)
        categories = Reference(
            ws, min_col=1, min_row=4, max_row=len(alternatives_names) + 3
        )

        chart.add_data(data, titles_from_data=True)
        chart.set_categories(categories)

        # Position chart
        ws.add_chart(chart, "E3")

        self.auto_adjust_columns(ws)

    def generate_hierarchy_analysis_excel(self, analysis_data):
        """Generate complete Excel file for hierarchy analysis

        Args:
            analysis_data: Dictionary containing all analysis data
        """
        self.create_workbook()

        # Extract data
        method_id = analysis_data["method_id"]
        task_description = analysis_data.get("task_description")
        criteria_names = analysis_data["criteria_names"]
        alternatives_names = analysis_data["alternatives_names"]
        criteria_weights = analysis_data["criteria_weights"]
        global_priorities = analysis_data["global_priorities"]
        criteria_matrix = analysis_data["criteria_matrix"]
        alternatives_matrices = analysis_data["alternatives_matrices"]
        criteria_eigenvector = analysis_data["criteria_eigenvector"]
        alternatives_eigenvectors = analysis_data["alternatives_eigenvectors"]
        criteria_consistency = analysis_data["criteria_consistency"]
        alternatives_consistency = analysis_data["alternatives_consistency"]

        # Create sheets in logical order
        # 1. General Information (overview)
        self.create_general_info_sheet(task_description, method_id)

        # 2. Criteria analysis
        self.create_criteria_sheet(criteria_names, criteria_weights)

        # 3. Alternatives analysis
        self.create_alternatives_sheet(alternatives_names, global_priorities)

        # 4. Criteria comparison matrix
        self.create_criteria_matrix_sheet(
            criteria_names, criteria_matrix, criteria_eigenvector, criteria_weights
        )

        # 5. Alternatives comparison matrices (for each criterion)
        for i, criteria_name in enumerate(criteria_names):
            self.create_alternatives_matrix_sheet(
                criteria_name,
                alternatives_names,
                alternatives_matrices[i],
                alternatives_eigenvectors[i],
                alternatives_eigenvectors[i],  # Using same data for normalized
            )

        # 6. Final results (summary)
        self.create_results_sheet(
            alternatives_names,
            criteria_names,
            criteria_weights,
            alternatives_eigenvectors,
            global_priorities,
        )

        # 7. Consistency indicators (validation)
        self.create_consistency_sheet(
            criteria_consistency, alternatives_consistency, criteria_names
        )

        # 8. Charts and visualization (appendix)
        self.create_chart_sheet(alternatives_names, global_priorities)

        return self.workbook

    def save_to_bytes(self):
        """Save workbook to bytes for download"""
        if not self.workbook:
            raise ValueError("No workbook to save")

        output = io.BytesIO()
        self.workbook.save(output)
        output.seek(0)
        return output.getvalue()
