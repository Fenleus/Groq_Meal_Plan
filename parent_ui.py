import streamlit as st
import os
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
    tab1, tab2, tab3 = st.tabs(["👶 My Children", "🍽️ Generate Meal Plan", "📄 Download Plans"])

    with tab1:
        show_children_overview()

    with tab2:
        show_meal_plan_generator()

    with tab3:
        show_download_plans()

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

    # ...existing code...
    if selected_child_id:
        child_data = data_manager.get_child_by_id(selected_child_id)
        st.subheader("👶 Child Summary")
        st.write(f"**Name:** {child_data['name']}")
        # Age in months
        age_months = int(child_data['age'] * 12) if child_data.get('age') else "Unknown"
        st.write(f"**Age:** {age_months} months")
        st.write(f"**BMI:** {child_data['bmi']} ({child_data['bmi_category']})")
        st.write(f"**Allergies:** {child_data['allergies']}")
        st.write(f"**Conditions:** {child_data['medical_conditions']}")
        # Religion input (default to child data if present)
        religion = st.text_input(
            "Religion (optional)",
            value=child_data.get('religion', "")
        )
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
                    religion=religion.strip() if religion else ""
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

def show_download_plans():
    """Download meal plans as PDF"""
    st.header("📄 Download Meal Plans")
    
    children = data_manager.get_children_by_parent(st.session_state.parent_id)
    
    if not children:
        st.warning("No children found.")
        return
    
    # Child selection
    child_options = {child['id']: f"{child['name']} ({child['age']} years)" for child in children}
    selected_child_id = st.selectbox(
        "Select Child for Download",
        options=list(child_options.keys()),
        format_func=lambda x: child_options[x]
    )
    
    if selected_child_id:
        meal_plans = data_manager.get_meal_plans_by_child(selected_child_id, months_back=6)
        
        if meal_plans:
            st.subheader(f"📋 Available Meal Plans for {child_options[selected_child_id]}")
            
            for plan in meal_plans:
                plan_date = datetime.fromisoformat(plan['created_at']).strftime("%B %d, %Y")
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"📅 **{plan_date}** - {plan['duration_days']} days")
                
                with col2:
                    if st.button("👀 Preview", key=f"preview_{plan['id']}"):
                        st.session_state[f"show_preview_{plan['id']}"] = True
                
                with col3:
                    # For now, just show the text (PDF generation can be added later)
                    if st.button("📥 Download", key=f"download_{plan['id']}"):
                        st.info("PDF download functionality will be implemented soon!")
                        # TODO: Implement PDF generation
                
                # Show preview if requested
                if st.session_state.get(f"show_preview_{plan['id']}", False):
                    with st.expander(f"Preview - {plan_date}", expanded=True):
                        st.markdown(plan['meal_plan'])
                        
                        # Show nutritionist notes
                        notes = data_manager.get_notes_for_meal_plan(plan['id'])
                        if notes:
                            st.subheader("👩‍⚕️ Nutritionist Notes:")
                            for note in notes:
                                note_date = datetime.fromisoformat(note['created_at']).strftime("%B %d, %Y")
                                st.info(f"**{note_date}:** {note['note']}")
                        
                        if st.button("❌ Close Preview", key=f"close_{plan['id']}"):
                            st.session_state[f"show_preview_{plan['id']}"] = False
                            st.rerun()
        else:
            st.info(f"No meal plans found for {child_options[selected_child_id]}.")

if __name__ == "__main__":
    main()
