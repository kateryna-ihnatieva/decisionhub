from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    current_app,
    Response,
)
from mymodules.mai import *
from models import *
from flask_login import current_user, login_required
from mymodules.methods import *
from mymodules.gpt_response import *
from mymodules.excel_export import HierarchyExcelExporter
from mymodules.file_upload import process_hierarchy_file
from datetime import datetime
import json

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
    # Проверяем, загружается ли черновик
    draft_id = request.args.get("draft")
    draft_data = None
    num_alternatives = 0
    num_criteria = 0
    hierarchy_task = None

    if draft_id:
        try:
            from models import Draft

            draft = Draft.query.filter_by(
                id=draft_id, user_id=current_user.get_id()
            ).first()

            if draft and draft.form_data:
                draft_data = draft.form_data
                # Восстанавливаем данные из черновика
                if draft_data.get("numAlternatives"):
                    num_alternatives = int(draft_data["numAlternatives"])
                if draft_data.get("numCriteria"):
                    num_criteria = int(draft_data["numCriteria"])
                if draft_data.get("task"):
                    hierarchy_task = draft_data["task"]
        except Exception as e:
            current_app.logger.error(f"Error loading draft: {str(e)}")
            # В случае ошибки используем значения по умолчанию
            num_alternatives = 0
            num_criteria = 0
            hierarchy_task = None
    else:
        # Если черновик не загружается, получаем данные из URL параметров
        try:
            num_alternatives = int(request.args.get("num_alternatives") or 0)
            num_criteria = int(request.args.get("num_criteria") or 0)
            hierarchy_task = request.args.get("hierarchy_task")
        except (ValueError, TypeError):
            num_alternatives = 0
            num_criteria = 0
            hierarchy_task = None

    # Збереження змінної у сесії
    session["num_criteria"] = num_criteria
    session["num_alternatives"] = num_alternatives
    session["hierarchy_task"] = hierarchy_task

    context = {
        "title": "Імена",
        "num_alternatives": num_alternatives,
        "num_criteria": num_criteria,
        "hierarchy_task": hierarchy_task,
        "name_alternatives": draft_data.get("alternatives") if draft_data else None,
        "name_criteria": draft_data.get("criteria") if draft_data else None,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    return render_template("Hierarchy/names.html", **context)


@hierarchy_bp.route("/matrix-krit", methods=["GET", "POST"])
def matrix_krit():
    # Debug: Log session data at the start
    current_app.logger.info(f"matrix_krit() called - method: {request.method}")
    current_app.logger.info(f"Session new_record_id: {session.get('new_record_id')}")
    current_app.logger.info(
        f"Session num_alternatives: {session.get('num_alternatives')}"
    )
    current_app.logger.info(f"Session num_criteria: {session.get('num_criteria')}")

    if request.method == "GET":
        # GET запрос - показываем страницу с возможностью загрузки черновика
        num_alternatives = int(session.get("num_alternatives", 0))
        num_criteria = int(session.get("num_criteria", 0))

        if num_alternatives == 0 or num_criteria == 0:
            # Если нет данных в сессии, перенаправляем на главную страницу метода
            return redirect(url_for("hierarchy.index"))

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
            except Exception as e:
                current_app.logger.error(f"Error loading draft: {str(e)}")

        # Получаем имена из сессии или черновика
        name_alternatives = session.get("name_alternatives", [])
        name_criteria = session.get("name_criteria", [])

        if draft_data:
            name_alternatives = draft_data.get("alternatives", name_alternatives)
            name_criteria = draft_data.get("criteria", name_criteria)

        context = {
            "title": "Матриця",
            "num_alternatives": num_alternatives,
            "num_criteria": num_criteria,
            "name_alternatives": name_alternatives,
            "name_criteria": name_criteria,
            "name": current_user.get_name() if current_user.is_authenticated else None,
        }

        return render_template("Hierarchy/matrix_krit.html", **context)

    # POST запрос - обработка формы
    current_app.logger.info(
        f"matrix_krit() POST - Session new_record_id: {session.get('new_record_id')}"
    )
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

    # Clean up session to avoid cookie size issues
    session.clear()

    # Сохраняем имена в сессии для возможного восстановления
    session["name_alternatives"] = name_alternatives
    session["name_criteria"] = name_criteria

    # Збереження даних у БД
    current_app.logger.info(f"Creating HierarchyCriteria with names: {name_criteria}")
    new_record_id = add_object_to_db(db, HierarchyCriteria, names=name_criteria)
    current_app.logger.info(f"Created HierarchyCriteria with ID: {new_record_id}")

    current_app.logger.info(
        f"Creating HierarchyAlternatives with ID: {new_record_id}, names: {name_alternatives}"
    )
    alternatives_id = add_object_to_db(
        db, HierarchyAlternatives, id=new_record_id, names=name_alternatives
    )
    current_app.logger.info(f"Created HierarchyAlternatives with ID: {alternatives_id}")

    if hierarchy_task:
        current_app.logger.info(
            f"Creating HierarchyTask with ID: {new_record_id}, task: {hierarchy_task}"
        )
        task_id = add_object_to_db(
            db, HierarchyTask, id=new_record_id, task=hierarchy_task
        )
        current_app.logger.info(f"Created HierarchyTask with ID: {task_id}")

    # Clean up session to avoid cookie size issues
    session.clear()
    session["new_record_id"] = new_record_id
    session["num_alternatives"] = num_alternatives
    session["num_criteria"] = num_criteria
    session["name_alternatives"] = name_alternatives
    session["name_criteria"] = name_criteria
    if hierarchy_task:
        session["hierarchy_task"] = hierarchy_task
    current_app.logger.info(f"Set session new_record_id to: {new_record_id}")
    current_app.logger.info(
        f"Session size after cleanup: {len(str(session))} characters"
    )

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
    # Debug: Log session data at the start
    current_app.logger.info(
        f"matrix_alt() called - session keys: {list(session.keys())}"
    )
    current_app.logger.info(f"Session new_record_id: {session.get('new_record_id')}")
    current_app.logger.info(
        f"Session num_alternatives: {session.get('num_alternatives')}"
    )
    current_app.logger.info(f"Session num_criteria: {session.get('num_criteria')}")

    # Проверяем, загружается ли черновик
    draft_id = request.args.get("draft")

    if draft_id and not session.get("new_record_id"):
        # Если загружается черновик, но нет new_record_id, создаем новую запись
        try:
            from models import Draft

            draft = Draft.query.filter_by(
                id=draft_id, user_id=current_user.get_id()
            ).first()

            if draft and draft.form_data:
                # Создаем новую запись в базе данных
                new_record_id = add_object_to_db(
                    db, HierarchyCriteria, names=draft.form_data.get("criteria", [])
                )
                add_object_to_db(
                    db,
                    HierarchyAlternatives,
                    id=new_record_id,
                    names=draft.form_data.get("alternatives", []),
                )

                if draft.form_data.get("task"):
                    add_object_to_db(
                        db,
                        HierarchyTask,
                        id=new_record_id,
                        task=draft.form_data["task"],
                    )

                # Устанавливаем данные в сессию
                session["new_record_id"] = new_record_id
                session["num_alternatives"] = len(
                    draft.form_data.get("alternatives", [])
                )
                session["num_criteria"] = len(draft.form_data.get("criteria", []))
                session["name_alternatives"] = draft.form_data.get("alternatives", [])
                session["name_criteria"] = draft.form_data.get("criteria", [])
                session["hierarchy_task"] = draft.form_data.get("task")

                # Сохраняем матрицу альтернатив из черновика в базу данных
                if draft.form_data.get("matrices", {}).get("alternatives"):
                    alternatives_data = draft.form_data["matrices"]["alternatives"]
                    # Преобразуем данные в формат, который ожидает база данных
                    matr_alt = []
                    for criteria_key in alternatives_data:
                        criteria_matrix = alternatives_data[criteria_key]
                        for i in range(len(criteria_matrix)):
                            for j in range(len(criteria_matrix[i])):
                                matr_alt.append(criteria_matrix[i][j] or "")

                    # Создаем запись в HierarchyAlternativesMatrix с базовыми значениями
                    add_object_to_db(
                        db,
                        HierarchyAlternativesMatrix,
                        id=new_record_id,
                        criteria_id=new_record_id,
                        hierarchy_alternatives_id=new_record_id,
                        matr_alt=matr_alt,
                        comparison_matrix=alternatives_data,
                        # Заполняем базовые поля, чтобы избежать ошибок
                        components_eigenvector_alt=[],
                        normalized_eigenvector_alt=[],
                        sum_col_alt=[],
                        prod_col_alt=[],
                        l_max_alt=[],
                        index_consistency_alt=[],
                        relation_consistency_alt=[],
                        lst_normalized_eigenvector_alt=[],
                        ranj_alt=[],
                        global_prior=[],
                        lst_normalized_eigenvector_global=[],
                        ranj_global=[],
                        global_priorities_plot_id=new_record_id,
                        task_id=new_record_id if draft.form_data.get("task") else None,
                    )
        except Exception as e:
            current_app.logger.error(f"Error creating record from draft: {str(e)}")
            flash("Помилка створення запису з чернетки", "error")
            return redirect(url_for("hierarchy.index"))

    new_record_id = int(session.get("new_record_id"))
    num_alternatives = int(session.get("num_alternatives"))
    num_criteria = int(session.get("num_criteria"))

    # Debug: Log the IDs we're working with
    current_app.logger.info(
        f"Processing hierarchy matrix_alt with new_record_id: {new_record_id}"
    )
    current_app.logger.info(
        f"Session data - num_alternatives: {num_alternatives}, num_criteria: {num_criteria}"
    )

    # Check if records exist before accessing them
    alternatives_record = HierarchyAlternatives.query.get(new_record_id)
    criteria_record = HierarchyCriteria.query.get(new_record_id)

    # Debug: Log what we found in the database
    current_app.logger.info(
        f"Database query results - alternatives_record: {alternatives_record}, criteria_record: {criteria_record}"
    )
    if alternatives_record:
        current_app.logger.info(
            f"Alternatives record ID: {alternatives_record.id}, names: {alternatives_record.names}"
        )
    if criteria_record:
        current_app.logger.info(
            f"Criteria record ID: {criteria_record.id}, names: {criteria_record.names}"
        )

    if not alternatives_record or not criteria_record:
        current_app.logger.error(
            f"Missing records - alternatives_record: {alternatives_record}, criteria_record: {criteria_record}"
        )
        flash("Error: Required data not found. Please start over.", "error")
        return redirect(url_for("hierarchy.index"))

    name_alternatives = alternatives_record.names
    name_criteria = criteria_record.names
    matr_krit = request.form.getlist("matrix_krit")

    # Если матрица критериев пустая, создаем базовую матрицу
    if not matr_krit:
        # Создаем базовую матрицу критериев с единицами на диагонали
        matrix_krit = []
        for i in range(num_criteria):
            row = []
            for j in range(num_criteria):
                if i == j:
                    row.append("1")
                else:
                    row.append("1")  # Базовое значение для недиагональных элементов
            matrix_krit.append(row)
    else:
        # Створення списку з матриць по рівнях
        # Debug: Check for Undefined values in criteria matrix from form
        print(
            f"[DEBUG] Criteria matrix from form (first 10 elements): {matr_krit[:10]}"
        )
        for i, val in enumerate(matr_krit[:10]):
            print(f"[DEBUG] Criteria element {i}: type={type(val)}, value={val}")

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

    # Проверяем, есть ли уже запись в HierarchyCriteriaMatrix с таким ID
    existing_matrix = HierarchyCriteriaMatrix.query.get(new_record_id)
    if existing_matrix:
        # Если запись уже существует, обновляем её
        existing_matrix.comparison_matrix = matrix_krit
        existing_matrix.components_eigenvector = components_eigenvector
        existing_matrix.normalized_eigenvector = normalized_eigenvector
        existing_matrix.sum_col = sum_col
        existing_matrix.prod_col = prod_col
        existing_matrix.l_max = l_max
        existing_matrix.index_consistency = index_consistency
        existing_matrix.relation_consistency = relation_consistency
        existing_matrix.lst_normalized_eigenvector = lst_normalized_eigenvector
        existing_matrix.ranj = ranj
        db.session.commit()
    else:
        # Если записи нет, создаём новую
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
        "task": session.get("hierarchy_task"),
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
        # Отримуємо дані з БД замість сесії
        alternatives_record = HierarchyAlternatives.query.get(new_record_id)
        criteria_record = HierarchyCriteria.query.get(new_record_id)

        if not alternatives_record or not criteria_record:
            flash("Данные не найдены", "error")
            return redirect(url_for("hierarchy.index"))

        num_alternatives = len(alternatives_record.names)
        num_criteria = len(criteria_record.names)

        # Встановлюємо дані в сесію для коректної роботи решти коду
        session["new_record_id"] = new_record_id
        session["num_alternatives"] = num_alternatives
        session["num_criteria"] = num_criteria

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
        hierarchy_task = None

    # Завантажуємо матрицю альтернатив з БД
    existing_alternatives_matrix = HierarchyAlternativesMatrix.query.get(new_record_id)
    if existing_alternatives_matrix and existing_alternatives_matrix.matr_alt:
        # Дані є в БД
        matr_alt = existing_alternatives_matrix.matr_alt

        # Проверяем, есть ли уже вычисленные результаты
        if (
            existing_alternatives_matrix.components_eigenvector_alt
            and existing_alternatives_matrix.normalized_eigenvector_alt
            and existing_alternatives_matrix.global_prior
        ):
            # Результаты уже вычислены, используем их
            matrix_alt = existing_alternatives_matrix.comparison_matrix
            components_eigenvector_alt = (
                existing_alternatives_matrix.components_eigenvector_alt
            )
            normalized_eigenvector_alt = (
                existing_alternatives_matrix.normalized_eigenvector_alt
            )
            sum_col_alt = existing_alternatives_matrix.sum_col_alt
            prod_col_alt = existing_alternatives_matrix.prod_col_alt
            l_max_alt = existing_alternatives_matrix.l_max_alt
            index_consistency_alt = existing_alternatives_matrix.index_consistency_alt
            relation_consistency_alt = (
                existing_alternatives_matrix.relation_consistency_alt
            )
            lst_normalized_eigenvector_alt = (
                existing_alternatives_matrix.lst_normalized_eigenvector_alt
            )
            ranj_alt = existing_alternatives_matrix.ranj_alt
            global_prior = existing_alternatives_matrix.global_prior
            lst_normalized_eigenvector_global = (
                existing_alternatives_matrix.lst_normalized_eigenvector_global
            )
            ranj_global = existing_alternatives_matrix.ranj_global

            # Пропускаем вычисления и переходим к формированию контекста
            skip_calculations = True
        else:
            skip_calculations = False
    else:
        # Даних немає в БД - проверяем форму
        if request.form.getlist("matrix_alt"):
            # Данные есть в форме - используем их для вычислений
            matr_alt = request.form.getlist("matrix_alt")
            skip_calculations = False
        else:
            # Нет данных ни в БД, ни в форме - это ошибка
            print("[ERROR] Нет данных матрицы альтернатив ни в БД, ни в форме")
            flash(
                "Неполные данные для отображения результата. Матрица альтернатив не найдена.",
                "error",
            )
            return redirect(url_for("hierarchy.index"))

    # Выполняем вычисления только если они не были выполнены ранее
    if not skip_calculations:
        # Перевіряємо розміри даних перед створенням матриці
        expected_matrix_size = num_criteria * num_alternatives * num_alternatives
        if len(matr_alt) != expected_matrix_size:
            print(f"[ERROR] Неправильный размер матрицы альтернатив!")
            print(
                f"[ERROR] Ожидается: {expected_matrix_size}, получено: {len(matr_alt)}"
            )
            print(
                f"[ERROR] num_criteria: {num_criteria}, num_alternatives: {num_alternatives}"
            )
            flash(
                f"Ошибка в данных матрицы альтернатив. Неправильный размер данных.",
                "error",
            )
            return redirect(url_for("hierarchy.index"))

        # Створення списку з матриць по рівнях
        try:
            # Debug: Check for Undefined values in alternatives matrix from form
            print(
                f"[DEBUG] Alternatives matrix from form (first 10 elements): {matr_alt[:10]}"
            )
            for i, val in enumerate(matr_alt[:10]):
                print(f"[DEBUG] Form element {i}: type={type(val)}, value={val}")

            matrix_alt = do_matrix(
                num_alt=num_alternatives, matrix=matr_alt, criteria=num_criteria
            )
            print(
                f"[DEBUG] Матрица альтернатив создана успешно: {len(matrix_alt)} критериев"
            )
        except (IndexError, ValueError) as e:
            print(f"[!] Error creating matrix_alt: {e}")
            flash("Ошибка в данных матрицы альтернатив", "error")
            return redirect(url_for("hierarchy.index"))

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
        try:
            sum_col_alt = do_sum_col(
                num_alt=num_alternatives, matr=matrix_alt, criteria=num_criteria
            )
            print(f"[DEBUG] Сумма по столбцам вычислена успешно")
        except (IndexError, ValueError) as e:
            print(f"[!] Error computing sum_col_alt: {e}")
            print(f"[DEBUG] matrix_alt structure: {len(matrix_alt)} criteria")
            for i, crit in enumerate(matrix_alt):
                print(f"[DEBUG] Criteria {i}: {len(crit)} alternatives")
            flash(
                "Ошибка при вычислении суммы по столбцам матрицы альтернатив", "error"
            )
            return redirect(url_for("hierarchy.index"))

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
            lst_norm_vector=lst_normalized_eigenvector_global,
            criteria=num_criteria,
            g=1,
        )

    # gpt_response = generate_gpt_response_mai(hierarchy_task, name_alternatives, name_criteria,
    #                                          ranj_global) if hierarchy_task else None

    existing_record = HierarchyAlternativesMatrix.query.get(new_record_id)
    if existing_record is None:
        # Збереження даних у БД
        plot_data = generate_plot(global_prior, name_alternatives)

        add_object_to_db(
            db,
            GlobalPrioritiesPlot,
            id=new_record_id,
            plot_data=plot_data,
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

    # Find result_id for this analysis
    result_id = None
    if current_user.is_authenticated:
        result = Result.query.filter_by(
            method_id=method_id, method_name="Hierarchy", user_id=current_user.get_id()
        ).first()
        if result:
            result_id = result.id

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
        "result_id": result_id,
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


@hierarchy_bp.route("/export/excel/<int:result_id>")
@login_required
def export_excel(result_id):
    """Export hierarchy analysis results to Excel file"""
    try:
        current_app.logger.info(f"Excel export requested for result_id: {result_id}")
        current_app.logger.info(
            f"Current user: {current_user.get_id() if current_user.is_authenticated else 'Not authenticated'}"
        )

        # Get the result record
        result = Result.query.get(result_id)
        current_app.logger.info(f"Found result: {result}")
        if not result:
            current_app.logger.error(f"No result found for result_id: {result_id}")
            return Response(
                "Analysis result not found", status=404, mimetype="text/plain"
            )

        # Check if user has access to this result
        if (
            result.user_id != current_user.get_id()
            and current_user.get_name() != "admin"
        ):
            return Response("Access denied", status=403, mimetype="text/plain")

        # Get analysis data from database
        method_id = result.method_id

        # Get basic data
        criteria_record = HierarchyCriteria.query.get(method_id)
        alternatives_record = HierarchyAlternatives.query.get(method_id)
        task_record = HierarchyTask.query.get(method_id)
        criteria_matrix_record = HierarchyCriteriaMatrix.query.get(method_id)
        alternatives_matrix_record = HierarchyAlternativesMatrix.query.get(method_id)

        current_app.logger.info(f"Data records found:")
        current_app.logger.info(f"  criteria_record: {criteria_record is not None}")
        current_app.logger.info(
            f"  alternatives_record: {alternatives_record is not None}"
        )
        current_app.logger.info(f"  task_record: {task_record is not None}")
        current_app.logger.info(
            f"  criteria_matrix_record: {criteria_matrix_record is not None}"
        )
        current_app.logger.info(
            f"  alternatives_matrix_record: {alternatives_matrix_record is not None}"
        )

        if not all(
            [
                criteria_record,
                alternatives_record,
                criteria_matrix_record,
                alternatives_matrix_record,
            ]
        ):
            current_app.logger.error(
                f"Incomplete analysis data for method_id: {method_id}"
            )
            return Response(
                "Incomplete analysis data", status=400, mimetype="text/plain"
            )

        # Prepare data for Excel export
        current_app.logger.info(f"Preparing analysis data:")
        current_app.logger.info(f"  method_id: {method_id}")
        current_app.logger.info(
            f"  task_description: {task_record.task if task_record else None}"
        )
        current_app.logger.info(f"  criteria_names: {criteria_record.names}")
        current_app.logger.info(f"  alternatives_names: {alternatives_record.names}")
        current_app.logger.info(
            f"  criteria_weights: {criteria_matrix_record.normalized_eigenvector}"
        )
        current_app.logger.info(
            f"  global_priorities: {alternatives_matrix_record.global_prior}"
        )
        current_app.logger.info(
            f"  criteria_matrix: {criteria_matrix_record.comparison_matrix}"
        )
        current_app.logger.info(
            f"  alternatives_matrices: {alternatives_matrix_record.comparison_matrix}"
        )
        current_app.logger.info(
            f"  criteria_eigenvector: {criteria_matrix_record.components_eigenvector}"
        )
        current_app.logger.info(
            f"  alternatives_eigenvectors: {alternatives_matrix_record.components_eigenvector_alt}"
        )
        current_app.logger.info(
            f"  criteria_consistency: ci={criteria_matrix_record.index_consistency[0]}, cr={criteria_matrix_record.relation_consistency[0]}"
        )
        current_app.logger.info(
            f"  alternatives_consistency: ci={alternatives_matrix_record.index_consistency_alt}, cr={alternatives_matrix_record.relation_consistency_alt}"
        )

        # Fix alternatives_consistency data format
        fixed_ci = [
            item[0] if isinstance(item, list) and len(item) > 0 else item
            for item in alternatives_matrix_record.index_consistency_alt
        ]
        fixed_cr = [
            item[0] if isinstance(item, list) and len(item) > 0 else item
            for item in alternatives_matrix_record.relation_consistency_alt
        ]
        current_app.logger.info(
            f"  Fixed alternatives_consistency: ci={fixed_ci}, cr={fixed_cr}"
        )

        analysis_data = {
            "method_id": method_id,
            "task_description": task_record.task if task_record else None,
            "criteria_names": criteria_record.names,
            "alternatives_names": alternatives_record.names,
            "criteria_weights": criteria_matrix_record.normalized_eigenvector,
            "global_priorities": alternatives_matrix_record.global_prior,
            "criteria_matrix": criteria_matrix_record.comparison_matrix,
            "alternatives_matrices": alternatives_matrix_record.comparison_matrix,
            "criteria_eigenvector": criteria_matrix_record.components_eigenvector,
            "alternatives_eigenvectors": alternatives_matrix_record.components_eigenvector_alt,
            "alternatives_weights": alternatives_matrix_record.normalized_eigenvector_alt,
            "criteria_consistency": {
                "ci": criteria_matrix_record.index_consistency[0],
                "cr": criteria_matrix_record.relation_consistency[0],
            },
            "alternatives_consistency": {
                "ci": fixed_ci,
                "cr": fixed_cr,
            },
        }

        # Generate Excel file
        exporter = HierarchyExcelExporter()
        workbook = exporter.generate_hierarchy_analysis_excel(analysis_data)
        excel_bytes = exporter.save_to_bytes()

        # Create filename with date and task ID
        filename = (
            f"AHP_Analysis_Task{method_id}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        )

        # Return Excel file as download
        return Response(
            excel_bytes,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(excel_bytes)),
            },
        )

    except Exception as e:
        current_app.logger.error(f"Excel export error: {str(e)}")
        return Response(
            f"Error generating Excel file: {str(e)}", status=500, mimetype="text/plain"
        )


