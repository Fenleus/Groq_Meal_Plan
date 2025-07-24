from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from data_manager import data_manager
from nutrition_chain import get_meal_plan_with_langchain
import os

app = FastAPI()

# Allow CORS for local development (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models for POST requests ---
class MealPlanRequest(BaseModel):
    child_id: str
    available_ingredients: Optional[str] = ""
    religion: Optional[str] = ""

class FamilyRecipeRequest(BaseModel):
    parent_id: str
    recipe_name: str
    recipe_description: str

class NutritionistNoteRequest(BaseModel):
    meal_plan_id: str
    nutritionist_id: str
    note: str

# --- API Endpoints ---
@app.get("/children/{parent_id}")
def get_children(parent_id: str):
    try:
        children = data_manager.get_children_by_parent(parent_id)
        return {"children": children}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving children: {str(e)}")

@app.get("/child/{child_id}")
def get_child(child_id: str):
    try:
        child = data_manager.get_child_by_id(child_id)
        if not child:
            raise HTTPException(status_code=404, detail="Child not found")
        return child
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving child: {str(e)}")

@app.post("/meal_plan/")
def generate_meal_plan(request: MealPlanRequest):
    try:
        result = get_meal_plan_with_langchain(
            request.child_id,
            request.available_ingredients,
            request.religion
        )
        return {"meal_plan": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating meal plan: {str(e)}")

@app.get("/meal_plans/child/{child_id}")
def get_meal_plans_by_child(child_id: str, months_back: int = Query(6, ge=1, le=24)):
    try:
        plans = data_manager.get_meal_plans_by_child(child_id, months_back)
        return {"meal_plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving meal plans: {str(e)}")

@app.get("/meal_plans/parent/{parent_id}")
def get_meal_plans_by_parent(parent_id: str):
    try:
        plans = data_manager.get_meal_plans_by_parent(parent_id)
        return {"meal_plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving meal plans: {str(e)}")

@app.post("/family_recipe/")
def add_family_recipe(request: FamilyRecipeRequest):
    try:
        recipe_id = data_manager.save_family_recipe(
            request.parent_id,
            request.recipe_name,
            request.recipe_description
        )
        return {"recipe_id": recipe_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving family recipe: {str(e)}")

@app.get("/family_recipes/{parent_id}")
def get_family_recipes(parent_id: str):
    try:
        recipes = data_manager.get_recipes_by_parent(parent_id)
        return {"recipes": recipes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving family recipes: {str(e)}")

@app.post("/nutritionist_note/")
def add_nutritionist_note(request: NutritionistNoteRequest):
    try:
        note_id = data_manager.save_nutritionist_note(
            request.meal_plan_id,
            request.nutritionist_id,
            request.note
        )
        return {"note_id": note_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving nutritionist note: {str(e)}")

@app.get("/nutritionist_notes/{meal_plan_id}")
def get_nutritionist_notes(meal_plan_id: str):
    try:
        notes = data_manager.get_notes_for_meal_plan(meal_plan_id)
        return {"notes": notes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving nutritionist notes: {str(e)}")

@app.get("/knowledge_base/")
def get_knowledge_base():
    try:
        kb = data_manager.get_knowledge_base()
        return kb
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving knowledge base: {str(e)}")

@app.get("/")
def root():
    try:
        return {"message": "Family Nutrition Management API is running."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
