import os
from groq import Groq
from dotenv import load_dotenv
from data_manager import data_manager
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

class ChildNutritionAI:
    def analyze_child_nutrition(
        self,
        name: str,
        age_in_months: int,
        bmi: float = None,
        allergies: str = None,
        medical_conditions: str = None,
        parent_id: str = None
    ) -> str:
        """Analyze a child's nutrition profile and return a summary or recommendations."""
        # Get child data if available, else use provided info
        child_info = {
            "name": name,
            "age_in_months": age_in_months,
            "bmi": bmi,
            "allergies": allergies,
            "medical_conditions": medical_conditions,
            "parent_id": parent_id
        }
        try:
            prompt = f"""You are a pediatric nutrition expert. Analyze the following child's nutrition profile and provide a summary of their nutritional status, potential concerns, and general recommendations.\n\nCHILD PROFILE:\n- Name: {name}\n- Age (months): {age_in_months}\n- BMI: {bmi}\n- Allergies: {allergies}\n- Medical Conditions: {medical_conditions}\n- Parent ID: {parent_id}\n\nGive practical, parent-friendly advice and highlight any red flags or areas for improvement."""

            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {"role": "system", "content": "You are a pediatric nutrition expert focused on Filipino children's health and development."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error analyzing child nutrition: {str(e)}"
    """
    Enhanced Nutrition AI for children (0-5 years) with BMI, allergies, and medical conditions
    """
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=self.api_key)
    
    def generate_patient_meal_plan(
        self,
        patient_id: str,
        duration_days: int = 7,
        parent_recipes: List[str] = None
    ) -> str:
        """Generate meal plan specifically for a patient based on their profile"""
        # Get patient data
        patient_data = data_manager.get_patient_by_id(patient_id)
        if not patient_data:
            return "Error: Patient data not found"
        # Get knowledge base for Filipino nutrition guidelines
        knowledge_base = data_manager.get_knowledge_base()
        filipino_foods = knowledge_base.get('filipino_foods', {})
        # Prepare parent recipes context
        parent_recipes_context = ""
        if parent_recipes:
            parent_recipes_context = f"\n\nParent Recipes to Consider:\n" + "\n".join(parent_recipes)
        # Build Filipino foods context
        filipino_context = ""
        if filipino_foods:
            filipino_recipes = []
            for recipe in filipino_foods.values():
                filipino_recipes.append(f"- {recipe['name']}: {recipe['nutrition_facts']}")
            filipino_context = f"\n\nFilipino Food Options:\n" + "\n".join(filipino_recipes)
        try:
            prompt = f"""You are a pediatric nutrition expert specializing in Filipino children's nutrition (ages 0-5). 

Create a {duration_days}-day meal plan for this patient:

PATIENT PROFILE:
- Age: {patient_data.get('age', 'Unknown')} years old
- BMI: {patient_data.get('bmi', 'Unknown')}
- BMI Category: {patient_data.get('bmi_category', 'Unknown')}
- Allergies: {patient_data.get('allergies', 'None')}
- Medical Conditions: {patient_data.get('medical_conditions', 'None')}
- Current Weight: {patient_data.get('weight', 'Unknown')} kg
- Current Height: {patient_data.get('height', 'Unknown')} cm

GUIDELINES:
1. Follow WHO nutrition guidelines for children 0-5 years
2. Consider Filipino dietary patterns and available foods
3. Account for BMI category - adjust portions and food types accordingly
4. Strictly avoid allergens mentioned above
5. Consider medical conditions in food recommendations
6. Provide age-appropriate textures and portions
7. Include traditional Filipino foods when appropriate
8. Focus on balanced nutrition for growing children

{parent_recipes_context}
{filipino_context}

MEAL PLAN FORMAT:
For each day, provide:
- Breakfast (with portion size appropriate for age)
- Mid-morning snack
- Lunch (with portion size)
- Afternoon snack  
- Dinner (with portion size)
- Before-bed snack (if appropriate for age)

Include:
- Specific portion sizes for the patient's age and BMI
- Filipino-friendly ingredients and cooking methods
- Nutritional benefits of each meal
- Any special preparation notes for the patient's conditions
- Alternative options if patient refuses certain foods

SAFETY NOTES:
- Highlight any foods to avoid due to allergies/conditions
- Note appropriate textures for the patient's age
- Include hydration recommendations


Keep recommendations practical for Filipino parents."""

            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {"role": "system", "content": "You are a pediatric nutrition expert focused on Filipino children's health and development. All nutrient values provided are based on 100 g of edible portion."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error generating meal plan: {str(e)}"
    

if __name__ == "__main__":

    try:
        nutrition_ai = ChildNutritionAI()
        print("✅ Child Nutrition AI initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure GROQ_API_KEY is set in .env file")
