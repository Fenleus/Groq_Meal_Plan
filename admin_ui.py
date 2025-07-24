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
main_tab, import_tab, logs_tab = st.tabs(["🍲 Food Database", "⬆️⬇️ Import/Export", "📜 Logs & Audit Trail"])

with main_tab:
    st.header("🍲 Food Database Management")
    food_data = load_food_data()
    df = pd.DataFrame(food_data)
    if not df.empty:
        st.dataframe(df[[col for col in df.columns if col != 'CompositionPer100g']], use_container_width=True)
    else:
        st.info("No food data available.")

    st.subheader("Add New Food")
    with st.form("add_food_form"):
        food_id = st.text_input("Food ID")
        food_name = st.text_input("Food Name/Description")
        scientific_name = st.text_input("Scientific Name")
        alt_names = st.text_input("Alternate/Common Names (comma separated)")
        edible_portion = st.text_input("Edible Portion (%)", value="100%")
        is_unsafe = st.checkbox("Flag as unsafe for 0-5 years old (e.g., choking hazard, high sodium, organ meats)")
        submitted = st.form_submit_button("Add Food")
        if submitted:
            new_food = {
                "Food_ID": food_id,
                "Food_name_and_Description": food_name,
                "Scientific_name": scientific_name,
                "Alternate_Common_names": [n.strip() for n in alt_names.split(",") if n.strip()],
                "Edible_portion": edible_portion,
                "is_unsafe": is_unsafe
            }
            food_data.append(new_food)
            save_food_data(food_data)
            log_action("Add Food", new_food)
            st.success(f"Added food: {food_name}")
            st.experimental_rerun()

    st.subheader("Edit/Remove Foods")
    if food_data:
        food_ids = [f.get("Food_ID", "") for f in food_data]
        selected = st.selectbox("Select Food to Edit/Remove", options=food_ids)
        if selected:
            idx = next((i for i, f in enumerate(food_data) if f.get("Food_ID") == selected), None)
            if idx is not None:
                food = food_data[idx]
                with st.form("edit_food_form"):
                    food_name = st.text_input("Food Name/Description", value=food.get("Food_name_and_Description", ""))
                    scientific_name = st.text_input("Scientific Name", value=food.get("Scientific_name", ""))
                    alt_names = st.text_input("Alternate/Common Names (comma separated)", value=", ".join(food.get("Alternate_Common_names", [])))
                    edible_portion = st.text_input("Edible Portion (%)", value=food.get("Edible_portion", "100%"))
                    is_unsafe = st.checkbox("Flag as unsafe for 0-5 years old", value=food.get("is_unsafe", False))
                    update = st.form_submit_button("Update Food")
                    delete = st.form_submit_button("Delete Food")
                    if update:
                        food.update({
                            "Food_name_and_Description": food_name,
                            "Scientific_name": scientific_name,
                            "Alternate_Common_names": [n.strip() for n in alt_names.split(",") if n.strip()],
                            "Edible_portion": edible_portion,
                            "is_unsafe": is_unsafe
                        })
                        food_data[idx] = food
                        save_food_data(food_data)
                        log_action("Edit Food", food)
                        st.success("Food updated.")
                        st.experimental_rerun()
                    if delete:
                        removed = food_data.pop(idx)
                        save_food_data(food_data)
                        log_action("Delete Food", removed)
                        st.warning("Food deleted.")
                        st.experimental_rerun()

with import_tab:
    st.header("⬆️⬇️ Bulk Import/Export Food Data")
    st.download_button("Download Food Data (JSON)", data=json.dumps(load_food_data(), indent=2), file_name="food_info.json", mime="application/json")
    st.download_button("Download Food Data (CSV)", data=df.to_csv(index=False), file_name="food_info.csv", mime="text/csv")
    st.subheader("Import Food Data (JSON)")
    uploaded = st.file_uploader("Upload food_info.json", type=["json"])
    if uploaded:
        try:
            new_data = json.load(uploaded)
            save_food_data(new_data)
            log_action("Import Food Data", f"Imported {len(new_data)} foods from JSON.")
            st.success(f"Imported {len(new_data)} foods.")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

with logs_tab:
    st.header("📜 Logs & Audit Trail")
    logs = load_logs()
    if logs:
        logs_df = pd.DataFrame(logs)
        st.dataframe(logs_df, use_container_width=True)
    else:
        st.info("No logs available yet.")
