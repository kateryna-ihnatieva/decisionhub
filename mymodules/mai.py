import operator
from fractions import Fraction
from graphviz import Digraph
from jinja2.runtime import Undefined


def convert_to_fraction(value, precision=0.001):
    """
    Convert decimal number to fraction string (e.g., 0.333... -> "1/3")
    """
    try:
        if isinstance(value, str):
            # If it's already a fraction string, return as is
            if "/" in value:
                return value
            value = float(value)

        if isinstance(value, (int, float)):
            # Handle special cases
            if abs(value - 1.0) < precision:
                return "1"
            elif abs(value) < precision:
                return "0"

            # Convert to fraction
            frac = Fraction(value).limit_denominator(1000)

            # If denominator is 1, return just the numerator
            if frac.denominator == 1:
                return str(frac.numerator)

            # Return as fraction string
            return f"{frac.numerator}/{frac.denominator}"

        return str(value)
    except (ValueError, TypeError):
        return str(value)


# Створення списку з матриць по рівнях
def do_matrix(krit=0, matrix=0, criteria=0, num_alt=0):
    print(
        f"[DEBUG] do_matrix called with krit={krit}, criteria={criteria}, "
        f"num_alt={num_alt}"
    )
    matrix_len = len(matrix) if hasattr(matrix, "__len__") else "N/A"
    print(f"[DEBUG] matrix type: {type(matrix)}, length: {matrix_len}")
    print(f"[DEBUG] matrix content: {matrix}")

    def process_matrix_element(matr, i, j):
        print(f"[DEBUG] process_matrix_element called with i={i}, j={j}")
        matr_len = len(matr) if hasattr(matr, "__len__") else "N/A"
        print(f"[DEBUG] matr type: {type(matr)}, length: {matr_len}")
        print(f"[DEBUG] matr[j] type: {type(matr[j])}, value: {matr[j]}")
        print(f"[DEBUG] Full matr structure: {matr}")

        if not isinstance(matr[j], list):
            error_msg = f"matr[{j}] is not a list: {matr[j]}, " f"type: {type(matr[j])}"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] Full matrix structure at error point: {matr}")
            print(f"[ERROR] Matrix indices: i={i}, j={j}")
            raise ValueError(f"matr[{j}] is not a list")

        value = matr[j][i]
        print(f"[DEBUG] Current value: {value}, type: {type(value)}")

        # Если значение пустое или Undefined — ставим 1.0 по умолчанию
        if value is None or isinstance(value, Undefined) or str(value).strip() == "":
            matr[i][j] = 1.0
            return

        # Обрабатываем значение как float
        try:
            if isinstance(value, str):
                if "/" in value:
                    frac = Fraction(value)
                    matr[i][j] = float(frac)
                else:
                    n = float(value)
                    if n == 0:
                        matr[i][j] = 1.0
                    elif n >= 1:
                        matr[i][j] = 1.0 / n
                    else:
                        matr[i][j] = n
            else:
                # Если уже число, конвертируем в float
                n = float(value)
                if n == 0:
                    matr[i][j] = 1.0
                elif n >= 1:
                    matr[i][j] = 1.0 / n
                else:
                    matr[i][j] = n
        except (ValueError, TypeError) as e:
            print(f"[WARNING] Failed to process value {value}: {e}, using 1.0")
            matr[i][j] = 1.0

    matr = []
    if krit:
        print("[DEBUG] Processing criteria matrix (krit=1)")
        print(f"[DEBUG] Input matrix: {matrix}")
        print(f"[DEBUG] Criteria count: {criteria}")

        # Преобразуем в матрицу float чисел
        matr = []
        for i in range(criteria):
            row = []
            for j in range(criteria):
                idx = i * criteria + j
                if idx < len(matrix):
                    try:
                        row.append(float(matrix[idx]))
                    except (ValueError, TypeError):
                        row.append(1.0)
                else:
                    row.append(1.0)
            matr.append(row)

        print(f"[DEBUG] Created matr: {matr}")
        dims = f"{len(matr)}x{len(matr[0]) if matr else 'N/A'}"
        print(f"[DEBUG] Matrix dimensions: {dims}")

        for i in range(len(matr)):
            for j in range(len(matr[i])):
                if i > j:
                    pos = f"({i}, {j})"
                    msg = f"[DEBUG] About to process element at position {pos}"
                    print(msg)
                    process_matrix_element(matr, i, j)
    else:
        print("[DEBUG] Processing alternatives matrix (krit=0)")
        for i in range(criteria):
            print(f"[DEBUG] Creating matrix for criterion {i}")
            new_matrix = []
            for row_idx in range(num_alt):
                row = []
                for col_idx in range(num_alt):
                    idx = i * num_alt * num_alt + row_idx * num_alt + col_idx
                    if idx < len(matrix):
                        try:
                            row.append(float(matrix[idx]))
                        except (ValueError, TypeError):
                            row.append(1.0)
                    else:
                        row.append(1.0)
                new_matrix.append(row)
            matr.append(new_matrix)

        print(f"[DEBUG] Final matr structure: {matr}")
        # Змінюємо елементи нижньої трикутної матриці
        for m_idx, m in enumerate(matr):
            print(f"[DEBUG] Processing matrix {m_idx}: {m}")
            m_type = type(m)
            m_len = len(m) if hasattr(m, "__len__") else "N/A"
            print(f"[DEBUG] Matrix {m_idx} type: {m_type}, length: {m_len}")
            for i in range(len(m)):
                for j in range(len(m[i])):
                    if i > j:
                        pos = f"matrix {m_idx}, position ({i}, {j})"
                        msg = (
                            f"[DEBUG] About to process alternatives "
                            f"element at {pos}"
                        )
                        print(msg)
                        process_matrix_element(m, i, j)

    return matr


