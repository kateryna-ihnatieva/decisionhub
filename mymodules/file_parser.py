import pandas as pd
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class FileParser:
    """Parser for Excel and CSV files containing decision matrices"""

    def __init__(self):
        self.supported_formats = [".xlsx", ".xls", ".csv"]

    def parse_file(
        self,
        file_path: str,
        method_type: str,
        expected_criteria: int = None,
        expected_alternatives: int = None,
    ) -> Dict[str, Any]:
        """
        Parse uploaded file and extract matrices based on method type

        Args:
            file_path: Path to uploaded file
            method_type: Type of decision method (hierarchy, laplasa, etc.)
            expected_criteria: Expected number of criteria
            expected_alternatives: Expected number of alternatives

        Returns:
            Dictionary with parsed data and validation results
        """
        try:
            # Read file based on extension
            file_ext = file_path.lower().split(".")[-1]

            if file_ext in ["xlsx", "xls"]:
                df = pd.read_excel(file_path, header=None)
            elif file_ext == "csv":
                # Try different separators
                for sep in [",", ";", "\t"]:
                    try:
                        df = pd.read_csv(
                            file_path, header=None, sep=sep, encoding="utf-8"
                        )
                        break
                    except Exception:
                        try:
                            df = pd.read_csv(
                                file_path, header=None, sep=sep, encoding="cp1251"
                            )
                            break
                        except Exception:
                            continue
                else:
                    raise ValueError("Could not parse CSV file with any separator")
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

            # Clean the dataframe
            df = df.fillna("").astype(str)

            # Parse based on method type
            if method_type == "hierarchy":
                return self._parse_hierarchy_file(
                    df, expected_criteria, expected_alternatives
                )
            elif method_type in ["laplasa", "maximin", "savage", "hurwitz"]:
                return self._parse_cost_matrix_file(
                    df, expected_alternatives, expected_criteria
                )
            elif method_type == "binary":
                return self._parse_binary_file(df, expected_alternatives)
            elif method_type == "experts":
                return self._parse_experts_file(df, expected_alternatives)
            else:
                raise ValueError(f"Unsupported method type: {method_type}")

        except Exception as e:
            logger.error("Error parsing file %s: %s", file_path, str(e))
            return {
                "success": False,
                "error": f"Error parsing file: {str(e)}",
                "criteria_names": [],
                "alternative_names": [],
                "matrices": [],
            }

    def _parse_hierarchy_file(
        self, df: pd.DataFrame, expected_criteria: int, expected_alternatives: int
    ) -> Dict[str, Any]:
        """Parse hierarchy analysis file with multiple matrices"""
        try:
            # Find matrices by looking for patterns
            matrices = []
            criteria_names = []
            alternative_names = []
            current_matrix = []
            current_names = []
            in_matrix = False

            for _, row in df.iterrows():
                row_values = [
                    str(val).strip()
                    for val in row.values
                    if str(val).strip() != "" and str(val).strip().lower() != "nan"
                ]

                if not row_values:
                    # Empty row - end current matrix if we're in one
                    if in_matrix and current_matrix:
                        matrices.append(
                            {"names": current_names, "matrix": current_matrix}
                        )
                        current_matrix = []
                        current_names = []
                        in_matrix = False
                    continue

                # Check if this row is a header row (all values are non-numeric)
                all_names = all(not self._is_numeric(val) for val in row_values)
                has_names = any(not self._is_numeric(val) for val in row_values)

                if all_names and len(row_values) >= 2:
                    # This is a header row with names
                    print(f"DEBUG: Found header row: {row_values}")
                    if in_matrix and current_matrix:
                        # End current matrix and start new one
                        print(
                            f"DEBUG: Ending current matrix with {len(current_matrix)} rows"
                        )
                        matrices.append(
                            {"names": current_names, "matrix": current_matrix}
                        )
                    current_names = row_values
                    in_matrix = True
                    current_matrix = []
                    print(f"DEBUG: Started new matrix with names: {current_names}")
                elif (
                    in_matrix
                    and len(row_values) == len(current_names)
                    and not all_names
                ):
                    # This is a data row
                    print(f"DEBUG: Found data row: {row_values}")
                    matrix_row = []
                    for val in row_values:
                        if self._is_numeric(val):
                            matrix_row.append(self._convert_to_float(val))
                        else:
                            # Skip non-numeric values in data rows
                            matrix_row.append(1.0)
                    current_matrix.append(matrix_row)
                    print(
                        f"DEBUG: Added row to matrix, total rows: {len(current_matrix)}"
                    )
                elif in_matrix and len(row_values) != len(current_names):
                    # End of current matrix due to size mismatch
                    if current_matrix:
                        matrices.append(
                            {"names": current_names, "matrix": current_matrix}
                        )
                    current_matrix = []
                    current_names = []
                    in_matrix = False

            # Add last matrix if exists
            if in_matrix and current_matrix:
                matrices.append({"names": current_names, "matrix": current_matrix})

            # Extract criteria and alternative names
            if matrices:
                # First matrix is criteria comparison
                criteria_names = matrices[0]["names"] if matrices else []
                # Alternative names from other matrices (should be the same)
                if len(matrices) > 1:
                    alternative_names = (
                        matrices[1]["names"] if matrices[1]["names"] else []
                    )
                else:
                    alternative_names = []

            # Validate dimensions
            validation_result = self._validate_hierarchy_data(
                matrices, expected_criteria, expected_alternatives
            )

            return {
                "success": validation_result["success"],
                "error": validation_result.get("error", ""),
                "criteria_names": criteria_names,
                "alternative_names": alternative_names,
                "matrices": matrices,
                "validation": validation_result,
            }

        except Exception as e:
            logger.error("Error parsing hierarchy file: %s", str(e))
            return {
                "success": False,
                "error": f"Error parsing hierarchy file: {str(e)}",
                "criteria_names": [],
                "alternative_names": [],
                "matrices": [],
            }

    def _parse_cost_matrix_file(
        self, df: pd.DataFrame, expected_alternatives: int, expected_conditions: int
    ) -> Dict[str, Any]:
        """Parse cost matrix file for Laplasa, Maximin, Savage, Hurwitz methods"""
        try:
            # Find the matrix data
            matrix_data = []
            alternative_names = []
            condition_names = []

            # Look for names in first row and first column
            for _, row in df.iterrows():
                row_values = [
                    str(val).strip()
                    for val in row.values
                    if str(val).strip() != "" and str(val).strip().lower() != "nan"
                ]
                if not row_values:
                    continue

                # Check if this row has names (non-numeric values)
                has_names = any(not self._is_numeric(val) for val in row_values)

                if has_names and not alternative_names:
                    # This is likely the header row
                    alternative_names = [
                        val for val in row_values[1:] if not self._is_numeric(val)
                    ]
                    condition_names = [
                        val for val in row_values[1:] if not self._is_numeric(val)
                    ]
                elif not has_names and len(row_values) > 1:
                    # This is a data row
                    row_name = (
                        row_values[0]
                        if not self._is_numeric(row_values[0])
                        else f"Row {len(matrix_data) + 1}"
                    )
                    if not alternative_names:
                        alternative_names.append(row_name)

                    matrix_row = []
                    for val in row_values[1:]:
                        if self._is_numeric(val):
                            matrix_row.append(self._convert_to_float(val))
                        else:
                            matrix_row.append(0.0)
                    matrix_data.append(matrix_row)

            # If we didn't find names in header, use row names
            if not condition_names and matrix_data:
                condition_names = [
                    f"Condition {i+1}" for i in range(len(matrix_data[0]))
                ]

            # Validate dimensions
            validation_result = self._validate_cost_matrix_data(
                matrix_data, expected_alternatives, expected_conditions
            )

            return {
                "success": validation_result["success"],
                "error": validation_result.get("error", ""),
                "alternative_names": alternative_names,
                "condition_names": condition_names,
                "matrix": matrix_data,
                "validation": validation_result,
            }

        except Exception as e:
            logger.error("Error parsing cost matrix file: %s", str(e))
            return {
                "success": False,
                "error": f"Error parsing cost matrix file: {str(e)}",
                "alternative_names": [],
                "condition_names": [],
                "matrix": [],
            }

    def _parse_binary_file(
        self, df: pd.DataFrame, expected_alternatives: int
    ) -> Dict[str, Any]:
        """Parse binary relations file"""
        try:
            matrix_data = []
            alternative_names = []

            # Find the matrix data
            for _, row in df.iterrows():
                row_values = [
                    str(val).strip()
                    for val in row.values
                    if str(val).strip() != "" and str(val).strip().lower() != "nan"
                ]
                if not row_values:
                    continue

                # Check if this row has names
                has_names = any(not self._is_numeric(val) for val in row_values)

                if has_names and not alternative_names:
                    # Header row
                    alternative_names = [
                        val for val in row_values[1:] if not self._is_numeric(val)
                    ]
                elif not has_names and len(row_values) > 1:
                    # Data row
                    matrix_row = []
                    for val in row_values[1:]:
                        if self._is_numeric(val):
                            matrix_row.append(int(self._convert_to_float(val)))
                        else:
                            matrix_row.append(0)
                    matrix_data.append(matrix_row)

            # Validate dimensions
            validation_result = self._validate_binary_data(
                matrix_data, expected_alternatives
            )

            return {
                "success": validation_result["success"],
                "error": validation_result.get("error", ""),
                "alternative_names": alternative_names,
                "matrix": matrix_data,
                "validation": validation_result,
            }

        except Exception as e:
            logger.error("Error parsing binary file: %s", str(e))
            return {
                "success": False,
                "error": f"Error parsing binary file: {str(e)}",
                "alternative_names": [],
                "matrix": [],
            }

    def _parse_experts_file(
        self, df: pd.DataFrame, expected_alternatives: int
    ) -> Dict[str, Any]:
        """Parse experts evaluation file"""
        try:
            matrix_data = []
            alternative_names = []

            # Similar to binary parsing but for experts data
            for _, row in df.iterrows():
                row_values = [
                    str(val).strip()
                    for val in row.values
                    if str(val).strip() != "" and str(val).strip().lower() != "nan"
                ]
                if not row_values:
                    continue

                has_names = any(not self._is_numeric(val) for val in row_values)

                if has_names and not alternative_names:
                    alternative_names = [
                        val for val in row_values[1:] if not self._is_numeric(val)
                    ]
                elif not has_names and len(row_values) > 1:
                    matrix_row = []
                    for val in row_values[1:]:
                        if self._is_numeric(val):
                            matrix_row.append(self._convert_to_float(val))
                        else:
                            matrix_row.append(0.0)
                    matrix_data.append(matrix_row)

            validation_result = self._validate_experts_data(
                matrix_data, expected_alternatives
            )

            return {
                "success": validation_result["success"],
                "error": validation_result.get("error", ""),
                "alternative_names": alternative_names,
                "matrix": matrix_data,
                "validation": validation_result,
            }

        except Exception as e:
            logger.error("Error parsing experts file: %s", str(e))
            return {
                "success": False,
                "error": f"Error parsing experts file: {str(e)}",
                "alternative_names": [],
                "matrix": [],
            }

    def _is_numeric(self, value: str) -> bool:
        """Check if a string represents a numeric value (including fractions)"""
        if not value or value.strip() == "":
            return False

        value = value.strip()

        # Check for fractions like "1/2", "1/3"
        if "/" in value:
            try:
                parts = value.split("/")
                if len(parts) == 2:
                    float(parts[0])
                    float(parts[1])
                    return True
            except Exception:
                pass

        # Check for regular numbers
        try:
            float(value)
            return True
        except Exception:
            return False

    def _convert_to_float(self, value: str) -> float:
        """Convert string to float, handling fractions"""
        if not value or value.strip() == "":
            return 0.0

        value = value.strip()

        # Handle fractions
        if "/" in value:
            try:
                parts = value.split("/")
                if len(parts) == 2:
                    return float(parts[0]) / float(parts[1])
            except Exception:
                pass

        # Handle regular numbers
        try:
            return float(value)
        except Exception:
            return 0.0

    def _validate_hierarchy_data(
        self, matrices: List[Dict], expected_criteria: int, expected_alternatives: int
    ) -> Dict[str, Any]:
        """Validate hierarchy analysis data"""
        errors = []

        if not matrices:
            errors.append("No matrices found in file")
            return {"success": False, "error": "; ".join(errors)}

        # Check criteria matrix (first matrix)
        if len(matrices) < 1:
            errors.append("Criteria comparison matrix not found")
        else:
            criteria_matrix = matrices[0]
            if len(criteria_matrix["names"]) != expected_criteria:
                errors.append(
                    f"Expected {expected_criteria} criteria, found {len(criteria_matrix['names'])}"
                )

            if len(criteria_matrix["matrix"]) != expected_criteria:
                errors.append(
                    f"Criteria matrix should be {expected_criteria}x{expected_criteria}"
                )

        # Check alternative matrices
        if len(matrices) < expected_criteria + 1:
            errors.append(
                f"Expected {expected_criteria + 1} matrices (1 criteria + {expected_criteria} alternatives), found {len(matrices)}"
            )
        else:
            for i in range(1, min(len(matrices), expected_criteria + 1)):
                alt_matrix = matrices[i]
                if len(alt_matrix["names"]) != expected_alternatives:
                    errors.append(
                        f"Alternative matrix {i} should have {expected_alternatives} alternatives"
                    )

                if len(alt_matrix["matrix"]) != expected_alternatives:
                    errors.append(
                        f"Alternative matrix {i} should be {expected_alternatives}x{expected_alternatives}"
                    )

        return {
            "success": len(errors) == 0,
            "error": "; ".join(errors) if errors else "",
            "errors": errors,
        }

    def _validate_cost_matrix_data(
        self,
        matrix: List[List[float]],
        expected_alternatives: int,
        expected_conditions: int,
    ) -> Dict[str, Any]:
        """Validate cost matrix data"""
        errors = []

        if not matrix:
            errors.append("No matrix data found")
            return {"success": False, "error": "; ".join(errors)}

        if len(matrix) != expected_alternatives:
            errors.append(
                f"Expected {expected_alternatives} alternatives, found {len(matrix)}"
            )

        if matrix and len(matrix[0]) != expected_conditions:
            errors.append(
                f"Expected {expected_conditions} conditions, found {len(matrix[0])}"
            )

        return {
            "success": len(errors) == 0,
            "error": "; ".join(errors) if errors else "",
            "errors": errors,
        }

    def _validate_binary_data(
        self, matrix: List[List[int]], expected_alternatives: int
    ) -> Dict[str, Any]:
        """Validate binary relations data"""
        errors = []

        if not matrix:
            errors.append("No matrix data found")
            return {"success": False, "error": "; ".join(errors)}

        if len(matrix) != expected_alternatives:
            errors.append(
                f"Expected {expected_alternatives} alternatives, found {len(matrix)}"
            )

        if matrix and len(matrix[0]) != expected_alternatives:
            errors.append(
                f"Matrix should be {expected_alternatives}x{expected_alternatives}"
            )

        return {
            "success": len(errors) == 0,
            "error": "; ".join(errors) if errors else "",
            "errors": errors,
        }

    def _validate_experts_data(
        self, matrix: List[List[float]], expected_alternatives: int
    ) -> Dict[str, Any]:
        """Validate experts evaluation data"""
        errors = []

        if not matrix:
            errors.append("No matrix data found")
            return {"success": False, "error": "; ".join(errors)}

        if len(matrix) != expected_alternatives:
            errors.append(
                f"Expected {expected_alternatives} alternatives, found {len(matrix)}"
            )

        return {
            "success": len(errors) == 0,
            "error": "; ".join(errors) if errors else "",
            "errors": errors,
        }
