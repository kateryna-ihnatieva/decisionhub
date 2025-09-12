import operator
from fractions import Fraction
from graphviz import Digraph
from jinja2.runtime import Undefined


# Створення списку з матриць по рівнях
def do_matrix(krit=0, matrix=0, criteria=0, num_alt=0):
    def process_matrix_element(matr, i, j):
        value = matr[j][i]

        # Если значение пустое или Undefined — ставим 1 по умолчанию
        if value is None or isinstance(value, Undefined) or str(value).strip() == "":
            matr[i][j] = "1"
            return

        if "/" in str(value):
            try:
                frac = Fraction(str(value))
                matr[i][j] = str(frac.denominator)
            except Exception:
                matr[i][j] = "1"
        else:
            try:
                n = int(value)
                matr[i][j] = str(Fraction(1, n))
            except (ValueError, TypeError):
                try:
                    n = float(value)
                    if n == 0:
                        matr[i][j] = "1"
                    elif n >= 1:
                        matr[i][j] = str(Fraction(1, n))
                    else:
                        frac = Fraction(n).limit_denominator()
                        matr[i][j] = str(frac.denominator)
                except Exception:
                    matr[i][j] = "1"

    matr = []
    if krit:
        matr = [matrix[i : i + criteria] for i in range(0, criteria**2, criteria)]
        for i in range(len(matr)):
            for j in range(len(matr[i])):
                if i > j:
                    process_matrix_element(matr, i, j)
    else:
        for i in range(criteria):
            matr.append(
                [matrix[j : j + num_alt] for j in range(0, num_alt**2, num_alt)]
            )
            matrix = matrix[num_alt**2 :]

        # Змінюємо елементи нижньої трикутної матриці
        for m in matr:
            for i in range(len(m)):
                for j in range(len(m[i])):
                    if i > j:
                        process_matrix_element(m, i, j)

    return matr


# Оцінки компонент власного вектора
def do_comp_vector(krit=0, criteria=0, matr=0, num_alt=0):
    comp_vector = [[] for _ in range(criteria)] if krit == 0 else []
    if krit:
        for c in range(criteria):
            dob = 1
            for i, num in enumerate(matr[c]):
                try:
                    eval_result = eval(str(num))
                    dob *= eval_result
                except Exception as e:
                    print(f"ERROR: Failed to eval '{num}': {e}")
                    raise e
            result = dob ** (1 / criteria)
            comp_vector.append(result)
    else:
        for count in range(criteria):
            for c in range(num_alt):
                dob = 1
                for i, num in enumerate(matr[count][c]):
                    try:
                        eval_result = eval(str(num))
                        dob *= eval_result
                    except Exception as e:
                        print(f"ERROR: Failed to eval '{num}': {e}")
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
                    eval_result = eval(str(matr[j][i]))
                    s += eval_result
                except Exception as e:
                    print(f"ERROR: Failed to eval '{matr[j][i]}': {e}")
                    raise e
            sum_col.append(s)
    else:
        for c in range(criteria):
            sum_col[c] = []
            for i in range(num_alt):
                column_sum = 0
                for j in range(num_alt):
                    try:
                        eval_result = eval(str(matr[c][j][i]))
                        column_sum += eval_result
                    except Exception as e:
                        print(f"ERROR: Failed to eval '{matr[c][j][i]}': {e}")
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
    if krit:
        lst_norm_vector = []
        lst_norm_vector.append({})
        for i in range(criteria):
            lst_norm_vector[0][name[i]] = norm_vector[i]

        # сортування списку
        lst_norm_vector[0] = sorted(
            lst_norm_vector[0].items(), key=operator.itemgetter(1), reverse=True
        )
        lst_norm_vector[0] = {k: v for k, v in lst_norm_vector[0]}

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
        ranj = [[] * i for i in range(criteria)]
        flag_key = 0

        for c in range(criteria):
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
    global_prior = []
    for i in range(num_alt):
        g_pr = 0
        for j in range(len(norm_vector_alt)):
            try:
                product = norm_vector[j] * norm_vector_alt[j][i]
                g_pr += product
            except Exception as e:
                print(
                    f"ERROR: Multiplication failed for criteria {j}, alternative {i}: {e}"
                )
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
    color_text = "#EDF5E1"
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
            print(f"ERROR: Failed to create criteria node {i}: {e}")
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
            for j, criteria_name in enumerate(name_criteria_tree):
                dot.edge(f"criteria_{criteria_name}", f"alternative_{alternative_name}")
        except Exception as e:
            print(f"ERROR: Failed to create alternative node {i}: {e}")
            raise e

    dot.attr(ranksep="1")
    try:
        dot.render("static/img/hierarchy_tree", format="png", cleanup=True)
    except Exception as e:
        print(f"ERROR: Failed to render hierarchy tree: {e}")
        raise e
