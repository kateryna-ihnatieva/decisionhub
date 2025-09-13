import os
import pandas as pd
import openpyxl
from werkzeug.utils import secure_filename
from flask import current_app


class FileUploadError(Exception):
    """Custom exception for file upload errors"""

    pass


def validate_file(file, max_size_mb=10):
    """
    Validate uploaded file for format and size

    Args:
        file: Flask file object
        max_size_mb: Maximum file size in MB

    Returns:
        tuple: (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, "No file selected"

    # Check file extension
    allowed_extensions = {".xlsx", ".xls", ".csv"}
    file_ext = os.path.splitext(file.filename.lower())[1]

    if file_ext not in allowed_extensions:
        formats = ", ".join(allowed_extensions)
        return (
            False,
            f"Unsupported file format. Allowed formats: {formats}",
        )

    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"File too large. Maximum size: {max_size_mb}MB"

    return True, None


def parse_excel_file(file_path, expected_size):
    """
    Parse Excel file and extract names and matrix data

    Args:
        file_path: Path to Excel file
        expected_size: Expected matrix size (rows/columns)

    Returns:
        dict: {'names': list, 'matrix': list, 'error': str or None}
    """
    try:
        # Try to read with openpyxl first (better for .xlsx)
        if file_path.endswith(".xlsx"):
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            worksheet = workbook.active

            # Convert to list of lists
            data = []
            for row in worksheet.iter_rows(values_only=True):
                data.append([cell if cell is not None else "" for cell in row])
        else:
            # Use pandas for .xls files
            df = pd.read_excel(file_path, header=None)
            data = df.fillna("").values.tolist()

        return extract_names_and_matrix(data, expected_size)

    except Exception as e:
        return {
            "names": [],
            "matrix": [],
            "error": f"Error reading Excel file: {str(e)}",
        }


def parse_csv_file(file_path, expected_size):
    """
    Parse CSV file and extract names and matrix data

    Args:
        file_path: Path to CSV file
        expected_size: Expected matrix size (rows/columns)

    Returns:
        dict: {'names': list, 'matrix': list, 'error': str or None}
    """
    try:
        # Try different separators
        separators = [",", ";", "\t", "|"]
        data = None

        for sep in separators:
            try:
                df = pd.read_csv(file_path, header=None, sep=sep)
                if not df.empty:
                    data = df.fillna("").values.tolist()
                    break
            except Exception:
                continue

        if data is None:
            return {
                "names": [],
                "matrix": [],
                "error": "Could not parse CSV file with any known separator",
            }

        return extract_names_and_matrix(data, expected_size)

    except Exception as e:
        return {"names": [], "matrix": [], "error": f"Error reading CSV file: {str(e)}"}


def extract_names_and_matrix(data, expected_size):
    """
    Extract names and matrix from parsed data for hierarchy analysis

    Args:
        data: List of lists containing the file data
        expected_size: Expected matrix size (rows/columns)

    Returns:
        dict: {'names': list, 'matrix': list, 'error': str or None}
    """
    try:
        if not data or len(data) == 0:
            return {"names": [], "matrix": [], "error": "File is empty"}

        # Clean data - remove completely empty rows
        data = [row for row in data if any(str(cell).strip() for cell in row)]

        if len(data) == 0:
            return {"names": [], "matrix": [], "error": "No data found in file"}

        # Determine matrix structure
        rows = len(data)
        cols = len(data[0]) if data else 0

        # Check if we have enough data for the expected size
        min_size = expected_size + 1
        if rows < min_size or cols < min_size:
            return {
                "names": [],
                "matrix": [],
                "error": f"Insufficient data. Expected at least {min_size}x{min_size}, got {rows}x{cols}",
            }

        # For hierarchy analysis, we expect names in both first row and first column
        # First cell (0,0) is usually empty or contains a label
        # Names are in first row (excluding first cell) and first column

        # Extract names from first row (excluding first cell)
        first_row_names = []
        for j in range(1, min(expected_size + 1, len(data[0]))):
            cell_value = str(data[0][j]).strip()
            if cell_value and cell_value != "":
                first_row_names.append(cell_value)

        # Extract names from first column (excluding first cell)
        first_col_names = []
        for i in range(1, min(expected_size + 1, len(data))):
            cell_value = str(data[i][0]).strip()
            if cell_value and cell_value != "":
                first_col_names.append(cell_value)

        # Determine which names to use (prefer first row, fallback to first column)
        names = []
        matrix_start_row = 1
        matrix_start_col = 1

        if len(first_row_names) >= expected_size:
            names = first_row_names[:expected_size]
        elif len(first_col_names) >= expected_size:
            names = first_col_names[:expected_size]
        else:
            # Try to combine both if neither has enough
            combined_names = list(set(first_row_names + first_col_names))
            if len(combined_names) >= expected_size:
                names = combined_names[:expected_size]
            else:
                # Use default names if nothing works
                names = [f"Item {i+1}" for i in range(expected_size)]
                matrix_start_row = 0
                matrix_start_col = 0

        # Extract matrix data
        matrix = []
        for i in range(matrix_start_row, matrix_start_row + expected_size):
            row = []
            for j in range(matrix_start_col, matrix_start_col + expected_size):
                if i < len(data) and j < len(data[i]):
                    cell_value = data[i][j]
                else:
                    cell_value = ""

                # Convert to string and clean
                cell_str = str(cell_value).strip()

                # Try to convert to float for numeric values
                # Handle fractions like "1/2", "1/5" etc.
                try:
                    if "/" in cell_str:
                        # Handle fractions
                        numerator, denominator = cell_str.split("/")
                        row.append(float(numerator) / float(denominator))
                    elif (
                        cell_str
                        and cell_str.replace(".", "")
                        .replace("-", "")
                        .replace("+", "")
                        .replace("e", "")
                        .replace("E", "")
                        .isdigit()
                    ):
                        row.append(float(cell_str))
                    else:
                        # Try to evaluate as expression (for cases like "1/2" written as "1/2")
                        try:
                            row.append(float(eval(cell_str)))
                        except Exception:
                            row.append(cell_str)
                except Exception:
                    row.append(cell_str)

            matrix.append(row)

        # Validate names
        if not names or len(names) != expected_size:
            return {
                "names": [],
                "matrix": [],
                "error": f"Could not extract {expected_size} valid names",
            }

        # Check for duplicate names
        if len(set(names)) != len(names):
            return {
                "names": [],
                "matrix": [],
                "error": "Duplicate names found. All names must be unique",
            }

        # Validate matrix contains numeric data
        numeric_count = 0
        for row in matrix:
            for cell in row:
                if isinstance(cell, (int, float)) and not pd.isna(cell):
                    numeric_count += 1

        if numeric_count == 0:
            return {
                "names": [],
                "matrix": [],
                "error": "No numeric data found in matrix",
            }

        return {"names": names, "matrix": matrix, "error": None}

    except Exception as e:
        return {"names": [], "matrix": [], "error": f"Error processing data: {str(e)}"}


def save_uploaded_file(file, upload_folder):
    """
    Save uploaded file to specified folder

    Args:
        file: Flask file object
        upload_folder: Path to upload folder

    Returns:
        str: Path to saved file
    """
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    return file_path


def cleanup_file(file_path):
    """
    Delete uploaded file after processing

    Args:
        file_path: Path to file to delete
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        current_app.logger.warning(f"Could not delete file {file_path}: {str(e)}")