# Оцінки компонент власного вектора
def do_comp_vector(krit=0, criteria=0, matr=0, num_alt=0):
    comp_vector = [[] for _ in range(criteria)] if krit == 0 else []
    if krit:
        for c in range(criteria):
            dob = 1
            for num in matr[c]:
                try:
                    # Теперь matr содержит float числа, не нужно eval
                    dob *= float(num)
                except Exception as e:
                    print(f"ERROR: Failed to convert '{num}' to float: {e}")
                    raise e
            result = dob ** (1 / criteria)
            comp_vector.append(result)
    else:
        for count in range(criteria):
            for c in range(num_alt):
                dob = 1
                for num in matr[count][c]:
                    try:
                        # Теперь matr содержит float числа, не нужно eval
                        dob *= float(num)
                    except Exception as e:
                        print(f"ERROR: Failed to convert '{num}' to float: {e}")
                        raise e
                result = dob ** (1 / num_alt)
                comp_vector[count].append(result)

    return comp_vector


# Нормалізовані оцінки вектора пріоритету
def do_norm_vector(krit=0, comp_vector=0, criteria=0, num_alt=0):
    norm_vector = [] if krit else [[] for _ in range(criteria)]
    if krit:
        for c in range(criteria):
            try:
                result = comp_vector[c] / sum(comp_vector)
                norm_vector.append(result)
            except Exception as e:
                print(f"ERROR: Division failed for criteria {c}: {e}")
                raise e
    else:
        for i in range(criteria):
            norm_vector[i] = []
            for c in range(num_alt):
                try:
                    result = comp_vector[i][c] / sum(comp_vector[i])
                    norm_vector[i].append(result)
                except Exception as e:
                    print(
                        f"ERROR: Division failed for criteria {i}, alternative {c}: {e}"
                    )
                    raise e

    return norm_vector


# Сума по стовпцям
def do_sum_col(krit=0, matr=0, criteria=0, num_alt=0):
    sum_col = [] if krit else [[] for _ in range(criteria)]
    if krit:
        for i in range(criteria):
            s = 0
            for j in range(criteria):
                try:
                    # Теперь matr содержит float числа, не нужно eval
                    s += float(matr[j][i])
                except Exception as e:
                    print(f"ERROR: Failed to convert '{matr[j][i]}' to float: {e}")
                    raise e
            sum_col.append(s)
    else:
        for c in range(criteria):
            sum_col[c] = []
            for i in range(num_alt):
                column_sum = 0
                for j in range(num_alt):
                    try:
                        # Теперь matr содержит float числа, не нужно eval
                        column_sum += float(matr[c][j][i])
                    except Exception as e:
                        print(
                            f"ERROR: Failed to convert '{matr[c][j][i]}' to float: {e}"
                        )
                        raise e
                sum_col[c].append(column_sum)

    return sum_col


