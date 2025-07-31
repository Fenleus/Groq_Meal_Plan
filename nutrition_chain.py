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

def get_meal_plan_with_langchain(child_id, available_ingredients=None, religion=None):
    """
    Use LangChain to generate a meal plan for a child using Groq LLM and a nutritionist-style prompt.

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

    # Retrieve relevant PDF knowledge for this child
    query = f"child nutrition {child_data.get('age_in_months', '')} months {child_data.get('bmi_category', '')} {child_data.get('allergies', '')} {child_data.get('medical_conditions', '')}"
    relevant_pdf_chunks = get_relevant_pdf_chunks(query, k=4)
    pdf_context = ""
    if relevant_pdf_chunks:

        pdf_context = "\nBACKGROUND KNOWLEDGE (for your reference only, do NOT mention or cite this in your response):\n" + "\n---\n".join(relevant_pdf_chunks)

    # Build the refined prompt string
    prompt_str = (
        "You are a pediatric nutrition expert. Using only the foods and ingredients listed in the provided food database, generate a general list of suitable foods or food combinations for a Filipino child (0-5 years old) with the following profile:\n"
        f"\n- Age (months): {{age_in_months}}"
        f"\n- BMI Category: {{bmi_category}}"
        f"\n- Allergies: {{allergies}}"
        f"\n- Medical Conditions: {{medical_conditions}}"
        f"\n- Religion: {{religion}}\n"
    )
    if available_ingredients:
        prompt_str += f"\nOnly use these available ingredients: {{available_ingredients}}\n"
    prompt_str += (
        "\nStrictly do not use or mention any foods, ingredients, or recipes that are not found in the food database. Do not invent or assume any foods. Avoid all allergens and respect all medical and religious restrictions."
        "\nDo not organize the output by breakfast, lunch, or dinner. Instead, provide a concise, general list of recommended foods or food combinations, and a brief explanation for your choices."
        "\nDo not include the child's name or any sensitive information."
        "\nIf you use any background knowledge provided, do NOT mention or cite the source, file, or that you used a document. Present all recommendations as your own expertise."
    )
    if pdf_context:
        prompt_str += "\n" + pdf_context
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