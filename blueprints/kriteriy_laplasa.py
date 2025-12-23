from flask import (
    Blueprint,
    render_template,
    request,
    session,
    Response,
    flash,
    redirect,
    url_for,
)
from mymodules.mai import *
from models import (
    LaplasaConditions,
    LaplasaAlternatives,
    LaplasaCostMatrix,
    LaplasaTask,
    db,
    Result,
)
from flask_login import current_user, login_required
from mymodules.methods import add_object_to_db, generate_plot
from mymodules.experts_func import make_table
from mymodules.laplasa_excel_export import LaplasaExcelExporter
from mymodules.file_upload import process_laplasa_file
from datetime import datetime

kriteriy_laplasa_bp = Blueprint("kriteriy_laplasa", __name__, url_prefix="/laplasa")


@kriteriy_laplasa_bp.route("/")
def index():
    context = {
        "title": "Критерій Лапласа",
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }
    return render_template("Laplasa/index.html", **context)


@kriteriy_laplasa_bp.route("/names", methods=["GET", "POST"])
def names():
    # Проверяем, загружается ли черновик
    draft_id = request.args.get("draft")
    draft_data = None
    num_alt = 0
    num_conditions = 0
    laplasa_task = None
    matrix_type = None

    if draft_id:
        try:
            from models import Draft

            draft = Draft.query.filter_by(
                id=draft_id, user_id=current_user.get_id()
            ).first()

            if draft and draft.form_data:
                draft_data = draft.form_data
                # Восстанавливаем данные из черновика
                num_alt = int(draft_data.get("numAlternatives") or 0)
                num_conditions = int(draft_data.get("numConditions") or 0)
                laplasa_task = draft_data.get("task")
                matrix_type = draft_data.get("matrixType")
            else:
                # Если черновик не найден, используем значения по умолчанию
                num_alt = 0
                num_conditions = 0
                laplasa_task = None
                matrix_type = None
        except Exception as e:
            print(f"Error loading draft: {str(e)}")
            # В случае ошибки используем значения по умолчанию
            num_alt = 0
            num_conditions = 0
            laplasa_task = None
            matrix_type = None
    else:
        # Если черновик не загружается, получаем данные из URL параметров
        try:
            num_alt = int(request.args.get("num_alt") or 0)
            num_conditions = int(request.args.get("num_conditions") or 0)
            laplasa_task = request.args.get("laplasa_task")
            matrix_type = request.args.get("matrix_type")
        except (ValueError, TypeError):
            num_alt = 0
            num_conditions = 0
            laplasa_task = None
            matrix_type = None

    # Збереження змінної у сесії
    session["num_alt"] = num_alt
    session["num_conditions"] = num_conditions
    session["laplasa_task"] = laplasa_task
    session["matrix_type"] = matrix_type

    context = {
        "title": "Імена",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "laplasa_task": laplasa_task,
        "matrix_type": matrix_type,
        "name_alternatives": draft_data.get("alternatives") if draft_data else None,
        "name_conditions": draft_data.get("conditions") if draft_data else None,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    return render_template("Laplasa/names.html", **context)


@kriteriy_laplasa_bp.route("/cost-matrix", methods=["GET", "POST"])
def cost_matrix():
    # Проверяем, загружается ли черновик
    draft_id = request.args.get("draft")
    draft_data = None
    matrix_type = None

    if draft_id:
        try:
            from models import Draft

            draft = Draft.query.filter_by(
                id=draft_id, user_id=current_user.get_id()
            ).first()

            if draft and draft.form_data:
                draft_data = draft.form_data
                # Восстанавливаем данные из черновика
                num_alt = int(draft_data.get("numAlternatives") or 0)
                num_conditions = int(draft_data.get("numConditions") or 0)
                laplasa_task = draft_data.get("task")
                matrix_type = draft_data.get("matrixType", "profit")
                name_alternatives = draft_data.get("alternatives", [])
                name_conditions = draft_data.get("conditions", [])

                # Проверяем, что имена не None и не содержат None значений
                if name_alternatives is None:
                    print(f"Warning: name_alternatives is None in draft {draft_id}")
                    name_alternatives = [f"Alternative {i+1}" for i in range(num_alt)]
                else:
                    name_alternatives = [
                        name if name and name != "None" else ""
                        for name in name_alternatives
                    ]
                    if all(not name for name in name_alternatives):
                        name_alternatives = [
                            f"Alternative {i+1}" for i in range(num_alt)
                        ]

                if name_conditions is None:
                    print(f"Warning: name_conditions is None in draft {draft_id}")
                    name_conditions = [
                        f"Condition {i+1}" for i in range(num_conditions)
                    ]
                else:
                    name_conditions = [
                        name if name and name != "None" else ""
                        for name in name_conditions
                    ]
                    if all(not name for name in name_conditions):
                        name_conditions = [
                            f"Condition {i+1}" for i in range(num_conditions)
                        ]

                # Обновляем сессию
                session["num_alt"] = num_alt
                session["num_conditions"] = num_conditions
                session["laplasa_task"] = laplasa_task
                session["matrix_type"] = matrix_type

                # Создаем новый ID записи для черновика
                new_record_id = add_object_to_db(
                    db, LaplasaConditions, names=name_conditions
                )
                add_object_to_db(
                    db, LaplasaAlternatives, id=new_record_id, names=name_alternatives
                )
                if laplasa_task or matrix_type:
                    add_object_to_db(
                        db,
                        LaplasaTask,
                        id=new_record_id,
                        task=laplasa_task,
                        matrix_type=matrix_type or "profit",
                    )

                session["new_record_id"] = new_record_id

                # Восстанавливаем матрицу из черновика
                cost_matrix = None
                if draft_data.get("matrices", {}).get("cost"):
                    cost_matrix = draft_data["matrices"]["cost"]
                    # Сохраняем матрицу в сессии для восстановления в шаблоне
                    session["cost_matrix"] = cost_matrix
                    # Устанавливаем флаг, что загружается черновик
                    session["draft_loaded"] = True
                    print(f"Restored cost matrix from draft: {cost_matrix}")
                else:
                    print("No cost matrix found in draft")

                context = {
                    "title": "Матриця Вартостей",
                    "num_alt": num_alt,
                    "num_conditions": num_conditions,
                    "name_alternatives": name_alternatives,
                    "name_conditions": name_conditions,
                    "name": (
                        current_user.get_name()
                        if current_user.is_authenticated
                        else None
                    ),
                    "id": new_record_id,
                    "cost_matrix": cost_matrix,  # Передаем матрицу в контекст
                    "matrix_type": matrix_type,
                }
                print(f"Context cost_matrix: {context['cost_matrix']}")
                return render_template("Laplasa/cost_matrix.html", **context)

        except Exception as e:
            print(f"Error loading draft: {str(e)}")

    # Обычная обработка
    num_alt = int(session.get("num_alt"))
    num_conditions = int(session.get("num_conditions"))
    laplasa_task = session.get("laplasa_task")
    matrix_type = session.get("matrix_type", "profit")

    name_alternatives = request.form.getlist("name_alternatives")
    name_conditions = request.form.getlist("name_conditions")

    if len(name_alternatives) != len(set(name_alternatives)) or len(
        name_conditions
    ) != len(set(name_conditions)):
        context = {
            "title": "Імена",
            "num_alt": num_alt,
            "num_conditions": num_conditions,
            "name_alternatives": name_alternatives,
            "name_conditions": name_conditions,
            "error": "Імена повинні бути унікальними!",
            "name": current_user.get_name() if current_user.is_authenticated else None,
        }

        return render_template("Laplasa/names.html", **context)

    # Збереження даних у БД
    new_record_id = add_object_to_db(db, LaplasaConditions, names=name_conditions)

    add_object_to_db(db, LaplasaAlternatives, id=new_record_id, names=name_alternatives)

    if laplasa_task or matrix_type:
        add_object_to_db(
            db,
            LaplasaTask,
            id=new_record_id,
            task=laplasa_task,
            matrix_type=matrix_type or "profit",
        )

    # Збереження даних у сесії
    session["new_record_id"] = new_record_id
    session["flag"] = 0

    # Сохраняем матрицу в сессии для восстановления в шаблоне
    # Получаем матрицу из формы
    cost_matrix_raw = request.form.getlist("cost_matrix")
    if cost_matrix_raw:
        cost_matrix = make_table(num_alt, num_conditions, cost_matrix_raw)
        session["cost_matrix"] = cost_matrix
    else:
        cost_matrix = None

    context = {
        "title": "Матриця Вартостей",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "name_alternatives": name_alternatives,
        "name_conditions": name_conditions,
        "name": current_user.get_name() if current_user.is_authenticated else None,
        "id": new_record_id,
        "cost_matrix": cost_matrix,  # Передаем матрицу в контекст
        "laplasa_task": laplasa_task,  # Передаем задачу в контекст
        "matrix_type": matrix_type,
    }

    return render_template("Laplasa/cost_matrix.html", **context)


@kriteriy_laplasa_bp.route("/result/<int:method_id>", methods=["GET", "POST"])
def result(method_id=None):
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
                num_alt = int(draft_data.get("numAlternatives") or 0)
                num_conditions = int(draft_data.get("numConditions") or 0)
                laplasa_task = draft_data.get("task")
                name_alternatives = draft_data.get("alternatives", [])
                name_conditions = draft_data.get("conditions", [])

                # Проверяем, что имена не None и не содержат None значений
                if name_alternatives is None:
                    print(f"Warning: name_alternatives is None in draft {draft_id}")
                    name_alternatives = [f"Alternative {i+1}" for i in range(num_alt)]
                else:
                    name_alternatives = [
                        name if name and name != "None" else ""
                        for name in name_alternatives
                    ]
                    if all(not name for name in name_alternatives):
                        name_alternatives = [
                            f"Alternative {i+1}" for i in range(num_alt)
                        ]

                if name_conditions is None:
                    print(f"Warning: name_conditions is None in draft {draft_id}")
                    name_conditions = [
                        f"Condition {i+1}" for i in range(num_conditions)
                    ]
                else:
                    name_conditions = [
                        name if name and name != "None" else ""
                        for name in name_conditions
                    ]
                    if all(not name for name in name_conditions):
                        name_conditions = [
                            f"Condition {i+1}" for i in range(num_conditions)
                        ]

                # Создаем новый ID записи для черновика
                new_record_id = add_object_to_db(
                    db, LaplasaConditions, names=name_conditions
                )
                add_object_to_db(
                    db, LaplasaAlternatives, id=new_record_id, names=name_alternatives
                )
                if laplasa_task or matrix_type:
                    add_object_to_db(
                        db,
                        LaplasaTask,
                        id=new_record_id,
                        task=laplasa_task,
                        matrix_type=matrix_type or "profit",
                    )

                session["new_record_id"] = new_record_id

                # Восстанавливаем матрицу из черновика
                if draft_data.get("matrices", {}).get("cost"):
                    cost_matrix = draft_data["matrices"]["cost"]
                else:
                    # Создаем пустую матрицу
                    cost_matrix = [["0"] * num_conditions for _ in range(num_alt)]

                # Вычисляем оптимальные варианты
                optimal_variants = [
                    round(sum(map(float, sublist)) / len(sublist), 2)
                    for sublist in cost_matrix
                ]

                if matrix_type == "profit":
                    max_value = max(optimal_variants)
                    max_index = optimal_variants.index(max_value)
                    optimal_alternative = name_alternatives[max_index]
                    optimal_message = f"Оптимальна альтернатива {optimal_alternative}, має максимальне значення очікуваної вигоди ('{max_value}')."
                else:
                    min_value = min(optimal_variants)
                    min_index = optimal_variants.index(min_value)
                    optimal_alternative = name_alternatives[min_index]
                    optimal_message = f"Оптимальна альтернатива {optimal_alternative}, має мінімальне значення очікуваних затрат ('{min_value}')."

                context = {
                    "title": "Результат",
                    "name": (
                        current_user.get_name()
                        if current_user.is_authenticated
                        else None
                    ),
                    "name_alternatives": name_alternatives,
                    "name_conditions": name_conditions,
                    "cost_matrix": cost_matrix,
                    "optimal_variants": optimal_variants,
                    "id": new_record_id,
                    "laplasa_task": laplasa_task,
                    "matrix_type": matrix_type,
                    "optimal_message": optimal_message,
                    "laplasa_plot": generate_plot(
                        optimal_variants,
                        name_alternatives,
                        False,
                        savage=False if matrix_type == "profit" else True,
                    ),
                }

                session["flag"] = 1
                return render_template("Laplasa/result.html", **context)

        except Exception as e:
            print(f"Error loading draft: {str(e)}")

    # Обычная обработка
    if not method_id:
        new_record_id = int(session.get("new_record_id"))
        num_alt = int(session.get("num_alt"))
        num_conditions = int(session.get("num_conditions"))
    else:
        new_record_id = method_id
        # Check if user owns this result (admin has access to all results)
        if current_user.is_authenticated:
            if current_user.get_name() != "admin":
                result = Result.query.filter_by(
                    method_id=new_record_id,
                    method_name="Laplasa",
                    user_id=current_user.get_id(),
                ).first()
                if not result:
                    flash("You don't have permission to access this result", "error")
                    return redirect(url_for("kriteriy_laplasa.index"))
        else:
            flash("Please log in to access this result", "error")
            return redirect(url_for("kriteriy_laplasa.index"))

        num_alt = len(LaplasaAlternatives.query.get(new_record_id).names)
        num_conditions = len(LaplasaConditions.query.get(new_record_id).names)

    name_alternatives = LaplasaAlternatives.query.get(new_record_id).names
    name_conditions = LaplasaConditions.query.get(new_record_id).names

    laplasa_task = session.get("laplasa_task")
    matrix_type = "profit"

    try:
        laplasa_task_record = LaplasaTask.query.get(new_record_id)
        if laplasa_task_record:
            laplasa_task = laplasa_task_record.task
            matrix_type = laplasa_task_record.matrix_type or "profit"
    except Exception as e:
        print("[!] Error:", e)

    flag = session.get("flag")

    # Если загружается черновик, используем матрицу из черновика
    if draft_id and draft_data and draft_data.get("matrices", {}).get("cost"):
        cost_matrix = draft_data["matrices"]["cost"]
        print(f"Using matrix from draft: {cost_matrix}")
        # Устанавливаем флаг, чтобы матрица не перезаписывалась из формы
        session["draft_loaded"] = True
    elif flag != 0 and not session.get("draft_loaded"):
        # Иначе берем из базы данных, но только если не загружался черновик
        cost_matrix_record = LaplasaCostMatrix.query.get(new_record_id)
        if cost_matrix_record:
            cost_matrix = cost_matrix_record.matrix
            print(f"Using matrix from database: {cost_matrix}")
        else:
            print(f"Warning: No cost matrix record found for ID {new_record_id}")
            # Создаем пустую матрицу как fallback
            cost_matrix = [["0"] * num_conditions for _ in range(num_alt)]
    else:
        # Иначе берем из формы, но только если не загружался черновик
        if not session.get("draft_loaded"):
            cost_matrix_raw = request.form.getlist("cost_matrix")
            cost_matrix = make_table(num_alt, num_conditions, cost_matrix_raw)
            print(f"Using matrix from form: {cost_matrix}")
        else:
            # Если загружался черновик, берем матрицу из сессии
            cost_matrix = session.get("cost_matrix")
            print(f"Using matrix from session (draft): {cost_matrix}")
            # Сбрасываем флаг
            session.pop("draft_loaded", None)

    optimal_variants = [
        round(sum(map(float, sublist)) / len(sublist), 2) for sublist in cost_matrix
    ]

    # Знаходимо оптимальне значення в залежності від типу матриці
    if matrix_type == "profit":
        max_value = max(optimal_variants)
        max_index = optimal_variants.index(max_value)
        optimal_alternative = name_alternatives[max_index]
        optimal_message = f"Оптимальна альтернатива {optimal_alternative}, має максимальне значення очікуваної вигоди ('{max_value}')."
    else:
        min_value = min(optimal_variants)
        min_index = optimal_variants.index(min_value)
        optimal_alternative = name_alternatives[min_index]
        optimal_message = f"Оптимальна альтернатива {optimal_alternative}, має мінімальне значення очікуваних затрат ('{min_value}')."

    existing_record = LaplasaCostMatrix.query.get(new_record_id)
    if existing_record is None and not session.get("draft_loaded"):
        # Создаем запись матрицы только если её нет и не загружается черновик
        add_object_to_db(
            db,
            LaplasaCostMatrix,
            id=new_record_id,
            laplasa_alternatives_id=new_record_id,
            matrix=cost_matrix,
            optimal_variants=optimal_variants,
        )

        if current_user.is_authenticated:
            add_object_to_db(
                db,
                Result,
                method_name="Laplasa",
                method_id=new_record_id,
                user_id=current_user.get_id(),
            )
    context = {
        "title": "Результат",
        "name": current_user.get_name() if current_user.is_authenticated else None,
        "name_alternatives": name_alternatives,
        "name_conditions": name_conditions,
        "cost_matrix": cost_matrix,
        "optimal_variants": optimal_variants,
        "id": new_record_id,
        "method_id": new_record_id,
        "laplasa_task": laplasa_task,
        "matrix_type": matrix_type,
        "optimal_message": optimal_message,
        "laplasa_plot": generate_plot(
            optimal_variants,
            name_alternatives,
            False,
            savage=False if matrix_type == "profit" else True,
        ),
    }

    session["flag"] = 1

    return render_template("Laplasa/result.html", **context)


@kriteriy_laplasa_bp.route("/export/excel/<int:method_id>")
def export_excel(method_id):
    """Export Laplasa analysis to Excel"""
    # Check if user owns this result (admin has access to all results)
    if current_user.is_authenticated:
        if current_user.get_name() != "admin":
            result = Result.query.filter_by(
                method_id=method_id,
                method_name="Laplasa",
                user_id=current_user.get_id(),
            ).first()
            if not result:
                return Response(
                    "You don't have permission to export this result",
                    status=403,
                    mimetype="text/plain",
                )
    else:
        return Response(
            "Please log in to export this result", status=403, mimetype="text/plain"
        )

    try:
        # Fetch data from database
        laplasa_conditions = LaplasaConditions.query.get(method_id)
        laplasa_alternatives = LaplasaAlternatives.query.get(method_id)
        laplasa_cost_matrix = LaplasaCostMatrix.query.get(method_id)
        laplasa_task = LaplasaTask.query.get(method_id)

        if not all([laplasa_conditions, laplasa_alternatives, laplasa_cost_matrix]):
            return Response("Data not found", status=404)

        # Get task description and matrix type
        task_description = "Laplasa Analysis"
        matrix_type = "profit"
        if laplasa_task:
            if laplasa_task.task:
                task_description = laplasa_task.task
            matrix_type = laplasa_task.matrix_type or "profit"

        # Calculate optimal message exactly like on website
        optimal_variants = laplasa_cost_matrix.optimal_variants or []
        name_alternatives = laplasa_alternatives.names or []

        if optimal_variants and name_alternatives:
            if matrix_type == "profit":
                max_value = max(optimal_variants)
                max_index = optimal_variants.index(max_value)
                optimal_alternative = name_alternatives[max_index]
                optimal_message = f"Оптимальна альтернатива {optimal_alternative}, має максимальне значення очікуваної вигоди ('{max_value}')."
            else:
                min_value = min(optimal_variants)
                min_index = optimal_variants.index(min_value)
                optimal_alternative = name_alternatives[min_index]
                optimal_message = f"Оптимальна альтернатива {optimal_alternative}, має мінімальне значення очікуваних затрат ('{min_value}')."
        else:
            optimal_message = "Немає даних для аналізу"

        # Prepare analysis data
        analysis_data = {
            "method_id": method_id,
            "laplasa_task": task_description,
            "matrix_type": matrix_type,
            "name_alternatives": name_alternatives,
            "name_conditions": laplasa_conditions.names or [],
            "cost_matrix": laplasa_cost_matrix.matrix or [],
            "optimal_variants": optimal_variants,
            "optimal_message": optimal_message,
        }

        # Generate Excel file
        exporter = LaplasaExcelExporter()
        workbook = exporter.generate_laplasa_analysis_excel(analysis_data)
        excel_bytes = exporter.save_to_bytes()

        # Return Excel file
        return Response(
            excel_bytes,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=Laplasa_Analysis_Task{method_id}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            },
        )

    except Exception as e:
        print(f"Excel export error: {e}")
        return Response(f"Export failed: {str(e)}", status=500)


