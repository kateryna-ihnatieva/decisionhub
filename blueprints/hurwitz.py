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

# from mymodules.mai import *  # Unused import removed
from models import (
    HurwitzConditions,
    HurwitzAlternatives,
    HurwitzCostMatrix,
    HurwitzTask,
    db,
    Result,
)
from flask_login import current_user, login_required
from mymodules.methods import add_object_to_db, generate_plot
from mymodules.experts_func import make_table
from mymodules.hurwitz_excel_export import HurwitzExcelExporter
from mymodules.file_upload import process_hurwitz_file
from datetime import datetime

hurwitz_bp = Blueprint("hurwitz", __name__, url_prefix="/hurwitz")


@hurwitz_bp.route("/")
def index():
    context = {
        "title": "Критерій Гурвіца",
        "name": (current_user.get_name() if current_user.is_authenticated else None),
    }
    return render_template("Hurwitz/index.html", **context)


@hurwitz_bp.route("/names", methods=["GET", "POST"])
def names():
    # Проверяем, загружается ли черновик
    draft_id = request.args.get("draft")
    draft_data = None
    num_alt = 0
    num_conditions = 0
    hurwitz_task = None
    alpha = 0.5

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
                hurwitz_task = draft_data.get("task")
                alpha = float(draft_data.get("alpha") or 0.5)
                matrix_type = draft_data.get("matrixType")
            else:
                # Если черновик не найден, используем значения по умолчанию
                num_alt = 0
                num_conditions = 0
                hurwitz_task = None
                alpha = 0.5
                matrix_type = None
        except Exception as e:
            print(f"Error loading draft: {str(e)}")
            # В случае ошибки используем значения по умолчанию
            num_alt = 0
            num_conditions = 0
            hurwitz_task = None
            alpha = 0.5
            matrix_type = None
    else:
        # Если черновик не загружается, получаем данные из URL параметров
        try:
            num_alt = int(request.args.get("num_alt") or 0)
            num_conditions = int(request.args.get("num_conditions") or 0)
            hurwitz_task = request.args.get("hurwitz_task")
            alpha = float(request.args.get("alpha") or 0.5)
            matrix_type = request.args.get("matrix_type")
        except (ValueError, TypeError):
            num_alt = 0
            num_conditions = 0
            hurwitz_task = None
            alpha = 0.5
            matrix_type = None

    # Збереження змінниї у сесії
    session["num_alt"] = num_alt
    session["num_conditions"] = num_conditions
    session["hurwitz_task"] = hurwitz_task
    session["alpha"] = alpha
    session["matrix_type"] = matrix_type

    context = {
        "title": "Імена",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "hurwitz_task": hurwitz_task,
        "alpha": alpha,
        "matrix_type": matrix_type,
        "name_alternatives": (draft_data.get("alternatives") if draft_data else None),
        "name_conditions": (draft_data.get("conditions") if draft_data else None),
        "name": (current_user.get_name() if current_user.is_authenticated else None),
    }

    return render_template("Hurwitz/names.html", **context)


@hurwitz_bp.route("/cost-matrix", methods=["GET", "POST"])
def cost_matrix():
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
        except Exception:
            pass  # Игнорируем ошибки загрузки черновика

    if draft_data:
        # Загружаем данные из черновика
        num_alt = int(draft_data.get("numAlternatives") or 0)
        num_conditions = int(draft_data.get("numConditions") or 0)
        hurwitz_task = draft_data.get("task")
        alpha = float(draft_data.get("alpha") or 0.5)
        matrix_type = draft_data.get("matrixType", "profit")
        name_alternatives = draft_data.get("alternatives", [])
        name_conditions = draft_data.get("conditions", [])
    else:
        # Загружаем данные из сессии и формы
        num_alt = int(session.get("num_alt"))
        num_conditions = int(session.get("num_conditions"))
        # Получаем hurwitz_task и matrix_type из формы или сессии
        hurwitz_task = request.form.get("hurwitz_task") or session.get("hurwitz_task")
        alpha = float(request.form.get("alpha") or session.get("alpha") or 0.5)
        matrix_type = session.get("matrix_type", "profit")
        name_alternatives = request.form.getlist("name_alternatives")
        name_conditions = request.form.getlist("name_conditions")

        # Обновляем сессию с актуальными значениями
        if hurwitz_task:
            session["hurwitz_task"] = hurwitz_task
        session["alpha"] = alpha
        if matrix_type:
            session["matrix_type"] = matrix_type

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
            "name": (
                current_user.get_name() if current_user.is_authenticated else None
            ),
        }

        return render_template("Hurwitz/names.html", **context)

    # Збереження даних у БД
    new_record_id = add_object_to_db(db, HurwitzConditions, names=name_conditions)

    add_object_to_db(db, HurwitzAlternatives, id=new_record_id, names=name_alternatives)

    if hurwitz_task or matrix_type:
        add_object_to_db(
            db,
            HurwitzTask,
            id=new_record_id,
            task=hurwitz_task,
            matrix_type=matrix_type or "profit",
        )

    session["new_record_id"] = new_record_id
    session["flag"] = 0

    context = {
        "title": "Матриця Вартостей",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "name_alternatives": name_alternatives,
        "name_conditions": name_conditions,
        "hurwitz_task": hurwitz_task,
        "alpha": alpha,
        "matrix_type": matrix_type,
        "name": (current_user.get_name() if current_user.is_authenticated else None),
        "id": new_record_id,
    }

    return render_template("Hurwitz/cost_matrix.html", **context)


