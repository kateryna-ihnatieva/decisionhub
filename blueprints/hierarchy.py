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
import json
from mymodules.mai import *
from models import *
from flask_login import current_user, login_required
from mymodules.methods import *
from mymodules.gpt_response import *
from mymodules.excel_export import HierarchyExcelExporter
from mymodules.file_upload import process_uploaded_file, process_hierarchy_file
from datetime import datetime

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

    # Сохраняем имена в сессии для возможного восстановления
    session["name_alternatives"] = name_alternatives
    session["name_criteria"] = name_criteria

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

    name_alternatives = HierarchyAlternatives.query.get(new_record_id).names
    name_criteria = HierarchyCriteria.query.get(new_record_id).names
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


@hierarchy_bp.route("/result", methods=["POST"])
@login_required
def result_from_file():
    """Handle result calculation when data comes from uploaded file"""
    try:
        # Debug: Print all form data
        print(f"[DEBUG] result_from_file called")
        print(f"[DEBUG] Form data: {dict(request.form)}")

        # Get data from form
        num_criteria = int(request.form.get("num_criteria"))
        num_alternatives = int(request.form.get("num_alternatives"))
        file_uploaded = request.form.get("file_uploaded") == "true"

        print(f"[DEBUG] num_criteria: {num_criteria}")
        print(f"[DEBUG] num_alternatives: {num_alternatives}")
        print(f"[DEBUG] file_uploaded: {file_uploaded}")

        if not file_uploaded:
            flash("No file uploaded", "error")
            return redirect(url_for("hierarchy.index"))

        # Get matrix data from hidden fields
        criteria_matrix_json = request.form.get("criteria_matrix")
        alternatives_matrices_json = request.form.get("alternatives_matrices")

        if not criteria_matrix_json or not alternatives_matrices_json:
            flash("Matrix data not found", "error")
            return redirect(url_for("hierarchy.index"))

        # Clean JSON strings to remove null bytes and control characters before parsing
        def clean_json_string(json_str):
            """Clean JSON string by removing null bytes and control characters"""
            if not json_str:
                return ""

            # Remove common null bytes and control characters
            cleaned = (
                json_str.replace("\x00", "")
                .replace("\x01", "")
                .replace("\x02", "")
                .replace("\x03", "")
            )
            cleaned = (
                cleaned.replace("\x04", "")
                .replace("\x05", "")
                .replace("\x06", "")
                .replace("\x07", "")
            )
            cleaned = (
                cleaned.replace("\x08", "")
                .replace("\x0b", "")
                .replace("\x0c", "")
                .replace("\x0e", "")
            )
            cleaned = (
                cleaned.replace("\x0f", "")
                .replace("\x10", "")
                .replace("\x11", "")
                .replace("\x12", "")
            )
            cleaned = (
                cleaned.replace("\x13", "")
                .replace("\x14", "")
                .replace("\x15", "")
                .replace("\x16", "")
            )
            cleaned = (
                cleaned.replace("\x17", "")
                .replace("\x18", "")
                .replace("\x19", "")
                .replace("\x1a", "")
            )
            cleaned = (
                cleaned.replace("\x1b", "")
                .replace("\x1c", "")
                .replace("\x1d", "")
                .replace("\x1e", "")
            )
            cleaned = cleaned.replace("\x1f", "")

            # Keep only printable characters, whitespace, and common JSON characters
            cleaned = "".join(
                char for char in cleaned if ord(char) >= 32 or char in "\t\n\r"
            )

            return cleaned.strip()

        criteria_matrix_json = clean_json_string(criteria_matrix_json)
        alternatives_matrices_json = clean_json_string(alternatives_matrices_json)

        # Parse JSON data
        criteria_matrix = json.loads(criteria_matrix_json)
        alternatives_matrices = json.loads(alternatives_matrices_json)

        # Get names from form
        criteria_names = []
        alternatives_names = []

        # Get all criteria names (they come as separate fields with same name)
        criteria_names_raw = request.form.getlist("name_criteria")
        criteria_names = []
        for name in criteria_names_raw:
            if name.strip():
                clean_name = clean_json_string(name)
                if clean_name:
                    criteria_names.append(clean_name)

        # Get all alternatives names (they come as separate fields with same name)
        alternatives_names_raw = request.form.getlist("name_alternatives")
        alternatives_names = []
        for name in alternatives_names_raw:
            if name.strip():
                clean_name = clean_json_string(name)
                if clean_name:
                    alternatives_names.append(clean_name)

        print(f"[DEBUG] criteria_names: {criteria_names}")
        print(f"[DEBUG] alternatives_names: {alternatives_names}")

        if (
            len(criteria_names) != num_criteria
            or len(alternatives_names) != num_alternatives
        ):
            print(
                f"[DEBUG] Names count mismatch: criteria={len(criteria_names)}/{num_criteria}, alternatives={len(alternatives_names)}/{num_alternatives}"
            )
            flash(
                f"Incomplete names data: criteria={len(criteria_names)}/{num_criteria}, alternatives={len(alternatives_names)}/{num_alternatives}",
                "error",
            )
            return redirect(url_for("hierarchy.index"))

        # Create new records in database
        new_record_id = create_hierarchy_records_from_file(
            criteria_names, alternatives_names, criteria_matrix, alternatives_matrices
        )

        if new_record_id:
            # Redirect to result page with the new record ID
            return redirect(url_for("hierarchy.result", method_id=new_record_id))
        else:
            flash("Failed to save data", "error")
            return redirect(url_for("hierarchy.index"))

    except Exception as e:
        current_app.logger.error(f"Error processing file upload result: {str(e)}")
        flash(f"Error processing file: {str(e)}", "error")
        return redirect(url_for("hierarchy.index"))


