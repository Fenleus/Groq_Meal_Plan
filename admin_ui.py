import streamlit as st
import pandas as pd
from datetime import datetime
import data_manager
import mysql.connector
import os
LOG_PATH = os.path.join("data", "admin_logs.json")

st.set_page_config(
    page_title="🛠️ Admin Dashboard",
    page_icon="🛠️",
    layout="wide"
)

st.markdown("""
<div class='main-header'>
    <span style='font-size:2.2rem;'>🛠️</span><br>
    <span style='font-size:1.7rem;font-weight:bold;'>Admin Dashboard</span>
    <p>Manage the food database, logs, and system settings</p>
</div>
""", unsafe_allow_html=True)

def load_logs():

    conn = data_manager.data_manager.conn
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT log_id, timestamp, action, details FROM admin_logs ORDER BY timestamp DESC")
    rows = cursor.fetchall()

    import json
    for row in rows:
        if isinstance(row.get('details'), str):
            try:
                row['details'] = json.loads(row['details'])
            except Exception:
                pass
    return rows

with st.sidebar:
    st.header("🛠️ Admin Login")
    st.info("Logged in as: System Administrator")
    st.write("ID: admin")
    st.subheader("📊 Quick Stats")

    try:
        food_count = len(data_manager.data_manager.get_foods_data())
    except Exception:
        food_count = 0
    try:
        log_count = len(load_logs())
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
    # Filter sensitive keys
    if isinstance(details, dict):
        sensitive_keys = [
            'child_name', 'parent_name', 'name', 'address', 'contact', 'email', 'phone',
            'children', 'parents', 'profile', 'bmi', 'bmi_category', 'age', 'age_in_months',
            'medical_conditions', 'allergies', 'religion', 'weight', 'height', 'notes',
            'history', 'meal_plans', 'recipes', 'password', 'token', 'id', 'user_id', 'parent_id', 'patient_id'
        ]
        filtered_details = {k: v for k, v in details.items() if k not in sensitive_keys}
    else:
        filtered_details = details
    # Save to MySQL admin_logs table
    import json
    conn = data_manager.data_manager.conn
    cursor = conn.cursor()
    sql = "INSERT INTO admin_logs (timestamp, action, details) VALUES (%s, %s, %s)"
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(sql, (now, action, json.dumps(filtered_details)))
    conn.commit()

def load_logs():
    # Load from MySQL admin_logs table
    conn = data_manager.data_manager.conn
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT log_id, timestamp, action, details FROM admin_logs ORDER BY timestamp DESC")
    rows = cursor.fetchall()

    import json
    for row in rows:
        if isinstance(row.get('details'), str):
            try:
                row['details'] = json.loads(row['details'])
            except Exception:
                pass
    return rows


# Tabs
tabs = st.tabs(["🍲 Food Database", "📜 Logs"])
main_tab = tabs[0]
logs_tab = tabs[1]


