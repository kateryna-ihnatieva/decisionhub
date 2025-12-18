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

    # Always create a task, even if no description provided
    task_description = (
        hierarchy_task
        if hierarchy_task
        else f"Hierarchy analysis with {num_criteria} criteria and {num_alternatives} alternatives"
    )
    current_app.logger.info(
        f"Creating HierarchyTask with ID: {new_record_id}, task: {task_description}"
    )
    task_id = add_object_to_db(db, HierarchyTask, task=task_description)
    current_app.logger.info(f"Created HierarchyTask with ID: {task_id}")

    # Clean up specific session keys to avoid cookie size issues
    # Keep user authentication data intact
    keys_to_remove = [
        key
        for key in session.keys()
        if key.startswith(("hierarchy_", "matrix_", "alt_", "crit_"))
    ]
    for key in keys_to_remove:
        session.pop(key, None)

    session["new_record_id"] = new_record_id
    session["num_alternatives"] = num_alternatives
    session["num_criteria"] = num_criteria
    session["name_alternatives"] = name_alternatives
    session["name_criteria"] = name_criteria
    session["task_id"] = task_id  # Always save task_id
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
        # Check for invalid values in criteria matrix from form
        if any(val in ["", None, "undefined", "Undefined"] for val in matr_krit[:10]):
            print(f"[ERROR] Invalid values found in criteria matrix")
            flash("Invalid criteria matrix data", "error")
            return redirect(url_for("hierarchy.index"))

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
def result(method_id=None, file_data=None):
    current_app.logger.info(
        f"[DEBUG] result() called with method_id={method_id}, file_data={file_data is not None}"
    )

    # Check if we have file data in session (from result_from_file redirect)
    if (
        not file_data
        and session.get("file_criteria_matrix")
        and session.get("file_alternatives_matrices")
    ):
        file_data = {
            "criteria_names": json.dumps(session.get("name_criteria", [])),
            "alternatives_names": json.dumps(session.get("name_alternatives", [])),
            "criteria_matrix": session.get("file_criteria_matrix"),
            "alternatives_matrices": session.get("file_alternatives_matrices"),
        }
        # Clear file data from session after processing
        session.pop("file_criteria_matrix", None)
        session.pop("file_alternatives_matrices", None)

    # If file_data is provided, process it first
    if file_data:
        try:
            current_app.logger.info(
                f"[DEBUG] Processing file_data in result function: {file_data}"
            )
            # Parse JSON data from file
            criteria_names = json.loads(file_data["criteria_names"])
            alternatives_names = json.loads(file_data["alternatives_names"])
            criteria_matrix = json.loads(file_data["criteria_matrix"])
            current_app.logger.info(f"[DEBUG] Parsed criteria_names: {criteria_names}")
            current_app.logger.info(
                f"[DEBUG] Parsed alternatives_names: {alternatives_names}"
            )
            current_app.logger.info(
                f"[DEBUG] Parsed criteria_matrix: {criteria_matrix}"
            )
            alternatives_matrices = json.loads(file_data["alternatives_matrices"])
            current_app.logger.info(
                f"[DEBUG] Parsed alternatives_matrices: {alternatives_matrices}, type: {type(alternatives_matrices)}"
            )

            # Ensure they are lists, not tuples
            if isinstance(criteria_names, tuple):
                criteria_names = list(criteria_names)
            if isinstance(alternatives_names, tuple):
                alternatives_names = list(alternatives_names)
            if isinstance(criteria_matrix, tuple):
                criteria_matrix = list(criteria_matrix)
            if isinstance(alternatives_matrices, tuple):
                alternatives_matrices = list(alternatives_matrices)

            # Convert all matrix elements to float to ensure proper data types
            criteria_matrix = [[float(x) for x in row] for row in criteria_matrix]

            # Fix nested structure issue - alternatives_matrices from file has extra nesting level
            if (
                alternatives_matrices
                and len(alternatives_matrices) > 0
                and isinstance(alternatives_matrices[0][0][0], list)
            ):
                # Data from file has structure [[[matrix1]], [[matrix2]], ...] - need to flatten
                alternatives_matrices = [matrix[0] for matrix in alternatives_matrices]

            alternatives_matrices = [
                [[float(x) for x in row] for row in matrix]
                for matrix in alternatives_matrices
            ]

            # Validate data
            if not all(
                [
                    criteria_names,
                    alternatives_names,
                    criteria_matrix,
                    alternatives_matrices,
                ]
            ):
                flash("Missing required data from file upload", "error")
                return redirect(url_for("hierarchy.index"))

            # Create hierarchy task with method_id as its ID
            # Use task from session if available, otherwise use default
            hierarchy_task = session.get("hierarchy_task")
            task_description = (
                hierarchy_task
                if hierarchy_task
                else f"Hierarchy analysis with {len(criteria_names)} criteria and {len(alternatives_names)} alternatives"
            )
            current_app.logger.info(
                f"[DEBUG] Creating HierarchyTask with id={method_id}, task='{task_description}'"
            )
            task_id = add_object_to_db(
                db,
                HierarchyTask,
                id=method_id,
                task=task_description,
            )
            current_app.logger.info(
                f"[DEBUG] Created HierarchyTask with task_id={task_id}"
            )
            task = HierarchyTask.query.get(task_id)
            current_app.logger.info(f"[DEBUG] Retrieved HierarchyTask: {task}")

            # Save criteria and alternatives with method_id as their ID
            criteria_id = add_object_to_db(
                db, HierarchyCriteria, id=method_id, names=criteria_names
            )
            alternatives_id = add_object_to_db(
                db, HierarchyAlternatives, id=method_id, names=alternatives_names
            )

            # Use method_id as the common reference ID
            common_id = method_id

            current_app.logger.info(
                f"[DEBUG] File upload - criteria_id: {criteria_id}, alternatives_id: {alternatives_id}, common_id: {common_id}, method_id: {method_id}"
            )

            # Process criteria matrix - keep as numbers, don't convert to strings
            # Flatten the 2D matrix to 1D list for do_matrix
            criteria_matrix_flat = []
            for row in criteria_matrix:
                criteria_matrix_flat.extend(
                    [str(x) for x in row]
                )  # Convert to strings only for do_matrix

            # Check for invalid values in criteria matrix
            if any(
                val in ["", None, "undefined", "Undefined"]
                for val in criteria_matrix_flat[:10]
            ):
                print(f"[ERROR] Invalid values found in criteria matrix")
                flash("Invalid criteria matrix data", "error")
                return redirect(url_for("hierarchy.index"))

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
                norm_vector=norm_vector_krit,
                criteria=len(criteria_names),
            )
            ranj_krit = do_ranj(krit=1, lst_norm_vector=lst_norm_vector_krit)

            # Create HierarchyCriteriaMatrix record for export functionality
            current_app.logger.info(
                f"[DEBUG] Creating HierarchyCriteriaMatrix with id={common_id}, hierarchy_criteria_id={criteria_id}"
            )
            criteria_matrix_id = add_object_to_db(
                db,
                HierarchyCriteriaMatrix,
                id=common_id,
                hierarchy_criteria_id=criteria_id,
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
            current_app.logger.info(
                f"[DEBUG] Created HierarchyCriteriaMatrix with ID: {criteria_matrix_id}"
            )

            # Create plot first
            plot_id = add_object_to_db(db, GlobalPrioritiesPlot, plot_data=[])

            # Process alternatives matrices - collect all data and create single record
            current_app.logger.info(
                f"[DEBUG] Starting to process alternatives_matrices: {alternatives_matrices}"
            )
            all_matrices_alt = []
            all_comp_vectors_alt = []
            all_norm_vectors_alt = []
            all_sum_cols_alt = []
            all_prod_cols_alt = []
            all_l_maxs_alt = []
            all_index_consistency_alt = []
            all_relation_consistency_alt = []
            all_lst_norm_vectors_alt = []
            all_ranjs_alt = []
            all_matr_alt_flat = []

            # Flatten all alternatives matrices into a single list
            all_alt_matrices_flat = []
            for i, alt_matrix in enumerate(alternatives_matrices):
                current_app.logger.info(
                    f"[DEBUG] Processing alternatives matrix {i + 1}/{len(alternatives_matrices)}: {alt_matrix}, type: {type(alt_matrix)}"
                )
                current_app.logger.info(
                    f"[DEBUG] Matrix structure check - is list: {isinstance(alt_matrix, list)}, length: {len(alt_matrix) if isinstance(alt_matrix, list) else 'N/A'}"
                )

                # Flatten the 2D matrix to 1D list
                alt_matrix_flat = []
                for row in alt_matrix:
                    alt_matrix_flat.extend([str(x) for x in row])

                # Check for invalid values in alternatives matrix
                if not alt_matrix_flat or any(
                    val in ["", None, "undefined", "Undefined"]
                    for val in alt_matrix_flat
                ):
                    print(f"[ERROR] Invalid values found in alternatives matrix {i}")
                    flash("Invalid matrix data detected", "error")
                    return redirect(url_for("hierarchy.index"))

                all_alt_matrices_flat.extend(alt_matrix_flat)

            # Process all alternatives matrices at once
            matrix_alt = do_matrix(
                krit=0,
                matrix=all_alt_matrices_flat,
                criteria=len(alternatives_matrices),
                num_alt=len(alternatives_names),
            )

            comp_vector_alt = do_comp_vector(
                krit=0,
                criteria=len(alternatives_matrices),
                matr=matrix_alt,
                num_alt=len(alternatives_names),
            )
            norm_vector_alt = do_norm_vector(
                krit=0,
                comp_vector=comp_vector_alt,
                criteria=len(alternatives_matrices),
                num_alt=len(alternatives_names),
            )
            sum_col_alt = do_sum_col(
                krit=0,
                matr=matrix_alt,
                criteria=len(alternatives_matrices),
                num_alt=len(alternatives_names),
            )
            prod_col_alt = do_prod_col(
                krit=0,
                criteria=len(alternatives_matrices),
                num_alt=len(alternatives_names),
                sum_col=sum_col_alt,
                norm_vector=norm_vector_alt,
            )
            l_max_alt = do_l_max(
                krit=0, prod_col=prod_col_alt, criteria=len(alternatives_matrices)
            )
            index_consistency_alt, relation_consistency_alt = do_consistency(
                krit=0,
                l_max=l_max_alt,
                criteria=len(alternatives_matrices),
                num_alt=len(alternatives_names),
            )
            lst_norm_vector_alt = do_lst_norm_vector(
                krit=0,
                name=alternatives_names,
                norm_vector=norm_vector_alt,
                criteria=len(alternatives_matrices),
                num_alt=len(alternatives_names),
            )
            ranj_alt = do_ranj(
                krit=0,
                lst_norm_vector=lst_norm_vector_alt,
                criteria=len(alternatives_matrices),
                g=0,
            )

            # Store results
            all_matrices_alt = matrix_alt
            all_comp_vectors_alt = comp_vector_alt
            all_norm_vectors_alt = norm_vector_alt
            all_sum_cols_alt = sum_col_alt
            all_prod_cols_alt = prod_col_alt
            all_l_maxs_alt = l_max_alt
            all_index_consistency_alt = index_consistency_alt
            all_relation_consistency_alt = relation_consistency_alt
            all_lst_norm_vectors_alt = lst_norm_vector_alt
            all_ranjs_alt = ranj_alt
            all_matr_alt_flat = all_alt_matrices_flat

            # Create single HierarchyAlternativesMatrix record with all data
            try:
                current_app.logger.info(
                    f"[DEBUG] Creating HierarchyAlternativesMatrix with id={common_id}, criteria_id={criteria_id}, hierarchy_alternatives_id={alternatives_id}"
                )
                alt_matrix_id = add_object_to_db(
                    db,
                    HierarchyAlternativesMatrix,
                    id=common_id,
                    criteria_id=criteria_id,
                    hierarchy_alternatives_id=alternatives_id,
                    matr_alt=all_matr_alt_flat,
                    comparison_matrix=all_matrices_alt,
                    components_eigenvector_alt=all_comp_vectors_alt,
                    normalized_eigenvector_alt=all_norm_vectors_alt,
                    sum_col_alt=all_sum_cols_alt,
                    prod_col_alt=all_prod_cols_alt,
                    l_max_alt=all_l_maxs_alt,
                    index_consistency_alt=all_index_consistency_alt,
                    relation_consistency_alt=all_relation_consistency_alt,
                    lst_normalized_eigenvector_alt=all_lst_norm_vectors_alt,
                    ranj_alt=all_ranjs_alt,
                    global_prior=[],
                    lst_normalized_eigenvector_global=[],
                    ranj_global=[],
                    global_priorities_plot_id=plot_id,
                    task_id=task_id,
                )
                current_app.logger.info(
                    f"[DEBUG] alt_matrix_id: {alt_matrix_id}, type: {type(alt_matrix_id)}"
                )
                alt_matrix_result = HierarchyAlternativesMatrix.query.get(alt_matrix_id)
                current_app.logger.info(
                    f"[DEBUG] alt_matrix_result: {alt_matrix_result}"
                )
                alternatives_matrices_results = [
                    alt_matrix_result
                ]  # Single record containing all matrices
                current_app.logger.info(
                    f"[DEBUG] alternatives_matrices_results: {alternatives_matrices_results}"
                )
            except Exception as e:
                print(
                    f"[ERROR] Failed to create HierarchyAlternativesMatrix record: {str(e)}"
                )
                flash("Failed to save analysis data", "error")
                return redirect(url_for("hierarchy.index"))

            # Calculate global priorities
            norm_vectors_alt = []
            alt_result = alternatives_matrices_results[
                0
            ]  # Single record containing all matrices

            # Extract normalized vectors for each criterion
            current_app.logger.info(
                f"[DEBUG] Processing normalized_eigenvector_alt: {alt_result.normalized_eigenvector_alt}"
            )
            current_app.logger.info(f"[DEBUG] alt_result type: {type(alt_result)}")
            current_app.logger.info(
                f"[DEBUG] alt_result.normalized_eigenvector_alt type: {type(alt_result.normalized_eigenvector_alt)}"
            )
            for i, norm_vector in enumerate(alt_result.normalized_eigenvector_alt):
                current_app.logger.info(
                    f"[DEBUG] Processing norm_vector[{i}]: {norm_vector}, type: {type(norm_vector)}"
                )

                # Handle different data structures for normalized vectors
                if isinstance(norm_vector, (int, float)):
                    # If it's a single number, wrap it in a list
                    current_app.logger.info(
                        f"[DEBUG] norm_vector[{i}] is single value: {norm_vector}"
                    )
                    norm_vectors_alt.append([norm_vector])
                elif isinstance(norm_vector, list) and len(norm_vector) > 0:
                    # If it's a list, check if it contains nested lists or dictionaries
                    if isinstance(norm_vector[0], list):
                        # Nested list structure - extract the first element
                        current_app.logger.info(
                            f"[DEBUG] norm_vector[{i}] is nested list with length {len(norm_vector)}"
                        )
                        criterion_vector = norm_vector[0]
                    elif isinstance(norm_vector[0], dict):
                        # List of dictionaries - extract values in order
                        current_app.logger.info(
                            f"[DEBUG] norm_vector[{i}] is list of dictionaries with length {len(norm_vector)}"
                        )
                        # Get the first dictionary and extract values in the order of alternatives
                        first_dict = norm_vector[0]
                        criterion_vector = [
                            first_dict.get(alt_name, 0.0)
                            for alt_name in alternatives_names
                        ]
                    else:
                        # Flat list structure
                        current_app.logger.info(
                            f"[DEBUG] norm_vector[{i}] is flat list with length {len(norm_vector)}"
                        )
                        criterion_vector = norm_vector
                    current_app.logger.info(
                        f"[DEBUG] criterion_vector[{i}]: {criterion_vector}"
                    )
                    norm_vectors_alt.append(criterion_vector)
                elif isinstance(norm_vector, dict):
                    # Single dictionary - extract values in order
                    current_app.logger.info(
                        f"[DEBUG] norm_vector[{i}] is single dictionary: {norm_vector}"
                    )
                    criterion_vector = [
                        norm_vector.get(alt_name, 0.0)
                        for alt_name in alternatives_names
                    ]
                    current_app.logger.info(
                        f"[DEBUG] criterion_vector[{i}]: {criterion_vector}"
                    )
                    norm_vectors_alt.append(criterion_vector)
                else:
                    current_app.logger.warning(
                        f"[WARNING] Empty or invalid normalized vector for criterion {i}: {norm_vector}"
                    )
                    norm_vectors_alt.append([])

            current_app.logger.info(
                f"[DEBUG] About to call do_global_prior with norm_vector_krit: {norm_vector_krit}"
            )
            current_app.logger.info(f"[DEBUG] norm_vectors_alt: {norm_vectors_alt}")
            current_app.logger.info(f"[DEBUG] num_alt: {len(alternatives_names)}")

            global_prior = do_global_prior(
                norm_vector=norm_vector_krit,
                norm_vector_alt=norm_vectors_alt,
                num_alt=len(alternatives_names),
            )

            # Create ranking string from global priorities
            # Create a dictionary mapping alternatives to their priorities
            alt_priorities = {}
            for i, alt_name in enumerate(alternatives_names):
                if i < len(global_prior):
                    alt_priorities[alt_name] = global_prior[i]

            # Sort by priority (descending)
            sorted_alternatives = sorted(
                alt_priorities.items(), key=lambda x: x[1], reverse=True
            )

            # Create ranking string
            ranj_global = []
            if sorted_alternatives:
                ranj_str = ""
                for i, (alt_name, priority) in enumerate(sorted_alternatives):
                    if i == 0:
                        ranj_str += alt_name
                    else:
                        prev_priority = sorted_alternatives[i - 1][1]
                        if abs(priority - prev_priority) < 0.001:  # Equal priority
                            ranj_str += " = " + alt_name
                        else:
                            ranj_str += " > " + alt_name
                ranj_global.append(ranj_str)

            # Update the single record with global priorities
            alt_matrix_result.global_prior = global_prior
            alt_matrix_result.lst_normalized_eigenvector_global = norm_vectors_alt
            alt_matrix_result.ranj_global = ranj_global
            db.session.commit()

            # Find result_id for export functionality
            result_id = None
            if current_user.is_authenticated:
                result_record = Result.query.filter_by(
                    method_id=method_id,
                    method_name="Hierarchy",
                    user_id=current_user.get_id(),
                ).first()
            else:
                result_record = Result.query.filter_by(
                    method_id=method_id, method_name="Hierarchy", user_id=None
                ).first()

            if result_record:
                result_id = result_record.id
                current_app.logger.info(
                    f"[DEBUG] Found result_id: {result_id} for method_id: {method_id}"
                )
            else:
                current_app.logger.warning(
                    f"[DEBUG] No result_id found for method_id: {method_id}"
                )

            # Render template with file data
            return render_template(
                "Hierarchy/result.html",
                hierarchy_task=task,
                name_criteria=criteria_names,
                name_alternatives=alternatives_names,
                num_criteria=len(criteria_names),
                num_alternatives=len(alternatives_names),
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
                matrix_alt=all_matrices_alt,
                components_eigenvector_alt=all_comp_vectors_alt,
                normalized_eigenvector_alt=all_norm_vectors_alt,
                sum_col_alt=all_sum_cols_alt,
                prod_col_alt=all_prod_cols_alt,
                l_max_alt=all_l_maxs_alt,
                index_consistency_alt=all_index_consistency_alt,
                relation_consistency_alt=all_relation_consistency_alt,
                lst_normalized_eigenvector_alt=all_lst_norm_vectors_alt,
                ranj_alt=all_ranjs_alt,
                ranj_global=ranj_global,
                lst_normalized_eigenvector_global=norm_vectors_alt,
                global_prior=global_prior,
                global_prior_plot=generate_plot(global_prior, alternatives_names),
                global_priorities_plot_id=plot_id,
                result_id=result_id,
                method_id=method_id,
            )

        except json.JSONDecodeError:
            flash("Invalid matrix data format", "error")
            return redirect(url_for("hierarchy.index"))
        except Exception as e:
            import traceback

            print(f"[ERROR] Error processing file data: {str(e)}")
            print(f"[ERROR] Full traceback: {traceback.format_exc()}")
            flash("Error processing file data", "error")
            return redirect(url_for("hierarchy.index"))

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
        # Try to find task by new_record_id first (for backward compatibility)
        hierarchy_task_record = HierarchyTask.query.get(new_record_id)
        if hierarchy_task_record:
            hierarchy_task = hierarchy_task_record.task
        else:
            # If not found, try to find by task_id from session
            task_id = session.get("task_id")
            if task_id:
                hierarchy_task_record = HierarchyTask.query.get(task_id)
                hierarchy_task = (
                    hierarchy_task_record.task if hierarchy_task_record else None
                )
            else:
                hierarchy_task = None
    except Exception as e:
        print("[!] Error:", e)
        hierarchy_task = None

    # Ensure task_id is defined
    if "task_id" not in locals():
        task_id = session.get("task_id") or new_record_id

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
            # Check for invalid values in alternatives matrix from form
            if any(
                val in ["", None, "undefined", "Undefined"] for val in matr_alt[:10]
            ):
                print(f"[ERROR] Invalid values found in alternatives matrix")
                flash("Invalid alternatives matrix data", "error")
                return redirect(url_for("hierarchy.index"))

            matrix_alt = do_matrix(
                num_alt=num_alternatives, matrix=matr_alt, criteria=num_criteria
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
        except (IndexError, ValueError) as e:
            print(f"[!] Error computing sum_col_alt: {e}")
            print(f"[ERROR] Matrix structure issue: {len(matrix_alt)} criteria")
            flash(
                "Ошибка при вычислении суммы по столбцам матрицы альтернатив", "error"
            )
            return redirect(url_for("hierarchy.index"))

        # Добуток додатку по стовпцях і нормалізованої оцінки вектора пріоритету
        prod_col_alt = do_prod_col(
            krit=0,
            num_alt=num_alternatives,
            criteria=num_criteria,
            sum_col=sum_col_alt,
            norm_vector=normalized_eigenvector_alt,
        )

        # Разом (Lmax)
        l_max_alt = do_l_max(krit=0, prod_col=prod_col_alt, criteria=num_criteria)

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
            krit=0,
            lst_norm_vector=lst_normalized_eigenvector_alt,
            criteria=num_criteria,
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
            krit=0,
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
            task_id=task_id,
        )

        # Create Result record for all users (authenticated and unauthenticated)
        user_id = current_user.get_id() if current_user.is_authenticated else None
        add_object_to_db(
            db,
            Result,
            method_name="Hierarchy",
            method_id=new_record_id,
            user_id=user_id,
        )

        # Create Result record for file data processing (if not already created)
        if file_data:
            # Use method_id for file data processing
            user_id = current_user.get_id() if current_user.is_authenticated else None
            existing_result = Result.query.filter_by(
                method_id=method_id, method_name="Hierarchy", user_id=user_id
            ).first()
            if not existing_result:
                add_object_to_db(
                    db,
                    Result,
                    method_name="Hierarchy",
                    method_id=method_id,
                    user_id=user_id,
                )
                current_app.logger.info(
                    f"[DEBUG] Created Result record with method_id={method_id}, user_id={user_id}"
                )
            else:
                current_app.logger.info(
                    f"[DEBUG] Result record already exists with method_id={method_id}, user_id={user_id}"
                )

            # Result record already has the correct method_id, no need to update

    generate_hierarchy_tree(
        name_criteria, name_alternatives, normalized_eigenvector, global_prior
    )

    # Find result_id for this analysis
    result_id = None
    user_id = current_user.get_id() if current_user.is_authenticated else None

    # For file data, use common_id; for regular data, use method_id
    search_method_id = common_id if file_data else method_id
    current_app.logger.info(
        f"[DEBUG] Searching for Result with method_id={search_method_id}, user_id={user_id}"
    )
    result = Result.query.filter_by(
        method_id=search_method_id, method_name="Hierarchy", user_id=user_id
    ).first()
    if result:
        result_id = result.id
        current_app.logger.info(f"[DEBUG] Found Result with id={result_id}")
    else:
        current_app.logger.info(
            f"[DEBUG] No Result found for method_id={search_method_id}, user_id={user_id}"
        )
        # Try to find any Result with this method_id regardless of user_id
        any_result = Result.query.filter_by(
            method_id=search_method_id, method_name="Hierarchy"
        ).first()
        if any_result:
            current_app.logger.info(
                f"[DEBUG] Found Result with different user_id: {any_result.user_id}"
            )
            result_id = any_result.id

    # Debug: Check current_user status
    current_app.logger.info(
        f"[DEBUG] current_user.is_authenticated: {current_user.is_authenticated}"
    )
    if current_user.is_authenticated:
        current_app.logger.info(
            f"[DEBUG] current_user.get_name(): {current_user.get_name()}"
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
        "result_id": result_id,
        "task": hierarchy_task if hierarchy_task else None,
        # 'gpt_response': gpt_response
    }

    # Debug: Check what name is being passed to template
    current_app.logger.info(f"[DEBUG] context['name']: {context['name']}")
    current_app.logger.info(f"[DEBUG] context['result_id']: {context['result_id']}")
    current_app.logger.info(f"[DEBUG] method_id: {method_id}")

    # Перевірка відношення узгодженості
    current_app.logger.info(
        f"[DEBUG] relation_consistency_alt: {relation_consistency_alt}"
    )
    for c in range(num_criteria):
        current_app.logger.info(
            f"[DEBUG] Processing relation_consistency_alt[{c}]: {relation_consistency_alt[c]}, type: {type(relation_consistency_alt[c])}"
        )
        # Check if relation_consistency_alt[c] is a list or single value
        cr_value = (
            relation_consistency_alt[c][0]
            if isinstance(relation_consistency_alt[c], list)
            and len(relation_consistency_alt[c]) > 0
            else relation_consistency_alt[c]
        )
        current_app.logger.info(f"[DEBUG] cr_value[{c}]: {cr_value}")
        if cr_value > 10:
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
        if current_user.is_authenticated:
            if (
                result.user_id != current_user.get_id()
                and current_user.get_name() != "admin"
            ):
                return Response("Access denied", status=403, mimetype="text/plain")
        # For unauthenticated users, allow access to any result

        # Get analysis data from database
        method_id = result.method_id
        current_app.logger.info(f"[DEBUG] Getting data for method_id: {method_id}")

        # Get basic data using method_id to find related records
        # For file uploads, we need to find records by method_id, not by ID
        criteria_record = HierarchyCriteria.query.filter_by(id=method_id).first()
        alternatives_record = HierarchyAlternatives.query.filter_by(
            id=method_id
        ).first()
        task_record = HierarchyTask.query.filter_by(id=method_id).first()
        criteria_matrix_record = HierarchyCriteriaMatrix.query.filter_by(
            id=method_id
        ).first()
        alternatives_matrix_record = HierarchyAlternativesMatrix.query.filter_by(
            id=method_id
        ).first()

        # If not found by id, try to find by criteria_id and alternatives_id
        if not criteria_matrix_record and criteria_record:
            current_app.logger.info(
                f"[DEBUG] Searching criteria_matrix by hierarchy_criteria_id={criteria_record.id}"
            )
            criteria_matrix_record = HierarchyCriteriaMatrix.query.filter_by(
                hierarchy_criteria_id=criteria_record.id
            ).first()
            current_app.logger.info(
                f"[DEBUG] Found criteria_matrix_record by hierarchy_criteria_id: {criteria_matrix_record is not None}"
            )
            if criteria_matrix_record:
                current_app.logger.info(
                    f"[DEBUG] Found criteria_matrix_record.id: {criteria_matrix_record.id}"
                )

        if not alternatives_matrix_record and alternatives_record:
            current_app.logger.info(
                f"[DEBUG] Searching alternatives_matrix by hierarchy_alternatives_id={alternatives_record.id}"
            )
            alternatives_matrix_record = HierarchyAlternativesMatrix.query.filter_by(
                hierarchy_alternatives_id=alternatives_record.id
            ).first()
            current_app.logger.info(
                f"[DEBUG] Found alternatives_matrix_record by hierarchy_alternatives_id: {alternatives_matrix_record is not None}"
            )
            if alternatives_matrix_record:
                current_app.logger.info(
                    f"[DEBUG] Found alternatives_matrix_record.id: {alternatives_matrix_record.id}"
                )

        # Additional search attempts if still not found
        if not criteria_matrix_record:
            current_app.logger.info(
                f"[DEBUG] Trying to find any HierarchyCriteriaMatrix records..."
            )
            all_criteria_matrices = HierarchyCriteriaMatrix.query.all()
            current_app.logger.info(
                f"[DEBUG] Found {len(all_criteria_matrices)} HierarchyCriteriaMatrix records"
            )
            for i, cm in enumerate(all_criteria_matrices[:5]):  # Show first 5
                current_app.logger.info(
                    f"[DEBUG]   [{i}] id={cm.id}, hierarchy_criteria_id={cm.hierarchy_criteria_id}"
                )

        if not alternatives_matrix_record:
            current_app.logger.info(
                f"[DEBUG] Trying to find any HierarchyAlternativesMatrix records..."
            )
            all_alternatives_matrices = HierarchyAlternativesMatrix.query.all()
            current_app.logger.info(
                f"[DEBUG] Found {len(all_alternatives_matrices)} HierarchyAlternativesMatrix records"
            )
            for i, am in enumerate(all_alternatives_matrices[:5]):  # Show first 5
                current_app.logger.info(
                    f"[DEBUG]   [{i}] id={am.id}, hierarchy_alternatives_id={am.hierarchy_alternatives_id}"
                )

        current_app.logger.info(
            f"[DEBUG] Retrieved records with method_id: {method_id}"
        )

        current_app.logger.info(f"Data records found:")
        current_app.logger.info(f"  criteria_record: {criteria_record is not None}")
        if criteria_record:
            current_app.logger.info(f"    criteria_record.id: {criteria_record.id}")
            current_app.logger.info(
                f"    criteria_record.names: {criteria_record.names}"
            )
        current_app.logger.info(
            f"  alternatives_record: {alternatives_record is not None}"
        )
        if alternatives_record:
            current_app.logger.info(
                f"    alternatives_record.id: {alternatives_record.id}"
            )
            current_app.logger.info(
                f"    alternatives_record.names: {alternatives_record.names}"
            )
        current_app.logger.info(f"  task_record: {task_record is not None}")
        if task_record:
            current_app.logger.info(f"    task_record.id: {task_record.id}")
            current_app.logger.info(f"    task_record.task: {task_record.task}")
        else:
            current_app.logger.info(
                f"    task_record: None - no task found for method_id={method_id}"
            )
        current_app.logger.info(
            f"  criteria_matrix_record: {criteria_matrix_record is not None}"
        )
        if criteria_matrix_record:
            current_app.logger.info(
                f"    criteria_matrix_record.id: {criteria_matrix_record.id}"
            )
            current_app.logger.info(
                f"    criteria_matrix_record.hierarchy_criteria_id: {criteria_matrix_record.hierarchy_criteria_id}"
            )
        current_app.logger.info(
            f"  alternatives_matrix_record: {alternatives_matrix_record is not None}"
        )
        if alternatives_matrix_record:
            current_app.logger.info(
                f"    alternatives_matrix_record.id: {alternatives_matrix_record.id}"
            )
            current_app.logger.info(
                f"    alternatives_matrix_record.hierarchy_alternatives_id: {alternatives_matrix_record.hierarchy_alternatives_id}"
            )

        if not all(
            [
                criteria_record,
                alternatives_record,
                criteria_matrix_record,
                alternatives_matrix_record,
            ]
        ):
            missing_records = []
            if not criteria_record:
                missing_records.append("criteria_record")
            if not alternatives_record:
                missing_records.append("alternatives_record")
            if not criteria_matrix_record:
                missing_records.append("criteria_matrix_record")
            if not alternatives_matrix_record:
                missing_records.append("alternatives_matrix_record")

            current_app.logger.error(
                f"Incomplete analysis data for method_id: {method_id}"
            )
            current_app.logger.error(f"Missing records: {', '.join(missing_records)}")
            current_app.logger.error(
                f"Search criteria: method_id={method_id}, criteria_id={criteria_record.id if criteria_record else 'None'}, alternatives_id={alternatives_record.id if alternatives_record else 'None'}"
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
        # Check if consistency values are lists or single values
        current_app.logger.info(
            f"[DEBUG] criteria_matrix_record.index_consistency: {criteria_matrix_record.index_consistency}, type: {type(criteria_matrix_record.index_consistency)}"
        )
        current_app.logger.info(
            f"[DEBUG] criteria_matrix_record.relation_consistency: {criteria_matrix_record.relation_consistency}, type: {type(criteria_matrix_record.relation_consistency)}"
        )
        ci_value = (
            criteria_matrix_record.index_consistency[0]
            if isinstance(criteria_matrix_record.index_consistency, list)
            else criteria_matrix_record.index_consistency
        )
        cr_value = (
            criteria_matrix_record.relation_consistency[0]
            if isinstance(criteria_matrix_record.relation_consistency, list)
            else criteria_matrix_record.relation_consistency
        )
        current_app.logger.info(f"  criteria_consistency: ci={ci_value}, cr={cr_value}")
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

        task_description_value = task_record.task if task_record else None
        current_app.logger.info(
            f"[DEBUG] task_description for Excel export: '{task_description_value}'"
        )

        analysis_data = {
            "method_id": method_id,
            "task_description": task_description_value,
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
                "ci": (
                    criteria_matrix_record.index_consistency[0]
                    if isinstance(criteria_matrix_record.index_consistency, list)
                    else criteria_matrix_record.index_consistency
                ),
                "cr": (
                    criteria_matrix_record.relation_consistency[0]
                    if isinstance(criteria_matrix_record.relation_consistency, list)
                    else criteria_matrix_record.relation_consistency
                ),
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
            return {"success": False, "error": "Файл не завантажено"}, 400

        # Get number of criteria and alternatives from request
        num_criteria = request.form.get("num_criteria")
        num_alternatives = request.form.get("num_alternatives")

        if not num_criteria or not num_alternatives:
            return {
                "success": False,
                "error": "Кількість критеріїв і альтернатив не вказана",
            }, 400

        try:
            num_criteria = int(num_criteria)
            num_alternatives = int(num_alternatives)
        except ValueError:
            return {
                "success": False,
                "error": "Невірна кількість критеріїв або альтернатив",
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
    """Process hierarchy analysis from uploaded file data and redirect to result page"""
    try:
        current_app.logger.info(f"[DEBUG] Starting result_from_file processing")
        # Get data from form
        file_data = {
            "criteria_names": request.form.get("criteria_names"),
            "alternatives_names": request.form.get("alternatives_names"),
            "criteria_matrix": request.form.get("criteria_matrix"),
            "alternatives_matrices": request.form.get("alternatives_matrices"),
        }

        # Get task description from form
        hierarchy_task = request.form.get("hierarchy_task")
        current_app.logger.info(f"[DEBUG] Extracted hierarchy_task: '{hierarchy_task}'")
        current_app.logger.info(f"[DEBUG] Extracted file_data: {file_data}")

        # Check if all required data is present
        if not all(file_data.values()):
            flash("Missing required data from file upload", "error")
            return redirect(url_for("hierarchy.index"))

        # Process file data and get method_id
        result_response = result(file_data=file_data)

        # If result is a redirect or error, return it as is
        if hasattr(result_response, "status_code") and result_response.status_code in [
            302,
            400,
            500,
        ]:
            return result_response

        # If result is a render_template, we need to extract method_id from the context
        # Since we can't easily extract method_id from render_template response,
        # let's modify the approach: process the data and get the method_id, then redirect

        # Parse the data to get method_id
        criteria_names = json.loads(file_data["criteria_names"])
        alternatives_names = json.loads(file_data["alternatives_names"])

        # Create records in database to get method_id
        new_record_id = add_object_to_db(db, HierarchyCriteria, names=criteria_names)
        current_app.logger.info(
            f"[DEBUG] Created HierarchyCriteria with ID: {new_record_id}"
        )
        add_object_to_db(
            db, HierarchyAlternatives, id=new_record_id, names=alternatives_names
        )
        current_app.logger.info(
            f"[DEBUG] Created HierarchyAlternatives with ID: {new_record_id}"
        )

        # Create HierarchyTask with new_record_id as its ID
        task_description = (
            hierarchy_task
            if hierarchy_task
            else f"Hierarchy analysis with {len(criteria_names)} criteria and {len(alternatives_names)} alternatives"
        )
        add_object_to_db(
            db,
            HierarchyTask,
            id=new_record_id,
            task=task_description,
        )
        current_app.logger.info(
            f"[DEBUG] Created HierarchyTask with ID: {new_record_id}, task: {task_description}"
        )

        # Create Result record for file uploads (if user is authenticated)
        # Create Result record for all users (authenticated and unauthenticated)
        user_id = current_user.get_id() if current_user.is_authenticated else None
        add_object_to_db(
            db,
            Result,
            method_name="Hierarchy",
            method_id=new_record_id,
            user_id=user_id,
        )

        # Store data in session for the result function
        session["new_record_id"] = new_record_id
        session["num_alternatives"] = len(alternatives_names)
        session["num_criteria"] = len(criteria_names)
        session["name_alternatives"] = alternatives_names
        session["name_criteria"] = criteria_names

        # Store file data in session for processing
        session["file_criteria_matrix"] = file_data["criteria_matrix"]
        session["file_alternatives_matrices"] = file_data["alternatives_matrices"]

        # Redirect to the result page with method_id
        current_app.logger.info(
            f"[DEBUG] Redirecting to /hierarchy/result/{new_record_id}"
        )
        return redirect(url_for("hierarchy.result", method_id=new_record_id))

    except Exception as e:
        current_app.logger.error(f"Error processing file data: {str(e)}")
        flash(f"Error processing file data: {str(e)}", "error")
        return redirect(url_for("hierarchy.index"))
