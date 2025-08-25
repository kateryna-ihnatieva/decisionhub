from flask import Flask, Blueprint, render_template, request, session
from mymodules.binary import *
from models import *
from mymodules.mai import *
from flask_login import current_user
from mymodules.methods import *
from mymodules.gpt_response import *

import operator

binary_relations_bp = Blueprint(
    "binary_relations", __name__, url_prefix="/binary-relations"
)


@binary_relations_bp.route("/")
def index():
    context = {
        "title": "Бінарні Відношення",
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }
    return render_template("Binary/index.html", **context)


@binary_relations_bp.route("/names", methods=["GET", "POST"])
def names():
    num = int(request.args.get("num"))
    binary_task = (
        request.args.get("binary_task") if request.args.get("binary_task") else None
    )

    # Збереження змінної у сесії
    session["num"] = num
    session["binary_task"] = binary_task

    context = {
        "title": "Імена",
        "num": num,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }
    return render_template("Binary/names.html", **context)


@binary_relations_bp.route("/matrix/", methods=["GET", "POST"])
def matrix():
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
        "title": "Імена",
        "num": num,
        "names": names,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    return render_template("Binary/matrix.html", **context)


@binary_relations_bp.route("/result/<int:method_id>", methods=["GET", "POST"])
def result(method_id=None):
    new_record_id = method_id if method_id else int(session.get("new_record_id"))
    binary_task = session.get("binary_task")

    try:
        binary_task_record = BinaryTask.query.get(new_record_id)
        binary_task = binary_task_record.task if binary_task_record else None
    except Exception as e:
        print("[!] Error:", e)

    names = BinaryNames.query.get(new_record_id).names
    num = len(names)

    # Перевіримо: якщо матриця вже є — session["matr"] має бути 1
    existing_matrix = BinaryMatrix.query.get(new_record_id)
    if existing_matrix:
        session["matr"] = 1
    else:
        session["matr"] = 0
    print(session["matr"])
    if session["matr"] == 0:
        matrix = process_matrix(request.form.getlist("matrix"), num)
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
