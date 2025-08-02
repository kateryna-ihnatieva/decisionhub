def check_tranz(a1, a2, a3, i, j, k):
    res = []
    i += 1
    j += 1
    k += 1

    if a1 == 1:
        if a2 == 1:
            res.append(f'a{i} > a{j}, a{j} > a{k}')

            # Відношення
            if a3 == 1:
                res.append(f'a{i} > a{k}')
                res.append('+')
            else:
                if a3 == -1:
                    res.append(f'a{i} < a{k}')
                else:
                    res.append(f'a{i} = a{k}')
                res.append('-')

        else:
            if a2 == 0:
                res.append(f'a{i} > a{j}, a{j} = a{k}')
            else:
                res.append(f'a{i} > a{j}, a{j} < a{k}')
            res.append('транзитивність не може бути перевірено')
            res.append('')

    elif a1 == 0:
        if a2 == 0:
            res.append(f'a{i} = a{j}, a{j} = a{k}')

            # Відношення
            if a3 == 0:
                res.append(f'a{i} = a{k}')
                res.append('+')
            else:
                if a3 == -1:
                    res.append(f'a{i} < a{k}')
                else:
                    res.append(f'a{i} > a{k}')
                res.append('-')

        else:
            if a2 == 1:
                res.append(f'a{i} = a{j}, a{j} > a{k}')
            else:
                res.append(f'a{i} = a{j}, a{j} < a{k}')
            res.append('транзитивність не може бути перевірено')
            res.append('')

    else:
        if a2 == -1:
            res.append(f'a{i} < a{j}, a{j} < a{k}')

            # Відношення
            if a3 == -1:
                res.append(f'a{i} < a{k}')
                res.append('+')
            else:
                if a3 == 1:
                    res.append(f'a{i} > a{k}')
                else:
                    res.append(f'a{i} = a{k}')
                res.append('-')

        else:
            if a2 == 0:
                res.append(f'a{i} < a{j}, a{j} = a{k}')
            else:
                res.append(f'a{i} < a{j}, a{j} > a{k}')
            res.append('транзитивність не може бути перевірено')
            res.append('')

    return res


# функція для обробки матриці
def process_matrix(matrix, num):
    processed_matrix = []
    for i in range(0, len(matrix), num):
        processed_matrix.append(matrix[i:i + num])
    for i in range(num):
        for j in range(num):
            if i > j:
                processed_matrix[i][j] = -int(processed_matrix[j][i])
            elif i == j:
                processed_matrix[i][j] = 0
            else:
                processed_matrix[i][j] = int(processed_matrix[i][j])
    return processed_matrix
