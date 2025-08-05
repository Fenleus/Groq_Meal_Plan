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
        # Nutritionist dropdown options (static for now)
        nutritionist_options = {
            '1': 'Anna Cruz',
            '2': 'Juan dela Paz'
        }
        st.session_state.nutritionist_options = nutritionist_options
        st.session_state.nutritionist_id = list(nutritionist_options.keys())[0]

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
    # Sidebar for nutritionist info
    with st.sidebar:
        st.header("👩‍⚕️ Nutritionist Login")
        nutritionist_options = st.session_state.get('nutritionist_options', {
            '1': 'Anna Cruz',
            '2': 'Juan dela Paz'
        })
        selected_nutritionist = st.selectbox(
            "Select Nutritionist Account",
            options=list(nutritionist_options.keys()),
            format_func=lambda x: nutritionist_options[x],
            index=0
        )
        st.session_state.nutritionist_id = selected_nutritionist
        st.info(f"Logged in as: {nutritionist_options[selected_nutritionist]}")
        st.write(f"ID: {selected_nutritionist}")
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
    # Barangay dropdown and search bar
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

    if 'expanded_parent' not in st.session_state:
        st.session_state['expanded_parent'] = None

    header_cols = st.columns([1, 4, 3, 2])
    header_labels = ["No.", "Parent", "Barangay", "# Children"]
    for i, label in enumerate(header_labels):
        header_cols[i].markdown(f"**{label}**")

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
    # ...existing code...
    parents_data = data_manager.get_parents_data()

    # Get all meal plans and show notes for all
    all_plans = data_manager.get_meal_plans()
    table_rows = []
    for plan in all_plans.values():
        child_data = data_manager.get_patient_by_id(plan['patient_id'])
        child_name = f"{child_data['first_name']} {child_data['last_name']}" if child_data else "Unknown"
        age_months = child_data['age_in_months'] if child_data and 'age_in_months' in child_data else None
        child_age = f"{age_months//12}y {age_months%12}m" if age_months is not None else "-"
        parent_id = child_data.get('parent_id') if child_data else None
        notes = data_manager.get_notes_for_meal_plan(plan.get('plan_id', ''))
        def format_created_at(val):
            if isinstance(val, str):
                try:
                    dt = datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
                except Exception:
                    return val
            elif isinstance(val, datetime):
                dt = val
            else:
                return str(val)
            return dt.strftime('%b %d')
        import json
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
            nutritionist_options = st.session_state.nutritionist_options if 'nutritionist_options' in st.session_state else {
                '1': 'Anna Cruz',
                '2': 'Juan dela Paz'
            }
            def get_nutritionist_name(nutritionist_id):
                return nutritionist_options.get(str(nutritionist_id), f"Nutritionist {nutritionist_id}")
            notes_str = "<br>".join([
                f"Noted by {get_nutritionist_name(note.get('nutritionist_id'))}: {clean_note(note['note'])}"
                for note in notes
            ])
        else:
            notes_str = "No notes yet"
        parent_full_name = "Unknown"
        barangay_val = "-"
        religion_val = "-"
        if parent_id is not None:
            parent_info = parents_data.get(str(parent_id))
            if parent_info:
                parent_full_name = parent_info.get('full_name', f"Parent {parent_id}")
                barangay_val = parent_info.get('barangay', '-')
                religion_val = parent_info.get('religion', '-')
            else:
                parent_full_name = f"Parent {parent_id}"
        plan_details_clean = clean_note(plan.get('plan_details', ''))
        generated_at_val = plan.get('generated_at', '')
        # Diet Restrictions
        medical_conditions = child_data.get('medical_conditions', '-') if child_data else '-'
        allergies = child_data.get('allergies', '-') if child_data else '-'
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
            "Notes": notes_str
        })

    # Sort by plan (newest first if possible)
    table_rows.sort(key=lambda x: x.get('Plan ID', ''), reverse=True)
    columns = ["Plan ID", "Child Name", "Child Age", "Parent", "Barangay", "Diet Restrictions", "Plan Details", "Generated at", "Notes", "Add note"]
    import pandas as pd
    if table_rows:
        # Render table header
        cols = st.columns(len(columns))
        for i, col in enumerate(columns):
            cols[i].markdown(f"**{col}**")
        # Render table rows
        for row in table_rows:
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
                    expand_key = f"plan_details_expanded_{plan_id}"
                    if expand_key not in st.session_state:
                        st.session_state[expand_key] = False
                    is_expanded = st.session_state[expand_key]
                    preview_len = 0  # Show only first 100 characters when minimized
                    if not is_expanded and isinstance(val, str) and len(val) > preview_len:
                        preview = val[:preview_len]
                        btn_label = "⌄ Show Plan Details"
                        val_cols[i].markdown(preview, unsafe_allow_html=True)
                        if val_cols[i].button(btn_label, key=f"expand_{plan_id}"):
                            st.session_state[expand_key] = True
                            st.rerun()
                    else:
                        btn_label = "^ Minimize"
                        val_cols[i].markdown(val, unsafe_allow_html=True)
                        if isinstance(val, str) and len(val) > preview_len:
                            if val_cols[i].button(btn_label, key=f"minimize_{plan_id}"):
                                st.session_state[expand_key] = False
                                st.rerun()
                elif columns[i] == "Notes":
                    val_cols[i].markdown(val, unsafe_allow_html=True)
                else:
                    val_cols[i].markdown(val)
            # Add note button and input in last column
            add_note_key = f"add_note_{plan_id}"
            show_input_key = f"show_note_input_{plan_id}"
            if not st.session_state.get(show_input_key):
                if val_cols[-1].button("Add Note", key=add_note_key):
                    st.session_state[show_input_key] = True
                    st.rerun()
            else:
                new_note = val_cols[-1].text_area("Enter note:", key=f"note_input_{plan_id}")
                if val_cols[-1].button("Save Note", key=f"save_note_{plan_id}"):
                    data_manager.save_nutritionist_note(plan_id, st.session_state.nutritionist_id, new_note)
                    st.success("Note added!")
                    st.session_state[show_input_key] = False
                    st.rerun()
    else:
        empty_df = pd.DataFrame([], columns=columns)
        st.dataframe(empty_df, use_container_width=True, hide_index=True)