@hierarchy_bp.route("/upload_matrix", methods=["POST"])
@login_required
def upload_matrix():
    """Handle file upload for hierarchy matrix data"""
    try:
        # Get the uploaded file
        file = request.files.get("matrix_file")
        if not file:
            return {"success": False, "error": "No file uploaded"}, 400

        # Get number of criteria and alternatives from request
        num_criteria = request.form.get("num_criteria")
        num_alternatives = request.form.get("num_alternatives")

        if not num_criteria or not num_alternatives:
            return {
                "success": False,
                "error": "Number of criteria and alternatives not provided",
            }, 400

        try:
            num_criteria = int(num_criteria)
            num_alternatives = int(num_alternatives)
        except ValueError:
            return {
                "success": False,
                "error": "Invalid number of criteria or alternatives",
            }, 400

        # Process the uploaded file for hierarchy analysis
        result = process_hierarchy_file(file, num_criteria, num_alternatives)

        if result["success"]:
            return {
                "success": True,
                "criteria_names": result["criteria_names"],
                "alternatives_names": result["alternatives_names"],
                "criteria_matrix": result["criteria_matrix"],
                "alternatives_matrices": result["alternatives_matrices"],
            }
        else:
            return {"success": False, "error": result["error"]}, 400

    except Exception as e:
        current_app.logger.error(f"File upload error: {str(e)}")
        return {"success": False, "error": f"Upload failed: {str(e)}"}, 500


