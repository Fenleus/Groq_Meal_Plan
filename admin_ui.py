import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

DATA_PATH = os.path.join("data", "food_info.json")
LOG_PATH = os.path.join("data", "admin_logs.json")


# Configure page
st.set_page_config(
    page_title="🛠️ Admin Dashboard",
    page_icon="🛠️",
    layout="wide"
)

# Show a styled header with subtitle (like parent UI)
st.markdown("""
<div class='main-header'>
    <span style='font-size:2.2rem;'>🛠️</span><br>
    <span style='font-size:1.7rem;font-weight:bold;'>Admin Dashboard</span>
    <p>Manage the food database, logs, and system settings</p>
</div>
""", unsafe_allow_html=True)

# Sidebar: Admin info and quick stats
with st.sidebar:
    st.header("🛠️ Admin Login")
    st.info("Logged in as: System Administrator")
    st.write("ID: admin")
    st.subheader("📊 Quick Stats")
    # Food count
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            food_count = len(json.load(f))
    except Exception:
        food_count = 0
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            log_count = len(json.load(f))
    except Exception:
        log_count = 0
    st.metric("Total Foods", food_count)
    st.metric("Total Logs", log_count)

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


def load_logs():
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
def save_food_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# Tabs
tabs = st.tabs(["🍲 Food Database", "📜 Logs"])
main_tab = tabs[0]
logs_tab = tabs[1]

with main_tab:
    st.header("🍲 Food Database Management")
    if st.session_state.get('show_nutrition_notice'):
        food_idx = st.session_state.get('show_nutrition_section', None)
        food_data_list = load_food_data() if food_idx else []
        food_name = ""
        if food_idx and 0 < food_idx <= len(food_data_list):
            food = food_data_list[food_idx-1]
            food_name = food.get('food_name_and_description', food.get('food_name', ''))
        st.markdown(f"""
            <div style='background:#2196F3;color:white;padding:0.75rem 1.5rem;border-radius:8px;font-weight:bold;margin-bottom:0.5rem;font-size:1.1rem;'>
                The nutrition data is shown below.<br>
                <span style='font-size:1rem;font-weight:normal;'>You are now viewing nutrition data for: <b>{food_name}</b></span>
            </div>
        """, unsafe_allow_html=True)
    food_data = load_food_data()
    if not food_data:
        st.info("No food data available.")
    else:

        # Search bar
        if 'food_db_search' not in st.session_state:
            st.session_state['food_db_search'] = ''
        prev_search = st.session_state['food_db_search']
        search_val = st.text_input(
            "🔍 Search food database",
            value=prev_search,
            key='food_db_search',
        )
        if search_val != prev_search:
            st.session_state['food_db_search'] = search_val
            st.rerun()
        def filter_foods(data, query):
            if not query:
                return data
            query = query.lower()
            filtered = []
            for item in data:
                for col in ["food_id", "food_name_and_description", "scientific_name", "alternate_common_names", "edible_portion"]:
                    val = item.get(col, '')
                    if isinstance(val, list):
                        val = ', '.join(val)
                    if query in str(val).lower():
                        filtered.append(item)
                        break
            return filtered

        filtered_food_data = filter_foods(food_data, search_val)

        # Pagination setup
        records_per_page = 10
        total_records = len(filtered_food_data)
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
        for idx, item in enumerate(filtered_food_data[start_idx:end_idx], start=start_idx+1):
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
                # Editing mode
                for i, col in enumerate(columns[1:-1], start=1):
                    st.session_state['edit_data'].setdefault(col, row[col])
                    cols[i].text_input("", value=st.session_state['edit_data'][col], key=f"edit_{col}_{row['No.']}")
                # Options: Save/Cancel
                btn_cols = cols[len(columns)-1].columns([1,0.1,1])
                save = btn_cols[0].button("✓ Save", key=f"save_{row['No.']}")
                btn_cols[1].markdown("", unsafe_allow_html=True) 
                edit_cancel = btn_cols[2].button("✗ Cancel", key=f"cancel_{row['No.']}")
                if save:
                    i = row['No.']-1
                    for col in columns[1:-1]:
                        food_data[i][col] = st.session_state['edit_data'][col]
                    save_food_data(food_data)
                    log_action("Edit Food", {"food_id": row['food_id']})
                    st.session_state['edit_row'] = None
                    st.session_state['edit_data'] = {}
                    st.rerun()
                if edit_cancel:
                    st.session_state['edit_row'] = None
                    st.session_state['edit_data'] = {}
                    st.rerun()
            else:
                for i, col in enumerate(columns[1:-1], start=1):
                    cols[i].markdown(row[col])
                # Options: Data/Edit
                btn_cols = cols[len(columns)-1].columns([1,0.1,1])
                data_btn = btn_cols[0].button("Data", key=f"data_{row['No.']}" )
                btn_cols[1].markdown("", unsafe_allow_html=True) 
                edit_btn = btn_cols[2].button("Edit", key=f"edit_{row['No.']}" )
                if data_btn:
                    st.session_state['show_nutrition_section'] = row['No.']
                    st.session_state['scroll_to_nutrition'] = True
                    st.session_state['show_nutrition_notice'] = True
                    st.rerun()
                if edit_btn:
                    st.session_state['edit_row'] = row['No.']
                    st.session_state['edit_data'] = {col: row[col] for col in columns[1:-1]}
                    st.rerun()

        # Nutrition data section with tabbed info
        if st.session_state.get('show_nutrition_section'):
            # Show nutrition section
            if st.session_state.get('scroll_to_nutrition'):
                st.session_state['scroll_to_nutrition'] = False
            i = st.session_state['show_nutrition_section']-1
            food = food_data[i]
            section_title = food.get('food_name_and_description', food.get('food_name', ''))
            st.markdown(f"<div class='nutrition-section-container'><h2 id='nutrition_data'>{section_title}</h2>", unsafe_allow_html=True)
            # Nutrition data
            tab_keys = [
                ("proximates", "Proximates"),
                ("other_carbohydrates", "Other Carbohydrate"),
                ("minerals", "Minerals"),
                ("vitamins", "Vitamins"),
                ("lipids", "Lipids")
            ]
            nutrition = None
            for k in ["composition", "composition_per100g"]:
                if k in food and isinstance(food[k], dict) and food[k]:
                    nutrition = food[k]
                    break
            if not nutrition:
                nutrition = food
            tabs = st.tabs([tab for _, tab in tab_keys])
            for idx, (nut_key, tab_name) in enumerate(tab_keys):
                with tabs[idx]:
                    nut_data = nutrition.get(nut_key, {})
                    if nut_data:
                        st.markdown(f"<div style='background:#2196F3;color:white;padding:0.5rem 1rem;border-radius:6px;font-weight:bold;margin-bottom:0.5rem;'>"
                                    f"{tab_name} <span style='float:right;'>Amount per 100 g E.P.</span></div>", unsafe_allow_html=True)
                        for k, v in nut_data.items():
                            # Prettify key
                            pretty_k = k.replace('_g', ' (g)').replace('_mg', ' (mg)').replace('_µg', ' (µg)').replace('_ug', ' (µg)').replace('_', ' ').capitalize()
                            display_val = v if (v is not None and str(v).strip() != "") else "-"
                            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:0.5rem 0.2rem;border-bottom:1px solid #eee;'><span>{pretty_k}</span><span style='font-weight:bold'>{display_val}</span></div>", unsafe_allow_html=True)
                    else:
                        st.info(f"No {tab_name.lower()} data available.")
            st.markdown("</div>", unsafe_allow_html=True)

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

