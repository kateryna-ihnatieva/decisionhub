from flask import Blueprint, render_template, request, session, send_file
from flask_login import current_user
from mymodules.gpt_response import *
from mymodules.methods import *
from models import *
from mymodules.experts_func import *
from docxtpl import DocxTemplate

experts_bp = Blueprint("experts", __name__, url_prefix="/experts")

name_arguments = [
    "Ступінь знайомства",
    "Теоретичний аналіз",
    "Досвід",
    "Література",
    "Інтуїція",
]


@experts_bp.route("/", methods=["GET", "POST"])
def index():
    context = {
        "title": "Експертні Оцінки",
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    file_expert = request.args.get("file_expert", False)

    template_path = "./static/Form.docx"
    doc = DocxTemplate(template_path)
    doc.save(template_path)

    if file_expert:
        return send_file(template_path, as_attachment=True)

    return render_template("Experts/index.html", **context)


@experts_bp.route("/names", methods=["GET", "POST"])
def names():
    num_experts = int(request.args.get("num_experts"))
    num_research = int(request.args.get("num_research"))
    experts_task = (
        request.args.get("experts_task") if request.args.get("experts_task") else None
    )

    # Збереження змінних у сесії
    session["num_experts"] = num_experts
    session["num_research"] = num_research
    session["experts_task"] = experts_task

    context = {
        "title": "Імена",
        "num_research": num_research,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    return render_template("Experts/names.html", **context)


@experts_bp.route("/experts_competence", methods=["GET", "POST"])
def experts_competence():
    num_experts = int(session.get("num_experts"))
    experts_task = session.get("experts_task")

    name_research = request.form.getlist("name_research")
    if len(name_research) != len(set(name_research)):
        num_research = int(session.get("num_research"))
        context = {
            "title": "Імена",
            "num_research": num_research,
            "names": name_research,
            "name": current_user.get_name() if current_user.is_authenticated else None,
            "error": "Імена повинні бути унікальними!",
        }
        return render_template("Experts/names.html", **context)

    # Збереження даних у БД
    new_record_id = add_object_to_db(db, ExpertsNameResearch, names=name_research)
    if experts_task:
        add_object_to_db(db, ExpertsTask, id=new_record_id, task=experts_task)

    session["new_record_id"] = new_record_id

    context = {
        "title": "Компетенція",
        "num_experts": num_experts,
        "name_arguments": name_arguments,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    return render_template("Experts/competence.html", **context)


@experts_bp.route("/experts_data", methods=["GET", "POST"])
def experts_data():
    new_record_id = int(session.get("new_record_id"))
    num_experts = int(session.get("num_experts"))
    name_research = ExpertsNameResearch.query.get(new_record_id).names
    table_competence_temp = request.form.getlist("table_competence")

    # створення списку з таблиць по експертах
    table_competence = make_table(
        num_experts, len(name_arguments), table_competence_temp
    )
    k_a = []
    k_k = []

    for i in table_competence:
        temp_lst = [float(j) for j in i]
        if sum(temp_lst[1:]) > 1:
            context = {
                "title": "Компетенція",
                "num_experts": num_experts,
                "name_arguments": name_arguments,
                "table_competence": table_competence,
                "name": (
                    current_user.get_name() if current_user.is_authenticated else None
                ),
                "error": "Коефіцієнт аргументованості рішень експерта має бути <= 1.",
            }
            return render_template("Experts/competence.html", **context)
        k_a.append(sum(temp_lst[1:]))

    for i in range(len(table_competence)):
        if float(table_competence[i][0]) > 1:
            context = {
                "title": "Компетенція",
                "num_experts": num_experts,
                "name_arguments": name_arguments,
                "table_competence": table_competence,
                "name": (
                    current_user.get_name() if current_user.is_authenticated else None
                ),
                "error": "Коефіцієнт ступеня знайомства експерта з проблемою має бути <= 1.",
            }
            return render_template("Experts/competence.html", **context)
        k_k.append((k_a[i] + float(table_competence[i][0])) / 2)

    add_object_to_db(
        db,
        ExpertsCompetency,
        id=new_record_id,
        table_competency=table_competence,
        k_a=k_a,
        k_k=k_k,
    )

    session["flag"] = 0

    context = {
        "id": new_record_id,
        "title": "Вихідні Дані",
        "name": current_user.get_name() if current_user.is_authenticated else None,
        "num_experts": num_experts,
        "name_research": name_research,
    }

    return render_template("Experts/experts_data.html", **context)


@experts_bp.route("/experts_result/<int:method_id>", methods=["GET", "POST"])
def experts_result(method_id=None):
    if not method_id:
        new_record_id = int(session.get("new_record_id"))
        num_experts = int(session.get("num_experts"))
    else:
        new_record_id = method_id
        num_experts = len(ExpertsCompetency.query.get(new_record_id).table_competency)

    try:
        experts_task_record = ExpertsTask.query.get(new_record_id)
        experts_task = experts_task_record.task if experts_task_record else None
    except Exception as e:
        print("[!] Error:", e)

    name_research = ExpertsNameResearch.query.get(new_record_id).names
    if request.method == "POST":
        experts_data_table_temp = request.form.getlist("experts_data_table")
        if not experts_data_table_temp:
            return "Помилка: форма не передала жодних даних.", 400
        experts_data_table = make_table(
            num_experts, len(name_research), experts_data_table_temp
        )
    else:
        existing_record = ExpertsData.query.get(new_record_id)
        if existing_record:
            experts_data_table = existing_record.experts_data_table
        else:
            return "Помилка: дані відсутні для цього запису.", 404

    name_research = ExpertsNameResearch.query.get(new_record_id).names
    k_k = ExpertsCompetency.query.get(new_record_id).k_k
    k_a = ExpertsCompetency.query.get(new_record_id).k_a
    table_competency = ExpertsCompetency.query.get(new_record_id).table_competency

    m_i = make_m_i(k_k, experts_data_table, num_experts, len(name_research))
    r_i = make_r_i(m_i)
    l_value = make_lambda(len(name_research), r_i)
    rank_str = rank_results(r_i, m_i, name_research)

    existing_record = ExpertsData.query.get(new_record_id)
    if existing_record is None:
        add_object_to_db(
            db,
            ExpertsData,
            id=new_record_id,
            experts_name_research_id=new_record_id,
            experts_data_table=experts_data_table,
            m_i=m_i,
            r_i=r_i,
            lambda_value=l_value,
        )

        if current_user.is_authenticated:
            add_object_to_db(
                db,
                Result,
                method_name="Experts",
                method_id=new_record_id,
                user_id=current_user.get_id(),
            )

    # gpt_response = generate_gpt_response_experts(experts_task, name_research, rank_str) if experts_task else None
    context = {
        "title": "Результат",
        "name": current_user.get_name() if current_user.is_authenticated else None,
        "num_experts": num_experts,
        "table_competency": table_competency,
        "k_k": k_k,
        "k_a": k_a,
        "name_arguments": name_arguments,
        "name_research": name_research,
        "experts_data_table": experts_data_table,
        "m_i": m_i,
        "r_i": r_i,
        "l_value": l_value,
        "l_value_sum": int(sum(l_value)),
        "method_id": method_id,
        "rank_str": rank_str,
        "experts_task": experts_task,
        "experts_plot": generate_plot(m_i, name_research, False),
        # 'gpt_response': gpt_response,
    }

    session["flag"] = 1
    return render_template("Experts/result.html", **context)
