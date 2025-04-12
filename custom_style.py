# custom_style.py

import streamlit as st

# Inject custom CSS for chat input and layout
def inject_chat_input_style() -> None:
    """
    Inject custom CSS to fix input bar at bottom, remove white bar, and adjust layout.
    """
    st.markdown("""
        <style>
        #chat_input_box {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #1e1e1e;
            padding: 1rem;
            z-index: 9999;
            box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.3);
        }

        .block-container {
            padding-bottom: 230px !important;
        }

        footer, header, .stDeployButton, div[data-testid="stStatusWidget"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        html, body {
            margin: 0 !important;
            padding: 0 !important;
            overflow-x: hidden !important;
            background-color: #0e1117 !important;
        }

        [data-testid="stVerticalBlock"] {
            padding-bottom: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)