# Добуток додатку по стовпцях і нормалізованої оцінки вектора пріоритету
def do_prod_col(krit=0, criteria=0, sum_col=0, norm_vector=0, num_alt=0):
    prod_col = [] if krit else [[] for _ in range(criteria)]
    if krit:
        for i in range(criteria):
            try:
                result = sum_col[i] * norm_vector[i]
                prod_col.append(result)
            except Exception as e:
                print(f"ERROR: Multiplication failed for criteria {i}: {e}")
                raise e
    else:
        for c in range(criteria):
            prod_col[c] = []
            for i in range(num_alt):
                try:
                    result = sum_col[c][i] * norm_vector[c][i]
                    prod_col[c].append(result)
                except Exception as e:
                    print(
                        f"ERROR: Multiplication failed for criteria {c}, alternative {i}: {e}"
                    )
                    raise e

    return prod_col


# Разом (Lmax)
def do_l_max(krit=0, prod_col=0, criteria=0):
    l_max = [] if krit else [[] for _ in range(criteria)]
    if krit:
        try:
            result = sum(prod_col)
            l_max = [result]
        except Exception as e:
            print(f"ERROR: Sum failed for prod_col: {e}")
            raise e
    else:
        for c in range(criteria):
            try:
                result = sum(prod_col[c])
                l_max[c].append(result)
            except Exception as e:
                print(f"ERROR: Sum failed for criteria {c}: {e}")
                raise e

    return l_max


# Індекс узгодженості i Відношення узгодженості
def do_consistency(krit=0, l_max=0, criteria=0, num_alt=0):
    # Випадкова узгодженість
    random_consistency = {
        "1": 0,
        "2": 0,
        "3": 0.58,
        "4": 0.9,
        "5": 1.12,
        "6": 1.24,
        "7": 1.32,
        "8": 1.41,
        "9": 1.45,
        "10": 1.49,
    }
    index_consistency = [] if krit else [[] for _ in range(criteria)]
    relation_consistency = [] if krit else [[] for _ in range(criteria)]
    if krit:
        if criteria >= 3:
            try:
                index_result = (l_max[0] - criteria) / (criteria - 1)
                index_consistency.append(index_result)

                relation_result = (
                    index_consistency[0] / (random_consistency[str(criteria)])
                ) * 100
                relation_consistency.append(relation_result)
            except Exception as e:
                print(f"ERROR: Consistency calculation failed for criteria: {e}")
                raise e
        else:
            index_consistency.append(0)
            relation_consistency.append(0)

    else:
        if num_alt >= 3:
            for c in range(criteria):
                try:
                    index_result = (l_max[c][0] - num_alt) / (num_alt - 1)
                    index_consistency[c].append(index_result)

                    relation_result = (
                        index_consistency[c][0] / (random_consistency[str(num_alt)])
                    ) * 100
                    relation_consistency[c].append(relation_result)
                except Exception as e:
                    print(
                        f"ERROR: Consistency calculation failed for criteria {c}: {e}"
                    )
                    raise e
        else:
            for c in range(criteria):
                index_consistency[c].append(0)
                relation_consistency[c].append(0)

    return index_consistency, relation_consistency


