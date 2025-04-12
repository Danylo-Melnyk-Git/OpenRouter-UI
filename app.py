# app.py

import os
from typing import Dict, Any, List

# Added error handling for imports
try:
    import streamlit as st
    from utils import (
        load_config,
        save_config,
        fetch_available_models
    )
    from ui import render_left_panel, render_chat_center, render_right_panel
    from chat_utils import save_chat_history, get_chat_dates, load_chat_by_date
    from custom_style import inject_chat_input_style
except ImportError as e:
    st.error(f"Failed to import a module: {e}")

# Added type hints and validation for initialize_session_state
def initialize_session_state(defaults: Dict[str, Any]) -> None:
    if not isinstance(defaults, dict):
        raise ValueError("Defaults must be a dictionary.")
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Added type hints and validation for restore_chat_metadata
def restore_chat_metadata(chat_history: List[Dict[str, Any]], config: Dict[str, Any]) -> None:
    if not isinstance(chat_history, list) or not all(isinstance(item, dict) for item in chat_history):
        raise ValueError("Chat history must be a list of dictionaries.")
    if chat_history and isinstance(chat_history[0], dict) and 'model' in chat_history[0]:
        header = chat_history.pop(0)
        st.session_state.selected_model = header.get('model', config.get("last_selected_model", ""))
        meta = header.get("meta", {})
        st.session_state.temperature = meta.get("temperature", 0.7)
        st.session_state.top_p = meta.get("top_p", 1.0)
        st.session_state.presence_penalty = meta.get("presence_penalty", 0.0)
        st.session_state.frequency_penalty = meta.get("frequency_penalty", 0.0)
        st.session_state.max_tokens = meta.get("max_tokens", 2048)

# Added type hints and validation for validate_selected_model
def validate_selected_model(models: List[str]) -> None:
    if not isinstance(models, list) or not all(isinstance(model, str) for model in models):
        raise ValueError("Models must be a list of strings.")
    if st.session_state.selected_model not in models:
        st.warning("Selected model not found. Resetting to default.")
        st.session_state.selected_model = models[0]

# Added type hints and validation for save_updated_state
def save_updated_state(updated: bool, config: Dict[str, Any]) -> None:
    if not isinstance(updated, bool):
        raise ValueError("Updated must be a boolean.")
    if updated:
        save_chat_history([{
            "model": st.session_state.selected_model,
            "meta": {
                "temperature": st.session_state.temperature,
                "top_p": st.session_state.top_p,
                "presence_penalty": st.session_state.presence_penalty,
                "frequency_penalty": st.session_state.frequency_penalty,
                "max_tokens": st.session_state.max_tokens,
            }
        }] + st.session_state.messages)

        config.update({
            "last_selected_model": st.session_state.selected_model,
            "api_key": st.session_state.api_key
        })
        save_config(config)

st.set_page_config(page_title="OpenRouter Chat", layout="wide")
inject_chat_input_style()

st.markdown("<h1 style='margin-bottom:0'>OpenRouter Local Chat</h1>", unsafe_allow_html=True)
st.caption("Chat with models via OpenRouter API")

config = load_config()
chat_dates = get_chat_dates()
chat_history = load_chat_by_date(chat_dates[0]) if chat_dates else []
restore_chat_metadata(chat_history, config)

# Initialize session state with defaults
defaults = {
    "api_key": config.get("api_key", ""),
    "selected_model": config.get("last_selected_model", ""),
    "temperature": 0.7,
    "top_p": 1.0,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
    "max_tokens": 2048,
    "messages": chat_history,
    "token_input": 0,
    "token_output": 0,
    "token_total": 0,
    "cost_total": 0.0,
    "input_height": 80,
    "custom_system_prompt": ""
}
initialize_session_state(defaults)

if not st.session_state.api_key:
    st.error("API key is missing. Please provide a valid API key in the settings.")
    st.stop()

models, multimodal, model_info = fetch_available_models(st.session_state.api_key)
if not models:
    st.error("No models available or invalid API key. Please check credentials.")
    st.stop()

# Validate selected model
validate_selected_model(models)

st.session_state.saved_models = models
st.session_state.saved_multimodal = multimodal
st.session_state.model_info = model_info

l_col, c_col, r_col = st.columns([1.0, 4.0, 1.0], gap="small")

with l_col:
    render_left_panel(
        api_key=st.session_state.api_key,
        models=[m for m in models if m not in multimodal],
        multimodal=[m for m in models if m in multimodal],
        model_info=model_info,
        config=config
    )

with c_col:
    updated = render_chat_center(
        model_info=model_info,
        multimodal_models=multimodal
    )

with r_col:
    st.markdown("### ℹ️ Model Info")
    render_right_panel(model_info=model_info)

# Save updated state if changes occurred
save_updated_state(updated, config)
