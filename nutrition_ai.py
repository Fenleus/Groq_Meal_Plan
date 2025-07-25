import os
from groq import Groq
from dotenv import load_dotenv
from data_manager import data_manager
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

class ChildNutritionAI:
    """
    Enhanced Nutrition AI for children (0-5 years) with BMI, allergies, and medical conditions
    """
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=self.api_key)
    
    def generate_child_meal_plan(
        self,
        child_id: str,
        duration_days: int = 7,
        parent_recipes: List[str] = None
    ) -> str:
        """Generate meal plan specifically for a child based on their profile"""
        
        # Get child data
        child_data = data_manager.get_child_by_id(child_id)
        if not child_data:
            return "Error: Child data not found"
        
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
            for recipe in list(filipino_foods.values())[:5]:  # Limit to 5 recipes
                filipino_recipes.append(f"- {recipe['name']}: {recipe['nutrition_facts']}")
            filipino_context = f"\n\nFilipino Food Options:\n" + "\n".join(filipino_recipes)
        
        try:
            prompt = f"""You are a pediatric nutrition expert specializing in Filipino children's nutrition (ages 0-5). 

Create a {duration_days}-day meal plan for this child:

CHILD PROFILE:
- Age: {child_data.get('age', 'Unknown')} years old
- BMI: {child_data.get('bmi', 'Unknown')}
- BMI Category: {child_data.get('bmi_category', 'Unknown')}
- Allergies: {child_data.get('allergies', 'None')}
- Medical Conditions: {child_data.get('medical_conditions', 'None')}
- Current Weight: {child_data.get('weight', 'Unknown')} kg
- Current Height: {child_data.get('height', 'Unknown')} cm

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
- Specific portion sizes for the child's age and BMI
- Filipino-friendly ingredients and cooking methods
- Nutritional benefits of each meal
- Any special preparation notes for the child's conditions
- Alternative options if child refuses certain foods

SAFETY NOTES:
- Highlight any foods to avoid due to allergies/conditions
- Note appropriate textures for the child's age
- Include hydration recommendations


Keep recommendations practical for Filipino parents."""

            response = self.client.chat.completions.create(
                model="llama-4-scout-17b-16e-instruct",
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
