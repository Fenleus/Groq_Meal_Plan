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
        columns = ["No.", "food_id", "food_name_and_description", "scientific_name", "alternate_names", "edible_portion", "Options"]
        # Show nutrition facts basis note
        if food_data and "nutrition_facts_basis" in food_data[0]:
            st.info(f"All nutrition facts are based on: {food_data[0]['nutrition_facts_basis']}")
        # Prepare table data
        table_rows = []
        for idx, item in enumerate(food_data[start_idx:end_idx], start=start_idx+1):
            food_id = item.get('food_id', f'f{idx:03d}')
            name_desc = item.get('food_name', '')
            if item.get('description'):
                name_desc += ", " + item['description']
            sci_name = item.get('scientific_name', '')
            alt_names = item.get('alternate_names', '')
            edible = item.get('edible_portion', '')
            table_rows.append({
                "No.": idx,
                "food_id": food_id,
                "food_name_and_description": name_desc,
                "scientific_name": sci_name,
                "alternate_names": alt_names,
                "edible_portion": edible,
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
            # No. and food_id (not editable)
            cols[0].markdown(f"{row['No.']}")
            cols[1].markdown(f"{row['food_id']}")
            # Edit mode check
            is_editing = st.session_state['edit_row'] == row['No.']
            if is_editing:
                # Editable fields
                st.session_state['edit_data'].setdefault('food_name_and_description', row['food_name_and_description'])
                st.session_state['edit_data'].setdefault('scientific_name', row['scientific_name'])
                st.session_state['edit_data'].setdefault('alternate_names', row['alternate_names'])
                st.session_state['edit_data'].setdefault('edible_portion', row['edible_portion'])
                cols[2].text_input("", value=st.session_state['edit_data']['food_name_and_description'], key=f"edit_name_{row['No.']}")
                cols[3].text_input("", value=st.session_state['edit_data']['scientific_name'], key=f"edit_sci_{row['No.']}")
                cols[4].text_input("", value=st.session_state['edit_data']['alternate_names'], key=f"edit_alt_{row['No.']}")
                cols[5].text_input("", value=st.session_state['edit_data']['edible_portion'], key=f"edit_edible_{row['No.']}")
                # Options: Save/Cancel true horizontal alignment
                btn_cols = cols[6].columns([1,0.1,1])
                save = btn_cols[0].button("✓ Save", key=f"save_{row['No.']}")
                btn_cols[1].markdown("", unsafe_allow_html=True)  # minimal gap
                edit_cancel = btn_cols[2].button("✗ Cancel", key=f"cancel_{row['No.']}")
                if save:
                    # Validate and update
                    i = row['No.']-1
                    food_data[i]['food_name'] = st.session_state['edit_data']['food_name_and_description'].split(',')[0].strip()
                    if ',' in st.session_state['edit_data']['food_name_and_description']:
                        food_data[i]['description'] = st.session_state['edit_data']['food_name_and_description'].split(',',1)[1].strip()
                    else:
                        food_data[i]['description'] = ''
                    food_data[i]['scientific_name'] = st.session_state['edit_data']['scientific_name']
                    food_data[i]['alternate_names'] = st.session_state['edit_data']['alternate_names']
                    food_data[i]['edible_portion'] = st.session_state['edit_data']['edible_portion']
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
                # Read-only fields
                cols[2].markdown(row['food_name_and_description'])
                cols[3].markdown(row['scientific_name'])
                cols[4].markdown(row['alternate_names'])
                cols[5].markdown(row['edible_portion'])
                # Options: Data/Edit true horizontal alignment
                btn_cols = cols[6].columns([1,0.1,1])
                data_btn = btn_cols[0].button("Data", key=f"data_{row['No.']}" )
                btn_cols[1].markdown("", unsafe_allow_html=True)  # minimal gap
                edit_btn = btn_cols[2].button("Edit", key=f"edit_{row['No.']}" )
                if data_btn:
                    st.session_state['show_modal'] = row['No.']
                if edit_btn:
                    st.session_state['edit_row'] = row['No.']
                    st.session_state['edit_data'] = {
                        'food_name_and_description': row['food_name_and_description'],
                        'scientific_name': row['scientific_name'],
                        'alternate_names': row['alternate_names'],
                        'edible_portion': row['edible_portion']
                    }
                    st.experimental_rerun()

        # Data modal
        if st.session_state.get('show_modal'):
            i = st.session_state['show_modal']-1
            food = food_data[i]
            modal_title = f"{food.get('food_name','')} Nutritional Data"
            st.markdown(f"<h3>{modal_title}</h3>", unsafe_allow_html=True)
            tabs = st.tabs(["Proximates", "Other Carbohydrates", "Minerals", "Vitamins", "Lipids"])
            # Use new keys directly from food (not nested under composition_per_100g)
            with tabs[0]:
                for k, v in food.get('proximates', {}).items():
                    st.write(f"{k}: {v}")
            with tabs[1]:
                for k, v in food.get('other_carbohydrates', {}).items():
                    st.write(f"{k}: {v}")
            with tabs[2]:
                for k, v in food.get('minerals', {}).items():
                    st.write(f"{k}: {v}")
            with tabs[3]:
                for k, v in food.get('vitamins', {}).items():
                    st.write(f"{k}: {v}")
            with tabs[4]:
                for k, v in food.get('lipids', {}).items():
                    st.write(f"{k}: {v}")
            if st.button("Close", key="close_modal"):
                st.session_state['show_modal'] = None
                st.experimental_rerun()

