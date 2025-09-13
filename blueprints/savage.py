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
    SavageConditions,
    SavageAlternatives,
    SavageCostMatrix,
    SavageTask,
    db,
    Result,
)
from flask_login import current_user, login_required
from mymodules.methods import add_object_to_db, generate_plot
from mymodules.experts_func import make_table
from mymodules.savage_excel_export import SavageExcelExporter
from mymodules.file_upload import process_savage_file
from datetime import datetime

savage_bp = Blueprint("savage", __name__, url_prefix="/savage")


@savage_bp.route("/")
def index():
    context = {
        "title": "Критерій Севіджа",
        "name": (current_user.get_name() if current_user.is_authenticated else None),
    }
    return render_template("Savage/index.html", **context)


@savage_bp.route("/names", methods=["GET", "POST"])
def names():
    # Проверяем, загружается ли черновик
    draft_id = request.args.get("draft")
    draft_data = None
    num_alt = 0
    num_conditions = 0
    savage_task = None

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
                savage_task = draft_data.get("task")
            else:
                # Если черновик не найден, используем значения по умолчанию
                num_alt = 0
                num_conditions = 0
                savage_task = None
        except Exception as e:
            print(f"Error loading draft: {str(e)}")
            # В случае ошибки используем значения по умолчанию
            num_alt = 0
            num_conditions = 0
            savage_task = None
    else:
        # Если черновик не загружается, получаем данные из URL параметров
        try:
            num_alt = int(request.args.get("num_alt") or 0)
            num_conditions = int(request.args.get("num_conditions") or 0)
            savage_task = request.args.get("savage_task")
        except (ValueError, TypeError):
            num_alt = 0
            num_conditions = 0
            savage_task = None

    # Збереження змінної у сесії
    session["num_alt"] = num_alt
    session["num_conditions"] = num_conditions
    session["savage_task"] = savage_task

    context = {
        "title": "Імена",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "savage_task": savage_task,
        "name_alternatives": (draft_data.get("alternatives") if draft_data else None),
        "name_conditions": (draft_data.get("conditions") if draft_data else None),
        "name": (current_user.get_name() if current_user.is_authenticated else None),
    }

    return render_template("Savage/names.html", **context)


@savage_bp.route("/cost-matrix", methods=["GET", "POST"])
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
        savage_task = draft_data.get("task")
        name_alternatives = draft_data.get("alternatives", [])
        name_conditions = draft_data.get("conditions", [])
    else:
        # Загружаем данные из сессии и формы
        num_alt = int(session.get("num_alt"))
        num_conditions = int(session.get("num_conditions"))
        # Получаем savage_task из формы или сессии
        savage_task = request.form.get("savage_task") or session.get("savage_task")
        name_alternatives = request.form.getlist("name_alternatives")
        name_conditions = request.form.getlist("name_conditions")

        # Обновляем сессию с актуальным значением savage_task
        if savage_task:
            session["savage_task"] = savage_task

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

        return render_template("Savage/names.html", **context)

    # Збереження даних у БД
    new_record_id = add_object_to_db(db, SavageConditions, names=name_conditions)

    add_object_to_db(db, SavageAlternatives, id=new_record_id, names=name_alternatives)

    if savage_task:
        add_object_to_db(db, SavageTask, id=new_record_id, task=savage_task)

    session["new_record_id"] = new_record_id
    session["flag"] = 0

    context = {
        "title": "Матриця Вартостей",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "name_alternatives": name_alternatives,
        "name_conditions": name_conditions,
        "savage_task": savage_task,
        "name": (current_user.get_name() if current_user.is_authenticated else None),
        "id": new_record_id,
    }

    return render_template("Savage/cost_matrix.html", **context)


