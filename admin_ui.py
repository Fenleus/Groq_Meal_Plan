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
    # Load from MySQL audit_logs table filtered by current admin
    admin_id = st.session_state.get('admin_id', '1')  # Default to admin 1 if not set
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

with st.sidebar:
    st.header("🛠️ Admin Login")
    
    # Load admin options from database
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
    
    # Check if admin changed and clear cache if needed
    if 'admin_id' not in st.session_state or st.session_state.admin_id != selected_admin:
        st.session_state.admin_id = selected_admin
        # Clear any cached data that should refresh when admin changes
        if 'cached_logs' in st.session_state:
            del st.session_state['cached_logs']
    
    st.info(f"Logged in as: {admin_options[selected_admin]}")
    st.write(f"ID: {selected_admin}")
    st.subheader("📊 Quick Stats")

    try:
        meal_count = len(data_manager.data_manager.get_meals_data())
    except Exception:
        meal_count = 0
    try:
        log_count = len(load_logs())
    except Exception:
        log_count = 0
    st.metric("Total Meals", meal_count)
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
    # Save to MySQL audit_logs table with user_id
    import json
    conn = data_manager.data_manager.conn
    cursor = conn.cursor()
    sql = "INSERT INTO audit_logs (log_timestamp, action, description, user_id) VALUES (%s, %s, %s, %s)"
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    admin_id = st.session_state.get('admin_id', '1')  # Default to admin 1 if not set
    cursor.execute(sql, (now, action, json.dumps(filtered_details), admin_id))
    conn.commit()


import json

