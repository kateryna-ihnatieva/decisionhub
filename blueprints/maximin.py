from flask import Blueprint, render_template, request, session, Response
from mymodules.mai import *
from models import (
    MaximinConditions,
    MaximinAlternatives,
    MaximinCostMatrix,
    MaximinTask,
    db,
    Result,
)
from flask_login import current_user
from mymodules.methods import add_object_to_db, generate_plot
from mymodules.experts_func import make_table
from mymodules.maximin_excel_export import MaximinExcelExporter
from datetime import datetime

maximin_bp = Blueprint("maximin", __name__, url_prefix="/maximin")


@maximin_bp.route("/")
def index():
    context = {
        "title": "Максимінний критерій",
        "name": (current_user.get_name() if current_user.is_authenticated else None),
    }
    return render_template("Maximin/index.html", **context)


@maximin_bp.route("/names", methods=["GET", "POST"])
def names():
    # Проверяем, загружается ли черновик
    draft_id = request.args.get("draft")
    draft_data = None
    num_alt = 0
    num_conditions = 0
    maximin_task = None
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
                maximin_task = draft_data.get("task")
                matrix_type = draft_data.get("matrixType")
            else:
                # Если черновик не найден, используем значения по умолчанию
                num_alt = 0
                num_conditions = 0
                maximin_task = None
                matrix_type = None
        except Exception:
            # В случае ошибки используем значения по умолчанию
            num_alt = 0
            num_conditions = 0
            maximin_task = None
            matrix_type = None
    else:
        # Если черновик не загружается, получаем данные из URL параметров
        try:
            num_alt = int(request.args.get("num_alt") or 0)
            num_conditions = int(request.args.get("num_conditions") or 0)
            maximin_task = request.args.get("maximin_task")
            matrix_type = request.args.get("matrix_type")
        except (ValueError, TypeError):
            num_alt = 0
            num_conditions = 0
            maximin_task = None
            matrix_type = None

    # Збереження змінної у сесії
    session["num_alt"] = num_alt
    session["num_conditions"] = num_conditions
    session["maximin_task"] = maximin_task
    session["matrix_type"] = matrix_type

    context = {
        "title": "Імена",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "maximin_task": maximin_task,
        "matrix_type": matrix_type,
        "name_alternatives": (draft_data.get("alternatives") if draft_data else None),
        "name_conditions": (draft_data.get("conditions") if draft_data else None),
        "name": (current_user.get_name() if current_user.is_authenticated else None),
    }

    return render_template("Maximin/names.html", **context)


@maximin_bp.route("/cost-matrix", methods=["GET", "POST"])
def cost_matrix():
    # Проверяем, загружается ли черновик
    draft_id = request.args.get("draft")
    draft_data = None
    num_alt = 0
    num_conditions = 0
    maximin_task = None
    matrix_type = None
    name_alternatives = []
    name_conditions = []

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
                maximin_task = draft_data.get("task")
                matrix_type = draft_data.get("matrixType")
                name_alternatives = draft_data.get("alternatives", [])
                name_conditions = draft_data.get("conditions", [])
            else:
                # Если черновик не найден, используем значения из сессии
                num_alt = int(session.get("num_alt", 0))
                num_conditions = int(session.get("num_conditions", 0))
                maximin_task = session.get("maximin_task")
                matrix_type = session.get("matrix_type")
                name_alternatives = request.form.getlist("name_alternatives")
                name_conditions = request.form.getlist("name_conditions")
        except Exception:
            # В случае ошибки используем значения из сессии
            num_alt = int(session.get("num_alt", 0))
            num_conditions = int(session.get("num_conditions", 0))
            maximin_task = session.get("maximin_task")
            matrix_type = session.get("matrix_type")
            name_alternatives = request.form.getlist("name_alternatives")
            name_conditions = request.form.getlist("name_conditions")
    else:
        # Если черновик не загружается, получаем данные из сессии или формы
        num_alt = int(session.get("num_alt", 0))
        num_conditions = int(session.get("num_conditions", 0))
        maximin_task = session.get("maximin_task")
        matrix_type = session.get("matrix_type")
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
            "name": (
                current_user.get_name() if current_user.is_authenticated else None
            ),
        }

        return render_template("Maximin/names.html", **context)

    # Збереження даних у БД
    new_record_id = add_object_to_db(db, MaximinConditions, names=name_conditions)

    add_object_to_db(db, MaximinAlternatives, id=new_record_id, names=name_alternatives)

    add_object_to_db(
        db, MaximinTask, id=new_record_id, task=maximin_task, matrix_type=matrix_type
    )

    session["new_record_id"] = new_record_id
    session["flag"] = 0

    context = {
        "title": "Матриця Вартостей",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "name_alternatives": name_alternatives,
        "name_conditions": name_conditions,
        "name": (current_user.get_name() if current_user.is_authenticated else None),
        "id": new_record_id,
    }

    return render_template("Maximin/cost_matrix.html", **context)


