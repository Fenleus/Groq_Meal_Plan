
import streamlit as st
import os
from nutrition_ai import ChildNutritionAI
from data_manager import data_manager
from datetime import datetime, timedelta
import json
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
import tempfile

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
    
    st.success("✅ Connected to Nutrition AI")
    
    # Sidebar for nutritionist info
    st.header("🧠 Filipino Nutrition Knowledge Base")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("� Current Knowledge Base")
        knowledge_base = data_manager.get_knowledge_base()
        # Show nutrition guidelines
        guidelines = knowledge_base.get('nutrition_guidelines', {})
        if guidelines:
            st.write("**Age-Specific Guidelines:**")
            for age_group, guideline in guidelines.items():
                st.info(f"**{age_group.replace('_', ' ').title()}:** {guideline}")
        # Show Filipino foods
        filipino_foods = knowledge_base.get('filipino_foods', {})
        if filipino_foods:
            st.write(f"**Filipino Foods Database: {len(filipino_foods)} recipes**")
            for food_id, food_data in list(filipino_foods.items())[:3]:
                with st.expander(f"🍽️ {food_data['name']}"):
                    st.write(f"**Ingredients:** {food_data['ingredients']}")
                    st.write(f"**Nutrition Facts:** {food_data['nutrition_facts']}")
                    st.write(f"**Instructions:** {food_data['instructions']}")
        # Show uploaded PDFs
        uploaded_pdfs = knowledge_base.get('uploaded_pdfs', [])
        if uploaded_pdfs:
            st.write(f"**Uploaded PDFs: {len(uploaded_pdfs)} documents**")
            for pdf in uploaded_pdfs:
                st.write(f"- {pdf.get('name', 'Unknown document')}")
        # Show vector store status
        if os.path.exists("pdf_vector.index"):
            st.success("PDF Vector Store: Ready for LLM retrieval!")
        else:
            st.warning("PDF Vector Store not initialized yet.")

    with col2:
        st.subheader("➕ Add Knowledge")
        # Add Filipino recipe
        recipe_name = st.text_input("Recipe Name", placeholder="e.g., Chicken Tinola")
        ingredients = st.text_area("Ingredients", placeholder="List main ingredients...")
        nutrition_facts = st.text_area("Nutrition Facts", placeholder="Nutritional benefits and considerations...")
        instructions = st.text_area("Instructions", placeholder="Brief cooking instructions...")
        if st.button("� Add Recipe to Database"):
            if all([recipe_name, ingredients, nutrition_facts, instructions]):
                recipe_id = data_manager.add_filipino_recipe(
                    nutritionist_id=st.session_state.nutritionist_id,
                    recipe_name=recipe_name,
                    ingredients=ingredients,
                    nutrition_facts=nutrition_facts,
                    instructions=instructions
                )
                st.success(f"Recipe '{recipe_name}' added to knowledge base!")
                st.rerun()
            else:
                st.error("Please fill in all fields!")
        st.markdown("---")
        # Add nutrition guideline
        st.write("**Add Nutrition Guideline:**")
        guideline_key = st.text_input("Guideline Key", placeholder="e.g., age_3_4_years")
        guideline_text = st.text_area("Guideline Text", placeholder="Nutrition recommendation...")
        if st.button("💾 Add Guideline"):
            if guideline_key and guideline_text:
                knowledge_base = data_manager.get_knowledge_base()
                if 'nutrition_guidelines' not in knowledge_base:
                    knowledge_base['nutrition_guidelines'] = {}
                knowledge_base['nutrition_guidelines'][guideline_key] = guideline_text
                data_manager.save_knowledge_base(knowledge_base)
                st.success("Guideline added!")
                st.rerun()
            else:
                st.error("Please fill in both fields!")
        st.markdown("---")
        # PDF upload and vector memory
        st.write("**Upload PDF Knowledge (LLM-Ready):**")
        uploaded_file = st.file_uploader("Choose PDF file", type="pdf")
        if uploaded_file is not None:
            with pdfplumber.open(uploaded_file) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                # Save to knowledge base for record
                knowledge_base = data_manager.get_knowledge_base()
                if 'uploaded_pdfs' not in knowledge_base:
                    knowledge_base['uploaded_pdfs'] = []
                knowledge_base['uploaded_pdfs'].append({
                    "name": uploaded_file.name,
                    "content": text[:1000] + ("..." if len(text) > 1000 else "")
                })
                data_manager.save_knowledge_base(knowledge_base)
                # Chunk and embed for vector memory
                with st.spinner("Indexing PDF for LLM retrieval (this may take a moment)..."):
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    docs = text_splitter.create_documents([text])
                    # Use a simple HuggingFace embedding (can swap for OpenAI or Groq if available)
                    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                    if os.path.exists("pdf_vector.index"):
                        db = FAISS.load_local("pdf_vector.index", embeddings)
                        db.add_documents(docs)
                    else:
                        db = FAISS.from_documents(docs, embeddings)
                    db.save_local("pdf_vector.index")
                st.success(f"PDF '{uploaded_file.name}' uploaded, extracted, and indexed for LLM retrieval!")
                st.rerun()
            else:
                st.error("No text could be extracted from this PDF.")
            with col2:
                # Show meal plan count
                meal_plans = []
                notes_count = sum(len(data_manager.get_notes_for_meal_plan(plan['id'])) for plan in meal_plans)

                st.metric("Meal Plans", len(meal_plans))
                st.metric("Your Notes", notes_count)

            # Show recent meal plans
            recent_plans = []

            if recent_plans:
                with st.expander(f"Recent Meal Plans for {child['name']}"):
                    for plan in recent_plans[:2]:  # Show 2 most recent
                        plan_date = datetime.fromisoformat(plan['created_at']).strftime("%B %d, %Y")

                        st.subheader(f"📅 {plan_date} ({plan['duration_days']} days)")

                        # Show meal plan in collapsed form
                        with st.expander("View Meal Plan"):
                            st.markdown(plan['meal_plan'])

                        # Show existing notes
                        notes = data_manager.get_notes_for_meal_plan(plan['id'])
                        if notes:
                            st.write("**Your Previous Notes:**")
                            for note in notes:
                                note_date = datetime.fromisoformat(note['created_at']).strftime("%B %d, %Y")
                                st.info(f"**{note_date}:** {note['note']}")

                        # Quick add note
                        quick_note = st.text_area(f"Add note for {plan_date} plan:", key=f"note_{plan['id']}")
                        if st.button(f"💾 Add Note", key=f"save_note_{plan['id']}"):
                            if quick_note:
                                data_manager.save_nutritionist_note(
                                    meal_plan_id=plan['id'],
                                    nutritionist_id=st.session_state.nutritionist_id,
                                    note=quick_note
                                )
                                st.success("Note added successfully!")
                                st.rerun()

            st.markdown("---")

