import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

DATA_PATH = os.path.join("data", "food_info.json")
LOG_PATH = os.path.join("data", "admin_logs.json")

st.set_page_config(page_title="🛠️ Admin Dashboard", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #607D8B, #00BCD4);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .stButton > button {
        background-color: #607D8B;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #455A64;
    }
</style>
""", unsafe_allow_html=True)

def log_action(action, details):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details
    }
    logs = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
            except:
                logs = []
    logs.append(log_entry)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

def load_food_data():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_food_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_logs():
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

st.markdown("""
<div class="main-header">
    <h1>🛠️ Admin Dashboard</h1>
    <p>Manage Food Database, Audit Logs, and Safety Flags</p>
</div>
""", unsafe_allow_html=True)

# Tabs
main_tab = st.tabs(["🍲 Food Database"])[0]

with main_tab:
    st.header("🍲 Food Database Management")
    food_data = load_food_data()
    df = pd.DataFrame(food_data)
    if not df.empty:
        st.dataframe(df[[col for col in df.columns if col != 'CompositionPer100g']], use_container_width=True)
    else:
        st.info("No food data available.")

    # Add and Edit/Remove Food functionality removed as requested.

    # Removed the import_tab block as it is now invalid and empty.

