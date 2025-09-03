from flask import Blueprint, render_template, request, session

# from mymodules.mai import *  # Unused import removed
from models import (
    SavageConditions,
    SavageAlternatives,
    SavageCostMatrix,
    SavageTask,
    db,
    Result,
)
from flask_login import current_user
from mymodules.methods import add_object_to_db, generate_plot
from mymodules.experts_func import make_table

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
