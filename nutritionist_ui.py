import streamlit as st
import os
import json
import pandas as pd
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

def load_nutritionist_options():
    """Load nutritionist options from database"""
    try:
        nutritionists = data_manager.get_nutritionists()
        options = {}
        for nutritionist in nutritionists:
            nutritionist_id = str(nutritionist['user_id'])
            full_name = f"{nutritionist.get('first_name', '')} {nutritionist.get('last_name', '')}".strip()
            options[nutritionist_id] = full_name
        return options
    except Exception as e:
        st.error(f"Error loading nutritionists: {e}")
        # Fallback to empty dict
        return {}

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
        # Load nutritionist options from database
        nutritionist_options = load_nutritionist_options()
        st.session_state.nutritionist_options = nutritionist_options
        if nutritionist_options:
            st.session_state.nutritionist_id = list(nutritionist_options.keys())[0]
        else:
            st.session_state.nutritionist_id = None

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
        nutritionist_options = st.session_state.get('nutritionist_options', {})
        if not nutritionist_options:
            st.error("No nutritionists found in database")
            return
        
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
    tab1, tab2, tab3, tab4 = st.tabs(["👨‍👩‍👧‍👦 All Parents", "📝 Add Notes", "🧠 Knowledge Base", "🍽️ Meal Database"])

    with tab1:
        show_all_parents()
    
    with tab2:
        show_add_notes()
    
    with tab3:
        show_knowledge_base()
    
    with tab4:
        show_meal_database()

def show_all_parents():
    """Display all parents and their children's meal plans"""
    st.header("👨‍👩‍👧‍👦 All Parents Overview")
    all_children = data_manager.get_children_data()
    parents_data = data_manager.get_parents_data()
    # Barangay dropdown and search bar
    barangay_list = ["All"]
    try:
        barangays = data_manager.get_all_barangays()
        barangay_list.extend(sorted(barangays.values()))
    except Exception:
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
        parent_name = data_manager.format_full_name(
            parent_info.get('first_name', ''),
            parent_info.get('middle_name', ''),
            parent_info.get('last_name', '')
        )
        # Get barangay name for first child (assuming all children in same family have same barangay)
        barangay = "-"
        if children:
            barangay_id = children[0].get('barangay_id')
            if barangay_id:
                barangay = data_manager.get_barangay_name(barangay_id)
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
                age_months = child.get('age_months')
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
                child_name = data_manager.format_full_name(
                    child.get('first_name', ''),
                    child.get('middle_name', ''),
                    child.get('last_name', '')
                )
                ccols[1].markdown(child_name)
                ccols[2].markdown(age_str)
                
                # Calculate BMI from weight and height
                weight_kg = child.get('weight_kg')
                height_cm = child.get('height_cm')
                bmi_str = "-"
                if weight_kg and height_cm:
                    try:
                        height_m = height_cm / 100
                        bmi = weight_kg / (height_m ** 2)
                        bmi_for_age = child.get('bmi_for_age', 'Unknown')
                        bmi_str = f"{bmi:.1f} ({bmi_for_age})"
                    except:
                        bmi_str = "-"
                ccols[3].markdown(bmi_str)
                ccols[4].markdown(child.get('allergies', '-'))
                ccols[5].markdown(child.get('other_medical_problems', '-'))

