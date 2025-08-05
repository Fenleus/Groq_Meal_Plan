
import streamlit as st
from nutrition_ai import ChildNutritionAI
from data_manager import data_manager
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="👨‍👩‍👧‍👦 Parent Dashboard",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .child-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #FF6B6B;
        margin: 1rem 0;
    }
    .stButton > button {
        background-color: #FF6B6B;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #FF5252;
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
    
    if 'parent_id' not in st.session_state:
        st.session_state.parent_id = "parent_001"

def main():
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>👨‍👩‍👧‍👦 Parent Dashboard</h1>
        <p>Manage your children's nutrition and meal plans</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check API status
    if not st.session_state.api_working:
        st.error(f"❌ API Error: {st.session_state.get('api_error', 'Unknown error')}")
        st.info("Make sure your GROQ_API_KEY is set in the .env file")
        return
        
    # Sidebar for parent selection
    with st.sidebar:
        st.header("👤 Parent Login")

        parents_data = data_manager.get_parents_data()

        parent_options = {str(pdata.get('parent_id', pid)): pdata.get('full_name', str(pdata.get('parent_id', pid))) for pid, pdata in parents_data.items()}
        selected_parent = st.selectbox(
            "Select Parent Account",
            options=list(parent_options.keys()),
            format_func=lambda x: parent_options[x],
            index=0
        )
        st.session_state.parent_id = selected_parent
        st.info(f"Logged in as: {parent_options[selected_parent]}")


    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["👶 My Children", "🍽️ Generate Meal Plan", "📝 Generated Meal Plans"])

    with tab1:
        show_children_overview()

    with tab2:
        show_meal_plan_generator()

    with tab3:
        show_generated_meal_plans()
def show_generated_meal_plans():
    """Show all generated meal plans and nutritionist notes for this parent's children"""
    st.header("📝 Generated Meal Plans & Nutritionist Notes")
    children = data_manager.get_children_by_parent(st.session_state.parent_id)
    if not children:
        st.info("No children found for this parent account.")
        return
    # Dropdown filter for children
    child_options = {child['patient_id']: f"{child['first_name']} {child['last_name']}" for child in children}
    selected_child_id = st.selectbox("Filter by Child", options=[None] + list(child_options.keys()), format_func=lambda x: child_options[x] if x else "All Children", index=0)
    # Get all plan_ids for these children
    child_ids = [child['patient_id'] for child in children]
    all_plans = data_manager.get_meal_plans()
    # Only show plans for this parent's children
    plans = [plan for plan in all_plans.values() if plan['patient_id'] in child_ids]
    if selected_child_id:
        plans = [plan for plan in plans if plan['patient_id'] == selected_child_id]
    # Get all nutritionist notes for these plans
    notes_by_plan = {}
    for plan in plans:
        plan_id = plan.get('plan_id')
        notes = data_manager.get_notes_for_meal_plan(plan_id)
        notes_by_plan[plan_id] = notes
    # Get nutritionist names
    nutritionists = data_manager.get_nutritionists()
    nutritionist_map = {str(n['nutritionist_id']): n.get('full_name', f"Nutritionist {n['nutritionist_id']}") for n in nutritionists}
    # Table rows
    table_rows = []
    for plan in plans:
        child = next((c for c in children if c['patient_id'] == plan['patient_id']), None)
        child_name = f"{child['first_name']} {child['last_name']}" if child else "Unknown"
        age_months = child.get('age_in_months') if child else None
        child_age = f"{age_months//12}y {age_months%12}m" if age_months is not None else "-"
        plan_details = plan.get('plan_details', '')
        # Clean plan_details
        import json
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
        plan_details_clean = clean_note(plan_details)
        generated_at_val = plan.get('generated_at', '')
        # Format generated_at robustly
        generated_at_val_fmt = generated_at_val
        if generated_at_val:
            val_str = str(generated_at_val).strip()
            try:
                dt = datetime.strptime(val_str, "%Y-%m-%d %H:%M:%S")
                month = dt.strftime('%B')
                day = dt.strftime('%d')
                year = dt.strftime('%Y')
                hour = dt.strftime('%I').lstrip('0') or '0'
                minute = dt.strftime('%M')
                ampm = dt.strftime('%p').lower()
                generated_at_val_fmt = f"{month} {day}, {year} {hour}:{minute} {ampm}"
            except Exception:
                pass
        notes = notes_by_plan.get(plan.get('plan_id'), [])
        notes_str = "<br>".join([
            f"Noted by {nutritionist_map.get(str(note.get('nutritionist_id')), str(note.get('nutritionist_id')))}: {clean_note(note.get('note', ''))}" for note in notes
        ]) if notes else "No notes yet"
        table_rows.append({
            "Child Name": child_name,
            "Child Age": child_age,
            "Plan Details": plan_details_clean,
            "Generated at": generated_at_val_fmt,
            "Notes": notes_str
        })
    columns = ["Child Name", "Child Age", "Plan Details", "Generated at", "Notes"]
    if table_rows:
        cols = st.columns(len(columns))
        for i, col in enumerate(columns):
            cols[i].markdown(f"**{col}**")
        for row in table_rows:
            vals = [row[col] for col in columns]
            val_cols = st.columns(len(columns))
            for i, val in enumerate(vals):
                if columns[i] == "Plan Details":
                    expand_key = f"plan_details_expanded_{row.get('Generated at','')}_{row.get('Child Name','')}"
                    if expand_key not in st.session_state:
                        st.session_state[expand_key] = False
                    is_expanded = st.session_state[expand_key]
                    preview_len = 0
                    if not is_expanded and isinstance(val, str) and len(val) > preview_len:
                        val_cols[i].markdown(val[:preview_len], unsafe_allow_html=True)
                        if val_cols[i].button("Show Details", key=f"show_details_{expand_key}"):
                            st.session_state[expand_key] = True
                            st.rerun()
                    else:
                        val_cols[i].markdown(val, unsafe_allow_html=True)
                        if is_expanded and val_cols[i].button("Hide Details", key=f"hide_details_{expand_key}"):
                            st.session_state[expand_key] = False
                            st.rerun()
                elif columns[i] == "Notes":
                    val_cols[i].markdown(val, unsafe_allow_html=True)
                else:
                    val_cols[i].markdown(val)
    else:
        if selected_child_id:
            child_name = child_options.get(selected_child_id, "this child")
            st.info(f"No meal plans found for {child_name}.")
        else:
            st.info("No meal plans found for your children.")