def show_add_notes():
    """Dedicated section for adding detailed notes to meal plans"""
    st.header("📝 Add Detailed Notes to Meal Plans")
    
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
        
        # Show nutrition guidelines
        guidelines = knowledge_base.get('nutrition_guidelines', {})
        if guidelines:
            st.write("**Age-Specific Guidelines:**")
            for age_group, guideline in guidelines.items():
                st.info(f"**{age_group.replace('_', ' ').title()}:** {guideline}")
        
        # Show Filipino foods
        filipino_foods = knowledge_base.get('filipino_foods', {})
        if filipino_foods:
            st.write(f"**Filipino Foods Database: {len(filipino_foods)} recipes**")
            
            for food_id, food_data in list(filipino_foods.items())[:3]:
                with st.expander(f"🍽️ {food_data['name']}"):
                    st.write(f"**Ingredients:** {food_data['ingredients']}")
                    st.write(f"**Nutrition Facts:** {food_data['nutrition_facts']}")
                    st.write(f"**Instructions:** {food_data['instructions']}")
        
        # Show uploaded PDFs
        uploaded_pdfs = knowledge_base.get('uploaded_pdfs', [])
        if uploaded_pdfs:
            st.write(f"**Uploaded PDFs: {len(uploaded_pdfs)} documents**")
            for pdf in uploaded_pdfs:
                st.write(f"- {pdf.get('name', 'Unknown document')}")
    
    with col2:
        st.subheader("➕ Add Knowledge")
        
        # Add Filipino recipe
        st.write("**Add Filipino Recipe:**")
        recipe_name = st.text_input("Recipe Name", placeholder="e.g., Chicken Tinola")
        ingredients = st.text_area("Ingredients", placeholder="List main ingredients...")
        nutrition_facts = st.text_area("Nutrition Facts", placeholder="Nutritional benefits and considerations...")
        instructions = st.text_area("Instructions", placeholder="Brief cooking instructions...")
        
        if st.button("💾 Add Recipe to Database"):
            if all([recipe_name, ingredients, nutrition_facts, instructions]):
                recipe_id = data_manager.add_filipino_recipe(
                    nutritionist_id=st.session_state.nutritionist_id,
                    recipe_name=recipe_name,
                    ingredients=ingredients,
                    nutrition_facts=nutrition_facts,
                    instructions=instructions
                )
                st.success(f"Recipe '{recipe_name}' added to knowledge base!")
                st.rerun()
            else:
                st.error("Please fill in all fields!")
        
        st.markdown("---")
        
        # Add nutrition guideline
        st.write("**Add Nutrition Guideline:**")
        guideline_key = st.text_input("Guideline Key", placeholder="e.g., age_3_4_years")
        guideline_text = st.text_area("Guideline Text", placeholder="Nutrition recommendation...")
        
        if st.button("💾 Add Guideline"):
            if guideline_key and guideline_text:
                knowledge_base = data_manager.get_knowledge_base()
                if 'nutrition_guidelines' not in knowledge_base:
                    knowledge_base['nutrition_guidelines'] = {}
                knowledge_base['nutrition_guidelines'][guideline_key] = guideline_text
                data_manager.save_knowledge_base(knowledge_base)
                st.success("Guideline added!")
                st.rerun()
            else:
                st.error("Please fill in both fields!")
        
        st.markdown("---")
        
        # PDF upload placeholder
        st.write("**Upload PDF Knowledge:**")
        uploaded_file = st.file_uploader("Choose PDF file", type="pdf")
        if uploaded_file is not None:
            st.info("PDF processing functionality will be implemented soon!")

