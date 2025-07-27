import streamlit as st
import os
from nutrition_ai import ChildNutritionAI
from data_manager import data_manager
from datetime import datetime, timedelta
import json
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
    table_rows = []
    for child in all_children.values():
        parent_id = child.get('parent_id')
        parent_name = parents_data.get(parent_id, {}).get('name', f"Parent {parent_id}")
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
        # Get meal plans and notes count (dummy/empty for now, can be filled in if available)
        meal_plans = []
        notes_count = sum(len(data_manager.get_notes_for_meal_plan(plan['id'])) for plan in meal_plans)
        table_rows.append({
            "Parent": parent_name,
            "Child": child.get('name', ''),
            "Age": age_str,
            "BMI": f"{child.get('bmi', '')} ({child.get('bmi_category', '')})",
            "Allergies": child.get('allergies', ''),
            "Conditions": child.get('medical_conditions', ''),
            "Meal Plans": len(meal_plans),
            "Your Notes": notes_count
        })
    if not table_rows:
        st.info("No parents or children found in the system.")
        return
    import pandas as pd
    df = pd.DataFrame(table_rows)
    df.index = df.index + 1
    st.dataframe(df, use_container_width=True)

def show_add_notes():
    """Dedicated section for adding detailed notes to meal plans"""
    st.header("📝 Add Notes to Meal Plans")
    
    # Search/filter options
    col1, col2 = st.columns(2)
    
    with col1:
        # Parent filter
        parent_options = {
            "all": "All Parents",
            "parent_001": "Santos Parent", 
            "parent_002": "Cruz Parent"
        }
        selected_parent = st.selectbox("Filter by Parent", 
                                     options=list(parent_options.keys()),
                                     format_func=lambda x: parent_options[x])
    
    with col2:
        # Date range
        days_back = st.selectbox("Show plans from last:", [7, 14, 30, 60], index=2)
    
    # Get meal plans based on filters
    all_plans = {}
    filtered_plans = []
    
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    for plan in all_plans.values():
        plan_date = datetime.fromisoformat(plan['created_at'])
        if plan_date >= cutoff_date:
            if selected_parent == "all" or plan['parent_id'] == selected_parent:
                # Add child info for display
                child_data = data_manager.get_child_by_id(plan['child_id'])
                plan['child_name'] = child_data['name'] if child_data else "Unknown"
                plan['child_age'] = child_data['age'] if child_data else "Unknown"
                filtered_plans.append(plan)
    
    # Sort by date (newest first)
    filtered_plans.sort(key=lambda x: x['created_at'], reverse=True)
    
    if not filtered_plans:
        st.info("No meal plans found for the selected criteria.")
        return
    
    # Display meal plans for note-taking
    for plan in filtered_plans:
        plan_date = datetime.fromisoformat(plan['created_at']).strftime("%B %d, %Y")
        
        with st.container():
            st.subheader(f"📋 {plan['child_name']} ({plan['child_age']} years) - {plan_date}")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Show meal plan
                with st.expander("📖 View Full Meal Plan"):
                    st.markdown(plan['meal_plan'])
                
                # Add new note
                st.write("**Add Nutritionist Note:**")
                note_categories = ["General Feedback", "Nutrition Concern", "Recommendation", "Follow-up Required"]
                note_category = st.selectbox("Note Category:", note_categories, key=f"cat_{plan['id']}")
                
                note_text = st.text_area(
                    "Your professional note:",
                    placeholder="Add your professional assessment, recommendations, or concerns...",
                    height=100,
                    key=f"detailed_note_{plan['id']}"
                )
                
                if st.button(f"💾 Save Professional Note", key=f"save_detailed_{plan['id']}"):
                    if note_text:
                        full_note = f"[{note_category}] {note_text}"
                        data_manager.save_nutritionist_note(
                            meal_plan_id=plan['id'],
                            nutritionist_id=st.session_state.nutritionist_id,
                            note=full_note
                        )
                        st.success("Professional note saved successfully!")
                        st.rerun()
                    else:
                        st.error("Please enter a note before saving.")
            
            with col2:
                # Show child summary and existing notes
                child_data = data_manager.get_child_by_id(plan['child_id'])
                if child_data:
                    st.write("**Child Summary:**")
                    st.write(f"Age: {child_data['age']} years")
                    st.write(f"BMI: {child_data['bmi']} ({child_data['bmi_category']})")
                    st.write(f"Allergies: {child_data['allergies']}")
                    st.write(f"Conditions: {child_data['medical_conditions']}")
                
                # Show existing notes
                existing_notes = data_manager.get_notes_for_meal_plan(plan['id'])
                if existing_notes:
                    st.write("**Previous Notes:**")
                    for note in existing_notes:
                        note_date = datetime.fromisoformat(note['created_at']).strftime("%b %d")
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
    DATA_PATH = os.path.join("data", "food_info.json")
    def load_food_data():
        if not os.path.exists(DATA_PATH):
            return []
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

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

        # Notification when a food is selected (styled banner like admin UI)
        if st.session_state.get('show_nutrition_notice'):
            food_idx = st.session_state.get('show_nutrition_section', None)
            food_data_list = food_data if food_idx else []
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
            st.session_state['show_nutrition_notice'] = False

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
                            pretty_k = k.replace('_g', ' (g)').replace('_mg', ' (mg)').replace('_µg', ' (µg)').replace('_ug', ' (µg)').replace('_', ' ').capitalize()
                            display_val = v if (v is not None and str(v).strip() != "") else "-"
                            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:0.5rem 0.2rem;border-bottom:1px solid #eee;'><span>{pretty_k}</span><span style='font-weight:bold'>{display_val}</span></div>", unsafe_allow_html=True)
                    else:
                        st.info(f"No {tab_name.lower()} data available.")
            st.markdown("</div>", unsafe_allow_html=True)
    

if __name__ == "__main__":
    main()