def show_children_overview():
    """Display children overview with their basic info and recent meal plans"""
    st.header("👶 Your Children")
    
    children = data_manager.get_children_by_parent(st.session_state.parent_id)
    
    if not children:
        st.info("No children found for this parent account.")
        return
    
    for child in children:
        with st.container():

            age_months = child.get('age_in_months')
            if age_months is None and child.get('date_of_birth'):
                dob = child['date_of_birth']
                if isinstance(dob, str):
                    dob = datetime.strptime(dob, "%Y-%m-%d").date()
                today = datetime.today().date()
                age_months = (today.year - dob.year) * 12 + (today.month - dob.month)
                if today.day < dob.day:
                    age_months -= 1
            if age_months is not None:
                years = age_months // 12
                months = age_months % 12
                if years > 0 and months > 0:
                    age_str = f"{years} years, {months} months old ({age_months} months)"
                elif years > 0:
                    age_str = f"{years} years old ({age_months} months)"
                else:
                    age_str = f"{months} months old"
            else:
                age_str = "Unknown"

            st.markdown(f"""
            <div class="child-card">
                <h3>👶 {child['first_name']} {child['last_name']}</h3>
                <p><strong>Age:</strong> {age_str}</p>
                <p><strong>BMI:</strong> {child.get('bmi', 'N/A')} ({child.get('bmi_category', 'N/A')})</p>
                <p><strong>Allergies:</strong> {child.get('allergies', 'N/A')}</p>
                <p><strong>Medical Conditions:</strong> {child.get('medical_conditions', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

def show_meal_plan_generator():
    """Generate new meal plans for children"""
    st.header("🍽️ Generate Meal Plan")
    
    children = data_manager.get_children_by_parent(st.session_state.parent_id)
    
    if not children:
        st.warning("No children found. Please check with your account administrator.")
        return
    
    patient_options = {child['patient_id']: f"{child['first_name']} {child['last_name']}" for child in children}
    selected_patient_id = st.selectbox(
        "Select Child",
        options=list(patient_options.keys()),
        format_func=lambda x: patient_options[x]
    )

    if selected_patient_id:
        patient_data = data_manager.get_patient_by_id(selected_patient_id)
        st.subheader("👶 Child Summary")
        st.write(f"**Name:** {patient_data['first_name']} {patient_data['last_name']}")

        age_months = patient_data.get('age_in_months')
        st.write(f"**Age:** {age_months if age_months is not None else 'Unknown'} months")
        st.write(f"**BMI:** {patient_data['bmi']} ({patient_data['bmi_category']})")
        st.write(f"**Allergies:** {patient_data['allergies']}")
        st.write(f"**Conditions:** {patient_data['medical_conditions']}")
        # Religion
        parent_id = patient_data.get('parent_id')
        religion = data_manager.get_religion_by_parent(parent_id) if parent_id else "Unknown"
        st.write(f"**Religion:** {religion if religion else 'Unknown'}")
        # Input for available ingredients
        available_ingredients = st.text_area(
            "Available Ingredients at Home (optional)",
            placeholder="e.g. rice, chicken, carrots, eggs"
        )

    # Generate button
    if st.button("🚀 Generate Meal Plan", type="primary"):
        if not selected_patient_id:
            st.error("Please select a child first!")
            return
        from nutrition_chain import get_meal_plan_with_langchain
        with st.spinner(f"🔥 Generating meal plan ..."):
            try:
                meal_plan = get_meal_plan_with_langchain(
                    patient_id=selected_patient_id,
                    available_ingredients=available_ingredients.strip() if selected_patient_id else "",
                    religion=religion if religion else ""
                )
                import json
                # Save meal plan to database as valid JSON
                meal_plan_json = json.dumps({"text": meal_plan})
                data_manager.save_meal_plan(
                    patient_id=str(selected_patient_id),
                    meal_plan=meal_plan_json,
                    duration_days=7,
                    parent_id=str(parent_id)
                )
                st.success(f"✅ Meal plan generated successfully!")
                st.markdown("### 📋 Your Child's Personalized Meal Plan")
                st.markdown(meal_plan)
            except Exception as e:
                st.error(f"❌ Error generating meal plan: {str(e)}")

def show_parent_recipes():
    pass



if __name__ == "__main__":
    main()
