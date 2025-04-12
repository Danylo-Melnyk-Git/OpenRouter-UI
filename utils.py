import os
import json
import requests
import base64
import docx
from PyPDF2 import PdfReader
from openai import OpenAI  # OpenRouter-compatible client
from typing import List, Dict, Any, Tuple

CONFIG_FILE = "config.json"
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Added type hints for MODEL_CONFIG_SCHEMA
def get_model_config_schema() -> Dict[str, Dict[str, Any]]:
    return {
        "temperature": {
            "type": "float",
            "range": [0.0, 2.0],
            "default": 1.0
        },
        "top_p": {
            "type": "float",
            "range": [0.0, 1.0],
            "default": 1.0
        },
        "context_length": {
            "type": "integer",
            "range": [1, 1000000],
            "default": 4096
        },
        "modality": {
            "type": "string",
            "allowed_values": ["text->text", "text+image->text"],
            "default": "text->text"
        },
        "fixed_params": {
            "type": "dict",
            "default": {}
        },
        "multimodal": {
            "type": "boolean",
            "default": False
        },
        "top_k": {
            "type": "integer",
            "range": [0, 1000],
            "default": 0
        },
        "frequency_penalty": {
            "type": "float",
            "range": [-2.0, 2.0],
            "default": 0.0
        },
        "presence_penalty": {
            "type": "float",
            "range": [-2.0, 2.0],
            "default": 0.0
        },
        "repetition_penalty": {
            "type": "float",
            "range": [0.0, 2.0],
            "default": 1.0
        },
        "max_tokens": {
            "type": "integer",
            "range": [1, 100000],
            "default": 1000
        },
        "logit_bias": {
            "type": "dict",
            "default": {}
        },
        "structured_outputs": {
            "type": "boolean",
            "default": False
        },
        "stop": {
            "type": "list",
            "default": []
        }
    }

MODEL_CONFIG_SCHEMA = get_model_config_schema()

# Load configuration file
def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_FILE):
        print("Config file not found. Creating a new one.")
        return create_default_config()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("Config file is corrupted. Recreating it.")
        return create_default_config()
    except Exception as e:
        print(f"Unexpected error loading config: {e}")
        return create_default_config()

# Create default configuration
def create_default_config() -> Dict[str, Any]:
    try:
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        models, multimodal, model_info = fetch_available_models(api_key)

        active_models = [
            model_id for model_id, info in model_info.items()
            if info.get("pricing", {}).get("prompt", 0) > 0 or info.get("pricing", {}).get("completion", 0) > 0
        ]

        default = {
            "api_key": api_key,
            "saved_models": active_models,
            "saved_multimodal": multimodal,
            "model_info": {model_id: model_info[model_id] for model_id in active_models},
            "last_selected_model": active_models[0] if active_models else "",
        }

        save_config(default)
        return default
    except Exception as e:
        print(f"Error creating default config: {e}")
        return {
            "api_key": "",
            "saved_models": [],
            "saved_multimodal": [],
            "model_info": {},
            "last_selected_model": "",
        }

# Save configuration to file
def save_config(config: Dict[str, Any]) -> None:
    try:
        existing = load_config()
        config["saved_models"] = sorted(set(config.get("saved_models", [])))
        config["saved_multimodal"] = sorted(set(config.get("saved_multimodal", [])))
        config["model_info"].update(existing.get("model_info", {}))
    except Exception:
        pass

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def remove_model_from_config(model_id):
    config = load_config()
    config["saved_models"] = [m for m in config.get("saved_models", []) if m != model_id]
    config["saved_multimodal"] = [m for m in config.get("saved_multimodal", []) if m != model_id]
    config["model_info"].pop(model_id, None)
    save_config(config)

# Fetch available models from API
def fetch_available_models(api_key: str) -> Tuple[List[str], List[str], Dict[str, Any]]:
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "",
            "X-Title": ""
        }
        res = requests.get(f"{OPENROUTER_BASE_URL}/models", headers=headers)
        res.raise_for_status()

        models_data = res.json().get("data", [])

        models, multimodal, model_info = parse_model_data(models_data)

        config = load_config()
        config.update({"model_info": model_info, "saved_models": models, "saved_multimodal": multimodal})
        save_config(config)

        return models, multimodal, model_info
    except Exception:
        return [], [], {}