def show_add_notes():
    """Dedicated section for adding detailed notes to meal plans"""
    st.header("📝 Add Notes to Meal Plans")
    parents_data = data_manager.get_parents_data()

    # --- FILTERS ---
    filter_cols = st.columns([2,2,2,2])
    with filter_cols[0]:
        search_val = st.text_input("🔍 Search by child, parent, or plan ID", value=st.session_state.get("add_notes_search", ""), key="add_notes_search")
    barangay_list = ["All"]
    try:
        conn = data_manager.data_manager.conn
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT barangay_name FROM barangays ORDER BY barangay_name")
        barangay_rows = cursor.fetchall()
        barangay_list.extend([row['barangay_name'] for row in barangay_rows])
    except Exception:
        barangay_list = ["All", "Bagong Silang", "Calendola", "Chrysanthemum", "Cuyab", "Estrella", "Fatima", "G.S.I.S", "Landayan", "Langgam", "Laram", "Magsaysay", "Maharlika", "Narra", "Nueva", "Pacita 1", "Pacita 2", "Poblacion", "Riverside", "Rosario", "Sampaguita Village", "San Antonio", "San Lorenzo Ruiz", "San Roque", "San Vicente", "Santo Niño", "United Bayanihan", "United Better Living"]
    with filter_cols[1]:
        barangay_selected = st.selectbox("🏘️ Filter by Barangay", barangay_list, key="add_notes_barangay")
    with filter_cols[2]:
        notes_filter = st.selectbox("🗒️ Filter by Notes", ["All", "Has Notes", "No Notes"], key="add_notes_notes_filter")
    with filter_cols[3]:
        sort_recent = st.checkbox("Sort by Most Recent", value=True, key="add_notes_sort_recent")

    # --- GET AND PREPARE MEAL PLANS ---
    all_plans = data_manager.get_meal_plans()
    table_rows = []
    for plan in all_plans.values():
        child_data = data_manager.get_patient_by_id(plan['patient_id'])
        child_name = data_manager.format_full_name(
            child_data.get('first_name', ''),
            child_data.get('middle_name', ''),
            child_data.get('last_name', '')
        ) if child_data else "Unknown"
        age_months = child_data['age_months'] if child_data and 'age_months' in child_data else None
        child_age = f"{age_months//12}y {age_months%12}m" if age_months is not None else "-"
        parent_id = child_data.get('parent_id') if child_data else None
        notes = data_manager.get_notes_for_meal_plan(plan.get('plan_id', ''))
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
            nutritionist_options = st.session_state.nutritionist_options if 'nutritionist_options' in st.session_state else load_nutritionist_options()
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
                parent_full_name = data_manager.format_full_name(
                    parent_info.get('first_name', ''),
                    parent_info.get('middle_name', ''),
                    parent_info.get('last_name', '')
                )
                # Get barangay name
                barangay_id = child_data.get('barangay_id') if child_data else None
                if barangay_id:
                    barangay_val = data_manager.get_barangay_name(barangay_id)
                else:
                    barangay_val = "-"
                religion_val = "-"  # Religion not available in new schema
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
    import pandas as pd
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
                    expand_key = f"plan_details_expanded_{plan_id}"
                    if expand_key not in st.session_state:
                        st.session_state[expand_key] = False
                    is_expanded = st.session_state[expand_key]
                    preview_len = 0  # Show only first 100 characters when minimized
                    if not is_expanded and isinstance(val, str) and len(val) > preview_len:
                        preview = val[:preview_len]
                        btn_label = "Show Plan Details"
                        val_cols[i].markdown(preview, unsafe_allow_html=True)
                        if val_cols[i].button(btn_label, key=f"expand_{plan_id}"):
                            st.session_state[expand_key] = True
                            st.rerun()
                    else:
                        btn_label = "Minimize"
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
                save_col, cancel_col = val_cols[-1].columns([1,1])
                if save_col.button("Save Note", key=f"save_note_{plan_id}"):
                    data_manager.save_nutritionist_note(plan_id, st.session_state.nutritionist_id, new_note)
                    st.success("Note added!")
                    st.session_state[show_input_key] = False
                    st.rerun()
                if cancel_col.button("Cancel", key=f"cancel_note_{plan_id}"):
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
        # Get PDFs uploaded by this nutritionist
        knowledge_base_raw = data_manager.get_knowledge_base()
        nutritionist_pdfs = []
        
        # Only include rows uploaded by this nutritionist
        if isinstance(knowledge_base_raw, dict):
            for kb in knowledge_base_raw.values():
                if kb.get('uploaded_by') == 'nutritionist' and str(kb.get('uploaded_by_id')) == str(st.session_state.nutritionist_id):
                    pdf_name = kb.get('pdf_name', '')
                    ai_summary = kb.get('ai_summary', '')
                    added_at = kb.get('added_at', '')
                    
                    if pdf_name:  # Only add if there's a PDF name
                        nutritionist_pdfs.append({
                            'name': pdf_name,
                            'ai_summary': ai_summary,
                            'added_at': added_at,
                            'kb_id': kb.get('kb_id')
                        })
        # Optionally, aggregate filipino_foods if needed (currently only showing from latest)
        filipino_foods = {}
        if isinstance(knowledge_base_raw, dict) and knowledge_base_raw:
            latest_kb = max(knowledge_base_raw.values(), key=lambda x: x.get('kb_id', 0))
            # filipino_foods is no longer stored in knowledge_base, so skip this for now
            filipino_foods = {}
            
        if filipino_foods:
            st.write(f"**Filipino Foods Database: {len(filipino_foods)} recipes**")
            for food_id, food_data in list(filipino_foods.items())[:3]:
                with st.expander(f"🍽️ {food_data['name']}"):
                    st.write(f"**Ingredients:** {food_data['ingredients']}")
                    st.write(f"**Nutrition Facts:** {food_data['nutrition_facts']}")
                    st.write(f"**Instructions:** {food_data['instructions']}" )

        # Show uploaded PDFs
        if 'pending_delete_pdf_idx' not in st.session_state:
            st.session_state['pending_delete_pdf_idx'] = None
        st.write(f"**Uploaded PDFs: {len(nutritionist_pdfs)} documents**")
        
        # Show total text information if available
        total_text_chars = 0
        for kb in knowledge_base_raw.values():
            if (kb.get('uploaded_by') == 'nutritionist' and 
                str(kb.get('uploaded_by_id')) == str(st.session_state.nutritionist_id)):
                pdf_text = kb.get('pdf_text', '')
                if pdf_text:
                    total_text_chars += len(pdf_text)
        
        if total_text_chars > 0:
            text_kb = total_text_chars / 1024  # Convert to KB
            if text_kb > 1024:
                text_size = f"{text_kb/1024:.1f} MB"
            else:
                text_size = f"{text_kb:.1f} KB"
            st.caption(f"📊 Total text content: {text_size}")
        
        for idx, pdf_data in enumerate(nutritionist_pdfs):
            pdf_name = pdf_data['name']
            ai_summary = pdf_data['ai_summary']
            added_at = pdf_data['added_at']
            
            col_pdf, col_actions = st.columns([7, 2])
            with col_pdf:
                st.write(f"📄 **{pdf_name}**")
                if added_at:
                    try:
                        if isinstance(added_at, str):
                            dt = datetime.strptime(added_at, '%Y-%m-%d %H:%M:%S')
                        else:
                            dt = added_at
                        st.caption(f"Uploaded: {dt.strftime('%b %d, %Y')}")
                    except:
                        st.caption(f"Uploaded: {added_at}")
            
            with col_actions:
                # Only show delete button
                delete_btn = st.button("🗑️", key=f"delete_pdf_{idx}", help=f"Delete {pdf_name}")

            # Create two columns for aligned expanders
            exp_col1, exp_col2 = st.columns(2)
            
            # Show AI insights in first column (if available)
            with exp_col1:
                if ai_summary:
                    with st.expander("🧠 View Insights"):
                        st.text_area("", value=ai_summary, height=200, key=f"insights_expanded_{idx}")
                else:
                    st.info("No AI insights available")

            # Show PDF text in second column
            with exp_col2:
                pdf_text_content = None
                for kb in knowledge_base_raw.values():
                    if (kb.get('uploaded_by') == 'nutritionist' and 
                        str(kb.get('uploaded_by_id')) == str(st.session_state.nutritionist_id) and
                        kb.get('pdf_name') == pdf_name):
                        pdf_text_content = kb.get('pdf_text', '')
                        break
                
                if pdf_text_content:
                    with st.expander(f"📄 Full Text: {pdf_name}"):
                        st.text_area(
                            "PDF Content:",
                            value=pdf_text_content,
                            height=400,
                            key=f"pdf_text_display_{idx}",
                            help="Full extracted text from the PDF"
                        )
                else:
                    st.warning("PDF text not found in database.")

            if delete_btn:
                st.session_state['pending_delete_pdf_idx'] = idx
                st.session_state['pending_delete_pdf_name'] = pdf_name
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
                    # Find and delete the knowledge base entry
                    kb_to_delete = None
                    for kb in knowledge_base_raw.values():
                        if (kb.get('uploaded_by') == 'nutritionist' and 
                            str(kb.get('uploaded_by_id')) == str(st.session_state.nutritionist_id) and
                            kb.get('pdf_name') == pdf_name):
                            kb_to_delete = kb
                            break
                    
                    if kb_to_delete:
                        # Delete the entire knowledge base entry
                        data_manager.delete_knowledge_base_entry(kb_to_delete['kb_id'])
                        
                        st.session_state['pending_delete_pdf_idx'] = None
                        st.session_state['pending_delete_pdf_name'] = None
                        st.success(f"Deleted '{pdf_name}' from knowledge base.")
                        st.rerun()
                elif confirm_no:
                    st.session_state['pending_delete_pdf_idx'] = None
                    st.session_state['pending_delete_pdf_name'] = None
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
                    with st.spinner("Processing PDF with AI..."):
                        knowledge_base = data_manager.get_knowledge_base()
                        existing_names = set()
                        # Check all knowledge base entries for existing PDF names
                        for kb in knowledge_base.values():
                            existing_pdf_name = kb.get('pdf_name', '')
                            if existing_pdf_name:
                                existing_names.add(existing_pdf_name)
                        
                        if st.session_state['pending_pdf_file'].name in existing_names:
                            st.warning(f"PDF '{st.session_state['pending_pdf_file'].name}' is already in the knowledge base.")
                            st.session_state['pending_pdf_file'] = None
                        else:
                            # Extract text from PDF
                            with pdfplumber.open(BytesIO(st.session_state['pending_pdf_file'].read())) as pdf:
                                all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                            
                            # Use AI to summarize nutrition-relevant content
                            if st.session_state.nutrition_ai:
                                st.info("🤖 Analyzing PDF content with AI for nutrition insights...")
                                nutrition_insights = st.session_state.nutrition_ai.summarize_pdf_for_nutrition_knowledge(
                                    all_text, 
                                    st.session_state['pending_pdf_file'].name
                                )
                                
                                if not nutrition_insights:
                                    st.warning("⚠️ No relevant nutrition content found for 0-5 year old children in this PDF.")
                                    st.session_state['pending_pdf_file'] = None
                                    return
                                
                                # Save to knowledge base with simplified structure
                                data_manager.save_knowledge_base(
                                    nutrition_insights,  # Pass insights list directly
                                    st.session_state['pending_pdf_file'].name,  # Pass filename directly
                                    pdf_text=all_text,
                                    uploaded_by='nutritionist',
                                    uploaded_by_id=st.session_state.nutritionist_id
                                )
                                
                                st.success(f"✅ PDF '{st.session_state['pending_pdf_file'].name}' processed successfully!")
                                st.info(f"🧠 Extracted {len(nutrition_insights)} nutrition insights for 0-5 year old children")
                                
                                # Show preview of insights
                                with st.expander("Preview of Extracted Insights", expanded=True):
                                    for insight in nutrition_insights[:5]:  # Show first 5
                                        st.write(insight)
                                    if len(nutrition_insights) > 5:
                                        st.write(f"... and {len(nutrition_insights) - 5} more insights")
                                
                                st.session_state['pending_pdf_file'] = None
                                st.rerun()
                            else:
                                st.error("AI system not available. Cannot process PDF.")
                except Exception as e:
                    st.error(f"Failed to process PDF: {e}")
                    import traceback
                    st.error(f"Details: {traceback.format_exc()}")

