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
    if isinstance(details, dict):
        sensitive_keys = [
            'child_name', 'parent_name', 'name', 'address', 'contact', 'email', 'phone',
            'children', 'parents', 'profile', 'bmi', 'bmi_category', 'age', 'age_in_months',
            'medical_conditions', 'allergies', 'religion', 'weight', 'height', 'notes',
            'history', 'meal_plans', 'recipes', 'password', 'token', 'id', 'user_id', 'parent_id', 'child_id'
        ]
        filtered_details = {k: v for k, v in details.items() if k not in sensitive_keys}
    else:
        filtered_details = details
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": filtered_details
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
</div>
""", unsafe_allow_html=True)


# Tabs
tabs = st.tabs(["🍲 Food Database", "📜 Logs"])
main_tab = tabs[0]
logs_tab = tabs[1]

with main_tab:
    st.header("🍲 Food Database Management")
    food_data = load_food_data()
    if not food_data:
        st.info("No food data available.")
    else:
        # Pagination setup
        records_per_page = 10
        total_records = len(food_data)
        total_pages = (total_records - 1) // records_per_page + 1
        page = st.session_state.get('food_db_page', 1)
        def set_page(new_page):
            st.session_state['food_db_page'] = new_page
        # Pagination controls
        pag_row = st.columns([0.18,0.82])
        with pag_row[0]:
            btn_cols = st.columns([1,1])
            btn_cols[0].button('Previous', key='prev_page', on_click=lambda: set_page(page-1), disabled=(page==1))
            btn_cols[1].button('Next', key='next_page', on_click=lambda: set_page(page+1), disabled=(page==total_pages))
        start_idx = (page-1)*records_per_page
        end_idx = min(start_idx+records_per_page, total_records)
        st.caption(f"Showing {start_idx+1} to {end_idx} of {total_records} rows | {records_per_page} records per page")

        # Restrict columns to the specified set
        columns = [
            "No.",
            "food_id",
            "food_name_and_description",
            "scientific_name",
            "alternate_common_names",
            "edible_portion",
            "Options"
        ]

        # Render column headers
        header_cols = st.columns([1,2,4,3,3,2,2])
        header_labels = [
            "No.",
            "Food ID",
            "Food Name and Description",
            "Scientific Name",
            "Alternate Common Names",
            "Edible Portion",
            "Options"
        ]
        for i, label in enumerate(header_labels):
            header_cols[i].markdown(f"**{label}**")

        # Prepare table data
        table_rows = []
        for idx, item in enumerate(food_data[start_idx:end_idx], start=start_idx+1):
            row = {
                "No.": idx,
                "food_id": item.get("food_id", ""),
                "food_name_and_description": item.get("food_name_and_description", item.get("food_name", "")),
                "scientific_name": item.get("scientific_name", ""),
                "alternate_common_names": ", ".join(item.get("alternate_common_names", item.get("alternate_names", []))) if isinstance(item.get("alternate_common_names", item.get("alternate_names", [])), list) else item.get("alternate_common_names", item.get("alternate_names", "")),
                "edible_portion": item.get("edible_portion", ""),
                "Options": ""
            }
            table_rows.append(row)

        # Edit state
        if 'edit_row' not in st.session_state:
            st.session_state['edit_row'] = None
        if 'edit_data' not in st.session_state:
            st.session_state['edit_data'] = {}

        # Render table
        for row_idx, row in enumerate(table_rows):
            col_widths = [1,2,4,3,3,2,2]
            cols = st.columns(col_widths)
            cols[0].markdown(f"{row['No.']}")
            is_editing = st.session_state['edit_row'] == row['No.']
            if is_editing:
                # Editable fields for all columns except No. and Options
                for i, col in enumerate(columns[1:-1], start=1):
                    st.session_state['edit_data'].setdefault(col, row[col])
                    cols[i].text_input("", value=st.session_state['edit_data'][col], key=f"edit_{col}_{row['No.']}")
                # Options: Save/Cancel
                btn_cols = cols[len(columns)-1].columns([1,0.1,1])
                save = btn_cols[0].button("✓ Save", key=f"save_{row['No.']}")
                btn_cols[1].markdown("", unsafe_allow_html=True)  # minimal gap
                edit_cancel = btn_cols[2].button("✗ Cancel", key=f"cancel_{row['No.']}")
                if save:
                    i = row['No.']-1
                    for col in columns[1:-1]:
                        food_data[i][col] = st.session_state['edit_data'][col]
                    save_food_data(food_data)
                    log_action("Edit Food", {"food_id": row['food_id']})
                    st.session_state['edit_row'] = None
                    st.session_state['edit_data'] = {}
                    st.experimental_rerun()
                if edit_cancel:
                    st.session_state['edit_row'] = None
                    st.session_state['edit_data'] = {}
                    st.experimental_rerun()
            else:
                for i, col in enumerate(columns[1:-1], start=1):
                    cols[i].markdown(row[col])
                # Options: Data/Edit
                btn_cols = cols[len(columns)-1].columns([1,0.1,1])
                data_btn = btn_cols[0].button("Data", key=f"data_{row['No.']}" )
                btn_cols[1].markdown("", unsafe_allow_html=True)  # minimal gap
                edit_btn = btn_cols[2].button("Edit", key=f"edit_{row['No.']}" )
                if data_btn:
                    st.session_state['show_modal'] = row['No.']
                if edit_btn:
                    st.session_state['edit_row'] = row['No.']
                    st.session_state['edit_data'] = {col: row[col] for col in columns[1:-1]}
                    st.experimental_rerun()

        # Data modal
        if st.session_state.get('show_modal'):
            i = st.session_state['show_modal']-1
            food = food_data[i]
            modal_title = f"{food.get('food_name','')} Nutritional Data"
            st.markdown(f"<h3>{modal_title}</h3>", unsafe_allow_html=True)
            # Show all nutrition data as pretty JSON
            with st.expander("Show Nutrition Data", expanded=True):
                st.code(json.dumps({
                    k: food[k] for k in ["proximates", "other_carbohydrates", "minerals", "vitamins", "lipids"] if k in food
                }, indent=2, ensure_ascii=False), language="json")
            if st.button("Close", key="close_modal"):
                st.session_state['show_modal'] = None
                st.experimental_rerun()


# Logs Tab
with logs_tab:
    st.header("📜 Admin Logs")
    logs = load_logs()
    if not logs:
        st.info("No logs available.")
    else:
        # Show logs in a table
        log_df = pd.DataFrame(logs)
        # Flatten details for display
        def flatten_details(details):
            if isinstance(details, dict):
                return ", ".join(f"{k}: {v}" for k, v in details.items())
            return str(details)
        if 'details' in log_df.columns:
            log_df['details'] = log_df['details'].apply(flatten_details)
        st.dataframe(log_df[['timestamp', 'action', 'details']], use_container_width=True)