# Parse model data
def parse_model_data(models_data: List[Dict[str, Any]]) -> Tuple[List[str], List[str], Dict[str, Any]]:
    models = [m["id"] for m in models_data]
    multimodal = [
        m["id"] for m in models_data
        if m.get("multimodal", False) or any(tag in m.get("tags", []) for tag in ["multimodal", "vision", "image", "audio"])
    ]
    model_info = {
        m["id"]: {
            **m,
            "pricing": m.get("pricing", {"input": 0.0, "output": 0.0}),
            "context_length": int(m.get("context_length", 4096)),
            "fixed_params": {"temperature": 0.0, "top_p": 1.0} if m["id"] == "mistral/small" else {}
        }
        for m in models_data
    }
    return models, multimodal, model_info

def init_openai(api_key, site_url="", site_name=""):
    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        default_headers={
            "HTTP-Referer": site_url,
            "X-Title": site_name
        }
    )

def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    return ""

def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def extract_text_from_docx(uploaded_file):
    doc = docx.Document(uploaded_file)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def image_to_base64(uploaded_image):
    return base64.b64encode(uploaded_image.read()).decode("utf-8") if uploaded_image else None

def parse_uploaded_files(files):
    attached_text = []
    image_base64_list = []
    for f in files or []:
        if f.name.endswith((".pdf", ".docx", ".txt")):
            attached_text.append(extract_text_from_file(f) if not f.name.endswith(".txt") else f.read().decode("utf-8"))
        elif f.name.endswith((".jpg", ".jpeg", ".png")):
            image_base64_list.append(image_to_base64(f))
    return "\n".join(attached_text).strip(), image_base64_list

def calculate_token_stats(messages, model_meta):
    pricing = model_meta.get("pricing", {"input": 0.0, "output": 0.0})
    input_price_per_token = pricing.get("input", 0.0) / 1_000_000
    output_price_per_token = pricing.get("output", 0.0) / 1_000_000

    input_tokens = sum(len(m["content"].split()) for m in messages if m["role"] == "user")
    output_tokens = sum(len(m["content"].split()) for m in messages if m["role"] == "assistant")
    total_tokens = input_tokens + output_tokens
    input_cost = input_tokens * input_price_per_token
    output_cost = output_tokens * output_price_per_token

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(input_cost + output_cost, 6),
        "context_limit": model_meta.get("context_length", 4096)
    }

def format_chat_metadata(chat_header):
    model = chat_header.get("model", "unknown")
    meta = chat_header.get("meta", {})
    return (
        f"**Model**: `{model}`  \n"
        f"**Temperature**: `{meta.get('temperature', '—')}`  \n"
        f"**Top-p**: `{meta.get('top_p', '—')}`  \n"
        f"**Presence penalty**: `{meta.get('presence_penalty', '—')}`  \n"
        f"**Frequency penalty**: `{meta.get('frequency_penalty', '—')}`  \n"
        f"**Max tokens**: `{meta.get('max_tokens', '—')}`"
    )

def validate_model_config(model_id, model_info):
    config = {}
    for key, schema in MODEL_CONFIG_SCHEMA.items():
        value = model_info.get(key, schema.get("default"))
        if schema["type"] == "float" and not (schema["range"][0] <= value <= schema["range"][1]):
            value = schema["default"]
        elif schema["type"] == "integer" and not (schema["range"][0] <= value <= schema["range"][1]):
            value = schema["default"]
        elif schema["type"] == "string" and value not in schema.get("allowed_values", []):
            value = schema["default"]
        elif schema["type"] == "boolean" and not isinstance(value, bool):
            value = schema["default"]
        config[key] = value
    return config

def is_multimodal(model_id, model_info):
    architecture = model_info.get(model_id, {}).get("architecture", {})
    input_modalities = architecture.get("input_modalities", [])
    return "image" in input_modalities or "video" in input_modalities

def get_chat_dates():
    try:
        chat_files = os.listdir("chat_history")
        return [
            os.path.splitext(chat_file)[0]
            for chat_file in chat_files
            if chat_file.endswith(".json")
        ]
    except FileNotFoundError:
        print("Chat history folder not found. Creating it.")
        os.makedirs("chat_history", exist_ok=True)
        return []
    except Exception as e:
        print(f"Unexpected error reading chat history: {e}")
        return []

if __name__ == "__main__":
    # Placeholder to avoid empty block error
    print("Utils module executed directly.")
