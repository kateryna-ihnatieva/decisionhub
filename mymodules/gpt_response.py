from g4f.client import Client
from g4f.errors import RetryProviderError

# Константи для моделі та повідомлення
GPT_MODEL = 'gpt-3.5-turbo'
GPT_PROMPT_MESSAGE = 'Напиши короткий результат. 1-2 речення. Врахуй тільки ранжування.'

# Ініціалізація клієнта GPT
client = Client()


def generate_gpt_response_experts(task, names, ranj):
    prompt = task + '\n' + 'Назва напрямку дослідження:\n'
    for i, obj in enumerate(names, start=1):
        prompt += f'{i}. {obj}\n'

    prompt += f'Отримане ранжування {ranj}\n'
    prompt += GPT_PROMPT_MESSAGE

    return _generate_gpt_response(prompt)


def generate_gpt_response_mai(task, alternatives, criteria, data):
    prompt = task + '\n' + 'Критерії:\n'
    for i, criterion in enumerate(criteria, start=1):
        prompt += f'{i}. {criterion}\n'
    prompt += 'Альтернативи:\n'
    for j, alternative in enumerate(alternatives, start=1):
        prompt += f'{j}. {alternative};\n'

    prompt += f'Отримане ранжування {data}\n'
    prompt += GPT_PROMPT_MESSAGE

    return _generate_gpt_response(prompt)


def generate_gpt_response_binary(task, names, ranj):
    prompt = task + '\n' + 'Імена обєктів:\n'
    for i, obj in enumerate(names, start=1):
        prompt += f'{i}. {obj}\n'

    prompt += f'Отримане ранжування {ranj}\n'
    prompt += GPT_PROMPT_MESSAGE

    return _generate_gpt_response(prompt)


def generate_gpt_response_mai(task, alternatives, criteria, data):
    prompt = task + '\n' + 'Критерії:\n'
    for i, criterion in enumerate(criteria, start=1):
        prompt += f'{i}. {criterion}\n'
    prompt += 'Альтернативи:\n'
    for j, alternative in enumerate(alternatives, start=1):
        prompt += f'{j}. {alternative};\n'

    prompt += f'Отримане ранжування {data}\n'
    prompt += GPT_PROMPT_MESSAGE

    return _generate_gpt_response(prompt)


def _generate_gpt_response(prompt):
    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
        )
        if response.choices and response.choices[0].message:
            return response.choices[0].message.content.strip()
        else:
            print("Отримано некоректну відповідь від сервера GPT.")
            return None
    except RetryProviderError as e:
        print("RetryProviderError виникла при спробі звернутися до сервера GPT:", e)
        return None
    except Exception as ex:
        print("Сталася невідома помилка:", ex)
        return None
