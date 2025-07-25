
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
        
    # Sidebar for parent selection (for demo)
    with st.sidebar:
        st.header("👤 Parent Login")
        # Dynamically load parent names from parents.json
        parents_data = data_manager.get_parents_data()
        parent_options = {pid: pdata.get('name', pid) for pid, pdata in parents_data.items()}
        selected_parent = st.selectbox(
            "Select Parent Account",
            options=list(parent_options.keys()),
            format_func=lambda x: parent_options[x],
            index=0
        )
        st.session_state.parent_id = selected_parent
        st.info(f"Logged in as: {parent_options[selected_parent]}")
    
    # Main tabs
    tab1, tab2 = st.tabs(["👶 My Children", "🍽️ Generate Meal Plan"])

    with tab1:
        show_children_overview()

    with tab2:
        show_meal_plan_generator()

def show_children_overview():
    """Display children overview with their basic info and recent meal plans"""
    st.header("👶 Your Children")
    
    children = data_manager.get_children_by_parent(st.session_state.parent_id)
    
    if not children:
        st.info("No children found for this parent account.")
        return
    
    for child in children:
        with st.container():
            # Calculate age in months
            age_months = child.get('age_in_months')
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
                <h3>👶 {child['name']}</h3>
                <p><strong>Age:</strong> {age_str}</p>
                <p><strong>BMI:</strong> {child['bmi']} ({child['bmi_category']})</p>
                <p><strong>Weight:</strong> {child['weight']} kg | <strong>Height:</strong> {child['height']} cm</p>
                <p><strong>Allergies:</strong> {child['allergies']}</p>
                <p><strong>Medical Conditions:</strong> {child['medical_conditions']}</p>
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
    
    # Child selection
    child_options = {child['id']: f"{child['name']}" for child in children}
    selected_child_id = st.selectbox(
        "Select Child",
        options=list(child_options.keys()),
        format_func=lambda x: child_options[x]
    )

    if selected_child_id:
        child_data = data_manager.get_child_by_id(selected_child_id)
        st.subheader("👶 Child Summary")
        st.write(f"**Name:** {child_data['name']}")
        # Age in months only
        age_months = child_data.get('age_in_months')
        st.write(f"**Age:** {age_months if age_months is not None else 'Unknown'} months")
        st.write(f"**BMI:** {child_data['bmi']} ({child_data['bmi_category']})")
        st.write(f"**Allergies:** {child_data['allergies']}")
        st.write(f"**Conditions:** {child_data['medical_conditions']}")
        # Religion
        parent_id = child_data.get('parent_id')
        religion = data_manager.get_religion_by_parent(parent_id) if parent_id else "Unknown"
        st.write(f"**Religion:** {religion if religion else 'Unknown'}")
        # Input for available ingredients
        available_ingredients = st.text_area(
            "Available Ingredients at Home (optional)",
            placeholder="e.g. rice, chicken, carrots, eggs"
        )

    # Generate button
    if st.button("🚀 Generate Meal Plan", type="primary"):
        if not selected_child_id:
            st.error("Please select a child first!")
            return
        from nutrition_chain import get_meal_plan_with_langchain
        with st.spinner(f"🔥 Generating meal plan (LangChain)..."):
            try:
                meal_plan = get_meal_plan_with_langchain(
                    child_id=selected_child_id,
                    available_ingredients=available_ingredients.strip() if selected_child_id else "",
                    religion=religion if religion else ""
                )
                st.success(f"✅ Meal plan generated successfully!")
                st.markdown("### 📋 Your Child's Personalized Meal Plan")
                st.markdown(meal_plan)
            except Exception as e:
                st.error(f"❌ Error generating meal plan: {str(e)}")

def show_family_recipes():
    pass



if __name__ == "__main__":
    main()
