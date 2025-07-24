
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
        st.session_state.parent_id = "parent_001"  # Default for demo

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
    
    st.success("✅ Connected to Nutrition AI")
    
    # Sidebar for parent selection (for demo)
    with st.sidebar:
        st.header("👤 Parent Login")
        parent_options = {
            "parent_001": "Santos Family",
            "parent_002": "Cruz Family"
        }
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
            st.markdown(f"""
            <div class="child-card">
                <h3>👶 {child['name']}</h3>
                <p><strong>Age:</strong> {child['age']} years old</p>
                <p><strong>BMI:</strong> {child['bmi']} ({child['bmi_category']})</p>
                <p><strong>Weight:</strong> {child['weight']} kg | <strong>Height:</strong> {child['height']} cm</p>
                <p><strong>Allergies:</strong> {child['allergies']}</p>
                <p><strong>Medical Conditions:</strong> {child['medical_conditions']}</p>
            </div>
            """, unsafe_allow_html=True)

            # Only show clickable link if no meal plans
            recent_plans = data_manager.get_meal_plans_by_child(child['id'], months_back=2)
            if not recent_plans:
                st.markdown(f"No meal plans yet for {child['name']}. [Generate one in the 'Generate Meal Plan' tab!](#🍽️-generate-meal-plan)")
            st.markdown("---")

def show_meal_plan_generator():
    """Generate new meal plans for children"""
    st.header("🍽️ Generate Meal Plan")
    
    children = data_manager.get_children_by_parent(st.session_state.parent_id)
    
    if not children:
        st.warning("No children found. Please check with your account administrator.")
        return
    
    # Child selection
    child_options = {child['id']: f"{child['name']} ({child['age']} years)" for child in children}
    selected_child_id = st.selectbox(
        "Select Child",
        options=list(child_options.keys()),
        format_func=lambda x: child_options[x]
    )

    if selected_child_id:
        child_data = data_manager.get_child_by_id(selected_child_id)
        st.subheader("👶 Child Summary")
        st.write(f"**Name:** {child_data['name']}")
        # Age in months (check if already in months)
        age_val = child_data.get('age')
        if age_val is not None:
            if age_val > 5:  # unlikely to be months if > 5
                age_months = int(age_val)
            else:
                age_months = int(age_val * 12)
        else:
            age_months = "Unknown"
        st.write(f"**Age:** {age_months} months")
        st.write(f"**BMI:** {child_data['bmi']} ({child_data['bmi_category']})")
        st.write(f"**Allergies:** {child_data['allergies']}")
        st.write(f"**Conditions:** {child_data['medical_conditions']}")
        # Religion (must be present in child data)
        religion = child_data.get('religion', "Unknown")
        st.write(f"**Religion:** {religion}")
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
                # Save the meal plan
                plan_id = data_manager.save_meal_plan(
                    child_id=selected_child_id,
                    meal_plan=meal_plan,
                    duration_days=None,
                    parent_id=st.session_state.parent_id
                )
                st.success(f"✅ Meal plan generated successfully!")
                st.markdown("### 📋 Your Child's Personalized Meal Plan")
                st.markdown(meal_plan)
                st.info(f"💾 Meal plan saved with ID: {plan_id}")
            except Exception as e:
                st.error(f"❌ Error generating meal plan: {str(e)}")

def show_family_recipes():
    pass



if __name__ == "__main__":
    main()