@savage_bp.route("/result/<int:method_id>", methods=["GET", "POST"])
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
        num_alt = len(SavageAlternatives.query.get(new_record_id).names)
        num_conditions = len(SavageConditions.query.get(new_record_id).names)

    name_alternatives = SavageAlternatives.query.get(new_record_id).names
    name_conditions = SavageConditions.query.get(new_record_id).names

    savage_task = session.get("savage_task")

    try:
        savage_task_record = SavageTask.query.get(new_record_id)
        savage_task = savage_task_record.task if savage_task_record else None
    except Exception as e:
        print("[!] Error:", e)

    flag = session.get("flag")

    # Проверяем, есть ли данные из формы (измененные значения из черновика)
    cost_matrix_raw = request.form.getlist("cost_matrix")
    has_form_data = cost_matrix_raw and any(value.strip() for value in cost_matrix_raw)

    if flag != 0 and not has_form_data:
        # Используем данные из базы данных только если нет новых данных из формы
        cost_record = SavageCostMatrix.query.get(new_record_id)
        cost_matrix = cost_record.matrix
        loss_matrix = cost_record.loss_matrix
        max_losses = cost_record.max_losses
        optimal_alternative = cost_record.optimal_variants[0]
    else:
        # Обрабатываем данные из формы (новые или измененные значения)
        if not cost_matrix_raw:
            # Если нет данных из формы, используем данные из базы
            cost_record = SavageCostMatrix.query.get(new_record_id)
            if cost_record:
                cost_matrix = cost_record.matrix
            else:
                cost_matrix = [
                    [0 for _ in range(num_conditions)] for _ in range(num_alt)
                ]
        else:
            cost_matrix = make_table(num_alt, num_conditions, cost_matrix_raw)

        loss_matrix = []
        for j in range(num_conditions):
            # Перетворюємо всі елементи стовпця в float
            col = [float(cost_matrix[i][j]) for i in range(num_alt)]
            max_in_col = max(col)
            loss_matrix.append([abs(max_in_col - val) for val in col])

        loss_matrix = list(map(list, zip(*loss_matrix)))
        max_losses = [max(row) for row in loss_matrix]
        min_loss = min(max_losses)
        min_index = max_losses.index(min_loss)
        optimal_alternative = name_alternatives[min_index]

        # Всегда обновляем данные в базе, если они изменились
        existing_record = SavageCostMatrix.query.get(new_record_id)
        if existing_record:
            # Обновляем существующую запись
            existing_record.matrix = cost_matrix
            existing_record.loss_matrix = loss_matrix
            existing_record.max_losses = max_losses
            existing_record.optimal_variants = [optimal_alternative]
            db.session.commit()
        else:
            # Создаем новую запись
            add_object_to_db(
                db,
                SavageCostMatrix,
                id=new_record_id,
                savage_alternatives_id=new_record_id,
                matrix=cost_matrix,
                loss_matrix=loss_matrix,
                max_losses=max_losses,
                optimal_variants=[optimal_alternative],
            )
        if current_user.is_authenticated:
            add_object_to_db(
                db,
                Result,
                method_name="Savage",
                method_id=new_record_id,
                user_id=current_user.get_id(),
            )

    optimal_message = (
        f"Оптимальна альтернатива за критерієм Севіджа: "
        f"{optimal_alternative} (мінімальні максимальні втрати = "
        f"{min(max_losses)})"
    )

    context = {
        "title": "Результат",
        "name": (current_user.get_name() if current_user.is_authenticated else None),
        "name_alternatives": name_alternatives,
        "name_conditions": name_conditions,
        "cost_matrix": cost_matrix,
        "loss_matrix": loss_matrix,
        "max_losses": max_losses,
        "id": new_record_id,
        "savage_task": savage_task,
        "optimal_message": optimal_message,
        "savage_plot": generate_plot(max_losses, name_alternatives, False, savage=True),
    }

    session["flag"] = 1
    return render_template("Savage/result.html", **context)


@savage_bp.route("/export/excel/<int:method_id>")
def export_excel(method_id):
    """Export savage analysis to Excel"""
    try:
        # Get data from database
        savage_conditions = SavageConditions.query.get(method_id)
        savage_alternatives = SavageAlternatives.query.get(method_id)
        savage_cost_matrix = SavageCostMatrix.query.get(method_id)
        savage_task = SavageTask.query.get(method_id)

        if not all([savage_conditions, savage_alternatives, savage_cost_matrix]):
            return Response("Data not found", status=404)

        # Get task description
        task_description = "Savage Analysis"
        if savage_task and savage_task.task:
            task_description = savage_task.task

        # Calculate optimal message exactly like on website
        cost_matrix = savage_cost_matrix.matrix or []
        loss_matrix = savage_cost_matrix.loss_matrix or []
        max_losses = savage_cost_matrix.max_losses or []
        name_alternatives = savage_alternatives.names or []

        if max_losses and name_alternatives:
            min_loss = min(max_losses)
            min_index = max_losses.index(min_loss)
            optimal_alternative = name_alternatives[min_index]
            optimal_message = f"Оптимальною за критерієм Севіджа є альтернатива {optimal_alternative} (мінімальні втрати {min_loss})."
        else:
            optimal_message = "Немає даних для аналізу"

        # Prepare analysis data
        analysis_data = {
            "method_id": method_id,
            "savage_task": task_description,
            "name_alternatives": name_alternatives,
            "name_conditions": savage_conditions.names or [],
            "cost_matrix": cost_matrix,
            "loss_matrix": loss_matrix,
            "max_losses": max_losses,
            "optimal_message": optimal_message,
        }

        # Generate Excel file
        exporter = SavageExcelExporter()
        workbook = exporter.generate_savage_analysis_excel(analysis_data)
        excel_bytes = exporter.save_to_bytes()

        # Return Excel file
        return Response(
            excel_bytes,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=Savage_Analysis_Task{method_id}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            },
        )

    except Exception as e:
        print(f"Excel export error: {e}")
        return Response("Export failed", status=500)