@kriteriy_laplasa_bp.route("/upload_matrix", methods=["POST"])
@login_required
def upload_matrix():
    """Handle file upload for Laplasa method"""
    try:
        # Get form data
        num_alt = int(request.form.get("num_alt", 0))
        num_conditions = int(request.form.get("num_conditions", 0))

        if num_alt <= 0 or num_conditions <= 0:
            return {
                "success": False,
                "error": "Невірна кількість альтернатив або умов",
            }

        # Get uploaded file
        if "matrix_file" not in request.files:
            return {"success": False, "error": "Файл не завантажено"}

        file = request.files["matrix_file"]
        if file.filename == "":
            return {"success": False, "error": "Файл не вибрано"}

        # Process file
        result = process_laplasa_file(file, num_alt, num_conditions)

        if result["success"]:
            return {
                "success": True,
                "alternatives_names": result["alternatives_names"],
                "conditions_names": result["conditions_names"],
                "cost_matrix": result["cost_matrix"],
            }
        else:
            return {"success": False, "error": result["error"]}

    except Exception as e:
        print(f"Upload error: {e}")
        return {"success": False, "error": f"Upload failed: {str(e)}"}


@kriteriy_laplasa_bp.route("/result_from_file", methods=["POST"])
@login_required
def result_from_file():
    """Process uploaded file data for Laplasa method"""
    try:
        print(f"Laplasa result_from_file called with form data: {request.form}")

        # Get data from form
        file_data = {
            "alternatives_names": request.form.get("uploaded_alternatives_names"),
            "conditions_names": request.form.get("uploaded_conditions_names"),
            "cost_matrix": request.form.get("uploaded_cost_matrix"),
        }

        print(f"Extracted file_data: {file_data}")

        # Get other form data
        laplasa_task = request.form.get("laplasa_task", "")
        matrix_type = request.form.get("matrix_type", "profit")
        num_alt = int(request.form.get("num_alt", 0))
        num_conditions = int(request.form.get("num_conditions", 0))

        print(f"Laplasa task: {laplasa_task}")
        print(f"Number of alternatives: {num_alt}")
        print(f"Number of conditions: {num_conditions}")

        # Parse the data
        import json

        try:
            alternatives_names = json.loads(file_data["alternatives_names"])
            conditions_names = json.loads(file_data["conditions_names"])
            cost_matrix = json.loads(file_data["cost_matrix"])
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            flash("Error parsing uploaded data", "error")
            return redirect(url_for("kriteriy_laplasa.index"))

        print(f"Parsed alternatives_names: {alternatives_names}")
        print(f"Parsed conditions_names: {conditions_names}")
        print(f"Parsed cost_matrix: {cost_matrix}")

        # Create records in database to get method_id
        print("Creating database records...")
        new_record_id = add_object_to_db(db, LaplasaConditions, names=conditions_names)
        print(f"Created LaplasaConditions with ID: {new_record_id}")

        add_object_to_db(
            db, LaplasaAlternatives, id=new_record_id, names=alternatives_names
        )
        print(f"Created LaplasaAlternatives with ID: {new_record_id}")

        # Calculate optimal variants
        optimal_variants = [
            round(sum(map(float, sublist)) / len(sublist), 2) for sublist in cost_matrix
        ]

        print(f"Calculated optimal_variants: {optimal_variants}")
        print(f"Matrix type: {matrix_type}")

        add_object_to_db(
            db,
            LaplasaCostMatrix,
            id=new_record_id,
            laplasa_alternatives_id=new_record_id,
            matrix=cost_matrix,
            optimal_variants=optimal_variants,
        )
        print(f"Created LaplasaCostMatrix with ID: {new_record_id}")

        # Create laplasa task if provided
        if laplasa_task or matrix_type:
            add_object_to_db(
                db,
                LaplasaTask,
                id=new_record_id,
                task=laplasa_task,
                matrix_type=matrix_type or "profit",
            )
            print(
                f"Created LaplasaTask with ID: {new_record_id}, matrix_type: {matrix_type}"
            )

        # Create result record for history if user is authenticated
        if current_user.is_authenticated:
            add_object_to_db(
                db,
                Result,
                method_name="Laplasa",
                method_id=new_record_id,
                user_id=current_user.get_id(),
            )
            print(f"Created Result record for history with ID: {new_record_id}")

        # Redirect to result page
        print(f"Redirecting to result page with method_id: {new_record_id}")
        return redirect(url_for("kriteriy_laplasa.result", method_id=new_record_id))

    except Exception as e:
        print(f"Exception in laplasa result_from_file: {str(e)}")
        import traceback

        traceback.print_exc()
        flash(f"Error processing file data: {str(e)}", "error")
        return redirect(url_for("kriteriy_laplasa.index"))