# Tabs: Meal Database, Knowledge Base, Meal Plans Overview, Logs
main_tab, kb_tab, meal_plans_tab, logs_tab = st.tabs([
    "�️ Meal Database", 
    "📚 Knowledge Base", 
    "📝 Meal Plans Overview", 
    "📜 Logs"
])
with main_tab:
    st.header("�️ Meal Database Management")
    # Load meal data from MySQL
    meal_data = data_manager.data_manager.get_meals_data()
    if not meal_data:
        st.info("No meal data available.")
    else:
        # Search bar
        if 'meal_db_search' not in st.session_state:
            st.session_state['meal_db_search'] = ''
        prev_search = st.session_state['meal_db_search']
        search_val = st.text_input(
            "🔍 Search meal database",
            value=prev_search,
            key='meal_db_search',
        )
        if search_val != prev_search:
            st.session_state['meal_db_search'] = search_val
            st.rerun()
        def filter_meals(data, query):
            if not query:
                return data
            query = query.lower()
            filtered = []
            for item in data:
                for col in ["meal_name", "description", "course", "keywords"]:
                    val = item.get(col, '')
                    if isinstance(val, list):
                        val = ', '.join(val)
                    if query in str(val).lower():
                        filtered.append(item)
                        break
            return filtered

        filtered_meal_data = filter_meals(meal_data, search_val)

        # Pagination setup
        records_per_page = 10
        total_records = len(filtered_meal_data)
        total_pages = (total_records - 1) // records_per_page + 1
        page = st.session_state.get('meal_db_page', 1)
        def set_page(new_page):
            st.session_state['meal_db_page'] = new_page
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
            "meal_id",
            "meal_name",
            "course",
            "prep_time_minutes",
            "servings",
            "calories_kcal",
            "Options"
        ]

        # Render column headers
        header_cols = st.columns([1,1,3,2,2,1,2,2])
        header_labels = [
            "No.",
            "Meal ID",
            "Meal Name",
            "Course",
            "Prep Time",
            "Servings",
            "Calories",
            "Options"
        ]
        for i, label in enumerate(header_labels):
            header_cols[i].markdown(f"**{label}**")

        # Prepare table data
        table_rows = []
        for idx, item in enumerate(filtered_meal_data[start_idx:end_idx], start=start_idx+1):
            row = {
                "No.": idx,
                "meal_id": item.get("meal_id", ""),
                "meal_name": item.get("meal_name", ""),
                "course": item.get("course", ""),
                "prep_time_minutes": f"{item.get('prep_time_minutes', 0)} min" if item.get('prep_time_minutes') else "-",
                "servings": item.get("servings", ""),
                "calories_kcal": f"{item.get('calories_kcal', 0)} kcal" if item.get('calories_kcal') else "-",
                "Options": ""
            }
            table_rows.append(row)

        # Render table
        for row_idx, row in enumerate(table_rows):
            col_widths = [1,1,3,2,2,1,2,2]
            cols = st.columns(col_widths)
            cols[0].markdown(f"{row['No.']}")

            for i, col in enumerate(columns[1:-1], start=1):
                cols[i].markdown(row[col])

            btn_cols = cols[len(columns)-1].columns([1,0.1,1])
            data_btn = btn_cols[0].button("Details", key=f"data_{row['No.']}" )
            edit_btn = btn_cols[2].button("Edit", key=f"edit_{row['No.']}" )

            if data_btn:
                st.session_state['show_meal_details'] = row['No.']
                st.session_state['show_meal_notice'] = True
                st.rerun()

            if edit_btn:
                st.session_state['edit_meal_id'] = filtered_meal_data[start_idx + row_idx]['meal_id']
                st.session_state['show_edit_form'] = True
                st.rerun()

        # Show meal editing form
        if st.session_state.get('show_edit_form') and st.session_state.get('edit_meal_id'):
            meal_id = st.session_state.get('edit_meal_id')
            meal_to_edit = data_manager.data_manager.get_meal_by_id(meal_id)
            
            if meal_to_edit:
                st.markdown("---")
                st.markdown(f"### ✏️ Edit Meal: {meal_to_edit.get('meal_name', '')}")
                
                with st.form("edit_meal_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Basic Information")
                        meal_name = st.text_input("Meal Name", value=meal_to_edit.get('meal_name', ''))
                        description = st.text_area("Description", value=meal_to_edit.get('description', ''))
                        course = st.text_input("Course", value=meal_to_edit.get('course', ''))
                        keywords = st.text_input("Keywords", value=meal_to_edit.get('keywords', ''))
                        
                        st.subheader("Cooking Information")
                        prep_time = st.number_input("Prep Time (minutes)", min_value=0, value=meal_to_edit.get('prep_time_minutes', 0))
                        cook_time = st.number_input("Cook Time (minutes)", min_value=0, value=meal_to_edit.get('cook_time_minutes', 0))
                        servings = st.number_input("Servings", min_value=1, value=meal_to_edit.get('servings', 1))
                        
                        # Ingredients handling
                        ingredients = meal_to_edit.get('ingredients', [])
                        if isinstance(ingredients, str):
                            try:
                                import json
                                ingredients = json.loads(ingredients)
                            except:
                                ingredients = [ingredients]
                        elif not isinstance(ingredients, list):
                            ingredients = []
                        
                        ingredients_text = '\n'.join(ingredients) if ingredients else ''
                        ingredients_input = st.text_area("Ingredients (one per line)", value=ingredients_text)
                        
                        instructions = st.text_area("Instructions", value=meal_to_edit.get('instructions', ''))
                        image_url = st.text_input("Image URL", value=meal_to_edit.get('image_url', ''))
                    
                    with col2:
                        st.subheader("Nutrition Information (per serving)")
                        calories = st.number_input("Calories (kcal)", min_value=0, value=meal_to_edit.get('calories_kcal', 0) or 0)
                        protein = st.number_input("Protein (g)", min_value=0.0, value=float(meal_to_edit.get('protein_g', 0) or 0), format="%.1f")
                        carbs = st.number_input("Carbohydrates (g)", min_value=0.0, value=float(meal_to_edit.get('carbohydrates_g', 0) or 0), format="%.1f")
                        fat = st.number_input("Fat (g)", min_value=0.0, value=float(meal_to_edit.get('fat_g', 0) or 0), format="%.1f")
                        
                        st.subheader("Detailed Nutrition")
                        sat_fat = st.number_input("Saturated Fat (g)", min_value=0.0, value=float(meal_to_edit.get('saturated_fat_g', 0) or 0), format="%.1f")
                        poly_fat = st.number_input("Polyunsaturated Fat (g)", min_value=0.0, value=float(meal_to_edit.get('polyunsaturated_fat_g', 0) or 0), format="%.1f")
                        mono_fat = st.number_input("Monounsaturated Fat (g)", min_value=0.0, value=float(meal_to_edit.get('monounsaturated_fat_g', 0) or 0), format="%.1f")
                        trans_fat = st.number_input("Trans Fat (g)", min_value=0.0, value=float(meal_to_edit.get('trans_fat_g', 0) or 0), format="%.1f")
                        cholesterol = st.number_input("Cholesterol (mg)", min_value=0.0, value=float(meal_to_edit.get('cholesterol_mg', 0) or 0), format="%.1f")
                        sodium = st.number_input("Sodium (mg)", min_value=0.0, value=float(meal_to_edit.get('sodium_mg', 0) or 0), format="%.1f")
                        potassium = st.number_input("Potassium (mg)", min_value=0.0, value=float(meal_to_edit.get('potassium_mg', 0) or 0), format="%.1f")
                        fiber = st.number_input("Fiber (g)", min_value=0.0, value=float(meal_to_edit.get('fiber_g', 0) or 0), format="%.1f")
                        sugar = st.number_input("Sugar (g)", min_value=0.0, value=float(meal_to_edit.get('sugar_g', 0) or 0), format="%.1f")
                        
                        st.subheader("Vitamins & Minerals")
                        vitamin_a = st.number_input("Vitamin A (IU)", min_value=0.0, value=float(meal_to_edit.get('vitamin_a_iu', 0) or 0), format="%.1f")
                        vitamin_c = st.number_input("Vitamin C (mg)", min_value=0.0, value=float(meal_to_edit.get('vitamin_c_mg', 0) or 0), format="%.1f")
                        calcium = st.number_input("Calcium (mg)", min_value=0.0, value=float(meal_to_edit.get('calcium_mg', 0) or 0), format="%.1f")
                        iron = st.number_input("Iron (mg)", min_value=0.0, value=float(meal_to_edit.get('iron_mg', 0) or 0), format="%.1f")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        save_btn = st.form_submit_button("💾 Save Changes", type="primary")
                    with col2:
                        cancel_btn = st.form_submit_button("❌ Cancel")
                    with col3:
                        delete_btn = st.form_submit_button("🗑️ Delete Meal", type="secondary")
                    
                    if save_btn:
                        # Prepare updated meal data
                        updated_meal_data = {
                            'meal_name': meal_name,
                            'description': description,
                            'course': course,
                            'keywords': keywords,
                            'prep_time_minutes': prep_time,
                            'cook_time_minutes': cook_time,
                            'servings': servings,
                            'ingredients': [line.strip() for line in ingredients_input.split('\n') if line.strip()],
                            'instructions': instructions,
                            'image_url': image_url,
                            'calories_kcal': calories,
                            'protein_g': protein,
                            'carbohydrates_g': carbs,
                            'fat_g': fat,
                            'saturated_fat_g': sat_fat,
                            'polyunsaturated_fat_g': poly_fat,
                            'monounsaturated_fat_g': mono_fat,
                            'trans_fat_g': trans_fat,
                            'cholesterol_mg': cholesterol,
                            'sodium_mg': sodium,
                            'potassium_mg': potassium,
                            'fiber_g': fiber,
                            'sugar_g': sugar,
                            'vitamin_a_iu': vitamin_a,
                            'vitamin_c_mg': vitamin_c,
                            'calcium_mg': calcium,
                            'iron_mg': iron
                        }
                        
                        try:
                            data_manager.data_manager.update_meal(meal_id, updated_meal_data)
                            
                            # Log the action
                            log_action("Update Meal", {
                                'meal_id': meal_id,
                                'meal_name': meal_name,
                                'action': 'meal_updated'
                            })
                            
                            st.success(f"Meal '{meal_name}' updated successfully!")
                            st.session_state['show_edit_form'] = False
                            del st.session_state['edit_meal_id']
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating meal: {e}")
                    
                    if cancel_btn:
                        st.session_state['show_edit_form'] = False
                        del st.session_state['edit_meal_id']
                        st.rerun()
                    
                    if delete_btn:
                        try:
                            meal_name_to_delete = meal_to_edit.get('meal_name', '')
                            data_manager.data_manager.delete_meal(meal_id)
                            
                            # Log the action
                            log_action("Delete Meal", {
                                'meal_id': meal_id,
                                'meal_name': meal_name_to_delete,
                                'action': 'meal_deleted'
                            })
                            
                            st.success(f"Meal '{meal_name_to_delete}' deleted successfully!")
                            st.session_state['show_edit_form'] = False
                            del st.session_state['edit_meal_id']
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting meal: {e}")
            else:
                st.error("Meal not found!")
                st.session_state['show_edit_form'] = False
                del st.session_state['edit_meal_id']

        # Show meal details section
        if st.session_state.get('show_meal_details'):
            if st.session_state.get('show_meal_notice'):
                meal_idx = st.session_state.get('show_meal_details', None)
                meal_name = ""
                if meal_idx and 0 < meal_idx <= len(filtered_meal_data):
                    meal = filtered_meal_data[meal_idx-1]
                    meal_name = meal.get('meal_name', '')
                st.markdown(f"""
                    <div style='background:#2196F3;color:white;padding:0.75rem 1.5rem;border-radius:8px;font-weight:bold;margin-bottom:0.5rem;font-size:1.1rem;'>
                        The meal details are shown below.<br>
                        <span style='font-size:1rem;font-weight:normal;'>You are now viewing details for: <b>{meal_name}</b></span>
                    </div>
                """, unsafe_allow_html=True)
                st.session_state['show_meal_notice'] = False

            i = st.session_state['show_meal_details']-1
            if 0 <= i < len(filtered_meal_data):
                meal = filtered_meal_data[i]
                section_title = meal.get('meal_name', '')
                st.markdown(f"<h2>{section_title}</h2>", unsafe_allow_html=True)
                
                # Meal Information
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Description:** {meal.get('description', 'N/A')}")
                    st.markdown(f"**Course:** {meal.get('course', 'N/A')}")
                    st.markdown(f"**Keywords:** {meal.get('keywords', 'N/A')}")
                    st.markdown(f"**Prep Time:** {meal.get('prep_time_minutes', 0)} minutes")
                    st.markdown(f"**Cook Time:** {meal.get('cook_time_minutes', 0)} minutes")
                    st.markdown(f"**Servings:** {meal.get('servings', 'N/A')}")
                
                with col2:
                    st.markdown("**Nutrition Information (per serving):**")
                    st.markdown(f"- Calories: {meal.get('calories_kcal', 'N/A')} kcal")
                    st.markdown(f"- Protein: {meal.get('protein_g', 'N/A')} g")
                    st.markdown(f"- Carbohydrates: {meal.get('carbohydrates_g', 'N/A')} g")
                    st.markdown(f"- Fat: {meal.get('fat_g', 'N/A')} g")
                    st.markdown(f"- Fiber: {meal.get('fiber_g', 'N/A')} g")
                    st.markdown(f"- Sodium: {meal.get('sodium_mg', 'N/A')} mg")
                    st.markdown(f"- Calcium: {meal.get('calcium_mg', 'N/A')} mg")
                    st.markdown(f"- Iron: {meal.get('iron_mg', 'N/A')} mg")
                
                # Ingredients
                ingredients = meal.get('ingredients', [])
                if ingredients:
                    st.markdown("**Ingredients:**")
                    if isinstance(ingredients, list):
                        for ingredient in ingredients:
                            st.markdown(f"- {ingredient}")
                    else:
                        st.markdown(ingredients)
                
                # Instructions
                instructions = meal.get('instructions', '')
                if instructions:
                    st.markdown("**Instructions:**")
                    st.markdown(instructions)