@savage_bp.route("/upload_matrix", methods=["POST"])
@login_required
def upload_matrix():
    """Handle file upload for Savage method"""
    try:
        # Get form data
        num_alt = int(request.form.get("num_alt", 0))
        num_conditions = int(request.form.get("num_conditions", 0))

        if num_alt <= 0 or num_conditions <= 0:
            return {
                "success": False,
                "error": "Invalid number of alternatives or conditions",
            }

        # Get uploaded file
        if "matrix_file" not in request.files:
            return {"success": False, "error": "No file uploaded"}

        file = request.files["matrix_file"]
        if file.filename == "":
            return {"success": False, "error": "No file selected"}

        # Process file
        result = process_savage_file(file, num_alt, num_conditions)

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


@savage_bp.route("/result_from_file", methods=["POST"])
@login_required
def result_from_file():
    """Process uploaded file data for Savage method"""
    try:
        print(f"Savage result_from_file called with form data: {request.form}")

        # Get data from form
        file_data = {
            "alternatives_names": request.form.get("uploaded_alternatives_names"),
            "conditions_names": request.form.get("uploaded_conditions_names"),
            "cost_matrix": request.form.get("uploaded_cost_matrix"),
        }

        print(f"Extracted file_data: {file_data}")

        # Get other form data
        savage_task = request.form.get("savage_task", "")
        num_alt = int(request.form.get("num_alt", 0))
        num_conditions = int(request.form.get("num_conditions", 0))

        print(f"Savage task: '{savage_task}'")
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
            return redirect(url_for("savage.index"))

        print(f"Parsed alternatives_names: {alternatives_names}")
        print(f"Parsed conditions_names: {conditions_names}")
        print(f"Parsed cost_matrix: {cost_matrix}")

        # Create records in database to get method_id
        print("Creating database records...")
        new_record_id = add_object_to_db(db, SavageConditions, names=conditions_names)
        print(f"Created SavageConditions with ID: {new_record_id}")

        add_object_to_db(
            db, SavageAlternatives, id=new_record_id, names=alternatives_names
        )
        print(f"Created SavageAlternatives with ID: {new_record_id}")

        # Calculate Savage matrices
        loss_matrix = []
        for j in range(num_conditions):
            # Convert all elements in column to float
            col = [float(cost_matrix[i][j]) for i in range(num_alt)]
            max_in_col = max(col)
            loss_matrix.append([abs(max_in_col - val) for val in col])

        loss_matrix = list(map(list, zip(*loss_matrix)))
        max_losses = [max(row) for row in loss_matrix]
        min_loss = min(max_losses)
        min_index = max_losses.index(min_loss)
        optimal_alternative = alternatives_names[min_index]

        print(f"Calculated loss_matrix: {loss_matrix}")
        print(f"Calculated max_losses: {max_losses}")
        print(f"Optimal alternative: {optimal_alternative}")

        add_object_to_db(
            db,
            SavageCostMatrix,
            id=new_record_id,
            savage_alternatives_id=new_record_id,
            matrix=cost_matrix,
            loss_matrix=loss_matrix,
            max_losses=max_losses,
            optimal_variants=[optimal_alternative],
        )
        print(f"Created SavageCostMatrix with ID: {new_record_id}")

        # Create savage task if provided
        if savage_task:
            add_object_to_db(db, SavageTask, id=new_record_id, task=savage_task)
            print(f"Created SavageTask with ID: {new_record_id}, task: '{savage_task}'")

        # Create result record for history if user is authenticated
        if current_user.is_authenticated:
            add_object_to_db(
                db,
                Result,
                method_name="Savage",
                method_id=new_record_id,
                user_id=current_user.get_id(),
            )
            print(f"Created Result record for history with ID: {new_record_id}")

        # Redirect to result page
        print(f"Redirecting to result page with method_id: {new_record_id}")
        return redirect(url_for("savage.result", method_id=new_record_id))

    except Exception as e:
        print(f"Exception in savage result_from_file: {str(e)}")
        import traceback

        traceback.print_exc()
        flash(f"Error processing file data: {str(e)}", "error")
        return redirect(url_for("savage.index"))
