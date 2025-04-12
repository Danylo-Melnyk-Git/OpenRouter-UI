import os
import tempfile
import shutil

# Removed unused imports and added error handling for imports
try:
    import streamlit as st
    import traceback
    from utils import (
        calculate_token_stats,
        parse_uploaded_files,
        init_openai,
        fetch_available_models
    )
    from chat_utils import (
        get_chat_dates,
        load_chat_by_date,
        delete_chat_by_date,
        save_chat_history,
        clear_all_chats
    )
    from custom_style import inject_chat_input_style
except ImportError as e:
    st.error(f"Failed to import a module: {e}")

# Use environment variable for base URL
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Added comment for clarity
# Key used to track the last selected model in session state
LAST_MODEL_KEY = "__last_model_for_switch_check__"

# Added type hints and error handling for initialize_session_state
def initialize_session_state(defaults: dict) -> None:
    if not isinstance(defaults, dict):
        raise ValueError("Defaults must be a dictionary.")
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Added type hints and optimized rerun logic in handle_model_switch
def handle_model_switch(selected: str, models: list, multimodal: list) -> None:
    if LAST_MODEL_KEY not in st.session_state:
        st.session_state[LAST_MODEL_KEY] = selected

    if selected != st.session_state[LAST_MODEL_KEY]:
        if st.session_state.messages:
            save_chat_history([{
                "model": st.session_state[LAST_MODEL_KEY],
                "meta": {
                    "temperature": st.session_state.temperature,
                    "top_p": st.session_state.top_p,
                    "presence_penalty": st.session_state.presence_penalty,
                    "frequency_penalty": st.session_state.frequency_penalty,
                    "max_tokens": st.session_state.max_tokens,
                },
                "system_prompt": st.session_state.custom_system_prompt
            }] + st.session_state.messages)
        st.session_state.update({
            LAST_MODEL_KEY: selected,
            "messages": []
        })
        st.rerun()

    st.session_state.selected_model = selected

def render_model_info(selected, model_info, multimodal):
    meta = model_info.get(selected, {})
    pricing = meta.get("pricing", {})
    context_limit = meta.get("context_length", 4096)
    st.session_state.context_limit = context_limit

    if st.session_state.max_tokens > context_limit:
        st.session_state.max_tokens = context_limit

    with st.expander("Model Info & Pricing"):
        st.markdown(f"- Prompt: {pricing.get('prompt', 'nd')} $/1M tokens")
        st.markdown(f"- Completion: {pricing.get('completion', 'nd')} $/1M tokens")
        st.markdown(f"- Image: {pricing.get('image', 'nd')} $/image")
        st.markdown(f"- Context: {context_limit} tokens")

    is_multimodal = meta.get("architecture", {}).get("modality", "").startswith("text+image")
    st.markdown(f"**Multimodal:** {'✅ Yes' if is_multimodal else '❌ No'}")

def render_chat_history():
    st.markdown("### 💬 Chat History")
    chat_dates = get_chat_dates()

    if chat_dates:
        selected_date = st.selectbox(
            "Select a chat session:",
            options=[f"{date} ({load_chat_by_date(date)[0].get('model', 'unknown')})" for date in chat_dates],
            key="chat_history_selector"
        )

        if st.button("Load Selected Chat"):
            selected_date_only = selected_date.split(" (")[0]
            st.session_state.messages = load_chat_by_date(selected_date_only)[1:]
            st.rerun()

        if st.button("Delete Selected Chat"):
            selected_date_only = selected_date.split(" (")[0]
            delete_chat_by_date(selected_date_only)
            st.rerun()
    else:
        st.markdown("No chat history available.")

def render_left_panel(api_key, models, multimodal, model_info, config):
    st.markdown("### Settings")
    st.session_state.api_key = st.text_input("API Key", type="password", value=api_key)

    st.markdown("### Model Selection")
    all_models = models + multimodal
    selected = st.selectbox(
        "Select Model", 
        all_models,
        index=all_models.index(st.session_state.get("selected_model", models[0])) 
        if st.session_state.get("selected_model") in all_models else 0
    )

    handle_model_switch(selected, models, multimodal)
    st.markdown(f"#### Active: {selected}")

    render_model_info(selected, model_info, multimodal)

    st.session_state.input_height = st.slider("Chat Input Height", 60, 300, st.session_state.input_height)

    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.attached_text = ""
        st.rerun()

    render_chat_history()

if "messages" not in st.session_state:
    st.session_state.messages = []

