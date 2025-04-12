# 🧠 OpenRouter Local Chat (Streamlit UI)

A local chat interface for interacting with Large Language Models (LLMs) via the [OpenRouter API](https://openrouter.ai). Built with **Streamlit**, this app provides a user-friendly interface for managing conversations, adjusting model parameters, and handling multimodal inputs.

---

## 🚀 Features

- **Chat History Management**: Save and load chat sessions with metadata (model, temperature, etc.).
- **Dynamic Model Selection**: Supports multiple models via OpenRouter, including multimodal models.
- **Customizable Parameters**: Adjust generation settings like temperature, top-p, and token limits.
- **File Upload Support**: Drag-and-drop support for PDFs, Word documents, and images.
- **Multimodal Input**: Automatically extracts text from files and integrates it into the chat context.
- **Real-Time Updates**: Automatically scrolls to the latest message in the chat.
- **Configurable UI**: Customize the chat input height, site name, and other UI elements.

---

## 🛠 Installation

### Prerequisites
- Python 3.8 or higher
- An API key from [OpenRouter](https://openrouter.ai)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/openrouter-chat.git
   cd openrouter-chat
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   streamlit run app.py
   ```

---

## 📂 Project Structure

```
.
├── app.py                # Main Streamlit app
├── ui.py                 # UI logic for left, center, and right panels
├── utils.py              # Utility functions for configuration, file parsing, etc.
├── chat_utils.py         # Chat history management
├── custom_style.py       # Custom CSS for UI styling
├── requirements.txt      # Python dependencies
├── chat_history/         # Directory for saved chat sessions (auto-created)
└── README.md             # Project documentation
```

---

## 🔑 API Key Setup

To use the app, you need an API key from OpenRouter. Once you have the key:
1. Launch the app.
2. Enter your API key in the **Settings** section of the left panel.

---

## 🧩 Supported File Inputs

The app supports the following file types for multimodal input:
- **PDF** (`.pdf`)
- **Word Documents** (`.docx`)
- **Images** (`.jpg`, `.jpeg`, `.png`)
- **Text Files** (`.txt`)

Uploaded files are processed, and their content is automatically added to the chat context.

---

## ⚙️ Customization

### Adjusting Fixed Parameters
To enforce fixed parameters for specific models, modify the `fetch_available_models` function in `utils.py`:
```python
if m["id"] == "mistral/small":
    m["fixed_params"] = {"temperature": 0.0, "top_p": 1.0}
```

### UI Customization
You can adjust the chat input height, site name, and other UI elements in the **Settings** section of the left panel.

---

## 🧠 Developer Notes

### Debugging
- Logs and errors are displayed directly in the Streamlit app for easier debugging.
- Ensure the `chat_history/` directory is writable for saving chat sessions.

### Extending the App
- Add new file types for multimodal input by extending the `parse_uploaded_files` function in `utils.py`.
- Integrate additional APIs or models by modifying the `fetch_available_models` and `init_openai` functions.

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve the app.