from flask import Blueprint, render_template, request, session
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

maximin_bp = Blueprint("maximin", __name__, url_prefix="/maximin")


@maximin_bp.route("/")
def index():
    context = {
        "title": "Максимінний критерій",
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }
    return render_template("Maximin/index.html", **context)


@maximin_bp.route("/names", methods=["GET", "POST"])
def names():
    num_alt = int(request.args.get("num_alt"))
    num_conditions = int(request.args.get("num_conditions"))
    maximin_task = (
        request.args.get("maximin_task") if request.args.get("maximin_task") else None
    )

    # Збереження змінниї у сесії
    session["num_alt"] = num_alt
    session["num_conditions"] = num_conditions
    session["maximin_task"] = maximin_task

    context = {
        "title": "Імена",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    return render_template("Maximin/names.html", **context)


@maximin_bp.route("/cost-matrix", methods=["GET", "POST"])
def cost_matrix():
    num_alt = int(session.get("num_alt"))
    num_conditions = int(session.get("num_conditions"))
    maximin_task = session.get("maximin_task")

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

        return render_template("Maximin/names.html", **context)

    # Збереження даних у БД
    new_record_id = add_object_to_db(db, MaximinConditions, names=name_conditions)

    add_object_to_db(db, MaximinAlternatives, id=new_record_id, names=name_alternatives)

    if maximin_task:
        add_object_to_db(db, MaximinTask, id=new_record_id, task=maximin_task)

    session["new_record_id"] = new_record_id
    session["flag"] = 0

    context = {
        "title": "Матриця Вартостей",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "name_alternatives": name_alternatives,
        "name_conditions": name_conditions,
        "name": current_user.get_name() if current_user.is_authenticated else None,
        "id": new_record_id,
    }

    return render_template("Maximin/cost_matrix.html", **context)


@maximin_bp.route("/result/<int:method_id>", methods=["GET", "POST"])
def result(method_id=None):
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

    maximin_task = session.get("maximin_task")

    try:
        maximin_task_record = MaximinTask.query.get(new_record_id)
        maximin_task = maximin_task_record.task if maximin_task_record else None
    except Exception as e:
        print("[!] Error:", e)

    flag = session.get("flag")
    if flag != 0:
        cost_matrix = MaximinCostMatrix.query.get(new_record_id).matrix
    else:
        cost_matrix_raw = request.form.getlist("cost_matrix")
        cost_matrix = make_table(num_alt, num_conditions, cost_matrix_raw)

    min_values = [min(map(int, sublist)) for sublist in cost_matrix]
    max_value = max(min_values)
    max_index = min_values.index(max_value)
    optimal_alternative = name_alternatives[max_index]

    optimal_message = f"Оптимальна альтернатива {optimal_alternative}, має максимальне значення очікуваної вигоди ('{max_value}')."

    existing_record = MaximinCostMatrix.query.get(new_record_id)
    if existing_record is None:
        add_object_to_db(
            db,
            MaximinCostMatrix,
            id=new_record_id,
            maximin_alternatives_id=new_record_id,
            matrix=cost_matrix,
            optimal_variants=min_values,
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
        "name": current_user.get_name() if current_user.is_authenticated else None,
        "name_alternatives": name_alternatives,
        "name_conditions": name_conditions,
        "cost_matrix": cost_matrix,
        "optimal_variants": min_values,
        "id": new_record_id,
        "maximin_task": maximin_task,
        "optimal_message": optimal_message,
        "maximin_plot": generate_plot(min_values, name_alternatives, False),
    }

    session["flag"] = 1

    return render_template("Maximin/result.html", **context)
