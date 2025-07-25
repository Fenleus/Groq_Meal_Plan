from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from data_manager import data_manager

load_dotenv()

def get_meal_plan_with_langchain(child_id, available_ingredients=None, religion=None):
    """
    Use LangChain to generate a meal plan for a child using Groq LLM and a nutritionist-style prompt.
    Only uses knowledge_base.json.
    Optionally includes available ingredients provided by the parent.
    """
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    # Get child data
    child_data = data_manager.get_child_by_id(child_id)
    if not child_data:
        return "Error: Child data not found"

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
        parent_id = child_data.get('parent_id')
        religion = data_manager.get_religion_by_parent(parent_id) if parent_id else ""
    # Build the prompt string without Jinja logic
    prompt_str = (
        "You are a pediatric nutrition expert. Based only on the foods in the knowledge based, generate a general meal plan for a Filipino child (0-5 years old) with the following profile:\n"
        f"\n- Age (months): {{age_in_months}}"
        f"\n- BMI Category: {{bmi_category}}"
        f"\n- Allergies: {{allergies}}"
        f"\n- Medical Conditions: {{medical_conditions}}"
        f"\n- Religion: {{religion}}\n"
    )
    # Add available ingredients line if provided
    if available_ingredients:
        prompt_str += f"\nOnly use these available ingredients: {{available_ingredients}}\n"
    prompt_str += (
        "\nDo NOT use any foods or ingredients not found in the database. Strictly avoid allergens and respect religious and medical restrictions. Do not include the child's name or any sensitive information.\n"
        "\nProvide a concise, general list of recommended meals and a brief explanation for your choices. Keep the output short and practical."
    )
    prompt_template = PromptTemplate(
        input_variables=["age_in_months", "bmi_category", "allergies", "medical_conditions", "available_ingredients", "religion"],
        template=prompt_str
    )

    prompt_inputs = {
        "age_in_months": child_data.get("age_in_months", "Unknown"),
        "bmi_category": child_data.get("bmi_category", "Unknown"),
        "allergies": child_data.get("allergies", "None"),
        "medical_conditions": child_data.get("medical_conditions", "None"),
        "available_ingredients": available_ingredients if available_ingredients else "",
        "religion": religion if religion else ""
    }

    # Groq LLM for LangChain
    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="llama3-8b-8192",
        temperature=0.3,
        max_tokens=3000
    )

    chain = LLMChain(
        llm=llm,
        prompt=prompt_template
    )

    # Run chain and return result
    result = chain.run(**prompt_inputs)
    return result