@hurwitz_bp.route("/result/<int:method_id>", methods=["GET", "POST"])
def result(method_id=None):
    # Проверяем, загружается ли черновик
    draft_id = request.args.get("draft")
    if draft_id:
        try:
            from models import Draft

            draft = Draft.query.filter_by(
                id=draft_id, user_id=current_user.get_id()
            ).first()
            if draft and draft.form_data:
                pass  # Черновик загружен, но не используется напрямую в этой функции
        except Exception:
            pass  # Игнорируем ошибки загрузки черновика

    if not method_id:
        new_record_id = int(session.get("new_record_id"))
        num_alt = int(session.get("num_alt"))
        num_conditions = int(session.get("num_conditions"))
    else:
        new_record_id = method_id
        # Проверка принадлежности результата пользователю
        if not current_user.is_authenticated:
            flash("Для доступу до результату потрібна авторизація", "error")
            return redirect(url_for("hurwitz.index"))
        result_record = Result.query.filter_by(
            method_name="Hurwitz",
            method_id=new_record_id,
            user_id=current_user.get_id(),
        ).first()
        if not result_record:
            flash("У вас немає доступу до цього результату", "error")
            return redirect(url_for("hurwitz.index"))
        num_alt = len(HurwitzAlternatives.query.get(new_record_id).names)
        num_conditions = len(HurwitzConditions.query.get(new_record_id).names)

    name_alternatives = HurwitzAlternatives.query.get(new_record_id).names
    name_conditions = HurwitzConditions.query.get(new_record_id).names

    # Спочатку пробуємо дістати з сесії
    alpha = session.get("alpha")

    # Якщо в сесії немає — беремо з БД
    if alpha is None:
        existing_record = HurwitzCostMatrix.query.get(new_record_id)
        if existing_record:
            alpha = existing_record.alpha
        else:
            return "Помилка: alpha не знайдено ні в сесії, ні в базі.", 400
    else:
        alpha = float(alpha)

    # Аналогічно з hurwitz_task та matrix_type
    hurwitz_task_record = HurwitzTask.query.get(new_record_id)
    hurwitz_task = (
        hurwitz_task_record.task if hurwitz_task_record else session.get("hurwitz_task")
    )
    matrix_type = "profit"
    if hurwitz_task_record:
        matrix_type = hurwitz_task_record.matrix_type or "profit"

    flag = session.get("flag")
    if flag != 0:
        cost_matrix = HurwitzCostMatrix.query.get(new_record_id).matrix
        alpha = HurwitzCostMatrix.query.get(new_record_id).alpha
    else:
        cost_matrix_raw = request.form.getlist("cost_matrix")
        cost_matrix = make_table(num_alt, num_conditions, cost_matrix_raw)

    max_values = []
    min_values = []
    hurwitz_values = []
    for row in cost_matrix:
        row_int = list(map(float, row))  # Перетворюємо в float
        min_val = min(row_int)
        max_val = max(row_int)
        if matrix_type == "profit":
            # Для прибыли: H = α * max + (1 - α) * min (максимизируем)
            H = alpha * max_val + (1 - alpha) * min_val
        else:
            # Для затрат: H = α * min + (1 - α) * max (минимизируем)
            H = alpha * min_val + (1 - alpha) * max_val
        hurwitz_values.append(H)
        max_values.append(max_val)
        min_values.append(min_val)

    if matrix_type == "profit":
        max_value = max(hurwitz_values)
        max_index = hurwitz_values.index(max_value)
        optimal_alternative = name_alternatives[max_index]
        optimal_message = (
            f"Оптимальна альтернатива {optimal_alternative}, "
            f"має максимальне значення критерію Гурвіца: "
            f"{max_value:.2f}."
        )
    else:
        min_value = min(hurwitz_values)
        min_index = hurwitz_values.index(min_value)
        optimal_alternative = name_alternatives[min_index]
        optimal_message = (
            f"Оптимальна альтернатива {optimal_alternative}, "
            f"має мінімальне значення критерію Гурвіца: "
            f"{min_value:.2f}."
        )

    existing_record = HurwitzCostMatrix.query.get(new_record_id)
    if existing_record is None:
        add_object_to_db(
            db,
            HurwitzCostMatrix,
            id=new_record_id,
            hurwitz_alternatives_id=new_record_id,
            matrix=cost_matrix,
            optimal_variants=hurwitz_values,
            alpha=alpha,
        )
        if current_user.is_authenticated:
            add_object_to_db(
                db,
                Result,
                method_name="Hurwitz",
                method_id=new_record_id,
                user_id=current_user.get_id(),
            )

    context = {
        "title": "Результат",
        "name": (current_user.get_name() if current_user.is_authenticated else None),
        "name_alternatives": name_alternatives,
        "name_conditions": name_conditions,
        "cost_matrix": cost_matrix,
        "min_values": min_values,
        "max_values": max_values,
        "hurwitz_values": hurwitz_values,
        "alpha": alpha,
        "id": new_record_id,
        "hurwitz_task": hurwitz_task,
        "matrix_type": matrix_type,
        "optimal_message": optimal_message,
        "hurwitz_plot": generate_plot(
            hurwitz_values,
            name_alternatives,
            False,
            savage=False if matrix_type == "profit" else True,
        ),
    }

    session["flag"] = 1

    return render_template("Hurwitz/result.html", **context)


