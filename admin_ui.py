import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import data_manager
import mysql.connector

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
    admin_id = st.session_state.get('admin_id', '1')
    conn = data_manager.data_manager.conn
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT log_id, log_timestamp, action, description FROM audit_logs WHERE user_id = %s ORDER BY log_timestamp DESC", (admin_id,))
    rows = cursor.fetchall()

    import json
    for row in rows:
        if isinstance(row.get('description'), str):
            try:
                row['description'] = json.loads(row['description'])
            except Exception:
                pass
    return rows

def load_admin_options():
    """Load admin options from database"""
    try:
        conn = data_manager.data_manager.conn
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, CONCAT(first_name, ' ', last_name) as full_name FROM users WHERE role_id = (SELECT role_id FROM roles WHERE role_name = 'admin') ORDER BY user_id")
        admin_rows = cursor.fetchall()
        return {str(row['user_id']): row['full_name'] for row in admin_rows}
    except Exception as e:
        st.error(f"Failed to load admin data: {e}")
        # Fallback to prevent app crash
        return {'1': 'Admin 1', '2': 'Admin 2'}

def load_all_user_options():
    """Load all user options (nutritionists and admins) from database"""
    try:
        conn = data_manager.data_manager.conn
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.user_id, CONCAT(u.first_name, ' ', u.last_name) as full_name, r.role_name 
            FROM users u 
            JOIN roles r ON u.role_id = r.role_id 
            WHERE r.role_name IN ('nutritionist', 'admin')
            ORDER BY u.user_id
        """)
        user_rows = cursor.fetchall()
        return {str(row['user_id']): {
            'full_name': row['full_name'], 
            'role': row['role_name']
        } for row in user_rows}
    except Exception as e:
        st.error(f"Error loading user data: {e}")
        return {}

def get_user_display_name(user_id, all_users_dict):
    """Get display name for a user (nutritionist or admin)"""
    user_info = all_users_dict.get(str(user_id))
    if user_info:
        name = user_info['full_name']
        # Don't show role in the display name to keep it clean
        return name
    return f"User {user_id}"

with st.sidebar:
    st.header("🛠️ Admin Login")
    
    admin_options = load_admin_options()
    
    if not admin_options:
        st.error("No admin accounts found in database")
        admin_options = {'1': 'Admin 1'}
    
    selected_admin = st.selectbox(
        "Select Admin Account",
        options=list(admin_options.keys()),
        format_func=lambda x: admin_options[x],
        index=0
    )
    
    if 'admin_id' not in st.session_state or st.session_state.admin_id != selected_admin:
        st.session_state.admin_id = selected_admin
        if 'cached_logs' in st.session_state:
            del st.session_state['cached_logs']
    
    st.info(f"Logged in as: {admin_options[selected_admin]}")
    st.write(f"ID: {selected_admin}")
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
    # Save to audit_logs table with user_id
    import json
    conn = data_manager.data_manager.conn
    cursor = conn.cursor()
    sql = "INSERT INTO audit_logs (log_timestamp, action, description, user_id) VALUES (%s, %s, %s, %s)"
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    admin_id = st.session_state.get('admin_id', '1')  # Default to admin 1 if not set
    cursor.execute(sql, (now, action, json.dumps(filtered_details), admin_id))
    conn.commit()

import json

main_tab, kb_tab, meal_plans_tab, add_notes_tab, logs_tab = st.tabs([
    "🍽️ Food Database", 
    "📚 Knowledge Base", 
    "📝 Meal Plans Overview", 
    "🗒️ Add Notes",
    "📜 Logs"
])

with main_tab:
    st.header("🍽️ Food Database Management")
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
                for col in ["food_id", "food_name_and_description", "alternate_common_names", "energy_kcal", "nutrition_tags"]:
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
            "alternate_common_names",
            "energy_kcal",
            "nutrition_tags",
            "Options"
        ]

        header_cols = st.columns([1,2,4,3,2,3,2])
        header_labels = [
            "No.",
            "Food ID",
            "Food Name and Description",
            "Alternative Names",
            "Energy (kcal)",
            "Nutrition Tags",
            "Options"
        ]
        for i, label in enumerate(header_labels):
            header_cols[i].markdown(f"**{label}**")

        table_rows = []
        for idx, item in enumerate(filtered_food_data[start_idx:end_idx], start=start_idx+1):
            row = {
                "No.": idx,
                "food_id": item.get("food_id", ""),
                "food_name_and_description": item.get("food_name_and_description", ""),
                "alternate_common_names": item.get("alternate_common_names", ""),
                "energy_kcal": item.get("energy_kcal", ""),
                "nutrition_tags": item.get("nutrition_tags", ""),
                "Options": ""
            }
            table_rows.append(row)

        for row_idx, row in enumerate(table_rows):
            col_widths = [1,2,4,3,2,3,2]
            cols = st.columns(col_widths)
            cols[0].markdown(f"{row['No.']}")
            for i, col in enumerate(columns[1:-1], start=1):
                cols[i].markdown(row[col])
            btn_cols = cols[len(columns)-1].columns([1])
            edit_btn = btn_cols[0].button("Edit", key=f"edit_{row['No.']}" )
            if edit_btn:
                st.session_state['edit_food_id'] = filtered_food_data[start_idx + row_idx]['food_id']
                st.session_state['show_edit_form'] = True
                st.rerun()

        # Show food editing form 
        if st.session_state.get('show_edit_form') and st.session_state.get('edit_food_id'):
            food_id = st.session_state.get('edit_food_id')
            food_to_edit = data_manager.data_manager.get_food_by_id(food_id)
            if food_to_edit:
                st.markdown("---")
                st.markdown(f"### ✏️ Edit Food: {food_to_edit.get('food_name_and_description', '')}")
                with st.form("edit_food_form"):
                    food_name_and_description = st.text_input("Food Name and Description", value=food_to_edit.get('food_name_and_description', ''))
                    alternate_common_names = st.text_input("Alternative Names", value=food_to_edit.get('alternate_common_names', ''))
                    energy_kcal = st.number_input("Energy (kcal)", min_value=0.0, value=float(food_to_edit.get('energy_kcal', 0) or 0), format="%.1f")
                    nutrition_tags = st.text_input("Nutrition Tags", value=food_to_edit.get('nutrition_tags', ''))
                    col1, col2 = st.columns(2)
                    with col1:
                        save_btn = st.form_submit_button("💾 Save Changes", type="primary")
                    with col2:
                        cancel_btn = st.form_submit_button("❌ Cancel")
                    if save_btn:
                        updated_food_data = {
                            'food_name_and_description': food_name_and_description,
                            'alternate_common_names': alternate_common_names,
                            'energy_kcal': energy_kcal,
                            'nutrition_tags': nutrition_tags
                        }
                        try:
                            data_manager.data_manager.update_food(food_id, updated_food_data)
                            log_action("Update Food", {
                                'food_id': food_id,
                                'food_name_and_description': food_name_and_description,
                                'action': 'food_updated'
                            })
                            st.success(f"Food '{food_name_and_description}' updated successfully!")
                            st.session_state['show_edit_form'] = False
                            del st.session_state['edit_food_id']
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating food: {e}")
                    if cancel_btn:
                        st.session_state['show_edit_form'] = False
                        del st.session_state['edit_food_id']
                        st.rerun()
            else:
                st.error("Food not found!")
                st.session_state['show_edit_form'] = False
                del st.session_state['edit_food_id']

# Knowledge Base Tab
with kb_tab:
    st.header("📚 Knowledge Base")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Knowledge Base Table")
        kb_entries = data_manager.data_manager.get_knowledge_base()
        table_rows = []
        if isinstance(kb_entries, dict):
            for kb in kb_entries.values():
                table_rows.append({
                    "kb_id": kb.get('kb_id', ''),
                    "ai_summary": kb.get('ai_summary', ''),
                    "pdf_name": kb.get('pdf_name', ''),
                    "pdf_text": kb.get('pdf_text', ''),
                    "added_at": kb.get('added_at', '')
                })
        columns = ["kb_id", "ai_summary", "pdf_name", "pdf_text", "added_at"]
        if table_rows:
            df = pd.DataFrame(table_rows, columns=columns)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            empty_df = pd.DataFrame([], columns=columns)
            st.dataframe(empty_df, use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Upload Knowledge Base PDF")
        uploaded_file = st.file_uploader("Choose PDF file", type="pdf", key="admin_pdf_upload")
        if uploaded_file is not None:
            st.info(f"Ready to upload: {uploaded_file.name}")
            if st.button("Submit PDF to Knowledge Base", key="submit_admin_pdf_knowledge"):
                try:
                    import pdfplumber
                    from io import BytesIO
                    import nutrition_ai
                    
                    # Extract PDF text
                    with pdfplumber.open(BytesIO(uploaded_file.read())) as pdf:
                        all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                    
                    # Process with AI for nutrition insights
                    nutrition_ai_instance = nutrition_ai.ChildNutritionAI()
                    with st.spinner("Generating AI insights for nutrition knowledge..."):
                        ai_summary = nutrition_ai_instance.summarize_pdf_for_nutrition_knowledge(all_text, uploaded_file.name)
                    
                    # knowledge base save as AI summary
                    data_manager.data_manager.save_knowledge_base(
                        pdf_text=all_text,
                        pdf_name=uploaded_file.name,
                        uploaded_by='admin',
                        uploaded_by_id=st.session_state.admin_id,
                        ai_summary=ai_summary
                    )
                    st.success(f"PDF '{uploaded_file.name}' processed with AI insights and added to knowledge base!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to process PDF: {e}")
                    import traceback
                    st.error(f"Detailed error: {traceback.format_exc()}")

with meal_plans_tab:
    st.header("📝 Meal Plans Overview")
    parents_data = data_manager.data_manager.get_parents_data()
    
    # Load all users for proper name display
    all_users = load_all_user_options()
    
    # --- FILTERS ---
    filter_cols = st.columns([2,2,2,2])
    with filter_cols[0]:
        search_val = st.text_input("🔍 Search by child, parent, or plan ID", value=st.session_state.get("meal_plans_search", ""), key="meal_plans_search")
    
    # Get barangays from database
    barangay_list = ["All"]
    try:
        barangays = data_manager.data_manager.get_all_barangays()
        barangay_list.extend(sorted(barangays.values()))
    except Exception:
        barangay_list = ["All"]
    
    with filter_cols[1]:
        barangay_selected = st.selectbox("🏘️ Filter by Barangay", barangay_list, key="meal_plans_barangay")
    with filter_cols[2]:
        notes_filter = st.selectbox("🗒️ Filter by Notes", ["All", "Has Notes", "No Notes"], key="meal_plans_notes_filter")
    with filter_cols[3]:
        sort_recent = st.checkbox("Sort by Most Recent", value=True, key="meal_plans_sort_recent")

    # --- MEAL PLANS ---
    all_plans = data_manager.data_manager.get_meal_plans()
    table_rows = []
    for plan in all_plans.values():
        child_data = data_manager.data_manager.get_patient_by_id(plan['patient_id'])
        child_name = data_manager.data_manager.format_full_name(
            child_data.get('first_name', ''),
            child_data.get('middle_name', ''),
            child_data.get('last_name', '')
        ) if child_data else "Unknown"
        age_months = child_data['age_months'] if child_data and 'age_months' in child_data else None
        child_age = f"{age_months//12}y {age_months%12}m" if age_months is not None else "-"
        parent_id = child_data.get('parent_id') if child_data else None
        notes = data_manager.data_manager.get_notes_for_meal_plan(plan.get('plan_id', ''))
        
        def format_created_at(val):
            if isinstance(val, str):
                return val
            if isinstance(val, datetime):
                return val.strftime('%b %d, %Y %I:%M %p')
            return str(val)
            
        def clean_note(note_val):
            if isinstance(note_val, str):
                try:
                    parsed = json.loads(note_val)
                    if isinstance(parsed, dict) and 'text' in parsed:
                        return parsed['text']
                except Exception:
                    pass
                note_val = note_val.replace('\r\n', '  \n').replace('\n', '  \n').replace('/n', '  \n')
            return note_val
        
        if notes:
            notes_str = "\n".join([
                f"Noted by {get_user_display_name(note.get('nutritionist_id'), all_users)}: {note.get('note', '')}" 
                for note in notes
            ])
        else:
            notes_str = ""
            
        parent_full_name = "Unknown"
        barangay_val = "-"
        if parent_id is not None:
            parent_info = parents_data.get(str(parent_id))
            if parent_info:
                parent_full_name = f"{parent_info.get('first_name', '')} {parent_info.get('last_name', '')}".strip()
                barangay_id = child_data.get('barangay_id') if child_data else None
                if barangay_id:
                    barangay_val = data_manager.data_manager.get_barangay_name(barangay_id)
                    
        plan_details_clean = clean_note(plan.get('plan_details', ''))
        generated_at_val = format_created_at(plan.get('generated_at', ''))

        medical_conditions = child_data.get('other_medical_problems', '-') if child_data else '-'
        allergies = child_data.get('allergies', '-') if child_data else '-'
        religion_val = child_data.get('religion', '-') if child_data else '-'
        diet_restrictions = f"Medical Condition: {medical_conditions}  \nAllergy: {allergies}  \nReligion: {religion_val}"
        
        table_rows.append({
            "Plan ID": plan.get('plan_id', ''),
            "Child Name": child_name,
            "Child Age": child_age,
            "Parent": parent_full_name,
            "Barangay": barangay_val,
            "Diet Restrictions": diet_restrictions,
            "Plan Details": plan_details_clean,
            "Generated at": generated_at_val,
            "Notes": notes_str,
            "_has_notes": bool(notes),
            "_raw_notes": notes,
            "_raw_child_name": child_name,
            "_raw_parent_name": parent_full_name,
            "_raw_plan_id": str(plan.get('plan_id', '')),
        })

    # --- APPLY FILTERS ---
    filtered_rows = table_rows
    # Search filter
    if search_val:
        search_val_lower = search_val.lower()
        filtered_rows = [row for row in filtered_rows if search_val_lower in row['_raw_child_name'].lower() or search_val_lower in row['_raw_parent_name'].lower() or search_val_lower in row['_raw_plan_id'].lower()]
    # Barangay filter
    if barangay_selected and barangay_selected != "All":
        filtered_rows = [row for row in filtered_rows if row["Barangay"] == barangay_selected]
    # Notes filter
    if notes_filter == "Has Notes":
        filtered_rows = [row for row in filtered_rows if row["_has_notes"]]
    elif notes_filter == "No Notes":
        filtered_rows = [row for row in filtered_rows if not row["_has_notes"]]
    # Sort by most recent
    if sort_recent:
        def get_dt(row):
            val = row.get('Generated at', '')
            try:
                return datetime.strptime(val, '%b %d, %Y %I:%M %p')
            except Exception:
                return datetime.min
        filtered_rows.sort(key=get_dt, reverse=True)
    else:
        # Sort by plan ID ascending (as int)
        filtered_rows.sort(key=lambda x: int(x.get('Plan ID', 0)))

    columns = ["Plan ID", "Child Name", "Child Age", "Parent", "Barangay", "Diet Restrictions", "Plan Details", "Generated at", "Notes"]
    if filtered_rows:
        # Render table header
        cols = st.columns(len(columns))
        for i, col in enumerate(columns):
            cols[i].markdown(f"**{col}**")
        # Render table rows
        for row in filtered_rows:
            plan_id = row.get("Plan ID")
            gen_at_val = row.get("Generated at")
            if gen_at_val:
                if isinstance(gen_at_val, str):
                    gen_at_val_fmt = gen_at_val
                elif isinstance(gen_at_val, datetime):
                    gen_at_val_fmt = gen_at_val.strftime("%b %d, %Y %I:%M %p")
                else:
                    gen_at_val_fmt = str(gen_at_val)
            else:
                gen_at_val_fmt = "-"
            vals = [row[col] if col != "Generated at" else gen_at_val_fmt for col in columns]
            val_cols = st.columns(len(columns))
            for i, val in enumerate(vals):
                if columns[i] == "Plan Details":
                    expand_key = f"meal_plans_details_expanded_{plan_id}"
                    if expand_key not in st.session_state:
                        st.session_state[expand_key] = False
                    is_expanded = st.session_state[expand_key]
                    preview_len = 0
                    if not is_expanded and isinstance(val, str) and len(val) > preview_len:
                        val_cols[i].markdown(val[:preview_len], unsafe_allow_html=True)
                        if val_cols[i].button("Show Details", key=f"meal_plans_show_details_{plan_id}"):
                            st.session_state[expand_key] = True
                            st.rerun()
                    else:
                        val_cols[i].markdown(val, unsafe_allow_html=True)
                        if is_expanded and val_cols[i].button("Minimize", key=f"meal_plans_hide_details_{plan_id}"):
                            st.session_state[expand_key] = False
                            st.rerun()
                elif columns[i] == "Notes":
                    val_cols[i].markdown(val, unsafe_allow_html=True)
                else:
                    val_cols[i].markdown(val)
    else:
        empty_df = pd.DataFrame([], columns=columns)
        st.dataframe(empty_df, use_container_width=True, hide_index=True)

# Add Notes Tab
with add_notes_tab:
    st.header("📝 Add Notes to Meal Plans")
    parents_data = data_manager.data_manager.get_parents_data()
    
    # Load all users for proper name display
    all_users = load_all_user_options()

    # --- FILTERS ---
    filter_cols = st.columns([2,2,2,2])
    with filter_cols[0]:
        search_val = st.text_input("🔍 Search by child, parent, or plan ID", value=st.session_state.get("add_notes_search", ""), key="add_notes_search")
    
    # Get barangays from database
    barangay_list = ["All"]
    try:
        conn = data_manager.data_manager.conn
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT barangay_name FROM barangays ORDER BY barangay_name")
        barangay_rows = cursor.fetchall()
        barangay_list.extend([row['barangay_name'] for row in barangay_rows])
    except Exception:
        barangay_list = ["All"]
    
    with filter_cols[1]:
        barangay_selected = st.selectbox("🏘️ Filter by Barangay", barangay_list, key="add_notes_barangay")
    with filter_cols[2]:
        notes_filter = st.selectbox("🗒️ Filter by Notes", ["All", "Has Notes", "No Notes"], key="add_notes_notes_filter")
    with filter_cols[3]:
        sort_recent = st.checkbox("Sort by Most Recent", value=True, key="add_notes_sort_recent")

    # --- GET AND PREPARE MEAL PLANS ---
    all_plans = data_manager.data_manager.get_meal_plans()
    table_rows = []
    for plan in all_plans.values():
        child_data = data_manager.data_manager.get_patient_by_id(plan['patient_id'])
        child_name = data_manager.data_manager.format_full_name(
            child_data.get('first_name', ''),
            child_data.get('middle_name', ''),
            child_data.get('last_name', '')
        ) if child_data else "Unknown"
        age_months = child_data['age_months'] if child_data and 'age_months' in child_data else None
        child_age = f"{age_months//12}y {age_months%12}m" if age_months is not None else "-"
        parent_id = child_data.get('parent_id') if child_data else None
        notes = data_manager.data_manager.get_notes_for_meal_plan(plan.get('plan_id', ''))
        
        def format_created_at(val):
            if isinstance(val, str):
                try:
                    dt = datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
                    return dt.strftime('%b %d')
                except Exception:
                    return val
            if isinstance(val, datetime):
                return val.strftime('%b %d')
            return str(val)
            
        def clean_note(note_val):
            if isinstance(note_val, str):
                try:
                    parsed = json.loads(note_val)
                    if isinstance(parsed, dict) and 'text' in parsed:
                        note_val = parsed['text']
                except Exception:
                    pass
            if isinstance(note_val, str):
                note_val = note_val.replace('\r\n', '  \n').replace('\n', '  \n').replace('/n', '  \n')
            return note_val
        
        if notes:
            notes_str = "<br>".join([
                f"Noted by {get_user_display_name(note.get('nutritionist_id'), all_users)}: {clean_note(note.get('notes', ''))}"
                for note in notes
            ])
        else:
            notes_str = "No notes yet"
            
        parent_full_name = "Unknown"
        barangay_val = "-"
        if parent_id is not None:
            parent_info = parents_data.get(str(parent_id))
            if parent_info:
                parent_full_name = data_manager.data_manager.format_full_name(
                    parent_info.get('first_name', ''),
                    parent_info.get('middle_name', ''),
                    parent_info.get('last_name', '')
                )
                # Get barangay name
                barangay_id = child_data.get('barangay_id') if child_data else None
                if barangay_id:
                    barangay_val = data_manager.data_manager.get_barangay_name(barangay_id)
                else:
                    barangay_val = "-"
            else:
                parent_full_name = f"Parent {parent_id}"
                
        plan_details_clean = clean_note(plan.get('plan_details', ''))
        generated_at_val = plan.get('generated_at', '')
        
        # Diet Restrictions
        medical_conditions = child_data.get('other_medical_problems', '-') if child_data else '-'
        allergies = child_data.get('allergies', '-') if child_data else '-'
        religion_val = child_data.get('religion', '-') if child_data else '-'
        diet_restrictions = f"Medical Condition: {medical_conditions}  \nAllergy: {allergies}  \nReligion: {religion_val}"
        
        table_rows.append({
            "Plan ID": plan.get('plan_id', ''),
            "Child Name": child_name,
            "Child Age": child_age,
            "Parent": parent_full_name,
            "Barangay": barangay_val,
            "Diet Restrictions": diet_restrictions,
            "Plan Details": plan_details_clean,
            "Generated at": generated_at_val,
            "Notes": notes_str,
            "_has_notes": bool(notes),
            "_raw_notes": notes,
            "_raw_child_name": child_name,
            "_raw_parent_name": parent_full_name,
            "_raw_plan_id": str(plan.get('plan_id', '')),
        })

    # --- APPLY FILTERS ---
    filtered_rows = table_rows
    # Search filter
    if search_val:
        search_val_lower = search_val.lower()
        filtered_rows = [row for row in filtered_rows if search_val_lower in row['_raw_child_name'].lower() or search_val_lower in row['_raw_parent_name'].lower() or search_val_lower in row['_raw_plan_id'].lower()]
    # Barangay filter
    if barangay_selected and barangay_selected != "All":
        filtered_rows = [row for row in filtered_rows if row["Barangay"] == barangay_selected]
    # Notes filter
    if notes_filter == "Has Notes":
        filtered_rows = [row for row in filtered_rows if row["_has_notes"]]
    elif notes_filter == "No Notes":
        filtered_rows = [row for row in filtered_rows if not row["_has_notes"]]
    # Sort by most recent
    if sort_recent:
        def get_dt(row):
            val = row.get("Generated at", "")
            # Try to parse datetime, fallback to plan ID (as int) if missing/invalid
            try:
                return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
            except Exception:
                try:
                    # Fallback: use plan ID as int (higher = newer)
                    return datetime.min.replace(year=1900) + timedelta(days=int(row.get('Plan ID', 0)))
                except Exception:
                    return datetime.min
        filtered_rows.sort(key=get_dt, reverse=True)
    else:
        # Sort by plan ID ascending (as int)
        filtered_rows.sort(key=lambda x: int(x.get('Plan ID', 0)))

    columns = ["Plan ID", "Child Name", "Child Age", "Parent", "Barangay", "Diet Restrictions", "Plan Details", "Generated at", "Notes", "Add note"]
    
    # Initialize admin as nutritionist ID for saving notes
    if 'admin_as_nutritionist_id' not in st.session_state:
        st.session_state.admin_as_nutritionist_id = st.session_state.get('admin_id', '1')

    if filtered_rows:
        # Render table header
        cols = st.columns(len(columns))
        for i, col in enumerate(columns):
            cols[i].markdown(f"**{col}**")
        # Render table rows
        for row in filtered_rows:
            plan_id = row.get("Plan ID")
            gen_at_val = row.get("Generated at")
            if gen_at_val:
                if isinstance(gen_at_val, str):
                    try:
                        gen_at_val_fmt = datetime.strptime(gen_at_val, "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y %I:%M %p")
                    except Exception:
                        gen_at_val_fmt = gen_at_val
                elif isinstance(gen_at_val, datetime):
                    gen_at_val_fmt = gen_at_val.strftime("%b %d, %Y %I:%M %p")
                else:
                    gen_at_val_fmt = str(gen_at_val)
            else:
                gen_at_val_fmt = "-"
            vals = [row[col] if col != "Generated at" else gen_at_val_fmt for col in columns[:-1]]
            val_cols = st.columns(len(columns))
            for i, val in enumerate(vals):
                if columns[i] == "Plan Details":
                    # Minimize/maximize logic
                    expand_key = f"add_notes_plan_details_expanded_{plan_id}"
                    if expand_key not in st.session_state:
                        st.session_state[expand_key] = False
                    is_expanded = st.session_state[expand_key]
                    preview_len = 0  # Show only first 0 characters when minimized
                    if not is_expanded and isinstance(val, str) and len(val) > preview_len:
                        preview = val[:preview_len]
                        btn_label = "Show Plan Details"
                        val_cols[i].markdown(preview, unsafe_allow_html=True)
                        if val_cols[i].button(btn_label, key=f"add_notes_expand_{plan_id}"):
                            st.session_state[expand_key] = True
                            st.rerun()
                    else:
                        btn_label = "Minimize"
                        val_cols[i].markdown(val, unsafe_allow_html=True)
                        if isinstance(val, str) and len(val) > preview_len:
                            if val_cols[i].button(btn_label, key=f"add_notes_minimize_{plan_id}"):
                                st.session_state[expand_key] = False
                                st.rerun()
                elif columns[i] == "Notes":
                    val_cols[i].markdown(val, unsafe_allow_html=True)
                else:
                    val_cols[i].markdown(val)
            
            # Add note button and input in last column
            add_note_key = f"admin_add_note_{plan_id}"
            show_input_key = f"admin_show_note_input_{plan_id}"
            if not st.session_state.get(show_input_key):
                if val_cols[-1].button("Add Note", key=add_note_key):
                    st.session_state[show_input_key] = True
                    st.rerun()
            else:
                new_note = val_cols[-1].text_area("Enter note:", key=f"admin_note_input_{plan_id}")
                save_col, cancel_col = val_cols[-1].columns([1,1])
                if save_col.button("Save Note", key=f"admin_save_note_{plan_id}"):
                    # Find patient_id for this plan
                    plan = next((p for p in all_plans.values() if str(p.get('plan_id')) == str(plan_id)), None)
                    patient_id = plan['patient_id'] if plan and 'patient_id' in plan else None
                    if not patient_id:
                        st.error('Could not determine patient_id for this meal plan.')
                    else:
                        # Use admin ID as nutritionist ID for saving notes
                        data_manager.data_manager.save_nutritionist_note(plan_id, patient_id, st.session_state.admin_as_nutritionist_id, new_note)
                        log_action("Add Note to Meal Plan", {
                            'plan_id': plan_id,
                            'patient_id': patient_id,
                            'note_length': len(new_note),
                            'action': 'note_added'
                        })
                    st.success("Note added!")
                    st.session_state[show_input_key] = False
                    st.rerun()
                if cancel_col.button("Cancel", key=f"admin_cancel_note_{plan_id}"):
                    st.session_state[show_input_key] = False
                    st.rerun()
    else:
        empty_df = pd.DataFrame([], columns=columns)
        st.dataframe(empty_df, use_container_width=True, hide_index=True)

# Logs Tab
with logs_tab:
    st.header("📜 Admin Logs")
    
    # Get current admin info for table keys
    current_admin_id = st.session_state.get('admin_id', '1')
    
    logs = load_logs()

    columns = ['action', 'description', 'log_timestamp']
    if logs:
        log_df = pd.DataFrame(logs)
        def flatten_details(details):
            if isinstance(details, dict):
                return ", ".join(f"{k}: {v}" for k, v in details.items())
            return str(details)
        if 'description' in log_df.columns:
            log_df['description'] = log_df['description'].apply(flatten_details)
        st.dataframe(log_df[columns], use_container_width=True, key=f"logs_table_{current_admin_id}")
    else:
        empty_df = pd.DataFrame([], columns=columns)
        st.dataframe(empty_df, use_container_width=True, key=f"empty_logs_table_{current_admin_id}")