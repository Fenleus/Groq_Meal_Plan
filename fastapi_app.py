
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from nutrition_ai import ChildNutritionAI
from data_manager import data_manager
from nutrition_chain import get_meal_plan_with_langchain
from typing import List, Optional

app = FastAPI(title="Nutritionist LLM API", description="API for LLM-powered nutrition functions", version="1.0")

# Instantiate the AI model
nutrition_ai = ChildNutritionAI()



class MealPlanRequest(BaseModel):
    patient_id: int
    available_foods: Optional[str] = None

class NutritionQuestionRequest(BaseModel):
    question: str

class FoodNutritionRequest(BaseModel):
    food_id: str

class ChildrenByParentRequest(BaseModel):

    parent_id: int


class SaveMealPlanRequest(BaseModel):
    patient_id: int
    meal_plan: str
    duration_days: int
    parent_id: int

class MealPlansByChildRequest(BaseModel):
    patient_id: int
    months_back: int = 6

class SaveAdminLogRequest(BaseModel):
    action: str
    details: dict




@app.post("/generate_meal_plan")
def generate_meal_plan(request: MealPlanRequest):
    """Generate a meal plan for a patient using LangChain prompt template, using nutrition analysis for guidance, but only return the meal plan."""
    try:
        # Fetch patient data for context
        patient_data = data_manager.get_patient_by_id(request.patient_id)
        if not patient_data:
            raise HTTPException(status_code=404, detail="Patient not found")
        # Extract all relevant info from patient and parent
        name = patient_data.get('first_name', '') + ' ' + patient_data.get('last_name', '')
        age_in_months = patient_data.get('age_in_months')
        bmi = patient_data.get('bmi')
        allergies = patient_data.get('allergies')
        medical_conditions = patient_data.get('medical_conditions')
        parent_id = patient_data.get('parent_id')
        religion = data_manager.get_religion_by_parent(parent_id) if parent_id else None

        # Nutrition analysis (LLM) for internal use only
        if name and age_in_months is not None:
            _ = nutrition_ai.analyze_child_nutrition(
                name=name,
                age_in_months=age_in_months,
                bmi=bmi,
                allergies=allergies,
                medical_conditions=medical_conditions,
                parent_id=parent_id
            )
        # Generate meal plan (LangChain) with all context
        meal_plan = get_meal_plan_with_langchain(
            patient_id=request.patient_id,
            available_ingredients=request.available_foods
        )
        return {
            "meal_plan": meal_plan
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get_foods_data")
def get_foods_data():
    try:
        foods = data_manager.get_foods_data()
        return {"foods": foods}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_food_nutrition")
def get_food_nutrition(request: FoodNutritionRequest):
    try:
        nutrition = data_manager.get_food_nutrition(request.food_id)
        return {"nutrition": nutrition}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_children_by_parent")
def get_children_by_parent(request: ChildrenByParentRequest):
    try:
        children = data_manager.get_children_by_parent(request.parent_id)
        return {"children": children}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_meal_plan")
def save_meal_plan(request: SaveMealPlanRequest):
    try:
        plan_id = data_manager.save_meal_plan(
            patient_id=request.patient_id,
            meal_plan=request.meal_plan,
            duration_days=request.duration_days,
            parent_id=request.parent_id
        )
        return {"plan_id": plan_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_meal_plans_by_child")
def get_meal_plans_by_child(request: MealPlansByChildRequest):
    try:
        plans = data_manager.get_meal_plans_by_patient(request.patient_id, months_back=request.months_back)
        return {"meal_plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_admin_log")
def save_admin_log(request: SaveAdminLogRequest):
    try:
        data_manager.save_admin_log(request.action, request.details)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_admin_logs")
def get_admin_logs():
    try:
        logs = data_manager.get_admin_logs()
        return {"admin_logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
