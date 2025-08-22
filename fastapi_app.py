
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from nutrition_ai import ChildNutritionAI
from data_manager import data_manager
from nutrition_chain import get_meal_plan_with_langchain, generate_patient_assessment
from typing import List, Optional


app = FastAPI(title="Nutritionist LLM API", description="API for LLM-powered nutrition functions", version="1.0")
nutrition_ai = ChildNutritionAI()

class MealPlanRequest(BaseModel):
    patient_id: int
    available_foods: Optional[str] = None

class NutritionQuestionRequest(BaseModel):
    question: str

class ChildrenByParentRequest(BaseModel):
    parent_id: int

class SaveMealPlanRequest(BaseModel):
    patient_id: int
    meal_plan: str
    duration_days: int
    parent_id: int

class MealPlansByChildRequest(BaseModel):
    patient_id: int
    most_recent: Optional[bool] = False

class SaveAdminLogRequest(BaseModel):
    action: str
    details: dict

class AssessmentRequest(BaseModel):
    patient_id: int

@app.post("/generate_meal_plan")
def generate_meal_plan(request: MealPlanRequest):
    """Generate a meal plan for a patient using LangChain prompt template, using nutrition analysis for guidance, but only return the meal plan."""
    try:
        # Fetch patient data for context
        patient_data = data_manager.get_patient_by_id(request.patient_id)
        if not patient_data:
            raise HTTPException(status_code=404, detail="Patient not found")
        # Extract all relevant info from patient and parent
        name = data_manager.format_full_name(
            patient_data.get('first_name', ''),
            patient_data.get('middle_name', ''),
            patient_data.get('last_name', '')
        )
        age_months = patient_data.get('age_months')
        weight_kg = patient_data.get('weight_kg')
        height_cm = patient_data.get('height_cm')
        other_medical_problems = patient_data.get('other_medical_problems')
        parent_id = patient_data.get('parent_id')
        religion = data_manager.get_religion_by_parent(parent_id) if parent_id else None

        # Nutrition analysis (LLM) for internal use only
        if name and age_months is not None:
            _ = nutrition_ai.analyze_child_nutrition(
                name=name,
                age_in_months=age_months,
                weight_kg=weight_kg,
                height_cm=height_cm,
                other_medical_problems=other_medical_problems,
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

@app.post("/assessment")
def generate_assessment(request: AssessmentRequest):
    """Generate a comprehensive pediatric dietary assessment for a patient."""
    try:
        # Fetch patient data
        patient_data = data_manager.get_patient_by_id(request.patient_id)
        if not patient_data:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Generate assessment using LangChain
        assessment = generate_patient_assessment(patient_id=request.patient_id)
        
        return {
            "patient_id": request.patient_id,
            "assessment": assessment
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Combined endpoint: returns all foods
@app.post("/get_foods_data")
def get_foods_data():
    try:
        foods = data_manager.get_foods_data()
        return {"foods": foods}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_children_by_parent")
def get_children_by_parent(request: ChildrenByParentRequest):
    try:
        children = data_manager.get_children_by_parent(request.parent_id)
        return {"children": children}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_meal_plans_by_child")
def get_meal_plans_by_child(request: MealPlansByChildRequest):
    try:
        plans = data_manager.get_meal_plans_by_patient(request.patient_id)
        if request.most_recent:
            # Return only the most recent plan (if any)
            if plans:
                return {"meal_plans": [plans[0]]}
            else:
                return {"meal_plans": []}
        return {"meal_plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class KnowledgeBaseRequest(BaseModel):
    pass  # No parameters needed for get_knowledge_base

@app.post("/get_knowledge_base")
def get_knowledge_base(request: KnowledgeBaseRequest):
    try:
        kb = data_manager.get_knowledge_base()
        return {"knowledge_base": kb}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MealPlanDetailRequest(BaseModel):
    plan_id: int

@app.post("/get_meal_plan_detail")
def get_meal_plan_detail(request: MealPlanDetailRequest):
    try:
        plan = data_manager.get_meal_plan_by_id(request.plan_id)
        return {"meal_plan": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))