def show_recipe_database():
    st.header("🇭 Filipino Recipes Database")
    knowledge_base = data_manager.get_knowledge_base()
    filipino_foods = knowledge_base.get('filipino_foods', {})
    if filipino_foods:
        st.write(f"**Total Filipino Recipes: {len(filipino_foods)}**")
        search_term = st.text_input("🔍 Search recipes:", placeholder="Enter recipe name or ingredient...")
        filtered_recipes = filipino_foods
        if search_term:
            filtered_recipes = {
                k: v for k, v in filipino_foods.items() 
                if search_term.lower() in v['name'].lower() or 
                   search_term.lower() in v['ingredients'].lower()
            }
        for recipe_id, recipe in filtered_recipes.items():
            with st.expander(f"🍽️ {recipe['name']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Ingredients:** {recipe['ingredients']}")
                    st.write(f"**Instructions:** {recipe['instructions']}")
                with col2:
                    st.write(f"**Nutrition Facts:** {recipe['nutrition_facts']}" )
                    added_date = datetime.fromisoformat(recipe['created_at']).strftime("%B %d, %Y")
                    st.write(f"**Added:** {added_date}")
                    st.write(f"**Added by:** {recipe['added_by']}")
    else:
        st.info("No Filipino recipes in database yet. Add some in the Knowledge Base tab!")

if __name__ == "__main__":
    main()
