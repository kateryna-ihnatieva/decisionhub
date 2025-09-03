import operator
from fractions import Fraction
from graphviz import Digraph


# Створення списку з матриць по рівнях
def do_matrix(krit=0, matrix=0, criteria=0, num_alt=0):
    def process_matrix_element(matr, i, j):
        value = matr[j][i]
        if "/" in value:
            frac = Fraction(value)
            matr[i][j] = str(frac.denominator)
        else:
            n = int(value)
            matr[i][j] = str(Fraction(1, n))

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
            for num in matr[c]:
                dob *= eval(num)
            comp_vector.append(dob ** (1 / criteria))  # За формулою
    else:
        for count in range(criteria):
            for c in range(num_alt):
                dob = 1
                for num in matr[count][c]:
                    dob *= eval(num)
                comp_vector[count].append(dob ** (1 / num_alt))
    return comp_vector


# Нормалізовані оцінки вектора пріоритету
def do_norm_vector(krit=0, comp_vector=0, criteria=0, num_alt=0):
    norm_vector = [] if krit else [[] for _ in range(criteria)]
    if krit:
        norm_vector = [comp_vector[c] / sum(comp_vector) for c in range(criteria)]
    else:
        for i in range(criteria):
            norm_vector[i] = [
                comp_vector[i][c] / sum(comp_vector[i]) for c in range(num_alt)
            ]

    return norm_vector


# Сума по стовпцям
def do_sum_col(krit=0, matr=0, criteria=0, num_alt=0):
    sum_col = [] if krit else [[] for _ in range(criteria)]
    if krit:
        for i in range(criteria):
            s = 0
            for j in range(criteria):
                s += eval(matr[j][i])
            sum_col.append(s)
    else:
        for c in range(criteria):
            sum_col[c] = [
                sum([eval(matr[c][j][i]) for j in range(num_alt)])
                for i in range(num_alt)
            ]

    return sum_col


# Добуток додатку по стовпцях і нормалізованої оцінки вектора пріоритету
def do_prod_col(krit=0, criteria=0, sum_col=0, norm_vector=0, num_alt=0):
    prod_col = [] if krit else [[] for _ in range(criteria)]
    if krit:
        prod_col = [sum_col[i] * norm_vector[i] for i in range(criteria)]
    else:
        for c in range(criteria):
            prod_col[c] = [sum_col[c][i] * norm_vector[c][i] for i in range(num_alt)]

    return prod_col


# Разом (Lmax)
def do_l_max(krit=0, prod_col=0, criteria=0):
    l_max = [] if krit else [[] for _ in range(criteria)]
    if krit:
        l_max = [sum(prod_col)]
    else:
        for c in range(criteria):
            l_max[c].append(sum(prod_col[c]))

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
            index_consistency.append((l_max[0] - criteria) / (criteria - 1))
            relation_consistency.append(
                (index_consistency[0] / (random_consistency[str(criteria)])) * 100
            )
        else:
            index_consistency.append(0)
            relation_consistency.append(0)

    else:
        if num_alt >= 3:
            for c in range(criteria):
                index_consistency[c].append((l_max[c][0] - num_alt) / (num_alt - 1))
                relation_consistency[c].append(
                    (index_consistency[c][0] / (random_consistency[str(num_alt)])) * 100
                )
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
                ranj_str += (
                    " > "
                    if lst_norm_vector[0][flag_key] > lst_norm_vector[0][key]
                    else " = "
                )
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
                    ranj_str += (
                        " > "
                        if lst_norm_vector[c][c][flag_key] > lst_norm_vector[c][c][key]
                        else " = "
                    )
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
            else:
                ranj_str += (
                    " > "
                    if lst_norm_vector[0][flag_key] > lst_norm_vector[0][key]
                    else " = "
                )
                ranj_str += key
            flag_key = key
        ranj.append(ranj_str)
    return ranj


# Глобальні пріоритети
def do_global_prior(norm_vector=0, norm_vector_alt=0, num_alt=0):
    global_prior = []
    for i in range(num_alt):
        g_pr = sum(
            norm_vector[j] * norm_vector_alt[j][i] for j in range(len(norm_vector_alt))
        )
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
    for criteria_name, priority in zip(name_criteria_tree, priority_vector):
        label = f"{criteria_name}\n({priority:.3f})"
        dot.node(
            f"criteria_{criteria_name}",
            label,
            shape="box",
            style="filled",
            fillcolor=color_accent,
        )

    # Альтернативи
    for alternative_name, global_priority in zip(name_alternatives_tree, global_prior):
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

    dot.attr(ranksep="1")
    dot.render("static/img/hierarchy_tree", format="png", cleanup=True)