def show_meal_database():
    st.header("Meal Database")

    meals = data_manager.get_meals_data()
    if not meals:
        st.info("No meal data available.")
        return

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
                if val and query in str(val).lower():
                    filtered.append(item)
                    break
        return filtered

    filtered_meals = filter_meals(meals, search_val)
    # Pagination setup
    records_per_page = 10
    total_records = len(filtered_meals)
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

    if st.session_state.get('show_meal_notice'):
        meal_idx = st.session_state.get('show_meal_section', None)
        meal_data_list = filtered_meals if meal_idx else []
        meal_name = ""
        if meal_idx and 0 < meal_idx <= len(meal_data_list):
            meal = meal_data_list[meal_idx-1]
            meal_name = meal.get('meal_name', '')
        st.markdown(f"""
            <div style='background:#2196F3;color:white;padding:0.75rem 1.5rem;border-radius:8px;font-weight:bold;margin-bottom:0.5rem;font-size:1.1rem;'>
                The meal details are shown below.<br>
                <span style='font-size:1rem;font-weight:normal;'>You are now viewing details for: <b>{meal_name}</b></span>
            </div>
        """, unsafe_allow_html=True)
        st.session_state['show_meal_notice'] = False

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
    for idx, item in enumerate(filtered_meals[start_idx:end_idx], start=start_idx+1):
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

        btn_cols = cols[len(columns)-1].columns([1])
        data_btn = btn_cols[0].button("Details", key=f"data_{row['No.']}" )
        if data_btn:
            st.session_state['show_meal_section'] = row['No.']
            st.session_state['scroll_to_meal'] = True
            st.session_state['show_meal_notice'] = True
            st.rerun()

    # Meal details section
    if st.session_state.get('show_meal_section'):
        # Show meal section
        if st.session_state.get('scroll_to_meal'):
            st.session_state['scroll_to_meal'] = False
        i = st.session_state['show_meal_section']-1
        meal = filtered_meals[i]
        section_title = meal.get('meal_name', '')
        st.markdown(f"<div class='meal-section-container'><h2 id='meal_data'>{section_title}</h2>", unsafe_allow_html=True)
        
        # Meal Information
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Basic Information:**")
            st.markdown(f"- **Description:** {meal.get('description', 'N/A')}")
            st.markdown(f"- **Course:** {meal.get('course', 'N/A')}")
            st.markdown(f"- **Keywords:** {meal.get('keywords', 'N/A')}")
            st.markdown(f"- **Prep Time:** {meal.get('prep_time_minutes', 0)} minutes")
            st.markdown(f"- **Cook Time:** {meal.get('cook_time_minutes', 0)} minutes")
            st.markdown(f"- **Servings:** {meal.get('servings', 'N/A')}")
        
        with col2:
            st.markdown("**Nutrition Information (per serving):**")
            st.markdown(f"- **Calories:** {meal.get('calories_kcal', 'N/A')} kcal")
            st.markdown(f"- **Protein:** {meal.get('protein_g', 'N/A')} g")
            st.markdown(f"- **Carbohydrates:** {meal.get('carbohydrates_g', 'N/A')} g")
            st.markdown(f"- **Fat:** {meal.get('fat_g', 'N/A')} g")
            st.markdown(f"- **Fiber:** {meal.get('fiber_g', 'N/A')} g")
            st.markdown(f"- **Sodium:** {meal.get('sodium_mg', 'N/A')} mg")
            st.markdown(f"- **Calcium:** {meal.get('calcium_mg', 'N/A')} mg")
            st.markdown(f"- **Iron:** {meal.get('iron_mg', 'N/A')} mg")
        
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
        
        st.markdown("</div>", unsafe_allow_html=True)
    

if __name__ == "__main__":
    main()