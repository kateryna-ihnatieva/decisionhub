from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    Response,
    flash,
)
from mymodules.binary import *
from models import *
from mymodules.mai import *
from flask_login import current_user, login_required
from mymodules.methods import *
from mymodules.gpt_response import *
from mymodules.binary_excel_export import BinaryExcelExporter
from mymodules.file_upload import process_uploaded_file, process_binary_file

import operator
from datetime import datetime

binary_relations_bp = Blueprint("binary_relations", __name__, url_prefix="/binary")


@binary_relations_bp.route("/")
def index():
    context = {
        "title": "Бінарні Відношення",
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }
    return render_template("Binary/index.html", **context)


@binary_relations_bp.route("/names", methods=["GET", "POST"])
def names():
    # Проверяем, загружается ли черновик
    draft_id = request.args.get("draft")
    draft_data = None
    num = 0
    binary_task = None
    names = None

    if draft_id:
        try:
            from models import Draft

            draft = Draft.query.filter_by(
                id=draft_id, user_id=current_user.get_id()
            ).first()

            if draft and draft.form_data:
                draft_data = draft.form_data
                # Восстанавливаем данные из черновика
                num = int(draft_data.get("numObjects") or 0)
                binary_task = draft_data.get("task")
                names = draft_data.get("objects", [])
            else:
                # Если черновик не найден, используем значения по умолчанию
                num = 0
                binary_task = None
                names = None
        except Exception as e:
            print(f"Error loading draft: {str(e)}")
            # В случае ошибки используем значения по умолчанию
            num = 0
            binary_task = None
            names = None
    else:
        # Если черновик не загружается, получаем данные из URL параметров
        try:
            num = int(request.args.get("num") or 0)
            binary_task = request.args.get("binary_task")
            names = None
        except (ValueError, TypeError):
            num = 0
            binary_task = None
            names = None

    # Збереження змінної у сесії
    session["num"] = num
    session["binary_task"] = binary_task

    context = {
        "title": "Імена",
        "num": num,
        "binary_task": binary_task,
        "names": names,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }
    return render_template("Binary/names.html", **context)


