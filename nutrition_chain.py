from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from data_manager import data_manager

load_dotenv()

def get_relevant_pdf_chunks(query, k=4):
    """Retrieve relevant PDF chunks from vector store for LLM context."""
    from langchain.vectorstores import FAISS
    from langchain.embeddings import HuggingFaceEmbeddings
    if not os.path.exists("pdf_vector.index"):
        return []
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.load_local("pdf_vector.index", embeddings)
    docs_and_scores = db.similarity_search_with_score(query, k=k)
    return [doc.page_content for doc, _ in docs_and_scores]

def get_meal_plan_with_langchain(patient_id, available_ingredients=None, religion=None):
    """
    Use LangChain to generate a meal plan for a patient using Groq LLM and a nutritionist-style prompt.

    Optionally includes available ingredients provided by the parent.
    """
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    # Get patient data
    patient_data = data_manager.get_patient_by_id(patient_id)
    if not patient_data:
        return "Error: Patient data not found"

    # Get Filipino foods from knowledge base
    knowledge_base = data_manager.get_knowledge_base()
    filipino_foods = knowledge_base.get('filipino_foods', {})
    filipino_context = ""
    if filipino_foods:
        filipino_recipes = []
        for recipe in list(filipino_foods.values())[:5]:
            filipino_recipes.append(f"- {recipe['name']}: {recipe['nutrition_facts']}")
        filipino_context = "\nFilipino Food Options:\n" + "\n".join(filipino_recipes)

    # Get religion from parent
    if not religion:
        parent_id = patient_data.get('parent_id')
        religion = data_manager.get_religion_by_parent(parent_id) if parent_id else ""

    # Retrieve relevant PDF knowledge for this patient
    query = f"child nutrition {patient_data.get('age_in_months', '')} months {patient_data.get('bmi_category', '')} {patient_data.get('allergies', '')} {patient_data.get('medical_conditions', '')}"
    relevant_pdf_chunks = get_relevant_pdf_chunks(query, k=4)
    pdf_context = ""
    if relevant_pdf_chunks:
        pdf_context = "\nBACKGROUND KNOWLEDGE (for your reference only, do NOT mention or cite this in your response):\n" + "\n---\n".join(relevant_pdf_chunks)

    # Get all food names from the database
    foods_data = data_manager.get_foods_data()
    food_names = []
    for food in foods_data:
        # Use food_name_and_description and alternate_common_names if available
        name = food.get('food_name_and_description')
        alternates = food.get('alternate_common_names')
        if name:
            if alternates:
                food_names.append(f"{name} ({alternates})")
            else:
                food_names.append(name)
    food_list_str = '\n- '.join(food_names)
    if food_list_str:
        food_list_str = 'FOOD DATABASE (only recommend foods from this list):\n- ' + food_list_str + '\n'
    else:
        food_list_str = ''

    # Build the refined prompt string, including the food list from the database
    prompt_str = (
        "You are a pediatric nutrition expert. You must ONLY recommend foods and ingredients that are present in the provided food database below. Do NOT recommend, mention, or invent any foods, ingredients, or recipes that are not found in the food database. If you are unsure if a food is in the database, do not include it. If you cannot recommend any foods from the database, say 'No suitable foods available.' IMPORTANT: Do NOT recommend or mention generic food groups (like 'fruits', 'vegetables', 'protein sources', 'iron-rich foods', 'complex carbohydrates', 'healthy fats', etc). ONLY list specific food names from the database. Do not output any generic categories.\n"
        + food_list_str
        + "Generate a general list of suitable foods or food combinations for a Filipino child (0-5 years old) with the following profile:\n"
        + f"\n- Age (months): {{age_in_months}}"
        + f"\n- BMI Category: {{bmi_category}}"
        + f"\n- Allergies: {{allergies}}"
        + f"\n- Medical Conditions: {{medical_conditions}}"
        + f"\n- Religion: {{religion}}\n"
        + "\nIf the child's age is less than 6 months, do NOT recommend any solid foods. Follow best pediatric nutrition guidelines for infants under 6 months."
        + (f"\nOnly use these available ingredients: {{available_ingredients}}\n" if available_ingredients else "")
        + "\nStrictly avoid all allergens and respect all medical and religious restrictions."
        + "\nDo not organize the output by breakfast, lunch, or dinner. Instead, provide a concise, general list of recommended foods or food combinations, and a brief explanation for your choices."
        + "\nDo not include the child's name or any sensitive information."
        + "\nIf you use any background knowledge provided, do NOT mention or cite the source, file, or that you used a document. Present all recommendations as your own expertise."
    # End of prompt_str assignment
    )
    if pdf_context:
        prompt_str += "\n" + pdf_context
    prompt_template = PromptTemplate(
        input_variables=["age_in_months", "bmi_category", "allergies", "medical_conditions", "available_ingredients", "religion"],
        template=prompt_str
    )

    prompt_inputs = {
        "age_in_months": patient_data.get("age_in_months", "Unknown"),
        "bmi_category": patient_data.get("bmi_category", "Unknown"),
        "allergies": patient_data.get("allergies", "None"),
        "medical_conditions": patient_data.get("medical_conditions", "None"),
        "available_ingredients": available_ingredients if available_ingredients else "",
        "religion": religion if religion else ""
    }

    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.3,
        max_tokens=3000
    )

    chain = LLMChain(
        llm=llm,
        prompt=prompt_template
    )

    result = chain.run(**prompt_inputs)
    return result