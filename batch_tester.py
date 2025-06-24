import json
import os
import time
import requests
from datetime import datetime

API_KEY = ""
API_URL = 'https://openrouter.ai/api/v1/chat/completions'

RETRY_COUNT = 3
RESULTS_DIR = 'batch_results'


def load_scenario(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def read_text_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[Ошибка чтения файла {file_path}: {e}]"

def send_request_to_api(model, system_prompt, user_prompt):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        return response
    except requests.exceptions.Timeout:
        print(f"[ERROR] Timeout while requesting model: {model}")
        return None
    except Exception as e:
        print(f"[ERROR] Exception while requesting model {model}: {e}")
        return None

# Проверка доступности модели
# def is_model_available(model):
#     headers = {
#         'Authorization': f'Bearer {API_KEY}',
#         'Content-Type': 'application/json',
#     }
#     payload = {
#         'model': model,
#         'messages': [
#             {'role': 'system', 'content': 'ping'},
#             {'role': 'user', 'content': 'ping'}
#         ]
#     }
#     try:
#         resp = requests.post(API_URL, headers=headers, json=payload, timeout=10)
#         return resp.status_code == 200
#     except Exception:
#         return False

def save_result(model, task_name, result_data):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    model_safe = model.replace('/', '-').replace(':', '-')
    now = datetime.now().strftime('%Y-%m-%d_%H-%M')
    filename = f"{model_safe}__{task_name}__{now}.json"
    with open(os.path.join(RESULTS_DIR, filename), 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

def main():
    scenario = load_scenario('scenario.json')
    for model in scenario['models']:
        # print(f"[INFO] Checking model availability: {model}")
        # if not is_model_available(model):
        #     print(f"[ERROR] Model {model} is not available. Skipping.")
        #     continue
        for i, task in enumerate(scenario['tasks']):
            attempt = 0
            success = False
            error_info = None
            start_time = datetime.now().isoformat()
            t0 = time.time()
            # Используем только текстовые файлы для описания задания
            attachment_path = task['attachments']['text']
            task_file = os.path.basename(attachment_path)
            task_name = os.path.splitext(task_file)[0]
            file_content = read_text_file(attachment_path)
            # Добавляем содержимое файла к user_prompt
            user_prompt = f"{task['user_prompt']}\n\n[Описание задания из файла]:\n{file_content}"
            while attempt < RETRY_COUNT and not success:
                try:
                    response = send_request_to_api(
                        model,
                        task['system_prompt'],
                        user_prompt
                    )
                    if response is not None and response.status_code == 200:
                        answer = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
                        success = True
                    else:
                        answer = None
                        error_info = {
                            'status_code': response.status_code if response is not None else None,
                            'text': response.text if response is not None else None
                        }
                except Exception as e:
                    answer = None
                    error_info = {'exception': str(e)}
                finally:
                    # Сохраняем результат даже если программа была прервана или возникла ошибка
                    duration = round(time.time() - t0, 3)
                    result = {
                        'model': model,
                        'system_prompt': task['system_prompt'],
                        'user_prompt': user_prompt,
                        'attachments': [attachment_path],
                        'answer': answer,
                        'error': error_info if not success else None,
                        'timestamp': start_time,
                        'duration_sec': duration,
                        'attempts': attempt + 1
                    }
                    save_result(model, task_name, result)
                if not success:
                    time.sleep(5)  # Задержка между попытками
            time.sleep(5)  # Задержка между задачами для одной модели

if __name__ == '__main__':
    main()