with main_tab:
    st.header("🍲 Food Database Management")
    # Load food data from MySQL
    food_data = data_manager.data_manager.get_foods_data()
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

        # Edit error and indication banners (above table, below pagination)
        if st.session_state.get('edit_row'):
            if st.session_state.get('show_edit_error'):
                st.markdown(f"""
                    <div style='background:#FFCDD2;color:#B71C1C;padding:0.75rem 1.5rem;border-radius:8px;font-weight:bold;margin-bottom:0.5rem;font-size:1.1rem;'>
                        You are currently editing a food entry. Please finish or cancel editing before viewing nutrition data.
                    </div>
                """, unsafe_allow_html=True)
                st.session_state['show_edit_error'] = False
            edit_data = st.session_state.get('edit_data', {})
            food_name = edit_data.get('food_name_and_description', '')
            st.markdown(f"""
                <div style='background:#FF9800;color:white;padding:0.75rem 1.5rem;border-radius:8px;font-weight:bold;margin-bottom:0.5rem;font-size:1.1rem;'>
                    You are about to edit food entry <b>{food_name}</b>.<br>
                    <span style='font-size:1rem;font-weight:normal;'>Edit form is shown <b>below</b>.</span>
                </div>
            """, unsafe_allow_html=True)

        if st.session_state.get('show_nutrition_notice'):
            food_idx = st.session_state.get('show_nutrition_section', None)
            food_data_list = filtered_food_data if food_idx else []
            food_name = ""
            if food_idx and 0 < food_idx <= len(food_data_list):
                food = food_data_list[food_idx-1]
                food_name = food.get('food_name_and_description', '')
            st.markdown(f"""
                <div style='background:#2196F3;color:white;padding:0.75rem 1.5rem;border-radius:8px;font-weight:bold;margin-bottom:0.5rem;font-size:1.1rem;'>
                    The nutrition data is shown below.<br>
                    <span style='font-size:1rem;font-weight:normal;'>You are now viewing nutrition data for: <b>{food_name}</b></span>
                </div>
            """, unsafe_allow_html=True)
            st.session_state['show_nutrition_notice'] = False

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
                "food_name_and_description": item.get("food_name_and_description", ""),
                "scientific_name": item.get("scientific_name", ""),
                "alternate_common_names": item.get("alternate_common_names", ""),
                "edible_portion": item.get("edible_portion", ""),
                "Options": ""
            }
            table_rows.append(row)

        if 'edit_row' not in st.session_state:
            st.session_state['edit_row'] = None
        if 'edit_data' not in st.session_state:
            st.session_state['edit_data'] = {}

        # Render table

        for row_idx, row in enumerate(table_rows):
            col_widths = [1,2,4,3,3,2,2]
            cols = st.columns(col_widths)
            cols[0].markdown(f"{row['No.']}")

            for i, col in enumerate(columns[1:-1], start=1):
                cols[i].markdown(row[col])

            btn_cols = cols[len(columns)-1].columns([1,0.1,1])
            data_btn = btn_cols[0].button("Data", key=f"data_{row['No.']}" )
            edit_btn = btn_cols[2].button("Edit", key=f"edit_{row['No.']}" )

            if data_btn:
                if st.session_state.get('edit_row'):
                    st.session_state['show_edit_error'] = True
                    st.rerun()
                else:
                    st.session_state['show_nutrition_section'] = row['No.']
                    st.session_state['scroll_to_nutrition'] = True
                    st.session_state['show_nutrition_notice'] = True
                    st.rerun()

            if edit_btn:
                st.session_state['edit_row'] = row['No.']
                st.session_state['edit_data'] = row
                st.rerun()

        # Edit form section with nutrition facts
        if st.session_state.get('edit_row'):
            edit_data = st.session_state.get('edit_data', {})
            st.markdown("<div style='background:#FFEB3B;padding:1rem 2rem;border-radius:8px;margin:1rem 0;'><b>Edit Food Entry</b></div>", unsafe_allow_html=True)
            # Fetch nutrition data for this food
            nutrition = data_manager.data_manager.get_food_nutrition(edit_data.get("food_id", ""))
            with st.form(key='edit_food_form'):
                food_id = st.text_input("Food ID", value=edit_data.get("food_id", ""), disabled=True)
                food_name_and_description = st.text_input("Food Name and Description", value=edit_data.get("food_name_and_description", ""))
                scientific_name = st.text_input("Scientific Name", value=edit_data.get("scientific_name", ""))
                alternate_common_names = st.text_input("Alternate Common Names", value=edit_data.get("alternate_common_names", ""))
                edible_portion = st.text_input("Edible Portion", value=edit_data.get("edible_portion", ""))

                st.markdown("<hr><b>Edit Nutrition Facts</b>", unsafe_allow_html=True)
                nutrition_inputs = {}
                tab_keys = [
                    ("proximates", "Proximates"),
                    ("other_carbohydrates", "Other Carbohydrate"),
                    ("minerals", "Minerals"),
                    ("vitamins", "Vitamins"),
                    ("lipids", "Lipids")
                ]
                for nut_key, tab_name in tab_keys:
                    st.subheader(tab_name)
                    nut_data = nutrition.get(nut_key, {})
                    nutrition_inputs[nut_key] = {}
                    for k, v in nut_data.items():
                        pretty_k = k.replace('_g', ' (g)').replace('_mg', ' (mg)').replace('_µg', ' (µg)').replace('_ug', ' (µg)').replace('_', ' ').capitalize()
                        nutrition_inputs[nut_key][k] = st.text_input(f"{tab_name}: {pretty_k}", value=str(v) if v is not None else "")

                submit = st.form_submit_button("Save Changes")
                cancel = st.form_submit_button("Cancel")
            if submit:
                # Compare old and new values to log only changed columns
                try:
                    original_data = edit_data.copy()
                    changed_fields = {"food_id": food_id}
                    # Compare main food fields and log old/new
                    if food_name_and_description != original_data.get("food_name_and_description", ""):
                        changed_fields["food_name_and_description"] = {
                            "old": original_data.get("food_name_and_description", ""),
                            "new": food_name_and_description
                        }
                    if scientific_name != original_data.get("scientific_name", ""):
                        changed_fields["scientific_name"] = {
                            "old": original_data.get("scientific_name", ""),
                            "new": scientific_name
                        }
                    if alternate_common_names != original_data.get("alternate_common_names", ""):
                        changed_fields["alternate_common_names"] = {
                            "old": original_data.get("alternate_common_names", ""),
                            "new": alternate_common_names
                        }
                    if edible_portion != original_data.get("edible_portion", ""):
                        changed_fields["edible_portion"] = {
                            "old": original_data.get("edible_portion", ""),
                            "new": edible_portion
                        }

                    # Update food in DB
                    data_manager.data_manager.update_food(
                        food_id=food_id,
                        food_name_and_description=food_name_and_description,
                        scientific_name=scientific_name,
                        alternate_common_names=alternate_common_names,
                        edible_portion=edible_portion
                    )

                    # Compare nutrition facts
                    original_nutrition = data_manager.data_manager.get_food_nutrition(food_id)
                    changed_nutrition = {}
                    for nut_key in nutrition_inputs:
                        nut_changes = {}
                        for k, v in nutrition_inputs[nut_key].items():
                            val = v.strip()
                            if val == "":
                                val = None
                            else:
                                try:
                                    val = float(val)
                                except Exception:
                                    val = None
                            orig_val = original_nutrition.get(nut_key, {}).get(k)
                            # Normalize both to string for comparison
                            def norm(x):
                                if x is None:
                                    return ""
                                try:
                                    return f"{float(x):.6g}".rstrip("0").rstrip(".") if "." in f"{float(x):.6g}" else f"{float(x):.6g}"
                                except Exception:
                                    return str(x)
                            if norm(val) != norm(orig_val):
                                nut_changes[k] = {
                                    "old": norm(orig_val),
                                    "new": v
                                }
                            # Update DB regardless
                            data_manager.data_manager.update_food_nutrition(food_id, nut_key, k, val)
                        if nut_changes:
                            changed_nutrition[nut_key] = nut_changes
                    # Only log nutrition_facts if any nutrition subfield changed
                    if any(changed_nutrition.values()):
                        changed_fields["nutrition_facts"] = changed_nutrition

                    # Log only changed fields
                    log_action(
                        action="edit_food_entry",
                        details=changed_fields
                    )
                    st.success("Food entry and nutrition facts updated successfully.")
                    st.session_state['edit_row'] = None
                    st.session_state['edit_data'] = {}
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update food entry or nutrition facts: {e}")
            if cancel:
                st.session_state['edit_row'] = None
                st.session_state['edit_data'] = {}
                st.rerun()

        # Nutrition data section with tabbed info
        # Only show nutrition section if not editing
        if st.session_state.get('show_nutrition_section') and not st.session_state.get('edit_row'):
            # Show nutrition section
            if st.session_state.get('scroll_to_nutrition'):
                st.session_state['scroll_to_nutrition'] = False
            i = st.session_state['show_nutrition_section']-1
            if 0 <= i < len(filtered_food_data):
                food = filtered_food_data[i]
                section_title = food.get('food_name_and_description', '')
                st.markdown(f"<div class='nutrition-section-container'><h2 id='nutrition_data'>{section_title}</h2>", unsafe_allow_html=True)
                # Nutrition data from MySQL
                nutrition = data_manager.data_manager.get_food_nutrition(food['food_id'])
                tab_keys = [
                    ("proximates", "Proximates"),
                    ("other_carbohydrates", "Other Carbohydrate"),
                    ("minerals", "Minerals"),
                    ("vitamins", "Vitamins"),
                    ("lipids", "Lipids")
                ]
                tabs = st.tabs([tab for _, tab in tab_keys])
                for idx, (nut_key, tab_name) in enumerate(tab_keys):
                    with tabs[idx]:
                        nut_data = nutrition.get(nut_key, {})
                        if nut_data:
                            st.markdown(f"<div style='background:#2196F3;color:white;padding:0.5rem 1rem;border-radius:6px;font-weight:bold;margin-bottom:0.5rem;'>"
                                        f"{tab_name} <span style='float:right;'>Amount per 100 g E.P.</span></div>", unsafe_allow_html=True)
                            for k, v in nut_data.items():
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

    columns = ['action', 'details', 'timestamp']
    if logs:
        log_df = pd.DataFrame(logs)
        def flatten_details(details):
            if isinstance(details, dict):
                return ", ".join(f"{k}: {v}" for k, v in details.items())
            return str(details)
        if 'details' in log_df.columns:
            log_df['details'] = log_df['details'].apply(flatten_details)
        st.dataframe(log_df[columns], use_container_width=True)
    else:
        empty_df = pd.DataFrame([], columns=columns)
        st.dataframe(empty_df, use_container_width=True)