def process_uploaded_file(file, expected_size, upload_folder="uploads"):
    """
    Main function to process uploaded file

    Args:
        file: Flask file object
        expected_size: Expected matrix size
        upload_folder: Folder to save uploaded files

    Returns:
        dict: {'success': bool, 'names': list, 'matrix': list, 'error': str}
    """
    try:
        # Validate file
        is_valid, error = validate_file(file)
        if not is_valid:
            return {"success": False, "names": [], "matrix": [], "error": error}

        # Save file
        file_path = save_uploaded_file(file, upload_folder)

        try:
            # Parse file based on extension
            file_ext = os.path.splitext(file.filename.lower())[1]

            if file_ext in [".xlsx", ".xls"]:
                result = parse_excel_file(file_path, expected_size)
            elif file_ext == ".csv":
                result = parse_csv_file(file_path, expected_size)
            else:
                return {
                    "success": False,
                    "names": [],
                    "matrix": [],
                    "error": "Unsupported file format",
                }

            # Clean up file
            cleanup_file(file_path)

            if result["error"]:
                return {
                    "success": False,
                    "names": [],
                    "matrix": [],
                    "error": result["error"],
                }

            return {
                "success": True,
                "names": result["names"],
                "matrix": result["matrix"],
                "error": None,
            }

        except Exception as e:
            # Clean up file on error
            cleanup_file(file_path)
            return {
                "success": False,
                "names": [],
                "matrix": [],
                "error": f"Error processing file: {str(e)}",
            }

    except Exception as e:
        return {
            "success": False,
            "names": [],
            "matrix": [],
            "error": f"Upload error: {str(e)}",
        }