@hierarchy_bp.route("/result/<int:method_id>", methods=["GET", "POST"])
def result(method_id=None):
    print(f"[DEBUG] Метод result вызван с method_id: {method_id}")
    print(f"[DEBUG] Метод запроса: {request.method}")
    print(f"[DEBUG] Данные формы: {dict(request.form)}")
    print(f"[DEBUG] Данные сессии: {dict(session)}")

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

    print(f"[DEBUG] new_record_id: {new_record_id}")
    print(f"[DEBUG] num_alternatives: {num_alternatives}")
    print(f"[DEBUG] num_criteria: {num_criteria}")

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

    # Завантажуємо всі матриці альтернатив з БД для данного method_id
    existing_alternatives_matrices = HierarchyAlternativesMatrix.query.filter_by(
        criteria_id=new_record_id
    ).all()
    print(
        f"[DEBUG] existing_alternatives_matrices: {len(existing_alternatives_matrices)} записей"
    )

    if existing_alternatives_matrices:
        print(
            f"[DEBUG] Первая матрица в БД: {existing_alternatives_matrices[0].matr_alt}"
        )

    if existing_alternatives_matrices and existing_alternatives_matrices[0].matr_alt:
        # Дані є в БД
        print(
            f"[DEBUG] Загружено {len(existing_alternatives_matrices)} матриц альтернатив из БД"
        )

        # Проверяем, есть ли уже вычисленные результаты в первой матрице
        first_matrix = existing_alternatives_matrices[0]
        if (
            first_matrix.components_eigenvector_alt
            and first_matrix.normalized_eigenvector_alt
            and first_matrix.global_prior
        ):
            # Результаты уже вычислены, используем их
            print("[DEBUG] Используем уже вычисленные результаты из БД")

            # Собираем данные из всех матриц
            matr_alt = [matrix.matr_alt for matrix in existing_alternatives_matrices]
            matrix_alt = [
                matrix.comparison_matrix for matrix in existing_alternatives_matrices
            ]
            components_eigenvector_alt = [
                matrix.components_eigenvector_alt
                for matrix in existing_alternatives_matrices
            ]
            normalized_eigenvector_alt = [
                matrix.normalized_eigenvector_alt
                for matrix in existing_alternatives_matrices
            ]
            sum_col_alt = [
                matrix.sum_col_alt for matrix in existing_alternatives_matrices
            ]
            prod_col_alt = [
                matrix.prod_col_alt for matrix in existing_alternatives_matrices
            ]
            l_max_alt = [matrix.l_max_alt for matrix in existing_alternatives_matrices]
            index_consistency_alt = [
                matrix.index_consistency_alt
                for matrix in existing_alternatives_matrices
            ]
            relation_consistency_alt = [
                matrix.relation_consistency_alt
                for matrix in existing_alternatives_matrices
            ]
            lst_normalized_eigenvector_alt = [
                matrix.lst_normalized_eigenvector_alt
                for matrix in existing_alternatives_matrices
            ]
            ranj_alt = [matrix.ranj_alt for matrix in existing_alternatives_matrices]
            # Extract scalar values from global_prior lists
            global_prior = []
            for i, matrix in enumerate(existing_alternatives_matrices):
                print(
                    f"[DEBUG] Matrix {i} global_prior: {type(matrix.global_prior)} = {matrix.global_prior}"
                )
                if (
                    isinstance(matrix.global_prior, list)
                    and len(matrix.global_prior) > 0
                ):
                    # If it's a list, take the first element
                    value = matrix.global_prior[0]
                    print(f"[DEBUG] Extracted value: {type(value)} = {value}")
                    global_prior.append(value)
                else:
                    # If it's already a scalar, use it directly
                    print(
                        f"[DEBUG] Using scalar value: {type(matrix.global_prior)} = {matrix.global_prior}"
                    )
                    global_prior.append(matrix.global_prior)

            print(f"[DEBUG] Final global_prior: {type(global_prior)} = {global_prior}")

            # Для глобальных значений используем данные из первой матрицы
            lst_normalized_eigenvector_global = (
                first_matrix.lst_normalized_eigenvector_global
            )
            ranj_global = first_matrix.ranj_global

            # Пропускаем вычисления и переходим к формированию контекста
            skip_calculations = True
        else:
            skip_calculations = False
    else:
        # Даних немає в БД - проверяем форму
        print(f"[DEBUG] Проверяем форму на наличие matrix_alt")
        print(
            f"[DEBUG] request.form.getlist('matrix_alt'): {request.form.getlist('matrix_alt')}"
        )
        if request.form.getlist("matrix_alt"):
            # Данные есть в форме - используем их для вычислений
            matr_alt = request.form.getlist("matrix_alt")
            print(f"[DEBUG] Матрица альтернатив из формы: {len(matr_alt)} элементов")
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
            matrix_alt = do_matrix(
                num_alt=num_alternatives, matrix=matr_alt, criteria=num_criteria
            )
            print(
                f"[DEBUG] Матрица альтернатив создана успешно: {len(matrix_alt)} критериев"
            )
        except (IndexError, ValueError) as e:
            print(f"[!] Error creating matrix_alt: {e}")
            print(f"[DEBUG] matr_alt: {matr_alt}")
            print(f"[DEBUG] num_alt: {num_alternatives}, criteria: {num_criteria}")
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
    # relation_consistency_alt теперь массив значений для каждого критерия
    if isinstance(relation_consistency_alt, list) and len(relation_consistency_alt) > 0:
        for c in range(min(num_criteria, len(relation_consistency_alt))):
            # Получаем значение consistency для критерия c
            if isinstance(relation_consistency_alt[c], list):
                # Если это список, берем первое значение
                consistency_value = (
                    relation_consistency_alt[c][0]
                    if len(relation_consistency_alt[c]) > 0
                    else 0
                )
            else:
                # Если это простое значение
                consistency_value = relation_consistency_alt[c]

            # Ensure consistency_value is a scalar
            if isinstance(consistency_value, list) and len(consistency_value) > 0:
                consistency_value = consistency_value[0]
            elif isinstance(consistency_value, list) and len(consistency_value) == 0:
                consistency_value = 0
            elif not isinstance(consistency_value, (int, float)):
                consistency_value = 0

            if consistency_value > 10:
                context["error"] = (
                    f'Перегляньте свої судження у матриці Критерію "{name_criteria[c]}"'
                )
                break

    for i in range(len(relation_consistency)):
        if relation_consistency[i] > 10:
            context["error"] = "Перегляньте свої судження у матриці для критеріїв"
            break

    session["matr_alt"] = 1

    # Debug logging
    print(
        f"[DEBUG] components_eigenvector_alt type: {type(components_eigenvector_alt)}"
    )
    print(
        f"[DEBUG] components_eigenvector_alt length: {len(components_eigenvector_alt) if components_eigenvector_alt else 'None'}"
    )
    if components_eigenvector_alt:
        for i, matrix in enumerate(components_eigenvector_alt):
            print(
                f"[DEBUG] Matrix {i}: {type(matrix)}, length: {len(matrix) if matrix else 'None'}"
            )
            if matrix:
                for j, val in enumerate(matrix):
                    print(f"[DEBUG]   [{i}][{j}]: {type(val)} = {val}")

    # Fix data structure - extract scalar values from lists
    def extract_scalar(value):
        if isinstance(value, list) and len(value) > 0:
            return value[0]
        return value

    # Fix all data structures that might contain nested lists
    data_structures = [
        "normalized_eigenvector_alt",
        "components_eigenvector_alt",
        "sum_col_alt",
        "prod_col_alt",
        "l_max_alt",
        "index_consistency_alt",
        "relation_consistency_alt",
    ]

    for data_name in data_structures:
        data = locals().get(data_name)
        if data and isinstance(data, list):
            for i, matrix in enumerate(data):
                if isinstance(matrix, list):
                    for j, val in enumerate(matrix):
                        if isinstance(val, list) and len(val) > 0:
                            data[i][j] = val[0]
                        elif isinstance(val, list) and len(val) == 0:
                            data[i][j] = 0.0

    # Also fix matrix_alt structure
    if "matrix_alt" in locals() and matrix_alt:
        for i, matrix in enumerate(matrix_alt):
            if isinstance(matrix, list):
                for j, row in enumerate(matrix):
                    if isinstance(row, list):
                        for k, val in enumerate(row):
                            if isinstance(val, list) and len(val) > 0:
                                matrix_alt[i][j][k] = val[0]
                            elif isinstance(val, list) and len(val) == 0:
                                matrix_alt[i][j][k] = 0.0

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
    """Handle file upload for matrix data"""
    try:
        # Get the uploaded file
        file = request.files.get("matrix_file")
        if not file:
            return {"success": False, "error": "No file uploaded"}, 400

        # Get expected sizes from request
        num_criteria = request.form.get("num_criteria")
        num_alternatives = request.form.get("num_alternatives")

        if not num_criteria or not num_alternatives:
            return {
                "success": False,
                "error": "Number of criteria and alternatives required",
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


def create_hierarchy_records_from_file(
    criteria_names, alternatives_names, criteria_matrix, alternatives_matrices
):
    """Create hierarchy records in database from uploaded file data"""
    try:
        # Save criteria names - let PostgreSQL auto-generate the ID
        criteria_record = HierarchyCriteria(names=criteria_names)
        db.session.add(criteria_record)
        db.session.flush()  # Get the auto-generated ID

        # Save alternatives names - use the same ID as criteria
        alternatives_record = HierarchyAlternatives(
            id=criteria_record.id, names=alternatives_names
        )
        db.session.add(alternatives_record)
        db.session.flush()  # Ensure records are saved

        # Use the criteria ID as the main record ID
        new_record_id = criteria_record.id

        # Process criteria matrix
        criteria_matrix_processed = process_criteria_matrix(
            criteria_matrix, criteria_names
        )

        # Save criteria matrix data
        criteria_matrix_record = HierarchyCriteriaMatrix(
            id=new_record_id,
            comparison_matrix=criteria_matrix_processed["comparison_matrix"],
            components_eigenvector=criteria_matrix_processed["components_eigenvector"],
            normalized_eigenvector=criteria_matrix_processed["normalized_eigenvector"],
            sum_col=criteria_matrix_processed["sum_col"],
            prod_col=criteria_matrix_processed["prod_col"],
            l_max=criteria_matrix_processed["l_max"],
            index_consistency=criteria_matrix_processed["index_consistency"],
            relation_consistency=criteria_matrix_processed["relation_consistency"],
            lst_normalized_eigenvector=criteria_matrix_processed[
                "lst_normalized_eigenvector"
            ],
            ranj=criteria_matrix_processed["ranj"],
        )
        db.session.add(criteria_matrix_record)

        # Save task record first - let PostgreSQL auto-generate the ID
        task_record = HierarchyTask(task="Analysis from uploaded file")
        db.session.add(task_record)
        db.session.flush()  # Get the task_id

        # Process alternatives matrices
        alternatives_matrices_processed = process_alternatives_matrices(
            alternatives_matrices, alternatives_names
        )

        # Save each alternatives matrix data
        for i, alternatives_matrix_processed in enumerate(
            alternatives_matrices_processed
        ):
            # Let PostgreSQL auto-generate the ID for each matrix
            alternatives_matrix_record = HierarchyAlternativesMatrix(
                criteria_id=new_record_id,
                hierarchy_alternatives_id=new_record_id,
                matr_alt=alternatives_matrix_processed["matr_alt"],
                comparison_matrix=alternatives_matrix_processed["comparison_matrix"],
                components_eigenvector_alt=alternatives_matrix_processed[
                    "components_eigenvector_alt"
                ],
                normalized_eigenvector_alt=alternatives_matrix_processed[
                    "normalized_eigenvector_alt"
                ],
                sum_col_alt=alternatives_matrix_processed["sum_col_alt"],
                prod_col_alt=alternatives_matrix_processed["prod_col_alt"],
                l_max_alt=alternatives_matrix_processed["l_max_alt"],
                index_consistency_alt=alternatives_matrix_processed[
                    "index_consistency_alt"
                ],
                relation_consistency_alt=alternatives_matrix_processed[
                    "relation_consistency_alt"
                ],
                lst_normalized_eigenvector_alt=alternatives_matrix_processed[
                    "lst_normalized_eigenvector_alt"
                ],
                ranj_alt=alternatives_matrix_processed["ranj_alt"],
                global_prior=alternatives_matrix_processed["global_prior"],
                task_id=task_record.id,  # Use the actual task_id from the created record
                gpt_response=None,
            )
            db.session.add(alternatives_matrix_record)
            # Flush after each record to ensure proper ID generation
            db.session.flush()

        # Save result record
        result_record = Result(
            method_name="hierarchy",
            method_id=new_record_id,
            user_id=current_user.get_id(),
        )
        db.session.add(result_record)

        # Commit all changes
        db.session.commit()

        return new_record_id

    except Exception as e:
        current_app.logger.error(
            f"Error creating hierarchy records from file: {str(e)}"
        )
        db.session.rollback()
        return None


def process_criteria_matrix(matrix, names):
    """Process criteria matrix and calculate all required values"""
    try:
        # Convert matrix to numpy array
        import numpy as np

        # Clean matrix data to remove null bytes
        cleaned_matrix = []
        for row in matrix:
            cleaned_row = []
            for cell in row:
                if isinstance(cell, str):
                    # Remove null bytes and other control characters
                    cell = (
                        cell.replace("\x00", "")
                        .replace("\x01", "")
                        .replace("\x02", "")
                        .replace("\x03", "")
                    )
                    cell = "".join(
                        char for char in cell if ord(char) >= 32 or char in "\t\n\r"
                    )
                cleaned_row.append(cell)
            cleaned_matrix.append(cleaned_row)

        matrix = cleaned_matrix
        matrix_array = np.array(matrix, dtype=float)

        # Import required functions
        from mymodules.mai import (
            do_comp_vector,
            do_norm_vector,
            do_sum_col,
            do_prod_col,
            do_l_max,
            do_consistency,
            do_lst_norm_vector,
            do_ranj,
        )

        # Calculate eigenvector and other values using existing functions
        components_eigenvector = do_comp_vector(
            krit=1, criteria=len(names), matr=matrix_array
        )
        normalized_eigenvector = do_norm_vector(
            krit=1, comp_vector=components_eigenvector, criteria=len(names)
        )
        sum_col = do_sum_col(krit=1, matr=matrix_array, criteria=len(names))
        prod_col = do_prod_col(
            krit=1,
            criteria=len(names),
            sum_col=sum_col,
            norm_vector=normalized_eigenvector,
        )
        l_max = do_l_max(krit=1, prod_col=prod_col, criteria=len(names))
        index_consistency, relation_consistency = do_consistency(
            krit=1, l_max=l_max, criteria=len(names)
        )
        lst_normalized_eigenvector = do_lst_norm_vector(
            krit=1, name=names, criteria=len(names), norm_vector=normalized_eigenvector
        )
        ranj = do_ranj(
            krit=1, lst_norm_vector=lst_normalized_eigenvector, criteria=len(names)
        )

        return {
            "comparison_matrix": matrix,
            "components_eigenvector": components_eigenvector,
            "normalized_eigenvector": normalized_eigenvector,
            "sum_col": sum_col,
            "prod_col": prod_col,
            "l_max": l_max,
            "index_consistency": index_consistency,
            "relation_consistency": relation_consistency,
            "lst_normalized_eigenvector": lst_normalized_eigenvector,
            "ranj": ranj,
        }
    except Exception as e:
        current_app.logger.error(f"Error processing criteria matrix: {str(e)}")
        raise


def process_alternatives_matrices(matrices, names):
    """Process alternatives matrices and calculate all required values"""
    try:
        import numpy as np

        # Process all matrices
        processed_matrices = []
        for i, matrix in enumerate(matrices):
            print(f"[DEBUG] Processing matrix {i}: {type(matrix)}")
            print(
                f"[DEBUG] Matrix shape: {len(matrix) if hasattr(matrix, '__len__') else 'No len'}"
            )

            # Clean matrix data to remove null bytes
            cleaned_matrix = []
            for row in matrix:
                cleaned_row = []
                for cell in row:
                    if isinstance(cell, str):
                        # Remove null bytes and other control characters
                        cell = (
                            cell.replace("\x00", "")
                            .replace("\x01", "")
                            .replace("\x02", "")
                            .replace("\x03", "")
                        )
                        cell = "".join(
                            char for char in cell if ord(char) >= 32 or char in "\t\n\r"
                        )
                    cleaned_row.append(cell)
                cleaned_matrix.append(cleaned_row)

            matrix = cleaned_matrix
            print(
                f"[DEBUG] Cleaned matrix shape: {len(matrix)}x{len(matrix[0]) if matrix else 0}"
            )
            matrix_array = np.array(matrix, dtype=float)
            print(f"[DEBUG] Matrix array shape: {matrix_array.shape}")

            # Import required functions
            from mymodules.mai import (
                do_comp_vector,
                do_norm_vector,
                do_sum_col,
                do_prod_col,
                do_l_max,
                do_consistency,
                do_lst_norm_vector,
                do_ranj,
            )

            # Calculate eigenvector and other values using existing functions
            print(
                f"[DEBUG] Calling do_comp_vector with num_alt={len(names)}, criteria=1, matr shape={matrix_array.shape}"
            )
            # Convert numpy array to list for compatibility with existing functions
            matrix_list = matrix_array.tolist()
            print(f"[DEBUG] Converted matrix to list: {type(matrix_list)}")
            components_eigenvector_alt = do_comp_vector(
                krit=1, num_alt=len(names), criteria=1, matr=matrix_list
            )
            print(
                f"[DEBUG] components_eigenvector_alt: {type(components_eigenvector_alt)} = {components_eigenvector_alt}"
            )

            print(
                f"[DEBUG] Calling do_norm_vector with num_alt={len(names)}, comp_vector={type(components_eigenvector_alt)}"
            )
            normalized_eigenvector_alt = do_norm_vector(
                krit=1,
                num_alt=len(names),
                comp_vector=components_eigenvector_alt,
                criteria=1,
            )
            print(
                f"[DEBUG] normalized_eigenvector_alt: {type(normalized_eigenvector_alt)} = {normalized_eigenvector_alt}"
            )

            print(
                f"[DEBUG] Calling do_sum_col with num_alt={len(names)}, matr shape={matrix_array.shape}"
            )
            sum_col_alt = do_sum_col(
                krit=1, num_alt=len(names), matr=matrix_list, criteria=1
            )
            print(f"[DEBUG] sum_col_alt: {type(sum_col_alt)} = {sum_col_alt}")

            print(
                f"[DEBUG] Calling do_prod_col with num_alt={len(names)}, sum_col={type(sum_col_alt)}"
            )
            prod_col_alt = do_prod_col(
                krit=1,
                num_alt=len(names),
                criteria=1,
                sum_col=sum_col_alt,
                norm_vector=normalized_eigenvector_alt,
            )
            print(f"[DEBUG] prod_col_alt: {type(prod_col_alt)} = {prod_col_alt}")

            print(f"[DEBUG] Calling do_l_max with prod_col={type(prod_col_alt)}")
            l_max_alt = do_l_max(krit=1, prod_col=prod_col_alt, criteria=1)
            print(f"[DEBUG] l_max_alt: {type(l_max_alt)} = {l_max_alt}")

            print(
                f"[DEBUG] Calling do_consistency with num_alt={len(names)}, l_max={type(l_max_alt)}"
            )
            index_consistency_alt, relation_consistency_alt = do_consistency(
                krit=1, num_alt=len(names), l_max=l_max_alt, criteria=1
            )
            print(
                f"[DEBUG] index_consistency_alt: {type(index_consistency_alt)} = {index_consistency_alt}"
            )
            print(
                f"[DEBUG] relation_consistency_alt: {type(relation_consistency_alt)} = {relation_consistency_alt}"
            )

            print(
                f"[DEBUG] Calling do_lst_norm_vector with num_alt={len(names)}, name={type(names)}"
            )
            lst_normalized_eigenvector_alt = do_lst_norm_vector(
                krit=1,
                num_alt=len(names),
                name=names,
                criteria=1,
                norm_vector=normalized_eigenvector_alt,
            )
            print(
                f"[DEBUG] lst_normalized_eigenvector_alt: {type(lst_normalized_eigenvector_alt)} = {lst_normalized_eigenvector_alt}"
            )

            print(
                f"[DEBUG] Calling do_ranj with lst_norm_vector={type(lst_normalized_eigenvector_alt)}"
            )
            ranj_alt = do_ranj(
                krit=1, lst_norm_vector=lst_normalized_eigenvector_alt, criteria=1
            )
            print(f"[DEBUG] ranj_alt: {type(ranj_alt)} = {ranj_alt}")

            # Calculate global priority (simplified for now)
            # This should be calculated properly
            global_prior = normalized_eigenvector_alt

            processed_matrix = {
                "matr_alt": matrix,
                "comparison_matrix": matrix,
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
            }

            processed_matrices.append(processed_matrix)

        return processed_matrices
    except Exception as e:
        current_app.logger.error(f"Error processing alternatives matrices: {str(e)}")
        raise