@hierarchy_bp.route("/result_from_file", methods=["POST"])
@login_required
def result_from_file():
    """Process hierarchy analysis from uploaded file data"""
    try:
        # Get data from form
        criteria_names = request.form.get("criteria_names")
        alternatives_names = request.form.get("alternatives_names")
        criteria_matrix_json = request.form.get("criteria_matrix")
        alternatives_matrices_json = request.form.get("alternatives_matrices")

        if not all(
            [
                criteria_names,
                alternatives_names,
                criteria_matrix_json,
                alternatives_matrices_json,
            ]
        ):
            flash("Missing required data from file upload", "error")
            return redirect(url_for("hierarchy.index"))

        # Parse JSON data
        try:
            print(
                f"DEBUG: Raw criteria_names from form: {criteria_names}, type: {type(criteria_names)}"
            )
            print(
                f"DEBUG: Raw alternatives_names from form: {alternatives_names}, type: {type(alternatives_names)}"
            )
            print(
                f"DEBUG: Raw criteria_matrix_json from form: {criteria_matrix_json}, type: {type(criteria_matrix_json)}"
            )
            print(
                f"DEBUG: Raw alternatives_matrices_json from form: {alternatives_matrices_json}, type: {type(alternatives_matrices_json)}"
            )

            criteria_names = json.loads(criteria_names)
            alternatives_names = json.loads(alternatives_names)
            criteria_matrix = json.loads(criteria_matrix_json)
            alternatives_matrices = json.loads(alternatives_matrices_json)

            print(
                f"DEBUG: After json.loads - criteria_names: {criteria_names}, type: {type(criteria_names)}"
            )
            print(
                f"DEBUG: After json.loads - alternatives_names: {alternatives_names}, type: {type(alternatives_names)}"
            )
            print(
                f"DEBUG: After json.loads - criteria_matrix: {criteria_matrix}, type: {type(criteria_matrix)}"
            )
            print(
                f"DEBUG: After json.loads - alternatives_matrices: {alternatives_matrices}, type: {type(alternatives_matrices)}"
            )

            # Ensure they are lists, not tuples
            if isinstance(criteria_names, tuple):
                print(f"DEBUG: Converting criteria_names from tuple to list")
                criteria_names = list(criteria_names)
            if isinstance(alternatives_names, tuple):
                print(f"DEBUG: Converting alternatives_names from tuple to list")
                alternatives_names = list(alternatives_names)
            if isinstance(criteria_matrix, tuple):
                print(f"DEBUG: Converting criteria_matrix from tuple to list")
                criteria_matrix = list(criteria_matrix)
            if isinstance(alternatives_matrices, tuple):
                print(f"DEBUG: Converting alternatives_matrices from tuple to list")
                alternatives_matrices = list(alternatives_matrices)

            print(
                f"DEBUG: Final types - criteria_names: {type(criteria_names)}, alternatives_names: {type(alternatives_names)}"
            )
            print(
                f"DEBUG: Final types - criteria_matrix: {type(criteria_matrix)}, alternatives_matrices: {type(alternatives_matrices)}"
            )

            # Convert all matrix elements to float to ensure proper data types
            criteria_matrix = [[float(x) for x in row] for row in criteria_matrix]
            alternatives_matrices = [
                [[float(x) for x in row] for row in matrix]
                for matrix in alternatives_matrices
            ]

            print(
                f"DEBUG: After float conversion - criteria_matrix sample: {criteria_matrix[0][:3]}"
            )
            print(
                f"DEBUG: After float conversion - alternatives_matrices sample: {alternatives_matrices[0][0][:3]}"
            )

        except json.JSONDecodeError:
            flash("Invalid matrix data format", "error")
            return redirect(url_for("hierarchy.index"))

        # Validate data
        if len(criteria_names) != len(criteria_matrix) or len(criteria_names) != len(
            criteria_matrix[0]
        ):
            flash("Invalid criteria matrix dimensions", "error")
            return redirect(url_for("hierarchy.index"))

        if len(alternatives_names) != len(alternatives_matrices[0]) or len(
            alternatives_names
        ) != len(alternatives_matrices[0][0]):
            flash("Invalid alternatives matrix dimensions", "error")
            return redirect(url_for("hierarchy.index"))

        # Create hierarchy task first to get a unique ID
        task_id = add_object_to_db(
            db,
            HierarchyTask,
            task=f"Hierarchy analysis with {len(criteria_names)} criteria and {len(alternatives_names)} alternatives",
        )
        task = HierarchyTask.query.get(task_id)

        # Use the same ID for all related records
        common_id = task_id

        # Save criteria with the same ID
        criteria_id = add_object_to_db(
            db, HierarchyCriteria, id=common_id, names=criteria_names
        )

        # Save alternatives with the same ID
        alternatives_id = add_object_to_db(
            db, HierarchyAlternatives, id=common_id, names=alternatives_names
        )

        # Process criteria matrix
        # Convert numeric matrix to string matrix and flatten for do_matrix
        criteria_matrix_str = []
        for row in criteria_matrix:
            str_row = []
            for cell in row:
                if isinstance(cell, (int, float)):
                    str_row.append(str(cell))
                else:
                    str_row.append(str(cell))
            criteria_matrix_str.append(str_row)

        # Flatten the 2D matrix to 1D list for do_matrix
        criteria_matrix_flat = []
        for row in criteria_matrix_str:
            criteria_matrix_flat.extend(row)

        # Debug: Check for Undefined values in criteria matrix
        print(
            f"[DEBUG] Criteria matrix flat (first 10 elements): {criteria_matrix_flat[:10]}"
        )
        for i, val in enumerate(criteria_matrix_flat[:10]):
            print(f"[DEBUG] Element {i}: type={type(val)}, value={val}")

        matrix_krit = do_matrix(
            krit=1, matrix=criteria_matrix_flat, criteria=len(criteria_names)
        )
        comp_vector_krit = do_comp_vector(
            krit=1, criteria=len(criteria_names), matr=matrix_krit
        )
        norm_vector_krit = do_norm_vector(
            krit=1, comp_vector=comp_vector_krit, criteria=len(criteria_names)
        )
        sum_col_krit = do_sum_col(
            krit=1, matr=matrix_krit, criteria=len(criteria_names)
        )
        prod_col_krit = do_prod_col(
            krit=1,
            criteria=len(criteria_names),
            sum_col=sum_col_krit,
            norm_vector=norm_vector_krit,
        )
        l_max_krit = do_l_max(
            krit=1, prod_col=prod_col_krit, criteria=len(criteria_names)
        )
        index_consistency_krit, relation_consistency_krit = do_consistency(
            krit=1, l_max=l_max_krit, criteria=len(criteria_names)
        )

        lst_norm_vector_krit = do_lst_norm_vector(
            krit=1,
            name=criteria_names,
            criteria=len(criteria_names),
            norm_vector=norm_vector_krit,
        )
        ranj_krit = do_ranj(krit=1, lst_norm_vector=lst_norm_vector_krit)

        # Save criteria matrix result
        add_object_to_db(
            db,
            HierarchyCriteriaMatrix,
            id=common_id,
            hierarchy_criteria_id=common_id,
            comparison_matrix=matrix_krit,
            components_eigenvector=comp_vector_krit,
            normalized_eigenvector=norm_vector_krit,
            sum_col=sum_col_krit,
            prod_col=prod_col_krit,
            l_max=l_max_krit,
            index_consistency=index_consistency_krit,
            relation_consistency=relation_consistency_krit,
            lst_normalized_eigenvector=lst_norm_vector_krit,
            ranj=ranj_krit,
        )

        # Create plot first
        plot_id = add_object_to_db(db, GlobalPrioritiesPlot, id=common_id, plot_data=[])

        # Process alternatives matrices
        alternatives_matrices_results = []
        for i, alt_matrix in enumerate(alternatives_matrices):
            # Convert numeric matrix to string matrix and flatten for do_matrix
            alt_matrix_str = []
            for row in alt_matrix:
                str_row = []
                for cell in row:
                    if isinstance(cell, (int, float)):
                        str_row.append(str(cell))
                    else:
                        str_row.append(str(cell))
                alt_matrix_str.append(str_row)

            # Flatten the 2D matrix to 1D list for do_matrix
            alt_matrix_flat = []
            for row in alt_matrix_str:
                alt_matrix_flat.extend(row)

            # Debug: Check for Undefined values in alternatives matrix
            print(
                f"[DEBUG] Alternatives matrix {i} flat (first 10 elements): {alt_matrix_flat[:10]}"
            )
            for j, val in enumerate(alt_matrix_flat[:10]):
                print(
                    f"[DEBUG] Alt matrix {i}, element {j}: type={type(val)}, value={val}"
                )

            matrix_alt = do_matrix(
                krit=0,
                matrix=alt_matrix_flat,
                criteria=1,
                num_alt=len(alternatives_names),
            )
            comp_vector_alt = do_comp_vector(
                krit=0, criteria=1, matr=matrix_alt, num_alt=len(alternatives_names)
            )
            norm_vector_alt = do_norm_vector(
                krit=0,
                comp_vector=comp_vector_alt,
                criteria=1,
                num_alt=len(alternatives_names),
            )
            sum_col_alt = do_sum_col(
                krit=0, matr=matrix_alt, criteria=1, num_alt=len(alternatives_names)
            )
            prod_col_alt = do_prod_col(
                krit=0,
                criteria=1,
                sum_col=sum_col_alt,
                norm_vector=norm_vector_alt,
                num_alt=len(alternatives_names),
            )
            l_max_alt = do_l_max(krit=0, prod_col=prod_col_alt, criteria=1)
            index_consistency_alt, relation_consistency_alt = do_consistency(
                krit=0, l_max=l_max_alt, criteria=1, num_alt=len(alternatives_names)
            )
            lst_norm_vector_alt = do_lst_norm_vector(
                krit=0,
                name=alternatives_names,
                criteria=1,
                norm_vector=norm_vector_alt,
                num_alt=len(alternatives_names),
            )
            ranj_alt = do_ranj(krit=0, lst_norm_vector=lst_norm_vector_alt, criteria=1)

            # Save alternatives matrix result
            alt_matrix_id = add_object_to_db(
                db,
                HierarchyAlternativesMatrix,
                id=common_id,
                criteria_id=common_id,
                hierarchy_alternatives_id=common_id,
                matr_alt=alt_matrix_flat,
                comparison_matrix=matrix_alt,
                components_eigenvector_alt=comp_vector_alt,
                normalized_eigenvector_alt=norm_vector_alt,
                sum_col_alt=sum_col_alt,
                prod_col_alt=prod_col_alt,
                l_max_alt=l_max_alt,
                index_consistency_alt=index_consistency_alt,
                relation_consistency_alt=relation_consistency_alt,
                lst_normalized_eigenvector_alt=lst_norm_vector_alt,
                ranj_alt=ranj_alt,
                global_prior=[],
                lst_normalized_eigenvector_global=[],
                ranj_global=[],
                global_priorities_plot_id=plot_id,
                task_id=common_id,
            )
            alt_matrix_result = HierarchyAlternativesMatrix.query.get(alt_matrix_id)
            alternatives_matrices_results.append(alt_matrix_result)

        # Calculate global priorities
        # Collect all normalized vectors for alternatives
        norm_vectors_alt = []
        for i, alt_result in enumerate(alternatives_matrices_results):
            print(f"[DEBUG] Processing alt_result {i}")
            print(
                f"[DEBUG] alt_result.normalized_eigenvector_alt: {alt_result.normalized_eigenvector_alt}"
            )
            print(
                f"[DEBUG] Length: {len(alt_result.normalized_eigenvector_alt) if alt_result.normalized_eigenvector_alt else 0}"
            )

            # Extract the normalized vector for this criterion
            if (
                alt_result.normalized_eigenvector_alt
                and len(alt_result.normalized_eigenvector_alt) > 0
            ):
                norm_vector = alt_result.normalized_eigenvector_alt[0]
            else:
                norm_vector = []
            norm_vectors_alt.append(norm_vector)

        ranj_global = do_global_prior(
            norm_vector=norm_vector_krit,
            norm_vector_alt=norm_vectors_alt,
            num_alt=len(alternatives_names),
        )
        lst_norm_vector_global = do_lst_norm_vector(
            krit=0,
            name=alternatives_names,
            criteria=1,
            norm_vector=ranj_global,
            num_alt=len(alternatives_names),
            g=1,
        )
        ranj_global_final = do_ranj(
            krit=0, lst_norm_vector=lst_norm_vector_global, criteria=1, g=1
        )

        # Generate plots
        plot_criteria = generate_plot(ranj_krit, criteria_names, "Criteria Priorities")
        plot_alternatives = []
        for i, alt_result in enumerate(alternatives_matrices_results):
            alt_plot = generate_plot(
                alt_result.ranj_alt,
                alternatives_names,
                f"Alternatives Priorities (Criterion {i+1})",
            )
            plot_alternatives.append(alt_plot)

        # Update plot data
        plot_record = GlobalPrioritiesPlot.query.get(plot_id)
        if plot_record:
            plot_record.plot_data = plot_criteria
            db.session.commit()

        # Skip saving individual alternative plots for now
        # for i, alt_plot in enumerate(plot_alternatives):
        #     add_object_to_db(
        #         db,
        #         HierarchyAlternativesMatrix,
        #         task_id=task.id,
        #         plot_data=alt_plot,
        #     )

        # Generate hierarchy tree
        tree_data = generate_hierarchy_tree(
            criteria_names, alternatives_names, norm_vector_krit, ranj_global
        )

        # Save result
        try:
            result = Result(
                method_name="hierarchy",
                method_id=common_id,
                user_id=current_user.get_id(),
            )
            db.session.add(result)
            db.session.commit()
            result_id = result.id
        except Exception as e:
            current_app.logger.error(f"Error creating result: {str(e)}")
            result_id = add_object_to_db(
                db,
                Result,
                method_name="hierarchy",
                method_id=common_id,
                user_id=current_user.get_id(),
            )
            result = Result.query.get(result_id)

        # Render results page
        return render_template(
            "Hierarchy/result.html",
            title="Результат",
            task=task,
            num_criteria=len(criteria_names),
            num_alternatives=len(alternatives_names),
            name_criteria=criteria_names,
            name_alternatives=alternatives_names,
            matrix_krit=matrix_krit,
            components_eigenvector=comp_vector_krit,
            normalized_eigenvector=norm_vector_krit,
            sum_col=sum_col_krit,
            prod_col=prod_col_krit,
            l_max=l_max_krit,
            index_consistency=index_consistency_krit,
            relation_consistency=relation_consistency_krit,
            lst_normalized_eigenvector=lst_norm_vector_krit,
            ranj=ranj_krit,
            matrix_alt=[alt.comparison_matrix for alt in alternatives_matrices_results],
            components_eigenvector_alt=[
                (
                    alt.components_eigenvector_alt[0]
                    if alt.components_eigenvector_alt
                    and len(alt.components_eigenvector_alt) > 0
                    else []
                )
                for alt in alternatives_matrices_results
            ],
            normalized_eigenvector_alt=[
                (
                    alt.normalized_eigenvector_alt[0]
                    if alt.normalized_eigenvector_alt
                    and len(alt.normalized_eigenvector_alt) > 0
                    else []
                )
                for alt in alternatives_matrices_results
            ],
            sum_col_alt=[
                alt.sum_col_alt[0] if alt.sum_col_alt else []
                for alt in alternatives_matrices_results
            ],
            prod_col_alt=[
                alt.prod_col_alt[0] if alt.prod_col_alt else []
                for alt in alternatives_matrices_results
            ],
            l_max_alt=[
                alt.l_max_alt[0] if alt.l_max_alt else []
                for alt in alternatives_matrices_results
            ],
            index_consistency_alt=[
                alt.index_consistency_alt[0] if alt.index_consistency_alt else []
                for alt in alternatives_matrices_results
            ],
            relation_consistency_alt=[
                alt.relation_consistency_alt[0] if alt.relation_consistency_alt else []
                for alt in alternatives_matrices_results
            ],
            lst_normalized_eigenvector_alt=[
                alt.lst_normalized_eigenvector_alt
                for alt in alternatives_matrices_results
            ],
            ranj_alt=[alt.ranj_alt for alt in alternatives_matrices_results],
            global_prior=[round(x, 3) for x in ranj_global],
            lst_normalized_eigenvector_global=lst_norm_vector_global,
            ranj_global=ranj_global_final,
            global_prior_plot=plot_criteria,
            result=result,
            result_id=result.id,
            method_id=common_id,
        )

    except Exception as e:
        current_app.logger.error(f"Error processing file data: {str(e)}")
        flash(f"Error processing file data: {str(e)}", "error")
        return redirect(url_for("hierarchy.index"))