def process_hierarchy_file(
    file, num_criteria, num_alternatives, upload_folder="uploads"
):
    """
    Process uploaded file specifically for hierarchy analysis
    Handles files with both criteria and alternatives matrices

    Args:
        file: Flask file object
        num_criteria: Number of criteria
        num_alternatives: Number of alternatives
        upload_folder: Folder to save uploaded files

    Returns:
        dict: {'success': bool, 'criteria_names': list, 'alternatives_names': list,
               'criteria_matrix': list, 'alternatives_matrices': list, 'error': str}
    """
    try:
        # Validate file
        is_valid, error = validate_file(file)
        if not is_valid:
            return {
                "success": False,
                "criteria_names": [],
                "alternatives_names": [],
                "criteria_matrix": [],
                "alternatives_matrices": [],
                "error": error,
            }

        # Save file
        file_path = save_uploaded_file(file, upload_folder)

        try:
            # Parse file based on extension
            file_ext = os.path.splitext(file.filename.lower())[1]

            if file_ext in [".xlsx", ".xls"]:
                data = parse_excel_data(file_path)
            elif file_ext == ".csv":
                data = parse_csv_data_with_empty_rows(file_path)
            else:
                return {
                    "success": False,
                    "criteria_names": [],
                    "alternatives_names": [],
                    "criteria_matrix": [],
                    "alternatives_matrices": [],
                    "error": "Unsupported file format",
                }

            # Process hierarchy data
            result = extract_hierarchy_data(data, num_criteria, num_alternatives)

            # Clean up file
            cleanup_file(file_path)

            return result

        except Exception as e:
            # Clean up file on error
            cleanup_file(file_path)
            return {
                "success": False,
                "criteria_names": [],
                "alternatives_names": [],
                "criteria_matrix": [],
                "alternatives_matrices": [],
                "error": f"Error processing file: {str(e)}",
            }

    except Exception as e:
        return {
            "success": False,
            "criteria_names": [],
            "alternatives_names": [],
            "criteria_matrix": [],
            "alternatives_matrices": [],
            "error": f"Upload error: {str(e)}",
        }


def parse_excel_data(file_path):
    """Parse Excel file and return raw data"""
    if file_path.endswith(".xlsx"):
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        worksheet = workbook.active
        data = []
        for row in worksheet.iter_rows(values_only=True):
            data.append([cell if cell is not None else "" for cell in row])
    else:
        df = pd.read_excel(file_path, header=None)
        data = df.fillna("").values.tolist()
    return data


def parse_csv_data(file_path):
    """Parse CSV file and return raw data"""
    separators = [",", ";", "\t", "|"]
    data = None

    for sep in separators:
        try:
            df = pd.read_csv(file_path, header=None, sep=sep)
            if not df.empty:
                data = df.fillna("").values.tolist()
                break
        except Exception:
            continue

    if data is None:
        raise Exception("Could not parse CSV file with any known separator")

    return data


def parse_csv_data_with_empty_rows(file_path):
    """Parse CSV file and return raw data preserving empty rows"""
    separators = [",", ";", "\t", "|"]
    data = None

    for sep in separators:
        try:
            df = pd.read_csv(
                file_path,
                header=None,
                sep=sep,
                keep_default_na=False,
                dtype=str,
                skip_blank_lines=False,
            )
            if not df.empty:
                data = df.values.tolist()
                break
        except Exception:
            continue

    if data is None:
        raise Exception("Could not parse CSV file with any known separator")

    return data


