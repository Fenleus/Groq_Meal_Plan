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

    # Prompt template
    prompt = f"""
    Generate a meal plan for a child using the following details:
    Age: {child_data.get('age', '')}
    Weight: {child_data.get('weight', '')}
    Height: {child_data.get('height', '')}
    BMI: {child_data.get('bmi', '')}
    Allergies: {child_data.get('allergies', '')}
    Medical Conditions: {child_data.get('medical_conditions', '')}
    Religion: {religion or child_data.get('religion', '')}
    Available Ingredients: {available_ingredients}
    Filipino Food Context: {filipino_context}
    
    Instructions:
    1. Recommend a nutritionally balanced meal plan for 0-5 year old children.
    2. Avoid foods that trigger allergies or conflict with medical conditions.
    3. Respect religious dietary restrictions and do not recommend foods that conflict with the child's religion.
    """
    # ...existing code...
    prompt_template = PromptTemplate(
        input_variables=["child_name", "age_months", "bmi", "bmi_category", "allergies", "medical_conditions", "weight", "height", "filipino_context", "available_ingredients", "religion"],
        template="""
You are a pediatric nutrition expert specializing in Filipino children's nutrition (ages 0-5).

Create a meal plan for this child:

CHILD PROFILE:
- Name: {child_name}
- Age: {age_months} months old
- BMI: {bmi}
- BMI Category: {bmi_category}
- Allergies: {allergies}
- Medical Conditions: {medical_conditions}
- Religion: {religion}
- Current Weight: {weight} kg
- Current Height: {height} cm

{filipino_context}

GUIDELINES:
1. Follow WHO nutrition guidelines for children 0-5 years
2. Consider Filipino dietary patterns and available foods
3. Account for BMI category - adjust portions and food types accordingly
4. Strictly avoid allergens mentioned above
5. Consider medical conditions in food recommendations
6. Provide age-appropriate textures and portions
7. Include traditional Filipino foods when appropriate
8. Focus on balanced nutrition for growing children
9. Respect religious dietary restrictions and do not recommend foods that conflict with the child's religion

MEAL PLAN FORMAT:
For each day, provide:
- Breakfast (with portion size appropriate for age)
- Mid-morning snack
- Lunch (with portion size)
- Afternoon snack
- Dinner (with portion size)
- Before-bed snack (if appropriate for age)

Include:
- Specific portion sizes for the child's age and BMI
- Filipino-friendly ingredients and cooking methods
- Nutritional benefits of each meal
- Any special preparation notes for the child's conditions
- Alternative options if child refuses certain foods

SAFETY NOTES:
- Highlight any foods to avoid due to allergies/conditions
- Note appropriate textures for the child's age
- Include hydration recommendations

Keep recommendations practical for Filipino families.

If the parent has listed available ingredients at home, prioritize using them in the meal plan. If left blank, use your best judgment based on Filipino foods and guidelines.

Available Ingredients at Home: {available_ingredients}
"""
    )

    # Prepare input variables
    age_val = child_data.get("age")
    if age_val is not None:
        if age_val > 5:
            age_months = int(age_val)
        else:
            age_months = int(age_val * 12)
    else:
        age_months = "Unknown"
    prompt_inputs = {
        "child_name": child_data.get("name", "Unknown"),
        "age_months": age_months,
        "bmi": child_data.get("bmi", "Unknown"),
        "bmi_category": child_data.get("bmi_category", "Unknown"),
        "allergies": child_data.get("allergies", "None"),
        "medical_conditions": child_data.get("medical_conditions", "None"),
        "weight": child_data.get("weight", "Unknown"),
        "height": child_data.get("height", "Unknown"),
        "filipino_context": filipino_context,
        "available_ingredients": available_ingredients if available_ingredients else "",
        "religion": religion if religion else ""
    }

    # Set up Groq LLM for LangChain
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