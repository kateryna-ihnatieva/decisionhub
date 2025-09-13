from flask import (
    Blueprint,
    render_template,
    request,
    session,
    send_file,
    Response,
    flash,
    redirect,
    url_for,
)
from flask_login import current_user
from mymodules.gpt_response import *
from mymodules.methods import *
from models import *
from mymodules.experts_func import *
from mymodules.experts_excel_export import ExpertsExcelExporter
from mymodules.file_upload import process_experts_file
from docxtpl import DocxTemplate
from datetime import datetime

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
    # Проверяем, загружается ли черновик
    draft_id = request.args.get("draft")
    draft_data = None
    num_experts = 0
    num_research = 0
    experts_task = None

    if draft_id:
        try:
            from models import Draft

            draft = Draft.query.filter_by(
                id=draft_id, user_id=current_user.get_id()
            ).first()

            if draft and draft.form_data:
                draft_data = draft.form_data
                # Восстанавливаем данные из черновика
                num_experts = int(draft_data.get("numExperts") or 0)
                num_research = int(draft_data.get("numResearch") or 0)
                experts_task = draft_data.get("task")
            else:
                # Если черновик не найден, используем значения по умолчанию
                num_experts = 0
                num_research = 0
                experts_task = None
        except Exception as e:
            print(f"Error loading draft: {str(e)}")
            # В случае ошибки используем значения по умолчанию
            num_experts = 0
            num_research = 0
            experts_task = None
    else:
        # Если черновик не загружается, получаем данные из URL параметров
        try:
            num_experts = int(request.args.get("num_experts") or 0)
            num_research = int(request.args.get("num_research") or 0)
            experts_task = request.args.get("experts_task")
        except (ValueError, TypeError):
            num_experts = 0
            num_research = 0
            experts_task = None

    # Збереження змінних у сесії
    session["num_experts"] = num_experts
    session["num_research"] = num_research
    session["experts_task"] = experts_task

    context = {
        "title": "Імена",
        "num_experts": num_experts,
        "num_research": num_research,
        "experts_task": experts_task,
        "names": draft_data.get("research") if draft_data else None,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    return render_template("Experts/names.html", **context)


@experts_bp.route("/experts_competence", methods=["GET", "POST"])
def experts_competence():
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
                num_experts = int(draft_data.get("numExperts") or 0)
                num_research = int(draft_data.get("numResearch") or 0)
                experts_task = draft_data.get("task")
                names = draft_data.get("research", [])

                # Проверяем, что names не None и не содержит None значений
                if names is None:
                    print(f"Warning: names is None in draft {draft_id}")
                    names = ["Research 1", "Research 2"]  # Значения по умолчанию
                else:
                    # Фильтруем None значения и заменяем их на пустые строки
                    names = [name if name and name != "None" else "" for name in names]
                    # Если все имена пустые, используем значения по умолчанию
                    if all(not name for name in names):
                        names = ["Research 1", "Research 2"]

                # Обновляем сессию
                session["num_experts"] = num_experts
                session["num_research"] = num_research
                session["experts_task"] = experts_task
                session["names"] = names

                # Создаем новый ID записи для черновика
                new_record_id = add_object_to_db(db, ExpertsNameResearch, names=names)
                if experts_task:
                    add_object_to_db(
                        db, ExpertsTask, id=new_record_id, task=experts_task
                    )

                session["new_record_id"] = new_record_id

                context = {
                    "id": new_record_id,
                    "title": "Компетенція",
                    "num_experts": num_experts,
                    "name_arguments": name_arguments,
                    "name": (
                        current_user.get_name()
                        if current_user.is_authenticated
                        else None
                    ),
                }
                return render_template("Experts/competence.html", **context)

        except Exception as e:
            print(f"Error loading draft: {str(e)}")

    # Обычная обработка POST запроса
    num_experts = int(session.get("num_experts"))
    experts_task = session.get("experts_task")

    name_research = request.form.getlist("name_research")

    # Сохраняем имена в сессии
    session["names"] = name_research

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
                num_experts = int(draft_data.get("numExperts") or 0)
                names = draft_data.get("research", [])

                # Проверяем, что names не None и не содержит None значений
                if names is None:
                    print(f"Warning: names is None in draft {draft_id}")
                    names = ["Research 1", "Research 2"]  # Значения по умолчанию
                else:
                    # Фильтруем None значения и заменяем их на пустые строки
                    names = [name if name and name != "None" else "" for name in names]
                    # Если все имена пустые, используем значения по умолчанию
                    if all(not name for name in names):
                        names = ["Research 1", "Research 2"]

                # Обновляем сессию
                session["num_experts"] = num_experts
                session["names"] = names

                # Создаем новый ID записи для черновика
                new_record_id = add_object_to_db(db, ExpertsNameResearch, names=names)
                session["new_record_id"] = new_record_id

                # Создаем пустую запись компетенции для черновика
                # Это нужно для корректной работы при переходе на результат
                if draft_data.get("matrices", {}).get("competence"):
                    competence_matrix = draft_data["matrices"]["competence"]
                    # Сохраняем матрицу компетенции в сессии для восстановления в шаблоне
                    session["competence_matrix"] = competence_matrix

                    # Вычисляем коэффициенты для матрицы компетенции
                    k_a = []
                    k_k = []
                    for i in competence_matrix:
                        temp_lst = [float(j) if j and j != "" else 0.0 for j in i]
                        k_a.append(sum(temp_lst[1:]))

                    for i in range(len(competence_matrix)):
                        k_k.append(
                            (
                                k_a[i]
                                + float(
                                    competence_matrix[i][0]
                                    if competence_matrix[i][0]
                                    else 0.0
                                )
                            )
                            / 2
                        )

                    add_object_to_db(
                        db,
                        ExpertsCompetency,
                        id=new_record_id,
                        table_competency=competence_matrix,
                        k_a=k_a,
                        k_k=k_k,
                    )
                else:
                    # Создаем пустую запись компетенции
                    empty_matrix = [
                        ["0.0"] * 5 for _ in range(num_experts)
                    ]  # 5 аргументов компетенции
                    # Сохраняем пустую матрицу в сессии
                    session["competence_matrix"] = empty_matrix

                    add_object_to_db(
                        db,
                        ExpertsCompetency,
                        id=new_record_id,
                        table_competency=empty_matrix,
                        k_a=[0.0] * num_experts,
                        k_k=[0.0] * num_experts,
                    )

                context = {
                    "id": new_record_id,
                    "title": "Вихідні Дані",
                    "name": (
                        current_user.get_name()
                        if current_user.is_authenticated
                        else None
                    ),
                    "num_experts": num_experts,
                    "name_research": names,
                }
                return render_template("Experts/experts_data.html", **context)

        except Exception as e:
            print(f"Error loading draft: {str(e)}")

    # Обычная обработка
    new_record_id = int(session.get("new_record_id"))
    num_experts = int(session.get("num_experts"))
    name_research = ExpertsNameResearch.query.get(new_record_id).names
    table_competence_temp = request.form.getlist("matrix_competence")

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

    # Сохраняем матрицу компетенции в сессии для восстановления в шаблоне
    session["competence_matrix"] = table_competence

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
        # Безопасно получаем количество экспертов
        try:
            competency_record = ExpertsCompetency.query.get(new_record_id)
            if competency_record and competency_record.table_competency:
                num_experts = len(competency_record.table_competency)
            else:
                # Если записи компетенции нет, используем значение по умолчанию
                num_experts = 2
        except Exception as e:
            print(f"Error getting num_experts: {str(e)}")
            num_experts = 2

    try:
        experts_task_record = ExpertsTask.query.get(new_record_id)
        experts_task = experts_task_record.task if experts_task_record else None
    except Exception as e:
        print("[!] Error:", e)

    name_research = ExpertsNameResearch.query.get(new_record_id).names

    # Проверяем, что name_research не None
    if name_research is None:
        print(f"Warning: name_research is None for record {new_record_id}")
        name_research = ["Research 1", "Research 2"]  # Значения по умолчанию

    if request.method == "POST":
        experts_data_table_temp = request.form.getlist("matrix_experts_data")
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

    # Безопасно получаем данные компетенции
    try:
        competency_record = ExpertsCompetency.query.get(new_record_id)
        if competency_record:
            k_k = competency_record.k_k
            k_a = competency_record.k_a
            table_competency = competency_record.table_competency
        else:
            # Если записи компетенции нет, создаем пустые значения
            k_k = [0.0] * num_experts
            k_a = [0.0] * num_experts
            table_competency = [["0.0"] * 5 for _ in range(num_experts)]
    except Exception as e:
        print(f"Error getting competency data: {str(e)}")
        # Создаем пустые значения в случае ошибки
        k_k = [0.0] * num_experts
        k_a = [0.0] * num_experts
        table_competency = [["0.0"] * 5 for _ in range(num_experts)]

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

    # Безопасно генерируем график
    try:
        experts_plot = generate_plot(m_i, name_research, False)
    except Exception as e:
        print(f"Error generating plot: {str(e)}")
        experts_plot = None

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
        "l_value_sum": round(sum(l_value)) if l_value else 0,
        "method_id": method_id,
        "rank_str": rank_str,
        "experts_task": experts_task,
        "experts_plot": experts_plot,
        # 'gpt_response': gpt_response,
    }

    session["flag"] = 1
    return render_template("Experts/result.html", **context)


