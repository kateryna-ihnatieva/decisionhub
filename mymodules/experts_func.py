def make_table(num_experts, num_research, original_table):
    new_table = []
    for _ in range(num_experts):
        expert_sublist = []
        for _ in range(num_research):
            expert_sublist.append(original_table.pop(0))
        new_table.append(expert_sublist)

    return new_table


def make_m_i(k_k, experts_data_table, num_experts, num_research):
    m_i = []
    for i in range(num_research):
        tmp_value = 0
        for j in range(num_experts):
            tmp_value += float(k_k[j]) * float(experts_data_table[j][i])
        tmp_value /= num_experts
        m_i.append(tmp_value)

    return m_i


def make_r_i(m_i):
    sorted_m_i = sorted(m_i)[::-1]
    r_i = [sorted_m_i.index(x) + 1 for x in m_i]
    return r_i


def make_lambda(num_research, r_i):
    lambda_values = []
    for i in range(num_research):
        tmp_value = 2 * (((num_research + 1) - r_i[i]) / (num_research * (num_research + 1)))
        lambda_values.append(tmp_value)
    return lambda_values


def rank_results(r_i, m_i, name_research):
    r_i_sorted_indices = sorted(range(len(r_i)), key=lambda x: r_i[x], reverse=True)
    m_i_sorted_indices = sorted(range(len(m_i)), key=lambda x: m_i[x], reverse=True)
    rank_str = ""
    for i in range(len(r_i_sorted_indices)):
        rank_str += f"{name_research[m_i_sorted_indices[i]]} > "
    rank_str = rank_str[:-3]  # Прибрати останній " > "
    return rank_str