def render_chat_center(model_info, multimodal_models):
    inject_chat_input_style()
    updated = False
    mdl = st.session_state.get("selected_model", "")

    for m in reversed(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"], unsafe_allow_html=True)

    st.markdown("<div id='end_of_chat'></div>", unsafe_allow_html=True)

    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []

    file_context, img64_list = parse_uploaded_files(st.session_state.uploaded_files)

    st.markdown('<div id="chat_input_box">', unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        prompt = st.text_area("Type your message...", key="chat_input", label_visibility="collapsed", height=st.session_state.input_height)
        files = st.file_uploader(
            "Drag and drop files here or click to upload",
            type=["png", "jpg", "jpeg", "pdf", "docx", "txt"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        if files:
            st.session_state.uploaded_files.extend(files)
            st.markdown("### Uploaded Files:")
            for file in st.session_state.uploaded_files:
                st.markdown(f"- {file.name}")
        submitted = st.form_submit_button("Send")
    st.markdown('</div>', unsafe_allow_html=True)

    if submitted and prompt.strip():
        if not mdl:
            st.warning("Select a model first")
            return False

        multimodal = model_info.get(mdl, {}).get("multimodal", False) or mdl in multimodal_models
        file_context = file_context.strip()

        if multimodal and img64_list:
            content = [{"type": "text", "text": prompt + (f"\n\n[File Context]:\n{file_context}" if file_context else "")}]
            content += [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}} for img in img64_list]
        else:
            if img64_list:
                st.warning("Selected model doesn't support images. Only text will be sent.")
            content = prompt + (f"\n\n[File Context]:\n{file_context}" if file_context else "")

        st.session_state.attached_text = ""

        system_prompt = {
            "role": "system",
            "content": st.session_state.custom_system_prompt
        }

        st.session_state.messages.append({"role": "user", "content": content})

        client = init_openai(
            api_key=st.session_state.api_key
        )

        with st.chat_message("user"):
            st.markdown(prompt, unsafe_allow_html=True)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                msgs = [system_prompt] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                completion = client.chat.completions.create(
                    model=mdl,
                    messages=msgs,
                    temperature=st.session_state.temperature,
                    max_tokens=st.session_state.max_tokens,
                    top_p=st.session_state.top_p,
                    presence_penalty=st.session_state.presence_penalty,
                    frequency_penalty=st.session_state.frequency_penalty
                )
                result = completion.choices[0].message.content
                placeholder.markdown(result, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": result})
                updated = True
            except Exception as e:
                st.error(f"Err: {e}")
                st.code(traceback.format_exc())

    st.components.v1.html("""
        <script>
            const el = document.getElementById("end_of_chat");
            if (el) {
                el.scrollIntoView({ behavior: "smooth" });
            }
        </script>
    """, height=0)

    return updated

# Cleanup temporary files on app exit
import atexit
@atexit.register
def cleanup_temp_files():
    if "temp_dir" in st.session_state:
        shutil.rmtree(st.session_state.temp_dir)

def render_right_panel(model_info):
    with st.expander("📊 Token Stats", expanded=True):
        selected = st.session_state.selected_model
        if not selected:
            st.warning("No model selected")
            return

        meta = model_info.get(selected, {})
        context_limit = meta.get("context_length", 4096)
        fixed_settings = meta.get("fixed_params", {})

        stats = calculate_token_stats(st.session_state.messages, meta)

        st.markdown(f"**Input tokens:** {stats['input_tokens']}")
        st.markdown(f"**Output tokens:** {stats['output_tokens']}")
        st.markdown(f"**Total tokens:** {stats['total_tokens']}")
        st.markdown("---")
        st.markdown(f"**Input cost:** ${stats['input_cost']}")
        st.markdown(f"**Output cost:** ${stats['output_cost']}")
        st.markdown(f"**Total cost:** **${stats['total_cost']}**")

        def slider_or_fixed(label, key, min_val, max_val, step, default):
            fixed = fixed_settings.get(key)
            if fixed is not None:
                st.markdown(f"**{label}**: `{fixed}` (fixed)")
                st.session_state[key] = fixed
            else:
                st.session_state[key] = st.slider(
                    label,
                    min_value=min_val,
                    max_value=max_val,
                    value=st.session_state.get(key, default),
                    step=step
                )

        slider_or_fixed("Max tokens", "max_tokens", 64, context_limit, 32, 2048)
        slider_or_fixed("Temperature", "temperature", 0.0, 1.0, 0.05, 0.7)
        slider_or_fixed("Top-p", "top_p", 0.0, 1.0, 0.05, 1.0)
        slider_or_fixed("Presence penalty", "presence_penalty", -2.0, 2.0, 0.1, 0.0)
        slider_or_fixed("Frequency penalty", "frequency_penalty", -2.0, 2.0, 0.1, 0.0)

        st.session_state.context_limit = context_limit

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔁 Refresh models"):
                models, multimodal, model_info = fetch_available_models(st.session_state.api_key)
                st.session_state.saved_models = models
                st.session_state.saved_multimodal = multimodal
                st.session_state.model_info = model_info
                st.rerun()
        with col2:
            if st.button("🧹 Reset config"):
                import os
                if os.path.exists("config.json"):
                    os.remove("config.json")
                st.rerun()

        st.markdown("---")
        if st.button("🗑️ Clear Chat History"):
            clear_all_chats()
            st.session_state.messages = []
            st.session_state.attached_text = ""
            st.rerun()

    with st.expander("System Prompt Editor"):
        st.session_state.custom_system_prompt = st.text_area(
            "Set a custom system prompt:",
            value=st.session_state.get("custom_system_prompt", ""),
            height=100
        )