def show_knowledge_base():
    """Manage Filipino nutrition knowledge base"""
    st.header("🧠 Filipino Nutrition Knowledge Base")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📚 Current Knowledge Base")
        # Aggregate all PDFs uploaded by this nutritionist
        knowledge_base_raw = data_manager.get_knowledge_base()
        import json
        def parse_json_field(field):
            if isinstance(field, str):
                try:
                    return json.loads(field)
                except Exception:
                    return []
            return field if field is not None else []
        all_pdf_name = []
        all_pdf_memories = []
        # Only include rows uploaded by this nutritionist
        if isinstance(knowledge_base_raw, dict):
            for kb in knowledge_base_raw.values():
                if kb.get('uploaded_by') == 'nutritionist' and str(kb.get('uploaded_by_id')) == str(st.session_state.nutritionist_id):
                    all_pdf_name.extend(parse_json_field(kb.get('pdf_name', [])))
                    all_pdf_memories.extend(parse_json_field(kb.get('pdf_memories', [])))
        # Optionally, aggregate filipino_foods if needed (currently only showing from latest)
        filipino_foods = {}
        if isinstance(knowledge_base_raw, dict) and knowledge_base_raw:
            latest_kb = max(knowledge_base_raw.values(), key=lambda x: x.get('kb_id', 0))
            filipino_foods = parse_json_field(latest_kb.get('filipino_foods', {}))
        if filipino_foods:
            st.write(f"**Filipino Foods Database: {len(filipino_foods)} recipes**")
            for food_id, food_data in list(filipino_foods.items())[:3]:
                with st.expander(f"🍽️ {food_data['name']}"):
                    st.write(f"**Ingredients:** {food_data['ingredients']}")
                    st.write(f"**Nutrition Facts:** {food_data['nutrition_facts']}")
                    st.write(f"**Instructions:** {food_data['instructions']}" )

        # Show all uploaded PDFs with delete option
        if 'pending_delete_pdf_idx' not in st.session_state:
            st.session_state['pending_delete_pdf_idx'] = None
        st.write(f"**Uploaded PDFs: {len(all_pdf_name)} documents**")
        for idx, pdf in enumerate(all_pdf_name):
            pdf_name = pdf if isinstance(pdf, str) else pdf.get('name', 'Unknown document')
            col_pdf, col_del = st.columns([8,1])
            with col_pdf:
                st.write(f"- {pdf_name}")
            with col_del:
                delete_btn = st.button("🗑️", key=f"delete_pdf_{idx}", help=f"Delete {pdf_name}")

            if delete_btn:
                st.session_state['pending_delete_pdf_idx'] = idx
                st.session_state['pending_delete_pdf_name'] = pdf_name
                # st.session_state['pending_delete_pdf_uploaded_at'] = None  # No longer needed
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
                    # Find and delete from the correct knowledge_base row
                    kb_to_update = None
                    for kb in knowledge_base_raw.values():
                        if kb.get('uploaded_by') == 'nutritionist' and str(kb.get('uploaded_by_id')) == str(st.session_state.nutritionist_id):
                            pdfs = parse_json_field(kb.get('pdf_name', []))
                            for p in pdfs:
                                if (p == pdf_name) or (isinstance(p, dict) and p.get('name') == pdf_name):
                                    kb_to_update = kb
                                    break
                            if kb_to_update:
                                break
                    if kb_to_update:
                        # Remove PDF from this kb row
                        new_pdfs = [p for p in parse_json_field(kb_to_update.get('pdf_name', [])) if not ((p == pdf_name) or (isinstance(p, dict) and p.get('name') == pdf_name))]
                        new_memories = [m for m in parse_json_field(kb_to_update.get('pdf_memories', [])) if not (m.get('name') == pdf_name)]
                        data_manager.save_knowledge_base(
                            new_memories,
                            new_pdfs,
                            uploaded_by='nutritionist',
                            uploaded_by_id=st.session_state.nutritionist_id
                        )
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

        import pdfplumber
        from io import BytesIO
        import math
        st.write("**Upload PDF Knowledge:**")
        if 'pending_pdf_file' not in st.session_state:
            st.session_state['pending_pdf_file'] = None
        uploaded_file = st.file_uploader("Choose PDF file", type="pdf", key="pdf_upload")
        # If the file uploader is cleared (cross clicked), remove pending_pdf_file
        if uploaded_file is None and st.session_state.get('pending_pdf_file') is not None:
            st.session_state['pending_pdf_file'] = None
        if uploaded_file is not None:
            st.session_state['pending_pdf_file'] = uploaded_file
        if st.session_state.get('pending_pdf_file') is not None:
            st.info(f"Ready to upload: {st.session_state['pending_pdf_file'].name}")
            if st.button("Submit PDF to Knowledge Base", key="submit_pdf_knowledge"):
                try:

                    knowledge_base = data_manager.get_knowledge_base()
                    existing_names = set()
                    if 'pdf_memories' in knowledge_base:
                        existing_names.update(entry.get('name') for entry in knowledge_base['pdf_memories'] if 'name' in entry)
                    if 'pdf_name' in knowledge_base:
                        existing_names.update(pdf.get('name') for pdf in knowledge_base['pdf_name'] if 'name' in pdf)
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
                        if 'pdf_name' not in knowledge_base:
                            knowledge_base['pdf_name'] = []
                        knowledge_base['pdf_name'].append(st.session_state['pending_pdf_file'].name)
                        # Determine uploader type and set fields accordingly
                        uploader_type = 'nutritionist'
                        uploader_nutritionist_id = st.session_state.get('nutritionist_id', None)
                        uploader_admin_id = None
                        data_manager.save_knowledge_base(
                            knowledge_base.get('pdf_memories', []),
                            knowledge_base.get('pdf_name', []),
                            uploaded_by=uploader_type,
                            uploaded_by_id=uploader_nutritionist_id
                        )
                        st.success(f"PDF '{st.session_state['pending_pdf_file'].name}' processed and added to knowledge base!")
                        st.session_state['pending_pdf_file'] = None
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to process PDF: {e}")

def show_recipe_database():
    st.header("Food Database")

    foods = data_manager.get_foods_data()
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

    # Render table
    for row_idx, row in enumerate(table_rows):
        col_widths = [1,2,4,3,3,2,2]
        cols = st.columns(col_widths)
        cols[0].markdown(f"{row['No.']}")
        for i, col in enumerate(columns[1:-1], start=1):
            cols[i].markdown(row[col])

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