@binary_relations_bp.route("/matrix/", methods=["GET", "POST"])
def matrix():
    # Проверяем, загружается ли черновик
    draft_id = request.args.get("draft")
    draft_data = None

    if draft_id:
        try:
            from models import Draft

            draft = Draft.query.filter_by(
                id=draft_id, user_id=current_user.get_id()
            ).first()

            if draft and draft.form_data:
                draft_data = draft.form_data
                # Восстанавливаем данные из черновика
                num = int(draft_data.get("numObjects") or 0)
                binary_task = draft_data.get("task")
                names = draft_data.get("objects", [])

                # Обновляем сессию
                session["num"] = num
                session["binary_task"] = binary_task
                session["names"] = names

                # Создаем новый ID записи для черновика
                new_record_id = add_object_to_db(db, BinaryNames, names=names)
                if binary_task:
                    add_object_to_db(db, BinaryTask, id=new_record_id, task=binary_task)

                session["new_record_id"] = new_record_id
                session["matr"] = 0

                context = {
                    "id": new_record_id,
                    "title": "Матриця попарних порівнянь",
                    "num": num,
                    "names": names,
                    "name": (
                        current_user.get_name()
                        if current_user.is_authenticated
                        else None
                    ),
                }
                return render_template("Binary/matrix.html", **context)

        except Exception as e:
            print(f"Error loading draft: {str(e)}")

    # Обычная обработка POST запроса
    num = int(session.get("num"))
    binary_task = session.get("binary_task")
    names = request.form.getlist("names")

    # Перевірка на унікальність введених імен об'єктів
    if len(names) != len(set(names)):
        error = "Імена об'єктів повинні бути унікальними!"
        context = {
            "title": "Імена",
            "num": num,
            "error": error,
            "names": names,
            "name": current_user.get_name() if current_user.is_authenticated else None,
        }
        return render_template("Binary/names.html", **context)

    # Збереження даних у БД
    new_record_id = add_object_to_db(db, BinaryNames, names=names)

    if binary_task:
        add_object_to_db(db, BinaryTask, id=new_record_id, task=binary_task)

    session["new_record_id"] = new_record_id
    session["matr"] = 0

    context = {
        "id": new_record_id,
        "title": "Матриця попарних порівнянь",
        "num": num,
        "names": names,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    return render_template("Binary/matrix.html", **context)


@binary_relations_bp.route("/result/<int:method_id>", methods=["GET", "POST"])
def result(method_id=None):
    print(f"Binary result function called with method_id: {method_id}")
    new_record_id = method_id if method_id else int(session.get("new_record_id"))
    print(f"Using new_record_id: {new_record_id}")
    binary_task = session.get("binary_task")

    try:
        binary_task_record = BinaryTask.query.get(new_record_id)
        binary_task = binary_task_record.task if binary_task_record else None
    except Exception as e:
        print("[!] Error:", e)

    binary_names_record = BinaryNames.query.get(new_record_id)
    if not binary_names_record:
        print(f"BinaryNames record not found for ID: {new_record_id}")
        flash("Binary names record not found", "error")
        return redirect(url_for("binary_relations.index"))

    names = binary_names_record.names
    num = len(names)
    print(f"Found names: {names}, count: {num}")

    # Перевіримо: якщо матриця вже є — session["matr"] має бути 1
    existing_matrix = BinaryMatrix.query.get(new_record_id)
    if existing_matrix:
        session["matr"] = 1
    else:
        session["matr"] = 0
    print(session["matr"])
    if session["matr"] == 0:
        matrix = process_matrix(request.form.getlist("matrix_binary"), num)
        add_object_to_db(
            db,
            BinaryMatrix,
            id=new_record_id,
            binary_names_id=new_record_id,
            matrix=matrix,
        )
    else:
        matrix = BinaryMatrix.query.get(new_record_id).matrix

    # створюємо словник для сум об'єктів
    sum_dict = {obj: sum([int(x) for x in row]) for obj, row in zip(names, matrix)}
    sorted_dict = dict(
        sorted(sum_dict.items(), key=operator.itemgetter(1), reverse=True)
    )

    ranj_str = ""
    ctn = 0
    flag_key = 0

    # Ранжування
    for key in sorted_dict.keys():
        if ctn == 0:
            ranj_str += key
            ctn += 1
        else:
            if sorted_dict[flag_key] > sorted_dict[key]:
                ranj_str += " > "
            else:
                ranj_str += " = "
            ranj_str += key
        flag_key = key

    existing_record = BinaryRanj.query.get(new_record_id)
    if existing_record is None:
        add_object_to_db(
            db,
            BinaryRanj,
            id=new_record_id,
            binary_names_id=new_record_id,
            binary_matrix_id=new_record_id,
            sorted_sum=sorted_dict,
            ranj=ranj_str,
            plot_data=generate_plot(
                list(sum_dict.values()), list(sum_dict.keys()), False
            ),
        )

    # Перевірка на транизитивність
    comb = []
    cond_tranz = []
    vidnosh = []
    prim = []

    for i in range(1, num - 1):
        for j in range(i + 1, num):
            for k in range(j + 1, num + 1):
                comb.append([f"a{i}", f"a{j}", f"a{k}"])
                res = check_tranz(
                    matrix[i - 1][j - 1],
                    matrix[j - 1][k - 1],
                    matrix[i - 1][k - 1],
                    i - 1,
                    j - 1,
                    k - 1,
                )
                cond_tranz.append(res[0])
                vidnosh.append(res[1])
                prim.append(res[2])

    # Розпаковка вкладених списків комбінацій
    for i in range(len(comb)):
        comb[i] = ", ".join(comb[i])

    # Висновок
    if prim.count("-") >= 1:
        visnovok = f'Перевірка на транзитивність показала, що у {prim.count("-")} випадках з {prim.count("-") + prim.count("+")} можливих для перевірки транзитивність була порушена. Це означає, що експерт у своїх оцінках був непослідовним. '
    else:
        visnovok = "Перевірка на транзитивність показала, що транзитивність жодного разу не була порушена. Це означає, що експерт у своїх оцінках був послідовним."

    # gpt_response = generate_gpt_response_binary(binary_task, names, ranj_str) if binary_task else None
    if existing_record is None:
        add_object_to_db(
            db,
            BinaryTransitivity,
            id=new_record_id,
            binary_names_id=new_record_id,
            binary_matrix_id=new_record_id,
            binary_ranj_id=new_record_id,
            comb=comb,
            condition_transitivity=cond_tranz,
            ratio=vidnosh,
            note=prim,
            binary_conclusion=visnovok,
            task_id=new_record_id if binary_task else None,
        )

        if current_user.is_authenticated:
            add_object_to_db(
                db,
                Result,
                method_name="Binary",
                method_id=new_record_id,
                user_id=current_user.get_id(),
            )

    context = {
        "title": "Результат",
        "num": num,
        "names": names,
        "matrix": matrix,
        "sorted_dict": sorted_dict,
        "ranj_str": ranj_str,
        "comb": comb,
        "len_comb": len(comb),
        "cond_tranz": cond_tranz,
        "vidnosh": vidnosh,
        "prim": prim,
        "visnovok": visnovok,
        "binary_plot": generate_plot(
            list(sum_dict.values()), list(sum_dict.keys()), False
        ),
        "name": current_user.get_name() if current_user.is_authenticated else None,
        "task": binary_task if binary_task else None,
        "method_id": method_id,
        # 'gpt_response': gpt_response,
    }

    session["matr"] = 1

    return render_template("Binary/result.html", **context)


@binary_relations_bp.route("/export/excel/<int:method_id>")
def export_excel(method_id):
    """Export binary analysis results to Excel"""
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return Response("Unauthorized", status=401)

        # Get result record
        result = Result.query.filter_by(
            method_id=method_id, user_id=current_user.get_id(), method_name="Binary"
        ).first()

        if not result:
            return Response("Result not found", status=404)

        # Get binary data
        binary_names = BinaryNames.query.get(method_id)
        binary_matrix = BinaryMatrix.query.get(method_id)
        binary_ranj = BinaryRanj.query.get(method_id)
        binary_transitivity = BinaryTransitivity.query.get(method_id)

        if not all([binary_names, binary_matrix, binary_ranj, binary_transitivity]):
            return Response("Binary data not found", status=404)

        # Get task description
        task_description = "Binary Relations Analysis"
        if binary_transitivity.task_id:
            binary_task = BinaryTask.query.get(binary_transitivity.task_id)
            if binary_task and binary_task.task:
                task_description = binary_task.task

        # Prepare analysis data
        names = binary_names.names
        matrix = binary_matrix.matrix
        sorted_dict = binary_ranj.sorted_sum
        ranj_str = binary_ranj.ranj

        # Calculate sums for matrix
        sum_dict = {obj: sum([int(x) for x in row]) for obj, row in zip(names, matrix)}

        analysis_data = {
            "method_id": method_id,
            "task_description": task_description,
            "names": names,
            "matrix": matrix,
            "sorted_dict": sum_dict,  # Use calculated sums
            "ranj_str": ranj_str,
            "comb": binary_transitivity.comb,
            "cond_tranz": binary_transitivity.condition_transitivity,
            "vidnosh": binary_transitivity.ratio,
            "prim": binary_transitivity.note,
            "visnovok": binary_transitivity.binary_conclusion,
        }

        # Generate Excel
        exporter = BinaryExcelExporter()
        workbook = exporter.generate_binary_analysis_excel(analysis_data)
        excel_bytes = exporter.save_to_bytes()

        # Prepare response
        from flask import make_response

        response = make_response(excel_bytes)
        response.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = (
            f'attachment; filename=Binary_Analysis_Task{method_id}_{datetime.now().strftime("%Y-%m-%d")}.xlsx'
        )

        return response

    except Exception as e:
        print(f"Excel export error: {e}")
        import traceback

        traceback.print_exc()
        return Response(f"Export error: {str(e)}", status=500)


@binary_relations_bp.route("/upload_matrix", methods=["POST"])
@login_required
def upload_matrix():
    """Handle file upload for binary relations matrix data"""
    try:
        # Get the uploaded file
        file = request.files.get("matrix_file")
        if not file:
            return {"success": False, "error": "No file uploaded"}, 400

        # Get number of objects from request
        num_objects = request.form.get("num_objects")
        if not num_objects:
            return {"success": False, "error": "Number of objects not provided"}, 400

        try:
            num_objects = int(num_objects)
        except ValueError:
            return {"success": False, "error": "Invalid number of objects"}, 400

        # Process the uploaded file for binary relations analysis
        result = process_binary_file(file, num_objects)
        print(f"Binary upload result: {result}")

        if result["success"]:
            response_data = {
                "success": True,
                "names": result["names"],
                "matrix": result["matrix"],
            }
            print(f"Returning response: {response_data}")
            return response_data
        else:
            return {"success": False, "error": result["error"]}, 400

    except Exception as e:
        return {"success": False, "error": f"Upload failed: {str(e)}"}, 500


@binary_relations_bp.route("/result_from_file", methods=["POST"])
@login_required
def result_from_file():
    """Process binary relations analysis from uploaded file data and redirect to result page"""
    try:
        print(f"result_from_file called with form data: {request.form}")

        # Get data from form
        file_data = {
            "names": request.form.get("uploaded_names"),
            "matrix": request.form.get("uploaded_matrix"),
        }

        print(f"Extracted file_data: {file_data}")

        # Get task description from form
        binary_task = request.form.get("binary_task")
        print(f"Binary task: {binary_task}")

        # Check if all required data is present
        if not all(file_data.values()):
            print("Missing required data from file upload")
            print(f"file_data values: {file_data}")
            flash("Missing required data from file upload", "error")
            return redirect(url_for("binary_relations.index"))

        # Parse the data
        import json

        try:
            names = json.loads(file_data["names"])
            matrix = json.loads(file_data["matrix"])
            print(f"Parsed names: {names}")
            print(f"Parsed matrix: {matrix}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            flash("Error parsing uploaded data", "error")
            return redirect(url_for("binary_relations.index"))

        # Create records in database to get method_id
        print("Creating database records...")
        new_record_id = add_object_to_db(db, BinaryNames, names=names)
        print(f"Created BinaryNames with ID: {new_record_id}")

        add_object_to_db(
            db,
            BinaryMatrix,
            id=new_record_id,
            binary_names_id=new_record_id,
            matrix=matrix,
        )
        print(f"Created BinaryMatrix with ID: {new_record_id}")

        # Create binary task if provided
        if binary_task:
            add_object_to_db(db, BinaryTask, id=new_record_id, task=binary_task)
            print(f"Created BinaryTask with ID: {new_record_id}")

        # Redirect to result page
        print(f"Redirecting to result page with method_id: {new_record_id}")
        return redirect(url_for("binary_relations.result", method_id=new_record_id))

    except Exception as e:
        print(f"Exception in result_from_file: {str(e)}")
        import traceback

        traceback.print_exc()
        flash(f"Error processing file data: {str(e)}", "error")
        return redirect(url_for("binary_relations.index"))