def extract_hierarchy_data(data, num_criteria, num_alternatives):
    """
    Extract criteria and alternatives data from hierarchy file

    For hierarchy analysis:
    - First matrix: criteria names and matrix
    - Second matrix: alternatives names and matrix
    - Subsequent matrices: alternatives comparison matrices for each criterion

    Args:
        data: Raw file data
        num_criteria: Number of criteria
        num_alternatives: Number of alternatives

    Returns:
        dict with criteria and alternatives data
    """
    try:
        if not data or len(data) == 0:
            return {
                "success": False,
                "criteria_names": [],
                "alternatives_names": [],
                "criteria_matrix": [],
                "alternatives_matrices": [],
                "error": "File is empty",
            }

        # Find matrix boundaries by looking for empty rows
        matrix_boundaries = []
        current_start = 0

        for i, row in enumerate(data):
            # Check if row is completely empty
            if not any(str(cell).strip() for cell in row):
                if i > current_start:
                    matrix_boundaries.append((current_start, i))
                current_start = i + 1

        # Add the last matrix if it doesn't end with empty row
        if current_start < len(data):
            matrix_boundaries.append((current_start, len(data)))

        # If no empty rows found, treat the entire data as one matrix
        if not matrix_boundaries:
            matrix_boundaries.append((0, len(data)))

        if len(matrix_boundaries) < 2:
            return {
                "success": False,
                "criteria_names": [],
                "alternatives_names": [],
                "criteria_matrix": [],
                "alternatives_matrices": [],
                "error": "File must contain at least 2 matrices (criteria and alternatives)",
            }

        # Clean data for each matrix separately
        cleaned_matrices = []
        for start, end in matrix_boundaries:
            matrix_data = data[start:end]
            # Clean data - remove completely empty rows
            cleaned_matrix = [
                row for row in matrix_data if any(str(cell).strip() for cell in row)
            ]
            if cleaned_matrix:  # Only add non-empty matrices
                # Split each row by comma if it's a single string
                processed_matrix = []
                for row in cleaned_matrix:
                    if len(row) == 1 and isinstance(row[0], str) and "," in row[0]:
                        # Split the string by comma
                        processed_row = [cell.strip() for cell in row[0].split(",")]
                        processed_matrix.append(processed_row)
                    else:
                        processed_matrix.append(row)
                cleaned_matrices.append(processed_matrix)

        if len(cleaned_matrices) < 2:
            return {
                "success": False,
                "criteria_names": [],
                "alternatives_names": [],
                "criteria_matrix": [],
                "alternatives_matrices": [],
                "error": "File must contain at least 2 matrices (criteria and alternatives)",
            }

        # Extract first matrix (criteria)
        criteria_data = cleaned_matrices[0]
        criteria_result = extract_names_and_matrix(criteria_data, num_criteria)

        if criteria_result["error"]:
            return {
                "success": False,
                "criteria_names": [],
                "alternatives_names": [],
                "criteria_matrix": [],
                "alternatives_matrices": [],
                "error": f"Error extracting criteria: {criteria_result['error']}",
            }

        # Extract second matrix (alternatives)
        alternatives_data = cleaned_matrices[1]
        alternatives_result = extract_names_and_matrix(
            alternatives_data, num_alternatives
        )

        if alternatives_result["error"]:
            return {
                "success": False,
                "criteria_names": [],
                "alternatives_names": [],
                "criteria_matrix": [],
                "alternatives_matrices": [],
                "error": f"Error extracting alternatives: {alternatives_result['error']}",
            }

        # For hierarchy analysis, we need multiple alternatives matrices
        # Extract all matrices after the first one (criteria matrix)
        alternatives_matrices = []

        # Process all matrices after the first one
        for i in range(1, len(cleaned_matrices)):
            alt_matrix_data = cleaned_matrices[i]
            alt_result = extract_names_and_matrix(alt_matrix_data, num_alternatives)

            if alt_result["error"]:
                return {
                    "success": False,
                    "criteria_names": [],
                    "alternatives_names": [],
                    "criteria_matrix": [],
                    "alternatives_matrices": [],
                    "error": f"Error extracting alternatives matrix {i}: {alt_result['error']}",
                }

            alternatives_matrices.append(alt_result["matrix"])

        # Validate that we have the right number of matrices
        num_criteria = len(criteria_result["names"])
        if len(alternatives_matrices) != num_criteria:
            return {
                "success": False,
                "criteria_names": [],
                "alternatives_names": [],
                "criteria_matrix": [],
                "alternatives_matrices": [],
                "error": f"Expected {num_criteria} alternatives matrices, but found {len(alternatives_matrices)}",
            }

        return {
            "success": True,
            "criteria_names": criteria_result["names"],
            "alternatives_names": alternatives_result["names"],
            "criteria_matrix": criteria_result["matrix"],
            "alternatives_matrices": alternatives_matrices,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "criteria_names": [],
            "alternatives_names": [],
            "criteria_matrix": [],
            "alternatives_matrices": [],
            "error": f"Error processing hierarchy data: {str(e)}",
        }