@maximin_bp.route("/result/<int:method_id>", methods=["GET", "POST"])
def result(method_id=None):
    # Проверяем, загружается ли черновик (для совместимости)
    draft_id = request.args.get("draft")

    if draft_id:
        try:
            from models import Draft

            draft = Draft.query.filter_by(
                id=draft_id, user_id=current_user.get_id()
            ).first()

            if draft and draft.form_data:
                # Черновик загружен, но в данной функции не используется
                pass
        except Exception:
            # Игнорируем ошибки загрузки черновика
            pass

    if not method_id:
        new_record_id = int(session.get("new_record_id"))
        num_alt = int(session.get("num_alt"))
        num_conditions = int(session.get("num_conditions"))
    else:
        new_record_id = method_id
        num_alt = len(MaximinAlternatives.query.get(new_record_id).names)
        num_conditions = len(MaximinConditions.query.get(new_record_id).names)

    name_alternatives = MaximinAlternatives.query.get(new_record_id).names
    name_conditions = MaximinConditions.query.get(new_record_id).names

    maximin_task = MaximinTask.query.get(new_record_id).task
    matrix_type = MaximinTask.query.get(new_record_id).matrix_type

    flag = session.get("flag")
    if flag != 0:
        cost_matrix = MaximinCostMatrix.query.get(new_record_id).matrix
    else:
        cost_matrix_raw = request.form.getlist("cost_matrix")
        cost_matrix = make_table(num_alt, num_conditions, cost_matrix_raw)

    if matrix_type == "profit":
        min_values = [min(map(int, sublist)) for sublist in cost_matrix]
        max_value = max(min_values)
        max_index = min_values.index(max_value)
        optimal_alternative = name_alternatives[max_index]
        optimal_message = (
            f"Оптимальною за критерієм максимуму мінімальних "
            f"значень є альтернатива {optimal_alternative} "
            f"(максимальне значення {max_value})."
        )
        optimal_variants = min_values
    else:
        max_values = [max(map(int, sublist)) for sublist in cost_matrix]
        min_value = min(max_values)
        min_index = max_values.index(min_value)
        optimal_alternative = name_alternatives[min_index]
        optimal_message = (
            f"Оптимальною за критерієм мінімуму максимальних "
            f"значень є альтернатива {optimal_alternative} "
            f"(мінімальне значення {min_value})."
        )
        optimal_variants = max_values

    existing_record = MaximinCostMatrix.query.get(new_record_id)
    if existing_record is None:
        add_object_to_db(
            db,
            MaximinCostMatrix,
            id=new_record_id,
            maximin_alternatives_id=new_record_id,
            matrix=cost_matrix,
            optimal_variants=optimal_variants,
        )
        if current_user.is_authenticated:
            add_object_to_db(
                db,
                Result,
                method_name="Maximin",
                method_id=new_record_id,
                user_id=current_user.get_id(),
            )

    context = {
        "title": "Результат",
        "name": (current_user.get_name() if current_user.is_authenticated else None),
        "name_alternatives": name_alternatives,
        "name_conditions": name_conditions,
        "cost_matrix": cost_matrix,
        "optimal_variants": optimal_variants,
        "id": new_record_id,
        "maximin_task": maximin_task,
        "matrix_type": matrix_type,
        "optimal_message": optimal_message,
        "maximin_plot": generate_plot(
            optimal_variants,
            name_alternatives,
            percent=False,
            savage=False if matrix_type == "profit" else True,
        ),
    }

    session["flag"] = 1

    return render_template("Maximin/result.html", **context)


@maximin_bp.route("/export/excel/<int:method_id>")
def export_excel(method_id):
    """Export maximin analysis to Excel"""
    try:
        # Get data from database
        maximin_conditions = MaximinConditions.query.get(method_id)
        maximin_alternatives = MaximinAlternatives.query.get(method_id)
        maximin_cost_matrix = MaximinCostMatrix.query.get(method_id)
        maximin_task = MaximinTask.query.get(method_id)

        if not all([maximin_conditions, maximin_alternatives, maximin_cost_matrix]):
            return Response("Data not found", status=404)

        # Get task description
        task_description = "Maximin Analysis"
        if maximin_task and maximin_task.task:
            task_description = maximin_task.task

        # Calculate optimal message exactly like on website
        cost_matrix = maximin_cost_matrix.matrix or []
        name_alternatives = maximin_alternatives.names or []
        matrix_type = maximin_task.matrix_type if maximin_task else "profit"

        if cost_matrix and name_alternatives:
            if matrix_type == "profit":
                min_values = [min(map(int, sublist)) for sublist in cost_matrix]
                max_value = max(min_values)
                max_index = min_values.index(max_value)
                optimal_alternative = name_alternatives[max_index]
                optimal_message = (
                    f"Оптимальною за критерієм максимуму мінімальних "
                    f"значень є альтернатива {optimal_alternative} "
                    f"(максимальне значення {max_value})."
                )
            else:  # cost matrix
                min_values = [min(map(int, sublist)) for sublist in cost_matrix]
                min_value = min(min_values)
                min_index = min_values.index(min_value)
                optimal_alternative = name_alternatives[min_index]
                optimal_message = (
                    f"Оптимальною за критерієм мінімуму максимальних "
                    f"значень є альтернатива {optimal_alternative} "
                    f"(мінімальне значення {min_value})."
                )
        else:
            optimal_message = "Немає даних для аналізу"
            min_values = []

        # Prepare analysis data
        analysis_data = {
            "method_id": method_id,
            "maximin_task": task_description,
            "name_alternatives": name_alternatives,
            "name_conditions": maximin_conditions.names or [],
            "cost_matrix": cost_matrix,
            "min_values": min_values,
            "matrix_type": matrix_type,
            "optimal_message": optimal_message,
        }

        # Generate Excel file
        exporter = MaximinExcelExporter()
        workbook = exporter.generate_maximin_analysis_excel(analysis_data)
        excel_bytes = exporter.save_to_bytes()

        # Return Excel file
        return Response(
            excel_bytes,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=Maximin_Analysis_Task{method_id}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            },
        )

    except Exception as e:
        print(f"Excel export error: {e}")
        return Response("Export failed", status=500)
