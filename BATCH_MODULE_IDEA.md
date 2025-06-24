# Batch Model Evaluation Module

This module is for automated batch testing of language models via the OpenRouter API. For each selected model, it runs the same set of tasks (each with its own system prompt, user prompt, and attached file). All results are saved for later analysis. The module is a standalone Python script with no UI.

**How it works:**
- Define a list of models to test (e.g., 5 models).
- Define a list of tasks (e.g., 10 tasks), each with: system prompt, user prompt, and a file.
- Every model is tested on every task (each model gets all 10 tasks).
- All results (answers, errors, logs) are saved for analysis.

**Scenario structure example:**

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

**How to run:**
1. Prepare your scenario as a JSON file or Python dict.
2. Run the module:
   ```bash
   python batch_tester.py
   ```
3. Results will appear in the `batch_results/` folder.

---

## Minimal integration (no dependencies on other project files)

1. Create a separate file, e.g., `batch_tester.py`.
2. Implement everything in this file:
   - Load scenario from JSON (or Python dict).
   - Function to send requests to OpenRouter API (use `requests` or `httpx`).
   - Handle attachments (read files if needed for the API).
   - Save results (answers, errors) to `batch_results/`.
3. Do not import anything from other project files unless absolutely necessary.
4. Example code structure:

```python
import json
import os
import requests  # or httpx

def load_scenario(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def send_request_to_api(model, system_prompt, user_prompt, attachments):
    # Implement sending a request to OpenRouter API here
    # Use requests.post(...)
    # Example:
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

5. All logic and functions should be inside `batch_tester.py`. This does not affect other parts of the project and does not break the UI.

---

This module is intended for research and engineering tasks to compare language models.