@experts_bp.route("/export/excel/<int:method_id>")
def export_excel(method_id):
    """Export experts analysis results to Excel"""
    try:
        # Get data from database
        experts_data = ExpertsData.query.get(method_id)
        if not experts_data:
            return Response("Analysis not found", status=404, mimetype="text/plain")

        experts_competency = ExpertsCompetency.query.get(method_id)
        if not experts_competency:
            return Response(
                "Competency data not found", status=404, mimetype="text/plain"
            )

        experts_name_research = ExpertsNameResearch.query.get(method_id)
        if not experts_name_research:
            return Response(
                "Research names not found", status=404, mimetype="text/plain"
            )

        experts_task = ExpertsTask.query.get(method_id)
        task_description = "Experts Analysis"
        if experts_task and experts_task.task:
            task_description = experts_task.task

        # Get data from database
        m_i = experts_data.m_i or []
        r_i = experts_data.r_i or []
        l_value = experts_data.lambda_value or []
        name_research = experts_name_research.names or []

        # Debug: print values
        print(f"Debug - m_i: {m_i}")
        print(f"Debug - r_i: {r_i}")
        print(f"Debug - l_value: {l_value}")
        print(f"Debug - l_value_sum: {sum(l_value) if l_value else 0}")

        # Recalculate values to ensure consistency
        try:
            # Import the calculation functions
            from mymodules.experts_func import make_m_i, make_r_i, make_lambda

            # Get competency data
            k_k = experts_competency.k_k or []
            experts_data_table = experts_data.experts_data_table or []
            num_experts = len(experts_data_table)

            # Recalculate values
            if k_k and experts_data_table and num_experts > 0:
                m_i = make_m_i(k_k, experts_data_table, num_experts, len(name_research))
                r_i = make_r_i(m_i)
                l_value = make_lambda(len(name_research), r_i)
                print(f"Debug - Recalculated m_i: {m_i}")
                print(f"Debug - Recalculated r_i: {r_i}")
                print(f"Debug - Recalculated l_value: {l_value}")
                print(
                    f"Debug - Recalculated l_value_sum: {sum(l_value) if l_value else 0}"
                )
        except Exception as e:
            print(f"Error recalculating values: {e}")
            # Use original values if recalculation fails
            pass

        try:
            rank_str = rank_results(r_i, m_i, name_research)
        except Exception as e:
            print(f"Error calculating rank_str: {e}")
            rank_str = "Аналіз завершено"

        # Prepare analysis data
        l_value_sum = round(sum(l_value)) if l_value else 0
        print(f"Debug - Final l_value_sum: {l_value_sum}")

        analysis_data = {
            "method_id": method_id,
            "experts_task": task_description,
            "table_competency": experts_competency.table_competency or [],
            "k_k": experts_competency.k_k or [],
            "k_a": experts_competency.k_a or [],
            "name_arguments": name_arguments,
            "name_research": name_research,
            "experts_data_table": experts_data.experts_data_table or [],
            "m_i": m_i,
            "r_i": r_i,
            "l_value": l_value,
            "l_value_sum": l_value_sum,
            "rank_str": rank_str,
        }

        # Generate Excel file
        exporter = ExpertsExcelExporter()
        workbook = exporter.generate_experts_analysis_excel(analysis_data)
        excel_bytes = exporter.save_to_bytes()

        # Create filename
        filename = f"Experts_Analysis_Task{method_id}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

        # Return Excel file
        return Response(
            excel_bytes,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(excel_bytes)),
            },
        )

    except Exception as e:
        print(f"Excel export error: {e}")
        return Response(f"Export failed: {str(e)}", status=500, mimetype="text/plain")