@hurwitz_bp.route("/export/excel/<int:method_id>")
def export_excel(method_id):
    """Export hurwitz analysis to Excel"""
    # Check if user owns this result
    if current_user.is_authenticated:
        result = Result.query.filter_by(
            method_id=method_id, method_name="Hurwitz", user_id=current_user.get_id()
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
        # Get data from database
        hurwitz_conditions = HurwitzConditions.query.get(method_id)
        hurwitz_alternatives = HurwitzAlternatives.query.get(method_id)
        hurwitz_cost_matrix = HurwitzCostMatrix.query.get(method_id)
        hurwitz_task = HurwitzTask.query.get(method_id)

        if not all([hurwitz_conditions, hurwitz_alternatives, hurwitz_cost_matrix]):
            return Response("Data not found", status=404)

        # Get task description and matrix type
        task_description = "Hurwitz Analysis"
        matrix_type = "profit"
        if hurwitz_task:
            if hurwitz_task.task:
                task_description = hurwitz_task.task
            matrix_type = hurwitz_task.matrix_type or "profit"

        # Calculate values exactly like in result function
        cost_matrix = hurwitz_cost_matrix.matrix or []
        alpha = hurwitz_cost_matrix.alpha or 0.5
        name_alternatives = hurwitz_alternatives.names or []

        # Calculate min_values, max_values, and hurwitz_values from cost_matrix
        min_values = []
        max_values = []
        hurwitz_values = []

        if cost_matrix and name_alternatives:
            for row in cost_matrix:
                row_int = list(map(float, row))  # Convert to float
                min_val = min(row_int)
                max_val = max(row_int)
                if matrix_type == "profit":
                    # Для прибыли: H = α * max + (1 - α) * min (максимизируем)
                    H = alpha * max_val + (1 - alpha) * min_val
                else:
                    # Для затрат: H = α * min + (1 - α) * max (минимизируем)
                    H = alpha * min_val + (1 - alpha) * max_val
                hurwitz_values.append(H)
                max_values.append(max_val)
                min_values.append(min_val)

            if hurwitz_values and name_alternatives:
                if matrix_type == "profit":
                    max_hurwitz = max(hurwitz_values)
                    max_index = hurwitz_values.index(max_hurwitz)
                    optimal_alternative = name_alternatives[max_index]
                    optimal_message = f"Оптимальна альтернатива {optimal_alternative}, має максимальне значення критерію Гурвіца: {max_hurwitz:.2f}."
                else:
                    min_hurwitz = min(hurwitz_values)
                    min_index = hurwitz_values.index(min_hurwitz)
                    optimal_alternative = name_alternatives[min_index]
                    optimal_message = f"Оптимальна альтернатива {optimal_alternative}, має мінімальне значення критерію Гурвіца: {min_hurwitz:.2f}."
            else:
                optimal_message = "Немає даних для аналізу"
        else:
            optimal_message = "Немає даних для аналізу"

        # Prepare analysis data
        analysis_data = {
            "method_id": method_id,
            "hurwitz_task": task_description,
            "matrix_type": matrix_type,
            "name_alternatives": name_alternatives,
            "name_conditions": hurwitz_conditions.names or [],
            "cost_matrix": cost_matrix,
            "min_values": min_values,
            "max_values": max_values,
            "hurwitz_values": hurwitz_values,
            "alpha": alpha,
            "optimal_message": optimal_message,
        }

        # Generate Excel file
        exporter = HurwitzExcelExporter()
        workbook = exporter.generate_hurwitz_analysis_excel(analysis_data)
        excel_bytes = exporter.save_to_bytes()

        # Return Excel file
        return Response(
            excel_bytes,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=Hurwitz_Analysis_Task{method_id}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            },
        )

    except Exception as e:
        print(f"Excel export error: {e}")
        return Response("Export failed", status=500)


