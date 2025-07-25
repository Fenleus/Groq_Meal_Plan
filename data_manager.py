import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

class DataManager:
    """
    Manages JSON-based data storage for the nutrition system
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.ensure_data_directory()
        self.ensure_data_files()
    
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def ensure_data_files(self):
        """Create JSON files with initial structure if they don't exist"""
        files = {
            'children.json': {},
            'parents.json': {},
            'meal_plans.json': {},
            'nutritionist_notes.json': {},
            'admin_logs.json': [],
            "foods_info.json": {},
            'knowledge_base.json': {
                "nutrition_guidelines": {},
                "uploaded_pdfs": []
            }
        }
        for filename, initial_data in files.items():
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                self.save_json(filepath, initial_data)
    # Parents Data Management
    def get_parents_data(self) -> Dict:
        """Get all parents data"""
        return self.load_json(os.path.join(self.data_dir, 'parents.json'))

    def get_parent_by_id(self, parent_id: str) -> Optional[Dict]:
        """Get specific parent data"""
        parents = self.get_parents_data()
        return parents.get(parent_id)

    def get_religion_by_parent(self, parent_id: str) -> Optional[str]:
        parent = self.get_parent_by_id(parent_id)
        if parent:
            return parent.get('religion')
        return None
    
    def load_json(self, filepath: str) -> Dict:
        """Load JSON data from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_json(self, filepath: str, data: Dict):
        """Save data to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Children Data Management
    def get_children_data(self) -> Dict:
        """Get all children data"""
        return self.load_json(os.path.join(self.data_dir, 'children.json'))
    
    def get_children_by_parent(self, parent_id: str) -> List[Dict]:
        """Get all children for a specific parent"""
        all_children = self.get_children_data()
        return [child for child in all_children.values() if child.get('parent_id') == parent_id]

    def get_children_ids_by_parent(self, parent_id: str) -> List[str]:
        """Get all children IDs for a specific parent"""
        parent = self.get_parent_by_id(parent_id)
        if parent:
            return [child['id'] for child in parent.get('children', [])]
        return []
    
    def get_child_by_id(self, child_id: str) -> Optional[Dict]:
        """Get specific child data"""
        children = self.get_children_data()
        return children.get(child_id)
    
    # Meal Plans Management
    def get_meal_plans(self) -> Dict:
        """Get all meal plans"""
        return self.load_json(os.path.join(self.data_dir, 'meal_plans.json'))
    
    def save_meal_plan(self, child_id: str, meal_plan: str, duration_days: int, parent_id: str) -> str:
        """Save a new meal plan"""
        meal_plans = self.get_meal_plans()
        
        plan_id = str(uuid.uuid4())
        plan_data = {
            'id': plan_id,
            'child_id': child_id,
            'parent_id': parent_id,
            'meal_plan': meal_plan,
            'duration_days': duration_days,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        meal_plans[plan_id] = plan_data
        self.save_json(os.path.join(self.data_dir, 'meal_plans.json'), meal_plans)
        return plan_id
    
    def get_meal_plans_by_child(self, child_id: str, months_back: int = 6) -> List[Dict]:
        """Get meal plans for a child within the last X months"""
        meal_plans = self.get_meal_plans()
        cutoff_date = datetime.now() - timedelta(days=months_back * 30)
        
        child_plans = []
        for plan in meal_plans.values():
            if plan.get('child_id') == child_id:
                plan_date = datetime.fromisoformat(plan['created_at'])
                if plan_date >= cutoff_date:
                    child_plans.append(plan)
        
        return sorted(child_plans, key=lambda x: x['created_at'], reverse=True)
    
    def get_meal_plans_by_parent(self, parent_id: str) -> List[Dict]:
        """Get all recent meal plans for a parent's children"""
        meal_plans = self.get_meal_plans()
        parent_plans = []
        
        for plan in meal_plans.values():
            if plan.get('parent_id') == parent_id:
                parent_plans.append(plan)
        
        return sorted(parent_plans, key=lambda x: x['created_at'], reverse=True)
    
    # Family Recipes Management
    def get_family_recipes(self) -> Dict:
        """Get all family recipes"""
        return self.load_json(os.path.join(self.data_dir, 'family_recipes.json'))
    
    def save_family_recipe(self, parent_id: str, recipe_name: str, recipe_description: str) -> str:
        """Save a family recipe"""
        recipes = self.get_family_recipes()
        
        recipe_id = str(uuid.uuid4())
        recipe_data = {
            'id': recipe_id,
            'parent_id': parent_id,
            'name': recipe_name,
            'description': recipe_description,
            'created_at': datetime.now().isoformat()
        }
        
        recipes[recipe_id] = recipe_data
        self.save_json(os.path.join(self.data_dir, 'family_recipes.json'), recipes)
        return recipe_id
    
    def get_recipes_by_parent(self, parent_id: str) -> List[Dict]:
        """Get recipes uploaded by a parent"""
        recipes = self.get_family_recipes()
        return [recipe for recipe in recipes.values() if recipe.get('parent_id') == parent_id]
    
    # Nutritionist Notes Management
    def get_nutritionist_notes(self) -> Dict:
        """Get all nutritionist notes"""
        return self.load_json(os.path.join(self.data_dir, 'nutritionist_notes.json'))
    
    def save_nutritionist_note(self, meal_plan_id: str, nutritionist_id: str, note: str) -> str:
        """Save a nutritionist note for a meal plan"""
        notes = self.get_nutritionist_notes()
        
        note_id = str(uuid.uuid4())
        note_data = {
            'id': note_id,
            'meal_plan_id': meal_plan_id,
            'nutritionist_id': nutritionist_id,
            'note': note,
            'created_at': datetime.now().isoformat()
        }
        
        notes[note_id] = note_data
        self.save_json(os.path.join(self.data_dir, 'nutritionist_notes.json'), notes)
        return note_id
    
    def get_notes_for_meal_plan(self, meal_plan_id: str) -> List[Dict]:
        """Get all notes for a specific meal plan"""
        notes = self.get_nutritionist_notes()
        return [note for note in notes.values() if note.get('meal_plan_id') == meal_plan_id]
    
    # Knowledge Base Management
    def get_knowledge_base(self) -> Dict:
        """Get nutrition knowledge base"""
        return self.load_json(os.path.join(self.data_dir, 'knowledge_base.json'))
    
    def save_knowledge_base(self, knowledge_data: Dict):
        """Save updated knowledge base"""
        self.save_json(os.path.join(self.data_dir, 'knowledge_base.json'), knowledge_data)
    
    def add_filipino_recipe(self, nutritionist_id: str, recipe_name: str, ingredients: str, 
                           nutrition_facts: str, instructions: str) -> str:
        """Add a Filipino recipe to knowledge base"""
        knowledge = self.get_knowledge_base()
        
        recipe_id = str(uuid.uuid4())
        recipe_data = {
            'id': recipe_id,
            'name': recipe_name,
            'ingredients': ingredients,
            'nutrition_facts': nutrition_facts,
            'instructions': instructions,
            'added_by': nutritionist_id,
            'created_at': datetime.now().isoformat()
        }
        
        if 'filipino_foods' not in knowledge:
            knowledge['filipino_foods'] = {}
        
        knowledge['filipino_foods'][recipe_id] = recipe_data
        self.save_knowledge_base(knowledge)
        return recipe_id

# Initialize global data manager
data_manager = DataManager()
