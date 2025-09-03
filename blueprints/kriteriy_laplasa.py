from flask import Blueprint, render_template, request, session
from mymodules.mai import *
from models import (
    LaplasaConditions,
    LaplasaAlternatives,
    LaplasaCostMatrix,
    LaplasaTask,
    db,
    Result,
)
from flask_login import current_user
from mymodules.methods import add_object_to_db, generate_plot
from mymodules.experts_func import make_table

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
            else:
                # Если черновик не найден, используем значения по умолчанию
                num_alt = 0
                num_conditions = 0
                laplasa_task = None
        except Exception as e:
            print(f"Error loading draft: {str(e)}")
            # В случае ошибки используем значения по умолчанию
            num_alt = 0
            num_conditions = 0
            laplasa_task = None
    else:
        # Если черновик не загружается, получаем данные из URL параметров
        try:
            num_alt = int(request.args.get("num_alt") or 0)
            num_conditions = int(request.args.get("num_conditions") or 0)
            laplasa_task = request.args.get("laplasa_task")
        except (ValueError, TypeError):
            num_alt = 0
            num_conditions = 0
            laplasa_task = None

    # Збереження змінної у сесії
    session["num_alt"] = num_alt
    session["num_conditions"] = num_conditions
    session["laplasa_task"] = laplasa_task

    context = {
        "title": "Імена",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "laplasa_task": laplasa_task,
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

                # Обновляем сессию
                session["num_alt"] = num_alt
                session["num_conditions"] = num_conditions
                session["laplasa_task"] = laplasa_task

                # Создаем новый ID записи для черновика
                new_record_id = add_object_to_db(
                    db, LaplasaConditions, names=name_conditions
                )
                add_object_to_db(
                    db, LaplasaAlternatives, id=new_record_id, names=name_alternatives
                )
                if laplasa_task:
                    add_object_to_db(
                        db, LaplasaTask, id=new_record_id, task=laplasa_task
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
                }
                print(f"Context cost_matrix: {context['cost_matrix']}")
                return render_template("Laplasa/cost_matrix.html", **context)

        except Exception as e:
            print(f"Error loading draft: {str(e)}")

    # Обычная обработка
    num_alt = int(session.get("num_alt"))
    num_conditions = int(session.get("num_conditions"))
    laplasa_task = session.get("laplasa_task")

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

    if laplasa_task:
        add_object_to_db(db, LaplasaTask, id=new_record_id, task=laplasa_task)

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
                if laplasa_task:
                    add_object_to_db(
                        db, LaplasaTask, id=new_record_id, task=laplasa_task
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
                    round(sum(map(int, sublist)) / len(sublist), 2)
                    for sublist in cost_matrix
                ]

                max_value = max(optimal_variants)
                max_index = optimal_variants.index(max_value)
                optimal_alternative = name_alternatives[max_index]
                optimal_message = f"Оптимальна альтернатива {optimal_alternative}, має максимальне значення очікуваної вигоди ('{max_value}')."

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
                    "optimal_message": optimal_message,
                    "laplasa_plot": generate_plot(
                        optimal_variants, name_alternatives, False
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
        num_alt = len(LaplasaAlternatives.query.get(new_record_id).names)
        num_conditions = len(LaplasaConditions.query.get(new_record_id).names)

    name_alternatives = LaplasaAlternatives.query.get(new_record_id).names
    name_conditions = LaplasaConditions.query.get(new_record_id).names

    laplasa_task = session.get("laplasa_task")

    try:
        laplasa_task_record = LaplasaTask.query.get(new_record_id)
        laplasa_task = laplasa_task_record.task if laplasa_task_record else None
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
        round(sum(map(int, sublist)) / len(sublist), 2) for sublist in cost_matrix
    ]
    # Знаходимо максимальне значення і його індекс
    max_value = max(optimal_variants)
    max_index = optimal_variants.index(max_value)
    optimal_alternative = name_alternatives[max_index]

    optimal_message = f"Оптимальна альтернатива {optimal_alternative}, має максимальне значення очікуваної вигоди ('{max_value}')."

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
        "laplasa_task": laplasa_task,
        "optimal_message": optimal_message,
        "laplasa_plot": generate_plot(optimal_variants, name_alternatives, False),
    }

    session["flag"] = 1

    return render_template("Laplasa/result.html", **context)
