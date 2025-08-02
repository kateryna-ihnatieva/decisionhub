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

kriteriy_laplasa_bp = Blueprint(
    "kriteriy_laplasa", __name__, url_prefix="/kriteriy-laplasa"
)


@kriteriy_laplasa_bp.route("/")
def index():
    context = {
        "title": "Критерій Лапласа",
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }
    return render_template("Laplasa/index.html", **context)


@kriteriy_laplasa_bp.route("/names", methods=["GET", "POST"])
def names():
    num_alt = int(request.args.get("num_alt"))
    num_conditions = int(request.args.get("num_conditions"))
    laplasa_task = (
        request.args.get("laplasa_task") if request.args.get("laplasa_task") else None
    )

    # Збереження змінної у сесії
    session["num_alt"] = num_alt
    session["num_conditions"] = num_conditions
    session["laplasa_task"] = laplasa_task

    context = {
        "title": "Імена",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    return render_template("Laplasa/names.html", **context)


@kriteriy_laplasa_bp.route("/cost-matrix", methods=["GET", "POST"])
def cost_matrix():
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

    context = {
        "title": "Матриця Вартостей",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "name_alternatives": name_alternatives,
        "name_conditions": name_conditions,
        "name": current_user.get_name() if current_user.is_authenticated else None,
        "id": new_record_id,
    }

    return render_template("Laplasa/cost_matrix.html", **context)


@kriteriy_laplasa_bp.route("/result/<int:method_id>", methods=["GET", "POST"])
def result(method_id=None):
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

    name_alternatives = LaplasaAlternatives.query.get(new_record_id).names
    name_conditions = LaplasaConditions.query.get(new_record_id).names

    flag = session.get("flag")
    if flag != 0:
        cost_matrix = LaplasaCostMatrix.query.get(new_record_id).matrix
    else:
        cost_matrix_raw = request.form.getlist("cost_matrix")
        cost_matrix = make_table(num_alt, num_conditions, cost_matrix_raw)

    optimal_variants = [
        round(sum(map(int, sublist)) / len(sublist), 2) for sublist in cost_matrix
    ]
    # Знаходимо максимальне значення і його індекс
    max_value = max(optimal_variants)
    max_index = optimal_variants.index(max_value)
    optimal_alternative = name_alternatives[max_index]

    optimal_message = f"Оптимальна альтернатива {optimal_alternative}, має максимальне значення очікуваної вигоди ('{max_value}')."

    existing_record = LaplasaCostMatrix.query.get(new_record_id)
    if existing_record is None:
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