# Knowledge Base Tab

with kb_tab:
    st.header("📚 Knowledge Base")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Knowledge Base Table")
        kb_entries = data_manager.data_manager.get_knowledge_base()
        conn = data_manager.data_manager.conn
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, CONCAT(first_name, ' ', last_name) as full_name FROM users WHERE role_id = (SELECT role_id FROM roles WHERE role_name = 'admin')")
        admins = {str(row['user_id']): row['full_name'] for row in cursor.fetchall()}
        cursor.execute("SELECT user_id, CONCAT(first_name, ' ', last_name) as full_name FROM users WHERE role_id = (SELECT role_id FROM roles WHERE role_name = 'nutritionist')")
        nutritionists = {str(row['user_id']): row['full_name'] for row in cursor.fetchall()}
        # Use a set to avoid duplicate (kb_id, file name) pairs
        seen_files = set()
        table_rows = []
        if isinstance(kb_entries, dict):
            for kb in kb_entries.values():
                kb_id = kb.get('kb_id', '')
                pdf_names = kb.get('pdf_name', [])
                if isinstance(pdf_names, str):
                    try:
                        pdf_names = json.loads(pdf_names)
                    except Exception:
                        pdf_names = [pdf_names]
                if not isinstance(pdf_names, list):
                    pdf_names = [pdf_names]
                uploaded_by_id = str(kb.get('uploaded_by_id', ''))
                uploaded_by_role = kb.get('uploaded_by', '')
                if uploaded_by_role == 'admin':
                    full_name = admins.get(uploaded_by_id, 'Unknown Admin')
                elif uploaded_by_role == 'nutritionist':
                    full_name = nutritionists.get(uploaded_by_id, 'Unknown Nutritionist')
                else:
                    full_name = 'Unknown'
                for pdf_name in pdf_names:
                    if isinstance(pdf_name, dict):
                        pdf_name_str = pdf_name.get('name', str(pdf_name))
                    else:
                        pdf_name_str = str(pdf_name)
                    file_key = (kb_id, pdf_name_str)
                    if file_key not in seen_files:
                        seen_files.add(file_key)
                        table_rows.append({
                            "id": kb_id,
                            "file name": pdf_name_str,
                            "uploaded by (full name)": full_name,
                            "uploaded by (role)": uploaded_by_role.capitalize() if uploaded_by_role else "Unknown",
                            "added at": kb.get('added_at', '')
                        })
        if table_rows:
            df = pd.DataFrame(table_rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            columns = ["id", "file name", "uploaded by (full name)", "uploaded by (role)", "added at"]
            empty_df = pd.DataFrame([], columns=columns)
            st.dataframe(empty_df, use_container_width=True, hide_index=True)
            # ...removed info message...
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
                    
                    # Save to knowledge base as admin with AI summary
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
                    # Show detailed error for debugging
                    import traceback
                    st.error(f"Detailed error: {traceback.format_exc()}")

# Logs Tab
with meal_plans_tab:
    st.header("📝 Meal Plans Overview")
    parents_data = data_manager.data_manager.get_parents_data()
    # --- FILTERS ---
    filter_cols = st.columns([2,2,2,2])
    with filter_cols[0]:
        search_val = st.text_input("🔍 Search by child, parent, or plan ID", value=st.session_state.get("add_notes_search", ""), key="add_notes_search")
    barangay_list = ["All"]
    try:
        barangays = data_manager.data_manager.get_all_barangays()
        barangay_list.extend(sorted(barangays.values()))
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
                # Replace newlines for markdown rendering
                note_val = note_val.replace('\r\n', '  \n').replace('\n', '  \n').replace('/n', '  \n')
            return note_val
        if notes:
            # Load nutritionist names from database
            try:
                conn = data_manager.data_manager.conn
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT user_id, CONCAT(first_name, ' ', last_name) as full_name FROM users WHERE role_id = (SELECT role_id FROM roles WHERE role_name = 'nutritionist')")
                nutritionist_rows = cursor.fetchall()
                nutritionist_options = {str(row['user_id']): row['full_name'] for row in nutritionist_rows}
            except Exception:
                nutritionist_options = {}
            
            def get_nutritionist_name(nutritionist_id):
                return nutritionist_options.get(str(nutritionist_id), f"Nutritionist {nutritionist_id}")
            notes_str = "\n".join([
                f"Noted by {get_nutritionist_name(note.get('nutritionist_id'))}: {note.get('note', '')}" for note in notes
            ])
        else:
            notes_str = ""
        parent_full_name = "Unknown"
        barangay_val = "-"
        religion_val = "-"
        if parent_id is not None:
            parent_info = parents_data.get(str(parent_id))
            if parent_info:
                parent_full_name = f"{parent_info.get('first_name', '')} {parent_info.get('last_name', '')}".strip()
                # Get barangay name if barangay_id exists
                barangay_id = child_data.get('barangay_id') if child_data else None
                if barangay_id:
                    barangay_val = data_manager.data_manager.get_barangay_name(barangay_id)
                religion_val = "-"  # Religion not available in new schema
        plan_details_clean = clean_note(plan.get('plan_details', ''))
        generated_at_val = format_created_at(plan.get('generated_at', ''))
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
                    expand_key = f"plan_details_expanded_{plan_id}"
                    if expand_key not in st.session_state:
                        st.session_state[expand_key] = False
                    is_expanded = st.session_state[expand_key]
                    preview_len = 0
                    if not is_expanded and isinstance(val, str) and len(val) > preview_len:
                        val_cols[i].markdown(val[:preview_len], unsafe_allow_html=True)
                        if val_cols[i].button("Show Details", key=f"show_details_{plan_id}"):
                            st.session_state[expand_key] = True
                            st.rerun()
                    else:
                        val_cols[i].markdown(val, unsafe_allow_html=True)
                        if is_expanded and val_cols[i].button("Minimize", key=f"hide_details_{plan_id}"):
                            st.session_state[expand_key] = False
                            st.rerun()
                elif columns[i] == "Notes":
                    val_cols[i].markdown(val, unsafe_allow_html=True)
                else:
                    val_cols[i].markdown(val)
    else:
        empty_df = pd.DataFrame([], columns=columns)
        st.dataframe(empty_df, use_container_width=True, hide_index=True)

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