@experts_bp.route("/upload_matrix", methods=["POST"])
def upload_matrix():
    """Handle file upload for experts evaluation data"""
    try:
        # Get the uploaded file
        file = request.files.get("matrix_file")
        if not file:
            return {"success": False, "error": "No file uploaded"}, 400

        # Get number of experts and alternatives from request
        num_experts = request.form.get("num_experts")
        num_alternatives = request.form.get("num_alternatives")

        if not num_experts or not num_alternatives:
            return {
                "success": False,
                "error": "Number of experts and alternatives not provided",
            }, 400

        try:
            num_experts = int(num_experts)
            num_alternatives = int(num_alternatives)
        except ValueError:
            return {
                "success": False,
                "error": "Invalid number of experts or alternatives",
            }, 400

        # Process the uploaded file for experts evaluation analysis
        result = process_experts_file(file, num_experts, num_alternatives)

        if result["success"]:
            return {
                "success": True,
                "competency_matrix": result["competency_matrix"],
                "evaluation_matrix": result["evaluation_matrix"],
                "alternatives_names": result["alternatives_names"],
            }
        else:
            return {"success": False, "error": result["error"]}, 400

    except Exception as e:
        return {"success": False, "error": f"Upload failed: {str(e)}"}, 500


@experts_bp.route("/result_from_file", methods=["POST"])
def result_from_file():
    """Process experts evaluation from uploaded file data and redirect to result page"""
    try:
        print(f"Experts result_from_file called with form data: {request.form}")

        # Get data from form
        file_data = {
            "competency_matrix": request.form.get("uploaded_competency_matrix"),
            "evaluation_matrix": request.form.get("uploaded_evaluation_matrix"),
            "alternatives_names": request.form.get("uploaded_alternatives_names"),
        }

        print(f"Extracted file_data: {file_data}")

        # Get task description from form
        experts_task = request.form.get("experts_task")
        print(f"Experts task: {experts_task}")

        # Check if all required data is present
        if not all(file_data.values()):
            print("Missing required data from file upload")
            print(f"file_data values: {file_data}")
            flash("Missing required data from file upload", "error")
            return redirect(url_for("experts.index"))

        # Parse the data
        import json

        try:
            competency_matrix = json.loads(file_data["competency_matrix"])
            evaluation_matrix = json.loads(file_data["evaluation_matrix"])
            alternatives_names = json.loads(file_data["alternatives_names"])
            print(f"Parsed competency_matrix: {competency_matrix}")
            print(f"Parsed evaluation_matrix: {evaluation_matrix}")
            print(f"Parsed alternatives_names: {alternatives_names}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            flash("Error parsing uploaded data", "error")
            return redirect(url_for("experts.index"))

        # Create records in database to get method_id
        print("Creating database records...")
        new_record_id = add_object_to_db(
            db, ExpertsNameResearch, names=alternatives_names
        )
        print(f"Created ExpertsNameResearch with ID: {new_record_id}")

        # Calculate k_a and k_k from competency matrix
        k_a = []
        k_k = []
        for i in competency_matrix:
            temp_lst = [float(j) if j and j != "" else 0.0 for j in i]
            k_a.append(sum(temp_lst[1:]))  # Sum of all criteria except first column

        for i in range(len(competency_matrix)):
            k_k.append(
                (
                    k_a[i]
                    + float(competency_matrix[i][0] if competency_matrix[i][0] else 0.0)
                )
                / 2
            )

        print(f"Calculated k_a: {k_a}")
        print(f"Calculated k_k: {k_k}")

        add_object_to_db(
            db,
            ExpertsCompetency,
            id=new_record_id,
            table_competency=competency_matrix,
            k_k=k_k,
            k_a=k_a,
        )
        print(f"Created ExpertsCompetency with ID: {new_record_id}")

        # Calculate m_i, r_i, and lambda_value from evaluation matrix
        from mymodules.experts_func import make_m_i, make_r_i, make_lambda

        num_experts = len(evaluation_matrix)
        num_research = len(alternatives_names)

        m_i = make_m_i(k_k, evaluation_matrix, num_experts, num_research)
        r_i = make_r_i(m_i)
        l_value = make_lambda(num_research, r_i)

        print(f"Calculated m_i: {m_i}")
        print(f"Calculated r_i: {r_i}")
        print(f"Calculated lambda_value: {l_value}")

        add_object_to_db(
            db,
            ExpertsData,
            id=new_record_id,
            experts_name_research_id=new_record_id,
            experts_data_table=evaluation_matrix,
            m_i=m_i,
            r_i=r_i,
            lambda_value=l_value,
        )
        print(f"Created ExpertsData with ID: {new_record_id}")

        # Create experts task if provided
        if experts_task:
            add_object_to_db(db, ExpertsTask, id=new_record_id, task=experts_task)
            print(f"Created ExpertsTask with ID: {new_record_id}")

        # Redirect to result page
        print(f"Redirecting to result page with method_id: {new_record_id}")
        return redirect(url_for("experts.experts_result", method_id=new_record_id))

    except Exception as e:
        print(f"Exception in experts result_from_file: {str(e)}")
        import traceback

        traceback.print_exc()
        flash(f"Error processing file data: {str(e)}", "error")
        return redirect(url_for("experts.index"))
