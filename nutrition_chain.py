from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from data_manager import data_manager

load_dotenv()

def get_relevant_pdf_chunks(query, k=4):
    """Retrieve relevant PDF text using simple keyword matching."""
    try:
        # Get PDF text directly from knowledge base
        knowledge_base = data_manager.get_knowledge_base()
        if not knowledge_base:
            return []
        
        query_keywords = query.lower().split()
        scored_chunks = []
        
        for kb in knowledge_base.values():
            ai_summary = kb.get('ai_summary', '')
            if ai_summary:
                # Simple scoring based on keyword matches
                summary_lower = ai_summary.lower()
                score = sum(1 for keyword in query_keywords if keyword in summary_lower)
                
                if score > 0:
                    # Split into smaller chunks if needed
                    if len(ai_summary) > 500:
                        chunks = ai_summary.split('\n')
                        for chunk in chunks:
                            if chunk.strip():
                                chunk_score = sum(1 for keyword in query_keywords if keyword in chunk.lower())
                                if chunk_score > 0:
                                    scored_chunks.append((chunk.strip(), chunk_score))
                    else:
                        scored_chunks.append((ai_summary, score))
        
        # Sort by score and return top k
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return [chunk[0] for chunk in scored_chunks[:k]]
        
    except Exception as e:
        return []

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

    # --- Nutrition analysis integration ---
    from nutrition_ai import ChildNutritionAI
    nutrition_analysis = ""
    try:
        nutrition_ai = ChildNutritionAI()
        name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}".strip()
        analysis_result = nutrition_ai.analyze_child_nutrition(
            name=name,
            age_in_months=patient_data.get('age_in_months'),
            bmi=patient_data.get('bmi'),
            allergies=patient_data.get('allergies'),
            medical_conditions=patient_data.get('medical_conditions'),
            parent_id=patient_data.get('parent_id')
        )
        nutrition_analysis = f"\nNUTRITION ANALYSIS FOR THIS CHILD:\n{analysis_result}\n"
    except Exception as e:
        nutrition_analysis = ""

    prompt_str = (
        "You are a pediatric nutrition expert. You must ONLY recommend foods and ingredients that are present in the provided food database below. Do NOT recommend, mention, or invent any foods, ingredients, or recipes that are not found in the food database. If you are unsure if a food is in the database, do not include it. If you cannot recommend any foods from the database, say 'No suitable foods available.' IMPORTANT: Do NOT recommend or mention generic food groups (like 'fruits', 'vegetables', 'protein sources', 'iron-rich foods', 'complex carbohydrates', 'healthy fats', etc). ONLY list specific food names from the database. Do not output any generic categories.\n"
        + food_list_str
        + "Create a 7-day meal plan for a Filipino child (0-5 years old) with the following profile. For each day, provide: Breakfast, Mid-morning Snack, Lunch, Afternoon Snack, Dinner, and (if age-appropriate) Before-bed Snack. For each meal, specify the Filipino dish name, portion size, and a brief explanation of its nutritional benefit. Focus on traditional Filipino dishes that are practical for parents to prepare.\n"
        + f"\n- Age (months): {{age_in_months}}"
        + f"\n- BMI Category: {{bmi_category}}"
        + f"\n- Allergies: {{allergies}}"
        + f"\n- Medical Conditions: {{medical_conditions}}"
        + f"\n- Religion: {{religion}}\n"
        + nutrition_analysis
        + filipino_context
        + (f"\nAVAILABLE INGREDIENTS AT HOME: {{available_ingredients}}\n" if available_ingredients else "")
        + "\nSPECIAL INSTRUCTIONS:\n"
        + "- For DAY 1 ONLY: Prioritize using the available ingredients at home when possible, but you can still use other foods from the database to create complete, balanced Filipino meals.\n"
        + "- For DAYS 2-7: Create varied Filipino meals using ANY foods from the database. Do NOT limit yourself to only the available ingredients.\n"
        + "- Each day should have DIFFERENT meals - avoid repeating the same dishes.\n"
        + "- Focus on Filipino dishes like: lugaw, sopas, giniling, adobo, sinigang, pancit, lumpia, etc. (only if ingredients are in database)\n"
        + "- Create complete meal combinations, not just single ingredients.\n\n"
        + "GUIDELINES:\n1. Follow WHO nutrition guidelines for children 0-5 years\n2. Account for BMI category, allergies, and medical conditions\n3. Strictly avoid all allergens and respect all medical and religious restrictions\n4. Provide age-appropriate textures and portions\n5. Include traditional Filipino foods and cooking methods\n6. Focus on balanced nutrition for growing children\n7. Include hydration recommendations\n8. Make each day's meals DIFFERENT from other days\n\n"
        + "MEAL PLAN FORMAT (repeat for each day):\nDay X:\n- Breakfast: [Filipino dish name, portion, nutritional explanation]\n- Mid-morning Snack: [snack, portion, explanation]\n- Lunch: [Filipino dish name, portion, nutritional explanation]\n- Afternoon Snack: [snack, portion, explanation]\n- Dinner: [Filipino dish name, portion, nutritional explanation]\n- Before-bed Snack: [if appropriate for age]\n\n"
        + "If the child's age is less than 6 months, do NOT recommend any solid foods.\nDo not include the child's name or any sensitive information.\nIf you use any background knowledge provided, do NOT mention or cite the source, file, or that you used a document. Present all recommendations as your own expertise."
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