@hurwitz_bp.route("/upload_matrix", methods=["POST"])
@login_required
def upload_matrix():
    """Handle file upload for Hurwitz method"""
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
        result = process_hurwitz_file(file, num_alt, num_conditions)

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


@hurwitz_bp.route("/result_from_file", methods=["POST"])
@login_required
def result_from_file():
    """Process uploaded file data for Hurwitz method"""
    try:
        print(f"Hurwitz result_from_file called with form data: {request.form}")

        # Get data from form
        file_data = {
            "alternatives_names": request.form.get("uploaded_alternatives_names"),
            "conditions_names": request.form.get("uploaded_conditions_names"),
            "cost_matrix": request.form.get("uploaded_cost_matrix"),
        }

        print(f"Extracted file_data: {file_data}")

        # Get other form data
        hurwitz_task = request.form.get("hurwitz_task", "")
        matrix_type = request.form.get("matrix_type", "profit")
        alpha = float(request.form.get("alpha", 0.5))
        num_alt = int(request.form.get("num_alt", 0))
        num_conditions = int(request.form.get("num_conditions", 0))

        print(f"Hurwitz task: '{hurwitz_task}'")
        print(f"Alpha: {alpha}")
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
            return redirect(url_for("hurwitz.index"))

        print(f"Parsed alternatives_names: {alternatives_names}")
        print(f"Parsed conditions_names: {conditions_names}")
        print(f"Parsed cost_matrix: {cost_matrix}")

        # Create records in database to get method_id
        print("Creating database records...")
        new_record_id = add_object_to_db(db, HurwitzConditions, names=conditions_names)
        print(f"Created HurwitzConditions with ID: {new_record_id}")

        add_object_to_db(
            db, HurwitzAlternatives, id=new_record_id, names=alternatives_names
        )
        print(f"Created HurwitzAlternatives with ID: {new_record_id}")

        # Calculate Hurwitz values
        max_values = []
        min_values = []
        hurwitz_values = []
        for row in cost_matrix:
            row_int = list(map(float, row))  # Convert to float
            min_val = min(row_int)
            max_val = max(row_int)
            if matrix_type == "profit":
                # Для прибыли: H = α * max + (1 - α) * min (максимизируем)
                H = alpha * max_val + (1 - alpha) * min_val
            else:
                # Для затрат: H = α * min + (1 - α) * max (минимизируем)
                H = alpha * min_val + (1 - alpha) * max_val
            hurwitz_values.append(H)
            max_values.append(max_val)
            min_values.append(min_val)

        if matrix_type == "profit":
            max_value = max(hurwitz_values)
            max_index = hurwitz_values.index(max_value)
            optimal_alternative = alternatives_names[max_index]
        else:
            min_value = min(hurwitz_values)
            min_index = hurwitz_values.index(min_value)
            optimal_alternative = alternatives_names[min_index]

        print(f"Calculated hurwitz_values: {hurwitz_values}")
        print(f"Optimal alternative: {optimal_alternative}")
        print(f"Matrix type: {matrix_type}")

        add_object_to_db(
            db,
            HurwitzCostMatrix,
            id=new_record_id,
            hurwitz_alternatives_id=new_record_id,
            matrix=cost_matrix,
            optimal_variants=hurwitz_values,
            alpha=alpha,
        )
        print(f"Created HurwitzCostMatrix with ID: {new_record_id}")

        # Create hurwitz task if provided
        if hurwitz_task or matrix_type:
            add_object_to_db(
                db,
                HurwitzTask,
                id=new_record_id,
                task=hurwitz_task,
                matrix_type=matrix_type or "profit",
            )
            print(
                f"Created HurwitzTask with ID: {new_record_id}, task: '{hurwitz_task}', matrix_type: {matrix_type}"
            )

        # Create result record for history if user is authenticated
        if current_user.is_authenticated:
            add_object_to_db(
                db,
                Result,
                method_name="Hurwitz",
                method_id=new_record_id,
                user_id=current_user.get_id(),
            )
            print(f"Created Result record for history with ID: {new_record_id}")

        # Redirect to result page
        print(f"Redirecting to result page with method_id: {new_record_id}")
        return redirect(url_for("hurwitz.result", method_id=new_record_id))

    except Exception as e:
        print(f"Exception in hurwitz result_from_file: {str(e)}")
        import traceback

        traceback.print_exc()
        flash(f"Error processing file data: {str(e)}", "error")
        return redirect(url_for("hurwitz.index"))