# список для Нормалізованих оцінок вектора пріоритету (для висновку)
def do_lst_norm_vector(krit=0, name=0, criteria=0, norm_vector=0, num_alt=0, g=0):
    print(f"[DEBUG] do_lst_norm_vector called with krit={krit}, criteria={criteria}")
    print(f"[DEBUG] name: {name}, type: {type(name)}")
    print(f"[DEBUG] norm_vector: {norm_vector}, type: {type(norm_vector)}")

    if krit:
        lst_norm_vector = []
        lst_norm_vector.append({})
        print(
            f"[DEBUG] Initial lst_norm_vector[0]: {lst_norm_vector[0]}, type: {type(lst_norm_vector[0])}"
        )

        for i in range(criteria):
            print(
                f"[DEBUG] Processing i={i}, name[i]={name[i]}, norm_vector[i]={norm_vector[i]}"
            )
            lst_norm_vector[0][name[i]] = norm_vector[i]
            print(
                f"[DEBUG] After assignment lst_norm_vector[0]: {lst_norm_vector[0]}, type: {type(lst_norm_vector[0])}"
            )

        # сортування списку
        print(
            f"[DEBUG] Before sorting lst_norm_vector[0]: {lst_norm_vector[0]}, type: {type(lst_norm_vector[0])}"
        )
        lst_norm_vector[0] = sorted(
            lst_norm_vector[0].items(), key=operator.itemgetter(1), reverse=True
        )
        print(
            f"[DEBUG] After sorting lst_norm_vector[0]: {lst_norm_vector[0]}, type: {type(lst_norm_vector[0])}"
        )
        lst_norm_vector[0] = {k: v for k, v in lst_norm_vector[0]}
        print(
            f"[DEBUG] Final lst_norm_vector[0]: {lst_norm_vector[0]}, type: {type(lst_norm_vector[0])}"
        )

    elif g == 1:
        lst_norm_vector = [{}]
        for i in range(num_alt):
            lst_norm_vector[0][name[i]] = norm_vector[i]

        lst_norm_vector[0] = sorted(
            lst_norm_vector[0].items(), key=operator.itemgetter(1), reverse=True
        )
        lst_norm_vector[0] = {k: v for k, v in lst_norm_vector[0]}

    else:
        lst_norm_vector = [[] for _ in range(criteria)]
        for c in range(criteria):
            for k in range(criteria):
                lst_norm_vector[c].append({})
                for i in range(num_alt):
                    lst_norm_vector[c][k][name[i]] = norm_vector[c][i]

        # сортування списку
        for c in range(criteria):
            lst_norm_vector[c][c] = sorted(
                lst_norm_vector[c][c].items(), key=operator.itemgetter(1), reverse=True
            )
            lst_norm_vector[c][c] = {k: v for k, v in lst_norm_vector[c][c]}

    return lst_norm_vector


# Ранжування
def do_ranj(krit=0, lst_norm_vector=0, criteria=0, g=0):
    print(f"[DEBUG] do_ranj called with krit={krit}, criteria={criteria}, g={g}")
    print(f"[DEBUG] lst_norm_vector: {lst_norm_vector}, type: {type(lst_norm_vector)}")
    if hasattr(lst_norm_vector, "__len__") and len(lst_norm_vector) > 0:
        print(
            f"[DEBUG] lst_norm_vector[0]: {lst_norm_vector[0]}, type: {type(lst_norm_vector[0])}"
        )

    if krit:
        ranj = []
        ctn = 0
        flag_key = None

        ranj_str = ""
        for key in lst_norm_vector[0].keys():
            if ctn == 0:
                ranj_str += key
                ctn += 1
            else:
                comparison = lst_norm_vector[0][flag_key] > lst_norm_vector[0][key]
                ranj_str += " > " if comparison else " = "
                ranj_str += key
            flag_key = key
        ranj.append(ranj_str)

    elif g == 0:
        print(f"[DEBUG] do_ranj g=0, criteria={criteria}")
        print(f"[DEBUG] lst_norm_vector: {lst_norm_vector}")
        ranj = [[] for _ in range(criteria)]
        flag_key = 0

        for c in range(criteria):
            print(f"[DEBUG] Processing criterion {c}")
            print(f"[DEBUG] lst_norm_vector[{c}][{c}]: {lst_norm_vector[c][c]}")
            ctn = 0
            ranj_str = ""
            for key in lst_norm_vector[c][c].keys():
                if ctn == 0:
                    ranj_str += key
                    ctn += 1
                else:
                    comparison = (
                        lst_norm_vector[c][c][flag_key] > lst_norm_vector[c][c][key]
                    )
                    ranj_str += " > " if comparison else " = "
                    ranj_str += key
                flag_key = key
            ranj[c].append(ranj_str)
            print(f"[DEBUG] ranj[{c}]: {ranj[c]}")
    else:
        ranj = []
        flag_key = 0
        ctn = 0
        ranj_str = ""

        for key in lst_norm_vector[0].keys():
            if ctn == 0:
                ranj_str += key
                ctn += 1
                ctn += 1
            else:
                comparison = lst_norm_vector[0][flag_key] > lst_norm_vector[0][key]
                ranj_str += " > " if comparison else " = "
                ranj_str += key
            flag_key = key
        ranj.append(ranj_str)

    return ranj


