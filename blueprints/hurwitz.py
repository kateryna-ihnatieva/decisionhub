from flask import Blueprint, render_template, request, session

# from mymodules.mai import *  # Unused import removed
from models import (
    HurwitzConditions,
    HurwitzAlternatives,
    HurwitzCostMatrix,
    HurwitzTask,
    db,
    Result,
)
from flask_login import current_user
from mymodules.methods import add_object_to_db, generate_plot
from mymodules.experts_func import make_table

hurwitz_bp = Blueprint("hurwitz", __name__, url_prefix="/hurwitz")


@hurwitz_bp.route("/")
def index():
    context = {
        "title": "Критерій Гурвиця",
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
            else:
                # Если черновик не найден, используем значения по умолчанию
                num_alt = 0
                num_conditions = 0
                hurwitz_task = None
                alpha = 0.5
        except Exception as e:
            print(f"Error loading draft: {str(e)}")
            # В случае ошибки используем значения по умолчанию
            num_alt = 0
            num_conditions = 0
            hurwitz_task = None
            alpha = 0.5
    else:
        # Если черновик не загружается, получаем данные из URL параметров
        try:
            num_alt = int(request.args.get("num_alt") or 0)
            num_conditions = int(request.args.get("num_conditions") or 0)
            hurwitz_task = request.args.get("hurwitz_task")
            alpha = float(request.args.get("alpha") or 0.5)
        except (ValueError, TypeError):
            num_alt = 0
            num_conditions = 0
            hurwitz_task = None
            alpha = 0.5

    # Збереження змінниї у сесії
    session["num_alt"] = num_alt
    session["num_conditions"] = num_conditions
    session["hurwitz_task"] = hurwitz_task
    session["alpha"] = alpha

    context = {
        "title": "Імена",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "hurwitz_task": hurwitz_task,
        "alpha": alpha,
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
        name_alternatives = draft_data.get("alternatives", [])
        name_conditions = draft_data.get("conditions", [])
    else:
        # Загружаем данные из сессии и формы
        num_alt = int(session.get("num_alt"))
        num_conditions = int(session.get("num_conditions"))
        # Получаем hurwitz_task из формы или сессии
        hurwitz_task = request.form.get("hurwitz_task") or session.get("hurwitz_task")
        alpha = float(request.form.get("alpha") or session.get("alpha") or 0.5)
        name_alternatives = request.form.getlist("name_alternatives")
        name_conditions = request.form.getlist("name_conditions")

        # Обновляем сессию с актуальными значениями
        if hurwitz_task:
            session["hurwitz_task"] = hurwitz_task
        session["alpha"] = alpha

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

    if hurwitz_task:
        add_object_to_db(db, HurwitzTask, id=new_record_id, task=hurwitz_task)

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

    # Аналогічно з hurwitz_task
    hurwitz_task_record = HurwitzTask.query.get(new_record_id)
    hurwitz_task = (
        hurwitz_task_record.task if hurwitz_task_record else session.get("hurwitz_task")
    )

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
        H = alpha * max_val + (1 - alpha) * min_val
        hurwitz_values.append(H)
        max_values.append(max_val)
        min_values.append(min_val)

    max_value = max(hurwitz_values)
    max_index = hurwitz_values.index(max_value)
    optimal_alternative = name_alternatives[max_index]

    optimal_message = (
        f"Оптимальна альтернатива {optimal_alternative}, "
        f"має максимальне значення критерію Гурвіца: "
        f"{max_value:.2f}."
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
        "optimal_message": optimal_message,
        "hurwitz_plot": generate_plot(hurwitz_values, name_alternatives, False),
    }

    session["flag"] = 1

    return render_template("Hurwitz/result.html", **context)
