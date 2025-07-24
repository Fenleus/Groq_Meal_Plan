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
</div>
""", unsafe_allow_html=True)

# Tabs
main_tab = st.tabs(["🍲 Food Database"])[0]

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
        # Pagination controls - left aligned
        pag_row = st.columns([0.18,0.82])
        with pag_row[0]:
            btn_cols = st.columns([1,1])
            btn_cols[0].button('Previous', key='prev_page', on_click=lambda: set_page(page-1), disabled=(page==1))
            btn_cols[1].button('Next', key='next_page', on_click=lambda: set_page(page+1), disabled=(page==total_pages))
        start_idx = (page-1)*records_per_page
        end_idx = min(start_idx+records_per_page, total_records)
        st.caption(f"Showing {start_idx+1} to {end_idx} of {total_records} rows | {records_per_page} records per page")

        # Table columns
        columns = ["No.", "Food_ID", "Food_name_and_Description", "Scientific_name", "Alternate_Common_names", "Edible_portion", "Options"]
        # Prepare table data
        table_rows = []
        for idx, item in enumerate(food_data[start_idx:end_idx], start=start_idx+1):
            food_id = item.get('Food_ID', f'F{idx:03d}')
            name_desc = item.get('Food_name', '')
            if item.get('Description'):
                name_desc += ", " + item['Description']
            sci_name = item.get('Scientific_name', '')
            alt_names = item.get('Alternate_Common_names', '')
            edible = item.get('Edible_portion', '')
            table_rows.append({
                "No.": idx,
                "Food_ID": food_id,
                "Food_name_and_Description": name_desc,
                "Scientific_name": sci_name,
                "Alternate_Common_names": alt_names,
                "Edible_portion": edible,
                "Options": ""
            })

        # Edit state
        if 'edit_row' not in st.session_state:
            st.session_state['edit_row'] = None
        if 'edit_data' not in st.session_state:
            st.session_state['edit_data'] = {}

        # Render table
        for row_idx, row in enumerate(table_rows):
            cols = st.columns([1,2,4,3,3,2,2])
            # No. and Food_ID (not editable)
            cols[0].markdown(f"{row['No.']}")
            cols[1].markdown(f"{row['Food_ID']}")
            # Edit mode check
            is_editing = st.session_state['edit_row'] == row['No.']
            if is_editing:
                # Editable fields
                st.session_state['edit_data'].setdefault('Food_name_and_Description', row['Food_name_and_Description'])
                st.session_state['edit_data'].setdefault('Scientific_name', row['Scientific_name'])
                st.session_state['edit_data'].setdefault('Alternate_Common_names', row['Alternate_Common_names'])
                st.session_state['edit_data'].setdefault('Edible_portion', row['Edible_portion'])
                cols[2].text_input("", value=st.session_state['edit_data']['Food_name_and_Description'], key=f"edit_name_{row['No.']}")
                cols[3].text_input("", value=st.session_state['edit_data']['Scientific_name'], key=f"edit_sci_{row['No.']}")
                cols[4].text_input("", value=st.session_state['edit_data']['Alternate_Common_names'], key=f"edit_alt_{row['No.']}")
                cols[5].text_input("", value=st.session_state['edit_data']['Edible_portion'], key=f"edit_edible_{row['No.']}")
                # Options: Save/Cancel true horizontal alignment
                btn_cols = cols[6].columns([1,0.1,1])
                save = btn_cols[0].button("✓ Save", key=f"save_{row['No.']}")
                btn_cols[1].markdown("", unsafe_allow_html=True)  # minimal gap
                edit_cancel = btn_cols[2].button("✗ Cancel", key=f"cancel_{row['No.']}")
                if save:
                    # Validate and update
                    i = row['No.']-1
                    food_data[i]['Food_name'] = st.session_state['edit_data']['Food_name_and_Description'].split(',')[0].strip()
                    if ',' in st.session_state['edit_data']['Food_name_and_Description']:
                        food_data[i]['Description'] = st.session_state['edit_data']['Food_name_and_Description'].split(',',1)[1].strip()
                    else:
                        food_data[i]['Description'] = ''
                    food_data[i]['Scientific_name'] = st.session_state['edit_data']['Scientific_name']
                    food_data[i]['Alternate_Common_names'] = st.session_state['edit_data']['Alternate_Common_names']
                    food_data[i]['Edible_portion'] = st.session_state['edit_data']['Edible_portion']
                    save_food_data(food_data)
                    log_action("Edit Food", {"Food_ID": row['Food_ID']})
                    st.session_state['edit_row'] = None
                    st.session_state['edit_data'] = {}
                    st.experimental_rerun()
                if edit_cancel:
                    st.session_state['edit_row'] = None
                    st.session_state['edit_data'] = {}
                    st.experimental_rerun()
            else:
                # Read-only fields
                cols[2].markdown(row['Food_name_and_Description'])
                cols[3].markdown(row['Scientific_name'])
                cols[4].markdown(row['Alternate_Common_names'])
                cols[5].markdown(row['Edible_portion'])
                # Options: Data/Edit true horizontal alignment
                btn_cols = cols[6].columns([1,0.1,1])
                data_btn = btn_cols[0].button("Data", key=f"data_{row['No.']}")
                btn_cols[1].markdown("", unsafe_allow_html=True)  # minimal gap
                edit_btn = btn_cols[2].button("Edit", key=f"edit_{row['No.']}")
                if data_btn:
                    st.session_state['show_modal'] = row['No.']
                if edit_btn:
                    st.session_state['edit_row'] = row['No.']
                    st.session_state['edit_data'] = {
                        'Food_name_and_Description': row['Food_name_and_Description'],
                        'Scientific_name': row['Scientific_name'],
                        'Alternate_Common_names': row['Alternate_Common_names'],
                        'Edible_portion': row['Edible_portion']
                    }
                    st.experimental_rerun()

        # Data modal
        if st.session_state.get('show_modal'):
            i = st.session_state['show_modal']-1
            food = food_data[i]
            modal_title = f"{food.get('Food_name','')} Nutritional Data"
            st.markdown(f"<h3>{modal_title}</h3>", unsafe_allow_html=True)
            tabs = st.tabs(["Proximates", "Other Carbohydrate", "Minerals", "Vitamins", "Lipids"])
            comp = food.get('CompositionPer100g', {})
            # Each tab: show relevant data (read-only)
            with tabs[0]:
                for k,v in comp.get('Proximates', {}).items():
                    st.write(f"{k}: {v}")
            with tabs[1]:
                for k,v in comp.get('Other Carbohydrate', {}).items():
                    st.write(f"{k}: {v}")
            with tabs[2]:
                for k,v in comp.get('Minerals', {}).items():
                    st.write(f"{k}: {v}")
            with tabs[3]:
                for k,v in comp.get('Vitamins', {}).items():
                    st.write(f"{k}: {v}")
            with tabs[4]:
                for k,v in comp.get('Lipids', {}).items():
                    st.write(f"{k}: {v}")
            if st.button("Close", key="close_modal"):
                st.session_state['show_modal'] = None
                st.experimental_rerun()