# Глобальні пріоритети
def do_global_prior(norm_vector=0, norm_vector_alt=0, num_alt=0):
    print(f"[DEBUG] do_global_prior called with:")
    print(f"[DEBUG] norm_vector: {norm_vector}, type: {type(norm_vector)}")
    print(f"[DEBUG] norm_vector_alt: {norm_vector_alt}, type: {type(norm_vector_alt)}")
    print(f"[DEBUG] num_alt: {num_alt}")

    global_prior = []
    for i in range(num_alt):
        g_pr = 0
        for j in range(len(norm_vector_alt)):
            try:
                print(f"[DEBUG] Processing criteria {j}, alternative {i}")
                nv_j = norm_vector[j]
                nv_alt_j = norm_vector_alt[j]
                print(f"[DEBUG] norm_vector[{j}]: {nv_j}, type: {type(nv_j)}")
                print(
                    f"[DEBUG] norm_vector_alt[{j}]: {nv_alt_j}, "
                    f"type: {type(nv_alt_j)}"
                )

                if isinstance(norm_vector_alt[j], list) and len(norm_vector_alt[j]) > i:
                    product = norm_vector[j] * norm_vector_alt[j][i]
                    g_pr += product
                else:
                    error_msg = (
                        f"norm_vector_alt[{j}] is not a list or too short: "
                        f"{norm_vector_alt[j]}"
                    )
                    print(f"[ERROR] {error_msg}")
                    raise ValueError(f"norm_vector_alt[{j}] is not a list or too short")

            except Exception as e:
                error_msg = (
                    f"Multiplication failed for criteria {j}, " f"alternative {i}: {e}"
                )
                print(f"ERROR: {error_msg}")
                raise e
        global_prior.append(g_pr)

    return global_prior


# дерево


def generate_hierarchy_tree(
    name_criteria_tree, name_alternatives_tree, priority_vector, global_prior
):
    dot = Digraph()

    # Кольори з CSS-змінних
    color_background = "#0B0C10"
    color_accent = "#66FCF1"
    color_accent_dark = "#05386B"
    color_link = "#8EE4AF"

    # Загальні налаштування
    dot.attr(bgcolor=color_background)  # фон графа
    dot.attr("node", fontcolor=color_background, fontname="Helvetica", fontsize="12")
    dot.attr("edge", color=color_accent_dark, penwidth="1.2", arrowhead="vee")

    # Критерії
    for i, (criteria_name, priority) in enumerate(
        zip(name_criteria_tree, priority_vector)
    ):
        try:
            label = f"{criteria_name}\n({priority:.3f})"
            dot.node(
                f"criteria_{criteria_name}",
                label,
                shape="box",
                style="filled",
                fillcolor=color_accent,
            )
        except Exception as e:
            error_msg = f"Failed to create criteria node {i}: {e}"
            print(f"ERROR: {error_msg}")
            raise e

    # Альтернативи
    for i, (alternative_name, global_priority) in enumerate(
        zip(name_alternatives_tree, global_prior)
    ):
        try:
            label = f"{alternative_name}\n({global_priority:.3f})"
            dot.node(
                f"alternative_{alternative_name}",
                label,
                shape="ellipse",
                style="filled",
                fillcolor=color_link,
            )
            for criteria_name in name_criteria_tree:
                dot.edge(f"criteria_{criteria_name}", f"alternative_{alternative_name}")
        except Exception as e:
            error_msg = f"Failed to create alternative node {i}: {e}"
            print(f"ERROR: {error_msg}")
            raise e

    dot.attr(ranksep="1")
    try:
        dot.render("static/img/hierarchy_tree", format="png", cleanup=True)
    except Exception as e:
        error_msg = f"Failed to render hierarchy tree: {e}"
        print(f"ERROR: {error_msg}")
        raise e
