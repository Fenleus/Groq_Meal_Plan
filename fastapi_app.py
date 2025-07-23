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
    children = data_manager.get_children_by_parent(parent_id)
    return {"children": children}

@app.get("/child/{child_id}")
def get_child(child_id: str):
    child = data_manager.get_child_by_id(child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    return child

@app.post("/meal_plan/")
def generate_meal_plan(request: MealPlanRequest):
    result = get_meal_plan_with_langchain(
        request.child_id,
        request.available_ingredients,
        request.religion
    )
    return {"meal_plan": result}

@app.get("/meal_plans/child/{child_id}")
def get_meal_plans_by_child(child_id: str, months_back: int = Query(6, ge=1, le=24)):
    plans = data_manager.get_meal_plans_by_child(child_id, months_back)
    return {"meal_plans": plans}

@app.get("/meal_plans/parent/{parent_id}")
def get_meal_plans_by_parent(parent_id: str):
    plans = data_manager.get_meal_plans_by_parent(parent_id)
    return {"meal_plans": plans}

@app.post("/family_recipe/")
def add_family_recipe(request: FamilyRecipeRequest):
    recipe_id = data_manager.save_family_recipe(
        request.parent_id,
        request.recipe_name,
        request.recipe_description
    )
    return {"recipe_id": recipe_id}

@app.get("/family_recipes/{parent_id}")
def get_family_recipes(parent_id: str):
    recipes = data_manager.get_recipes_by_parent(parent_id)
    return {"recipes": recipes}

@app.post("/nutritionist_note/")
def add_nutritionist_note(request: NutritionistNoteRequest):
    note_id = data_manager.save_nutritionist_note(
        request.meal_plan_id,
        request.nutritionist_id,
        request.note
    )
    return {"note_id": note_id}

@app.get("/nutritionist_notes/{meal_plan_id}")
def get_nutritionist_notes(meal_plan_id: str):
    notes = data_manager.get_notes_for_meal_plan(meal_plan_id)
    return {"notes": notes}

@app.get("/knowledge_base/")
def get_knowledge_base():
    kb = data_manager.get_knowledge_base()
    return kb

@app.get("/")
def root():
    return {"message": "Family Nutrition Management API is running."}
