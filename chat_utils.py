# chat_utils.py

import os
import json
from datetime import datetime
import streamlit as st

CHAT_DIR = "chat_history"

# Ensure chat directory exists
def ensure_chat_directory_exists() -> None:
    os.makedirs(CHAT_DIR, exist_ok=True)

def ensure_directory_exists(directory: str) -> None:
    os.makedirs(directory, exist_ok=True)

# Get available chat dates
def get_chat_dates() -> list:
    try:
        files = sorted(
            [f for f in os.listdir(CHAT_DIR) if f.endswith(".json")],
            reverse=True
        )
        return [os.path.splitext(f)[0] for f in files]
    except FileNotFoundError:
        return []

# Load chat by date
def load_chat_by_date(date_str: str) -> list:
    path = os.path.join(CHAT_DIR, f"{date_str}.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Delete chat by date
def delete_chat_by_date(date_str: str) -> None:
    path = os.path.join(CHAT_DIR, f"{date_str}.json")
    try:
        if os.path.exists(path):
            os.remove(path)
    except (FileNotFoundError, PermissionError):
        pass

# Save chat history
def save_chat_history(messages: list) -> None:
    if not messages:
        return

    ensure_directory_exists(CHAT_DIR)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(CHAT_DIR, f"{timestamp}.json")

    try:
        if isinstance(messages[0], dict) and "model" in messages[0]:
            messages[0]["system_prompt"] = st.session_state.get("custom_system_prompt", "")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
    except (PermissionError, OSError):
        pass

# Clear all chat histories
def clear_all_chats() -> None:
    try:
        for f in os.listdir(CHAT_DIR):
            if f.endswith(".json"):
                os.remove(os.path.join(CHAT_DIR, f))
    except (FileNotFoundError, PermissionError):
        pass
