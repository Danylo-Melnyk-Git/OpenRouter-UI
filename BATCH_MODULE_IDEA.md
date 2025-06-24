# Batch Model Evaluation Module

Модуль для автоматизированного массового тестирования языковых моделей через OpenRouter API. Для каждой выбранной модели автоматически прогоняет одинаковый набор заданий (тасков), где у каждого задания есть свой system prompt, user prompt и прикреплённый файл. Все результаты сохраняются для последующего анализа. Модуль работает как отдельный Python-скрипт без UI.

**Как работает:**
- Задаёшь список моделей для тестирования (например, 5 моделей).
- Задаёшь список тасков (например, 10 штук), у каждого: system prompt, user prompt, файл.
- Для каждой модели прогоняются все таски (каждая модель получает все 10 заданий).
- Все результаты (ответы, ошибки, логи) сохраняются для анализа.

**Пример структуры сценария:**

```json
{
  "models": ["openai/gpt-4o", "google/gemini-pro", ...],
  "tasks": [
    {
      "system_prompt": "...",
      "user_prompt": "...",
      "attachments": ["file1.pdf"]
    },
    {
      "system_prompt": "...",
      "user_prompt": "...",
      "attachments": ["file2.pdf"]
    }
    // ...
  ]
}
```

**Запуск:**
1. Подготовь сценарий в формате JSON или Python-словаря.
2. Запусти модуль командой:
   ```bash
   python batch_tester.py
   ```
3. Результаты появятся в папке `batch_results/`.

---

## Как реализовать модуль (минимально взаимодействуя с другими файлами проекта)

1. Создай отдельный файл, например, `batch_tester.py`.
2. В этом файле реализуй всё необходимое:
   - Загрузку сценария из JSON (или Python-словаря).
   - Функцию отправки запросов к OpenRouter API (можно использовать стандартные библиотеки: `requests` или `httpx`).
   - Обработку вложений (чтение файлов, если нужно отправлять их в API).
   - Сохранение результатов (ответов, ошибок) в папку `batch_results/`.
3. Не импортируй ничего из других файлов проекта, если это не требуется.
4. Примерная структура кода:

```python
import json
import os
import requests  # или httpx

def load_scenario(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def send_request_to_api(model, system_prompt, user_prompt, attachments):
    # Здесь реализуй отправку запроса к OpenRouter API
    # Используй requests.post(...)
    # Пример:
    # response = requests.post(url, headers=headers, json=payload, files=files)
    # return response.json()
    pass

def save_result(model, task_idx, result):
    os.makedirs('batch_results', exist_ok=True)
    with open(f'batch_results/{model}_task{task_idx}.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def main():
    scenario = load_scenario('scenario.json')
    for model in scenario['models']:
        for i, task in enumerate(scenario['tasks']):
            result = send_request_to_api(
                model,
                task['system_prompt'],
                task['user_prompt'],
                task['attachments']
            )
            save_result(model, i, result)

if __name__ == '__main__':
    main()
```

5. Все функции и логика — только внутри `batch_tester.py`. Это не затрагивает другие части проекта и не ломает UI.

---

Модуль предназначен для исследовательских и инженерных задач по сравнению языковых моделей.
