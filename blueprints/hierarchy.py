from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    current_app,
)
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
        print(f"[DEBUG] Загружена матрица альтернатив из БД: {len(matr_alt)} элементов")

        # Проверяем, есть ли уже вычисленные результаты
        if (
            existing_alternatives_matrix.components_eigenvector_alt
            and existing_alternatives_matrix.normalized_eigenvector_alt
            and existing_alternatives_matrix.global_prior
        ):
            # Результаты уже вычислены, используем их
            print("[DEBUG] Используем уже вычисленные результаты из БД")
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
