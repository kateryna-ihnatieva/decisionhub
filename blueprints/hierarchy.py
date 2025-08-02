from flask import Flask, Blueprint, render_template, request, session
from mymodules.mai import *
from models import *
from flask_login import current_user
from mymodules.methods import *
from mymodules.gpt_response import *

hierarchy_bp = Blueprint("hierarchy", __name__, url_prefix="/hierarchy")


@hierarchy_bp.route("/")
def index():
    context = {
        "title": "Метод Аналізу Ієрархій",
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }
    return render_template("Hierarchy/index.html", **context)


@hierarchy_bp.route("/names", methods=["GET", "POST"])
def names():
    num_alternatives = int(request.args.get("num_alternatives"))
    num_criteria = int(request.args.get("num_criteria"))
    hierarchy_task = (
        request.args.get("hierarchy_task")
        if request.args.get("hierarchy_task")
        else None
    )

    # Збереження змінної у сесії
    session["num_criteria"] = num_criteria
    session["num_alternatives"] = num_alternatives
    session["hierarchy_task"] = hierarchy_task

    context = {
        "title": "Імена",
        "num_alternatives": num_alternatives,
        "num_criteria": num_criteria,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    return render_template("Hierarchy/names.html", **context)


@hierarchy_bp.route("/matrix-krit", methods=["GET", "POST"])
def matrix_krit():
    num_alternatives = int(session.get("num_alternatives"))
    num_criteria = int(session.get("num_criteria"))
    hierarchy_task = session.get("hierarchy_task")

    name_alternatives = request.form.getlist("name_alternatives")
    name_criteria = request.form.getlist("name_criteria")

    if len(name_alternatives) != len(set(name_alternatives)) or len(
        name_criteria
    ) != len(set(name_criteria)):
        context = {
            "title": "Імена",
            "num_alternatives": num_alternatives,
            "num_criteria": num_criteria,
            "name_alternatives": name_alternatives,
            "name_criteria": name_criteria,
            "error": "Імена повинні бути унікальними!",
            "name": current_user.get_name() if current_user.is_authenticated else None,
        }

        return render_template("Hierarchy/names.html", **context)

    # Збереження даних у БД
    new_record_id = add_object_to_db(db, HierarchyCriteria, names=name_criteria)

    add_object_to_db(
        db, HierarchyAlternatives, id=new_record_id, names=name_alternatives
    )

    if hierarchy_task:
        add_object_to_db(db, HierarchyTask, id=new_record_id, task=hierarchy_task)

    session["new_record_id"] = new_record_id

    context = {
        "title": "Матриця",
        "num_alternatives": num_alternatives,
        "num_criteria": num_criteria,
        "name_alternatives": name_alternatives,
        "name_criteria": name_criteria,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    return render_template("Hierarchy/matrix_krit.html", **context)


@hierarchy_bp.route("/matrix-alt", methods=["GET", "POST"])
def matrix_alt():
    new_record_id = int(session.get("new_record_id"))
    num_alternatives = int(session.get("num_alternatives"))
    num_criteria = int(session.get("num_criteria"))

    name_alternatives = HierarchyAlternatives.query.get(new_record_id).names
    name_criteria = HierarchyCriteria.query.get(new_record_id).names
    matr_krit = request.form.getlist("matrix_krit")

    # Створення списку з матриць по рівнях
    matrix_krit = do_matrix(krit=1, matrix=matr_krit, criteria=num_criteria)

    # Оцінки компонент власного вектора
    components_eigenvector = do_comp_vector(
        krit=1, criteria=num_criteria, matr=matrix_krit
    )

    # Нормалізовані оцінки вектора пріоритету
    normalized_eigenvector = do_norm_vector(
        krit=1, comp_vector=components_eigenvector, criteria=num_criteria
    )

    # Сума по стовпцям
    sum_col = do_sum_col(krit=1, matr=matrix_krit, criteria=num_criteria)

    # Добуток додатку по стовпцях і нормалізованої оцінки вектора пріоритету
    prod_col = do_prod_col(
        krit=1,
        criteria=num_criteria,
        sum_col=sum_col,
        norm_vector=normalized_eigenvector,
    )

    # Разом (Lmax)
    l_max = do_l_max(krit=1, prod_col=prod_col, criteria=num_criteria)

    # Індекс узгодженості i Відношення узгодженості
    index_consistency, relation_consistency = do_consistency(
        krit=1, l_max=l_max, criteria=num_criteria
    )

    # список для Нормалізованих оцінок вектора пріоритету (для висновку)
    lst_normalized_eigenvector = do_lst_norm_vector(
        krit=1,
        name=name_criteria,
        criteria=num_criteria,
        norm_vector=normalized_eigenvector,
    )

    # Ранжування
    ranj = do_ranj(
        krit=1, lst_norm_vector=lst_normalized_eigenvector, criteria=num_criteria
    )

    # Збереження даних у БД
    add_object_to_db(
        db,
        HierarchyCriteriaMatrix,
        id=new_record_id,
        hierarchy_criteria_id=new_record_id,
        comparison_matrix=matrix_krit,
        components_eigenvector=components_eigenvector,
        normalized_eigenvector=normalized_eigenvector,
        sum_col=sum_col,
        prod_col=prod_col,
        l_max=l_max,
        index_consistency=index_consistency,
        relation_consistency=relation_consistency,
        lst_normalized_eigenvector=lst_normalized_eigenvector,
        ranj=ranj,
    )

    session["matr_alt"] = 0

    context = {
        "id": new_record_id,
        "title": "Матриця",
        "num_alternatives": num_alternatives,
        "num_criteria": num_criteria,
        "name_alternatives": name_alternatives,
        "name_criteria": name_criteria,
        "matrix_krit": matrix_krit,
        "components_eigenvector": components_eigenvector,
        "normalized_eigenvector": normalized_eigenvector,
        "sum_col": sum_col,
        "prod_col": prod_col,
        "l_max": l_max,
        "index_consistency": index_consistency,
        "relation_consistency": relation_consistency,
        "lst_normalized_eigenvector": lst_normalized_eigenvector,
        "ranj": ranj,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    return render_template("Hierarchy/matrix_alt.html", **context)


@hierarchy_bp.route("/result/<int:method_id>", methods=["GET", "POST"])
def result(method_id=None):
    if not method_id:
        new_record_id = int(session.get("new_record_id"))
        num_alternatives = int(session.get("num_alternatives"))
        num_criteria = session.get("num_criteria")
    else:
        new_record_id = method_id
        num_alternatives = len(HierarchyAlternatives.query.get(new_record_id).names)
        num_criteria = len(HierarchyCriteria.query.get(new_record_id).names)

    name_alternatives = HierarchyAlternatives.query.get(new_record_id).names
    name_criteria = HierarchyCriteria.query.get(new_record_id).names
    matrix_krit = HierarchyCriteriaMatrix.query.get(new_record_id).comparison_matrix
    components_eigenvector = HierarchyCriteriaMatrix.query.get(
        new_record_id
    ).components_eigenvector
    normalized_eigenvector = HierarchyCriteriaMatrix.query.get(
        new_record_id
    ).normalized_eigenvector
    sum_col = HierarchyCriteriaMatrix.query.get(new_record_id).sum_col
    prod_col = HierarchyCriteriaMatrix.query.get(new_record_id).prod_col
    l_max = HierarchyCriteriaMatrix.query.get(new_record_id).l_max
    index_consistency = HierarchyCriteriaMatrix.query.get(
        new_record_id
    ).index_consistency
    relation_consistency = HierarchyCriteriaMatrix.query.get(
        new_record_id
    ).relation_consistency
    lst_normalized_eigenvector = HierarchyCriteriaMatrix.query.get(
        new_record_id
    ).lst_normalized_eigenvector
    ranj = HierarchyCriteriaMatrix.query.get(new_record_id).ranj

    try:
        hierarchy_task_record = HierarchyTask.query.get(new_record_id)
        hierarchy_task = hierarchy_task_record.task if hierarchy_task_record else None
    except Exception as e:
        print("[!] Error:", e)

    matr_alt = session.get("matr_alt")
    if matr_alt != 0:
        matr_alt = HierarchyAlternativesMatrix.query.get(new_record_id).matr_alt
    else:
        matr_alt = request.form.getlist("matrix_alt")

    # Створення списку з матриць по рівнях
    matrix_alt = do_matrix(
        num_alt=num_alternatives, matrix=matr_alt, criteria=num_criteria
    )

    # Оцінки компонент власного вектора
    components_eigenvector_alt = do_comp_vector(
        num_alt=num_alternatives, criteria=num_criteria, matr=matrix_alt
    )

    # Нормалізовані оцінки вектора пріоритету
    normalized_eigenvector_alt = do_norm_vector(
        num_alt=num_alternatives,
        comp_vector=components_eigenvector_alt,
        criteria=num_criteria,
    )

    # Сума по стовпцям
    sum_col_alt = do_sum_col(
        num_alt=num_alternatives, matr=matrix_alt, criteria=num_criteria
    )

    # Добуток додатку по стовпцях і нормалізованої оцінки вектора пріоритету
    prod_col_alt = do_prod_col(
        num_alt=num_alternatives,
        criteria=num_criteria,
        sum_col=sum_col_alt,
        norm_vector=normalized_eigenvector_alt,
    )

    # Разом (Lmax)
    l_max_alt = do_l_max(prod_col=prod_col_alt, criteria=num_criteria)

    # Індекс узгодженості i Відношення узгодженості
    index_consistency_alt, relation_consistency_alt = do_consistency(
        num_alt=num_alternatives, l_max=l_max_alt, criteria=num_criteria
    )

    # список для Нормалізованих оцінок вектора пріоритету (для висновку)
    lst_normalized_eigenvector_alt = do_lst_norm_vector(
        num_alt=num_alternatives,
        name=name_alternatives,
        criteria=num_criteria,
        norm_vector=normalized_eigenvector_alt,
    )

    # Ранжування
    ranj_alt = do_ranj(
        lst_norm_vector=lst_normalized_eigenvector_alt, criteria=num_criteria
    )

    # Глобальні пріоритети
    global_prior = do_global_prior(
        norm_vector=normalized_eigenvector,
        norm_vector_alt=normalized_eigenvector_alt,
        num_alt=num_alternatives,
    )

    # Ранжування глобальних пріоритетів

    lst_normalized_eigenvector_global = do_lst_norm_vector(
        num_alt=num_alternatives,
        name=name_alternatives,
        criteria=num_criteria,
        norm_vector=global_prior,
        g=1,
    )
    ranj_global = do_ranj(
        lst_norm_vector=lst_normalized_eigenvector_global, criteria=num_criteria, g=1
    )

    # gpt_response = generate_gpt_response_mai(hierarchy_task, name_alternatives, name_criteria,
    #                                          ranj_global) if hierarchy_task else None

    existing_record = HierarchyAlternativesMatrix.query.get(new_record_id)
    if existing_record is None:
        # Збереження даних у БД
        add_object_to_db(
            db,
            GlobalPrioritiesPlot,
            id=new_record_id,
            plot_data=generate_plot(global_prior, name_alternatives),
        )

        add_object_to_db(
            db,
            HierarchyAlternativesMatrix,
            id=new_record_id,
            criteria_id=new_record_id,
            hierarchy_alternatives_id=new_record_id,
            matr_alt=matr_alt,
            comparison_matrix=matrix_alt,
            components_eigenvector_alt=components_eigenvector_alt,
            normalized_eigenvector_alt=normalized_eigenvector_alt,
            sum_col_alt=sum_col_alt,
            prod_col_alt=prod_col_alt,
            l_max_alt=l_max_alt,
            index_consistency_alt=index_consistency_alt,
            relation_consistency_alt=relation_consistency_alt,
            lst_normalized_eigenvector_alt=lst_normalized_eigenvector_alt,
            ranj_alt=ranj_alt,
            global_prior=global_prior,
            lst_normalized_eigenvector_global=lst_normalized_eigenvector_global,
            ranj_global=ranj_global,
            global_priorities_plot_id=new_record_id,
            task_id=new_record_id if hierarchy_task else None,
        )

        if current_user.is_authenticated:
            add_object_to_db(
                db,
                Result,
                method_name="Hierarchy",
                method_id=new_record_id,
                user_id=current_user.get_id(),
            )

    generate_hierarchy_tree(
        name_criteria, name_alternatives, normalized_eigenvector, global_prior
    )

    context = {
        "title": "Результат",
        "num_alternatives": num_alternatives,
        "num_criteria": num_criteria,
        "name_alternatives": name_alternatives,
        "name_criteria": name_criteria,
        "matrix_krit": matrix_krit,
        "components_eigenvector": components_eigenvector,
        "normalized_eigenvector": normalized_eigenvector,
        "sum_col": sum_col,
        "prod_col": prod_col,
        "l_max": l_max,
        "index_consistency": index_consistency,
        "relation_consistency": relation_consistency,
        "lst_normalized_eigenvector": lst_normalized_eigenvector,
        "ranj": ranj,
        "matrix_alt": matrix_alt,
        "components_eigenvector_alt": components_eigenvector_alt,
        "normalized_eigenvector_alt": normalized_eigenvector_alt,
        "sum_col_alt": sum_col_alt,
        "prod_col_alt": prod_col_alt,
        "l_max_alt": l_max_alt,
        "index_consistency_alt": index_consistency_alt,
        "relation_consistency_alt": relation_consistency_alt,
        "lst_normalized_eigenvector_alt": lst_normalized_eigenvector_alt,
        "ranj_alt": ranj_alt,
        "global_prior": global_prior,
        "lst_normalized_eigenvector_global": lst_normalized_eigenvector_global,
        "ranj_global": ranj_global,
        "global_prior_plot": generate_plot(global_prior, name_alternatives),
        "name": current_user.get_name() if current_user.is_authenticated else None,
        "method_id": method_id,
        "task": hierarchy_task if hierarchy_task else None,
        # 'gpt_response': gpt_response
    }

    # Перевірка відношення узгодженості
    for c in range(num_criteria):
        if relation_consistency_alt[c][0] > 10:
            context["error"] = (
                f'Перегляньте свої судження у матриці Критерію "{name_criteria[c]}"'
            )
            break

    for i in range(len(relation_consistency)):
        if relation_consistency[i] > 10:
            context["error"] = "Перегляньте свої судження у матриці для критеріїв"
            break

    session["matr_alt"] = 1

    return render_template("Hierarchy/result.html", **context)
