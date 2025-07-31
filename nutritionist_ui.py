import streamlit as st
import os
from nutrition_ai import ChildNutritionAI
from data_manager import data_manager
from datetime import datetime, timedelta

import pdfplumber
from io import BytesIO
import math

# Configure page
st.set_page_config(
    page_title="👩‍⚕️ Nutritionist Dashboard",
    page_icon="👩‍⚕️",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #4CAF50, #2E7D32);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .parent-card {
        background: #e8f5e8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
    .child-info {
        background: #f0f8f0;
        padding: 0.8rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'nutrition_ai' not in st.session_state:
        try:
            st.session_state.nutrition_ai = ChildNutritionAI()
            st.session_state.api_working = True
        except Exception as e:
            st.session_state.nutrition_ai = None
            st.session_state.api_working = False
            st.session_state.api_error = str(e)
    
    if 'nutritionist_id' not in st.session_state:
        st.session_state.nutritionist_id = "nutritionist_001" 

def main():
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>👩‍⚕️ Nutritionist Dashboard</h1>
        <p>Monitor and guide children's nutrition across all families</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check API status
    if not st.session_state.api_working:
        st.error(f"❌ API Error: {st.session_state.get('api_error', 'Unknown error')}")
        st.info("Make sure your GROQ_API_KEY is set in the .env file")
        return
    
    # st.success("✅ Connected to Nutrition AI")
    
    # Sidebar for nutritionist info
    with st.sidebar:
        st.header("👩‍⚕️ Nutritionist Login")
        st.info(f"Logged in as: Dr. Maria Rodriguez")
        st.write(f"ID: {st.session_state.nutritionist_id}")
        
        # Quick stats
        st.subheader("📊 Quick Stats")
        all_children = data_manager.get_children_data()
        all_meal_plans = {}
        st.metric("Total Children", len(all_children))
        st.metric("Total Meal Plans", len(all_meal_plans))
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["👨‍👩‍👧‍👦 All Parents", "📝 Add Notes", "🧠 Knowledge Base", "🍽️ Food Database"])

    with tab1:
        show_all_parents()
    
    with tab2:
        show_add_notes()
    
    with tab3:
        show_knowledge_base()
    
    with tab4:
        show_recipe_database()

def show_all_parents():
    """Display all parents and their children's meal plans"""
    st.header("👨‍👩‍👧‍👦 All Parents Overview")
    all_children = data_manager.get_children_data()
    parents_data = data_manager.get_parents_data()
    # Compact filter row: barangay dropdown and search bar on same line
    barangay_list = [
        "All",
        "Bagong Silang", "Calendola", "Chrysanthemum", "Cuyab", "Estrella", "Fatima", "G.S.I.S", "Landayan", "Langgam", "Laram", "Magsaysay", "Maharlika", "Narra", "Nueva", "Pacita 1", "Pacita 2", "Poblacion", "Riverside", "Rosario", "Sampaguita Village", "San Antonio", "San Lorenzo Ruiz", "San Roque", "San Vicente", "Santo Niño", "United Bayanihan", "United Better Living"
    ]
    filter_cols = st.columns([3, 2])
    with filter_cols[0]:
        search_val = st.text_input("🔍 Search parents", value="", key="all_parents_search")
    with filter_cols[1]:
        barangay_selected = st.selectbox("🏘️ Filter by Barangay", barangay_list, key="barangay_filter")

    # Group children by parent_id
    parent_to_children = {}
    for child in all_children.values():
        parent_id = str(child.get('parent_id'))
        if parent_id not in parent_to_children:
            parent_to_children[parent_id] = []
        parent_to_children[parent_id].append(child)

    # Prepare parent rows: show all parents, even those with no children
    parent_rows = []
    for parent_id, parent_info in parents_data.items():
        children = parent_to_children.get(str(parent_id), [])
        parent_name = parent_info.get('full_name', f"Parent {parent_id}")
        barangay = parent_info.get('barangay', '')
        num_children = len(children)
        parent_rows.append({
            "parent_id": str(parent_id),
            "Parent": parent_name,
            "Barangay": barangay,
            "# Children": num_children
        })

    # Filter by barangay
    if barangay_selected and barangay_selected != "All":
        parent_rows = [row for row in parent_rows if row["Barangay"] == barangay_selected]
    # Filter by search
    if search_val:
        search_val_lower = search_val.lower()
        parent_rows = [row for row in parent_rows if search_val_lower in row['Parent'].lower() or search_val_lower in row['parent_id'].lower()]

    if not parent_rows:
        st.info("No parents found in the system.")
        return

    # Track which parent's children are expanded
    if 'expanded_parent' not in st.session_state:
        st.session_state['expanded_parent'] = None

    # Render table header (remove Allergies and Conditions columns)
    header_cols = st.columns([1, 4, 3, 2])
    header_labels = ["No.", "Parent", "Barangay", "# Children"]
    for i, label in enumerate(header_labels):
        header_cols[i].markdown(f"**{label}**")

    # Render parent rows with expanders (remove Allergies and Conditions columns)
    for idx, row in enumerate(parent_rows, start=1):
        cols = st.columns([1, 4, 3, 2])
        cols[0].markdown(f"{idx}")
        cols[1].markdown(row["Parent"])
        cols[2].markdown(row["Barangay"])
        cols[3].markdown(str(row["# Children"]))

        with st.expander(f"Show children for {row['Parent']} ({row['# Children']} children)", expanded=False):
            children = parent_to_children[row['parent_id']]
            child_header = st.columns([1, 3, 2, 2, 2, 2])
            child_labels = ["No.", "Child Name", "Age", "BMI", "Allergies", "Conditions"]
            for i, label in enumerate(child_labels):
                child_header[i].markdown(f"<span style='color:#388e3c;font-weight:bold'>{label}</span>", unsafe_allow_html=True)
            for cidx, child in enumerate(children, start=1):
                ccols = st.columns([1, 3, 2, 2, 2, 2])
                age_months = child.get('age_in_months')
                if age_months is not None:
                    years = age_months // 12
                    months = age_months % 12
                    if years > 0 and months > 0:
                        age_str = f"{years} years, {months} months ({age_months} months)"
                    elif years > 0:
                        age_str = f"{years} years ({age_months} months)"
                    else:
                        age_str = f"{months} months"
                else:
                    age_str = "Unknown"
                ccols[0].markdown(f"{cidx}")
                child_name = f"{child.get('first_name', '')} {child.get('last_name', '')}".strip()
                ccols[1].markdown(child_name)
                ccols[2].markdown(age_str)
                ccols[3].markdown(f"{child.get('bmi', '')} ({child.get('bmi_category', '')})")
                ccols[4].markdown(child.get('allergies', ''))
                ccols[5].markdown(child.get('medical_conditions', ''))

def show_add_notes():
    """Dedicated section for adding detailed notes to meal plans"""
    st.header("📝 Add Notes to Meal Plans")
    
    # Search/filter options
    col1, col2 = st.columns(2)
    
    with col1:
        # Parent filter (dynamic)
        parents_data = data_manager.get_parents_data()
        parent_options = {"all": "All Parents"}
        for pid, pdata in parents_data.items():
            parent_options[pid] = pdata.get('full_name', f"Parent {pid}")
        selected_parent = st.selectbox("Filter by Parent", 
                                     options=list(parent_options.keys()),
                                     format_func=lambda x: parent_options[x])
    
    with col2:
        # Date range
        days_back = st.selectbox("Show plans from last:", [7, 14, 30, 60], index=2)
    
    # Get meal plans based on filters
    # Get meal plans based on filters
    all_plans = data_manager.get_meal_plans()
    filtered_plans = []
    cutoff_date = datetime.now() - timedelta(days=days_back)
    for plan in all_plans.values():
        plan_date = datetime.strptime(plan['created_at'], "%Y-%m-%d %H:%M:%S")
        if plan_date >= cutoff_date:
            # Get child data
            child_data = data_manager.get_child_by_id(plan['patient_id'])
            plan['child_name'] = f"{child_data['first_name']} {child_data['last_name']}" if child_data else "Unknown"
            age_months = child_data['age_in_months'] if child_data and 'age_in_months' in child_data else None
            if age_months is not None:
                years = age_months // 12
                months = age_months % 12
                if years > 0 and months > 0:
                    plan['child_age'] = f"{years} years, {months} months ({age_months} months)"
                elif years > 0:
                    plan['child_age'] = f"{years} years ({age_months} months)"
                else:
                    plan['child_age'] = f"{months} months"
            else:
                plan['child_age'] = "Unknown"
            # Filter by parent
            if selected_parent == "all" or (child_data and child_data.get('parent_id') == selected_parent):
                filtered_plans.append(plan)
    # Sort by date (newest first)
    filtered_plans.sort(key=lambda x: x['created_at'], reverse=True)
    if not filtered_plans:
        st.info("No meal plans found for the selected criteria.")
        return
    # Display meal plans for note-taking
    for plan in filtered_plans:
        plan_date = datetime.strptime(plan['created_at'], "%Y-%m-%d %H:%M:%S").strftime("%B %d, %Y")
        with st.container():
            st.subheader(f"📋 {plan['child_name']} ({plan['child_age']}) - {plan_date}")
            col1, col2 = st.columns([2, 1])
            with col1:
                # Show meal plan
                with st.expander("📖 View Full Meal Plan"):
                    st.markdown(plan['plan_details'])
                # Add new note
                st.write("**Add Nutritionist Note:**")
                note_categories = ["General Feedback", "Nutrition Concern", "Recommendation", "Follow-up Required"]
                note_category = st.selectbox("Note Category:", note_categories, key=f"cat_{plan['plan_id']}")
                note_text = st.text_area(
                    "Your professional note:",
                    placeholder="Add your professional assessment, recommendations, or concerns...",
                    height=100,
                    key=f"detailed_note_{plan['plan_id']}"
                )
                if st.button(f"💾 Save Professional Note", key=f"save_detailed_{plan['plan_id']}"):
                    if note_text:
                        full_note = f"[{note_category}] {note_text}"
                        data_manager.save_nutritionist_note(
                            meal_plan_id=plan['plan_id'],
                            nutritionist_id=st.session_state.nutritionist_id,
                            note=full_note
                        )
                        st.success("Professional note saved successfully!")
                        st.rerun()
                    else:
                        st.error("Please enter a note before saving.")
            with col2:
                # Show child summary and existing notes
                child_data = data_manager.get_child_by_id(plan['patient_id'])
                if child_data:
                    st.write("**Child Summary:**")
                    age_months = child_data.get('age_in_months')
                    if age_months is not None:
                        years = age_months // 12
                        months = age_months % 12
                        if years > 0 and months > 0:
                            age_str = f"{years} years, {months} months ({age_months} months)"
                        elif years > 0:
                            age_str = f"{years} years ({age_months} months)"
                        else:
                            age_str = f"{months} months"
                    else:
                        age_str = "Unknown"
                    st.write(f"Age: {age_str}")
                    st.write(f"BMI: {child_data.get('bmi', '')} ({child_data.get('bmi_category', '')})")
                    st.write(f"Allergies: {child_data.get('allergies', '')}")
                    st.write(f"Conditions: {child_data.get('medical_conditions', '')}")
                # Show existing notes
                existing_notes = data_manager.get_notes_for_meal_plan(plan['plan_id'])
                if existing_notes:
                    st.write("**Previous Notes:**")
                    for note in existing_notes:
                        note_date = datetime.strptime(note['created_at'], "%Y-%m-%d %H:%M:%S").strftime("%b %d")
                        st.info(f"**{note_date}:** {note['note']}")
            st.markdown("---")

def show_knowledge_base():
    """Manage Filipino nutrition knowledge base"""
    st.header("🧠 Filipino Nutrition Knowledge Base")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📚 Current Knowledge Base")
        knowledge_base = data_manager.get_knowledge_base()
        filipino_foods = knowledge_base.get('filipino_foods', {})
        if filipino_foods:
            st.write(f"**Filipino Foods Database: {len(filipino_foods)} recipes**")
            for food_id, food_data in list(filipino_foods.items())[:3]:
                with st.expander(f"🍽️ {food_data['name']}"):
                    st.write(f"**Ingredients:** {food_data['ingredients']}")
                    st.write(f"**Nutrition Facts:** {food_data['nutrition_facts']}")
                    st.write(f"**Instructions:** {food_data['instructions']}")

        # Show uploaded PDFs with delete option
        uploaded_pdfs = knowledge_base.get('uploaded_pdfs', [])
        # Use a session state variable to track which PDF is pending deletion
        if 'pending_delete_pdf_idx' not in st.session_state:
            st.session_state['pending_delete_pdf_idx'] = None
        st.write(f"**Uploaded PDFs: {len(uploaded_pdfs)} documents**")
        for idx, pdf in enumerate(uploaded_pdfs):
            pdf_name = pdf.get('name', 'Unknown document')
            col_pdf, col_del = st.columns([8,1])
            with col_pdf:
                st.write(f"- {pdf_name}")
            with col_del:
                delete_btn = st.button("🗑️", key=f"delete_pdf_{idx}", help=f"Delete {pdf_name}")
            # If delete button is clicked, set pending_delete_pdf_idx
            if delete_btn:
                st.session_state['pending_delete_pdf_idx'] = idx
                st.session_state['pending_delete_pdf_name'] = pdf_name
                st.session_state['pending_delete_pdf_uploaded_at'] = pdf.get('uploaded_at')
                st.rerun()
            # Show confirmation dialog only for the selected PDF
            if st.session_state.get('pending_delete_pdf_idx') == idx:
                confirm = st.warning(f"Are you sure you want to delete '{pdf_name}'? This will remove it from the knowledge base.", icon="⚠️")
                confirm_col1, confirm_col2 = st.columns([1,1])
                with confirm_col1:
                    confirm_yes = st.button("Yes, delete", key=f"confirm_delete_{idx}")
                with confirm_col2:
                    confirm_no = st.button("Cancel", key=f"cancel_delete_{idx}")
                if confirm_yes:
                    # Remove from uploaded_pdfs
                    knowledge_base = data_manager.get_knowledge_base()  # reload in case of changes
                    # Remove from uploaded_pdfs by name and uploaded_at
                    uploaded_pdfs_new = [p for p in knowledge_base.get('uploaded_pdfs', []) if not (p.get('name') == pdf_name and p.get('uploaded_at') == pdf.get('uploaded_at'))]
                    knowledge_base['uploaded_pdfs'] = uploaded_pdfs_new
                    # Remove from pdf_memories by name and uploaded_at if present
                    if 'pdf_memories' in knowledge_base:
                        pdf_memories_new = [m for m in knowledge_base['pdf_memories'] if not (m.get('name') == pdf_name and m.get('uploaded_at', None) == pdf.get('uploaded_at', None))]
                        knowledge_base['pdf_memories'] = pdf_memories_new
                    data_manager.save_knowledge_base(knowledge_base)
                    # Clear pending delete state
                    st.session_state['pending_delete_pdf_idx'] = None
                    st.session_state['pending_delete_pdf_name'] = None
                    st.session_state['pending_delete_pdf_uploaded_at'] = None
                    st.success(f"Deleted '{pdf_name}' from knowledge base.")
                    st.rerun()
                elif confirm_no:
                    st.session_state['pending_delete_pdf_idx'] = None
                    st.session_state['pending_delete_pdf_name'] = None
                    st.session_state['pending_delete_pdf_uploaded_at'] = None
                    st.rerun()
    
    with col2:
        # PDF upload and processing with submit button and duplicate prevention
        import pdfplumber
        from io import BytesIO
        import math
        st.write("**Upload PDF Knowledge:**")
        if 'pending_pdf_file' not in st.session_state:
            st.session_state['pending_pdf_file'] = None
        uploaded_file = st.file_uploader("Choose PDF file", type="pdf", key="pdf_upload")
        if uploaded_file is not None:
            st.session_state['pending_pdf_file'] = uploaded_file
        if st.session_state['pending_pdf_file'] is not None:
            st.info(f"Ready to upload: {st.session_state['pending_pdf_file'].name}")
            if st.button("Submit PDF to Knowledge Base", key="submit_pdf_knowledge"):
                try:
                    # Check for duplicate by name in knowledge_base
                    knowledge_base = data_manager.get_knowledge_base()
                    existing_names = set()
                    if 'pdf_memories' in knowledge_base:
                        existing_names.update(entry.get('name') for entry in knowledge_base['pdf_memories'] if 'name' in entry)
                    if 'uploaded_pdfs' in knowledge_base:
                        existing_names.update(pdf.get('name') for pdf in knowledge_base['uploaded_pdfs'] if 'name' in pdf)
                    if st.session_state['pending_pdf_file'].name in existing_names:
                        st.warning(f"PDF '{st.session_state['pending_pdf_file'].name}' is already in the knowledge base.")
                        st.session_state['pending_pdf_file'] = None
                    else:
                        with pdfplumber.open(BytesIO(st.session_state['pending_pdf_file'].read())) as pdf:
                            all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                        chunk_size = 1000
                        chunks = [all_text[i:i+chunk_size] for i in range(0, len(all_text), chunk_size)]
                        if 'pdf_memories' not in knowledge_base:
                            knowledge_base['pdf_memories'] = []
                        pdf_entry = {
                            'name': st.session_state['pending_pdf_file'].name,
                            'chunks': chunks,
                            'uploaded_at': datetime.now().isoformat(),
                            'source': 'pdf_upload',
                        }
                        knowledge_base['pdf_memories'].append(pdf_entry)
                        if 'uploaded_pdfs' not in knowledge_base:
                            knowledge_base['uploaded_pdfs'] = []
                        knowledge_base['uploaded_pdfs'].append({'name': st.session_state['pending_pdf_file'].name, 'uploaded_at': datetime.now().isoformat()})
                        data_manager.save_knowledge_base(knowledge_base)
                        st.success(f"PDF '{st.session_state['pending_pdf_file'].name}' processed and added to knowledge base!")
                        st.session_state['pending_pdf_file'] = None
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to process PDF: {e}")

def show_recipe_database():
    st.header("Food Database")
    # Load food data from MySQL via data_manager
    foods = data_manager.get_foods_data()  # Should return a list of dicts, one per food
    if not foods:
        st.info("No food data available.")
        return

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
                if val and query in str(val).lower():
                    filtered.append(item)
                    break
        return filtered

    filtered_foods = filter_foods(foods, search_val)
    # Pagination setup
    records_per_page = 10
    total_records = len(filtered_foods)
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

    # Notification when a food is selected (styled banner like admin UI)
    if st.session_state.get('show_nutrition_notice'):
        food_idx = st.session_state.get('show_nutrition_section', None)
        food_data_list = filtered_foods if food_idx else []
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
    for idx, item in enumerate(filtered_foods[start_idx:end_idx], start=start_idx+1):
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

    # Render table (no edit button)
    for row_idx, row in enumerate(table_rows):
        col_widths = [1,2,4,3,3,2,2]
        cols = st.columns(col_widths)
        cols[0].markdown(f"{row['No.']}")
        for i, col in enumerate(columns[1:-1], start=1):
            cols[i].markdown(row[col])
        # Options: Only Data button, no Edit
        btn_cols = cols[len(columns)-1].columns([1])
        data_btn = btn_cols[0].button("Data", key=f"data_{row['No.']}" )
        if data_btn:
            st.session_state['show_nutrition_section'] = row['No.']
            st.session_state['scroll_to_nutrition'] = True
            st.session_state['show_nutrition_notice'] = True
            st.rerun()

    # Nutrition data section with tabbed info
    if st.session_state.get('show_nutrition_section'):
        # Show nutrition section
        if st.session_state.get('scroll_to_nutrition'):
            st.session_state['scroll_to_nutrition'] = False
        i = st.session_state['show_nutrition_section']-1
        food = filtered_foods[i]
        section_title = food.get('food_name_and_description', '')
        st.markdown(f"<div class='nutrition-section-container'><h2 id='nutrition_data'>{section_title}</h2>", unsafe_allow_html=True)
        # Nutrition data
        tab_keys = [
            ("proximates", "Proximates"),
            ("other_carbohydrates", "Other Carbohydrate"),
            ("minerals", "Minerals"),
            ("vitamins", "Vitamins"),
            ("lipids", "Lipids")
        ]
        # Get nutrition data for this food from data_manager
        nutrition = data_manager.get_food_nutrition(food['food_id'])
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
    

if __name__ == "__main__":
    main()