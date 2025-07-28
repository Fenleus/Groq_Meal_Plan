from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from nutrition_ai import ChildNutritionAI
from typing import List, Optional

app = FastAPI(title="Nutritionist LLM API", description="API for LLM-powered nutrition functions", version="1.0")

# Instantiate the AI model
nutrition_ai = ChildNutritionAI()

class ChildNutritionRequest(BaseModel):
    name: str
    age_in_months: int
    bmi: Optional[float] = None
    allergies: Optional[str] = None
    medical_conditions: Optional[str] = None
    parent_id: Optional[str] = None

class MealPlanRequest(BaseModel):
    child_id: str
    preferences: Optional[List[str]] = None
    restrictions: Optional[List[str]] = None

class NutritionQuestionRequest(BaseModel):
    question: str

@app.post("/analyze_child_nutrition")
def analyze_child_nutrition(request: ChildNutritionRequest):
    """Analyze a child's nutrition using the LLM"""
    try:
        result = nutrition_ai.analyze_child_nutrition(
            name=request.name,
            age_in_months=request.age_in_months,
            bmi=request.bmi,
            allergies=request.allergies,
            medical_conditions=request.medical_conditions,
            parent_id=request.parent_id
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_meal_plan")
def generate_meal_plan(request: MealPlanRequest):
    """Generate a meal plan for a child"""
    try:
        result = nutrition_ai.generate_meal_plan(
            child_id=request.child_id,
            preferences=request.preferences,
            restrictions=request.restrictions
        )
        return {"meal_plan": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask_nutrition_question")
def ask_nutrition_question(request: NutritionQuestionRequest):
    """Ask a nutrition-related question to the LLM"""
    try:
        answer = nutrition_ai.answer_question(request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
