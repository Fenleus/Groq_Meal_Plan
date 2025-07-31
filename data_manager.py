
from db import get_connection
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

class DataManager:
    """
    Manages MySQL-based data storage for the nutrition system
    """
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor(dictionary=True)
    # Parents Data Management

    def get_parents_data(self) -> Dict:
        """Get all parents data from MySQL"""
        self.cursor.execute("SELECT * FROM parents")
        rows = self.cursor.fetchall()
        return {str(row['id']): row for row in rows}


    def get_parent_by_id(self, parent_id: str) -> Optional[Dict]:
        """Get specific parent data from MySQL"""
        self.cursor.execute("SELECT * FROM parents WHERE id = %s", (parent_id,))
        row = self.cursor.fetchone()
        return row


    def get_religion_by_parent(self, parent_id: str) -> Optional[str]:
        parent = self.get_parent_by_id(parent_id)
        if parent:
            return parent.get('religion')
        return None
    
    # All other methods should be refactored to use MySQL instead of JSON
    
    # Children Data Management
    def get_children_data(self) -> Dict:
        """Get all children data from MySQL (patients table)"""
        self.cursor.execute("SELECT * FROM patients")
        rows = self.cursor.fetchall()
        return {str(row['id']): row for row in rows}

    def get_children_by_parent(self, parent_id: str) -> List[Dict]:
        """Get all children for a specific parent from MySQL"""
        self.cursor.execute("SELECT * FROM patients WHERE parent_id = %s", (parent_id,))
        return self.cursor.fetchall()

    def get_children_ids_by_parent(self, parent_id: str) -> List[str]:
        """Get all children IDs for a specific parent from MySQL"""
        self.cursor.execute("SELECT id FROM patients WHERE parent_id = %s", (parent_id,))
        rows = self.cursor.fetchall()
        return [str(row['id']) for row in rows]

    def get_child_by_id(self, child_id: str) -> Optional[Dict]:
        """Get specific child data from MySQL"""
        self.cursor.execute("SELECT * FROM patients WHERE id = %s", (child_id,))
        row = self.cursor.fetchone()
        return row
    
    # Meal Plans Management
    def get_meal_plans(self) -> Dict:
        """Get all meal plans from MySQL"""
        self.cursor.execute("SELECT * FROM meal_plans")
        rows = self.cursor.fetchall()
        return {str(row['plan_id']): row for row in rows}

    def save_meal_plan(self, child_id: str, meal_plan: str, duration_days: int, parent_id: str) -> str:
        """Save a new meal plan to MySQL"""
        sql = """
            INSERT INTO meal_plans (patient_id, plan_details, created_at)
            VALUES (%s, %s, %s)
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (child_id, meal_plan, now))
        self.conn.commit()
        return str(self.cursor.lastrowid)

    def get_meal_plans_by_child(self, child_id: str, months_back: int = 6) -> List[Dict]:
        """Get meal plans for a child within the last X months from MySQL"""
        cutoff_date = (datetime.now() - timedelta(days=months_back * 30)).strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(
            "SELECT * FROM meal_plans WHERE patient_id = %s AND created_at >= %s ORDER BY created_at DESC",
            (child_id, cutoff_date)
        )
        return self.cursor.fetchall()

    def get_meal_plans_by_parent(self, parent_id: str) -> List[Dict]:
        """Get all recent meal plans for a parent's children from MySQL"""
        self.cursor.execute("SELECT * FROM meal_plans WHERE patient_id IN (SELECT id FROM patients WHERE parent_id = %s) ORDER BY created_at DESC", (parent_id,))
        return self.cursor.fetchall()
    
    # Parent Recipes Management
    def get_parent_recipes(self) -> Dict:
        """Get all parent recipes from MySQL"""
        self.cursor.execute("SELECT * FROM parent_recipes")
        rows = self.cursor.fetchall()
        return {str(row['id']): row for row in rows}

    def save_parent_recipe(self, parent_id: str, recipe_name: str, recipe_description: str) -> str:
        """Save a parent recipe to MySQL"""
        sql = """
            INSERT INTO parent_recipes (parent_id, name, description, created_at)
            VALUES (%s, %s, %s, %s)
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (parent_id, recipe_name, recipe_description, now))
        self.conn.commit()
        return str(self.cursor.lastrowid)

    def get_recipes_by_parent(self, parent_id: str) -> List[Dict]:
        """Get recipes uploaded by a parent from MySQL"""
        self.cursor.execute("SELECT * FROM parent_recipes WHERE parent_id = %s", (parent_id,))
        return self.cursor.fetchall()
    
    # Nutritionist Notes Management
    def get_nutritionist_notes(self) -> Dict:
        """Get all nutritionist notes from MySQL"""
        self.cursor.execute("SELECT * FROM nutritionist_notes")
        rows = self.cursor.fetchall()
        return {str(row['note_id']): row for row in rows}

    def save_nutritionist_note(self, meal_plan_id: str, nutritionist_id: str, note: str) -> str:
        """Save a nutritionist note for a meal plan to MySQL"""
        sql = """
            INSERT INTO nutritionist_notes (meal_plan_id, nutritionist_id, note, created_at)
            VALUES (%s, %s, %s, %s)
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (meal_plan_id, nutritionist_id, note, now))
        self.conn.commit()
        return str(self.cursor.lastrowid)

    def get_notes_for_meal_plan(self, meal_plan_id: str) -> List[Dict]:
        """Get all notes for a specific meal plan from MySQL"""
        self.cursor.execute("SELECT * FROM nutritionist_notes WHERE meal_plan_id = %s", (meal_plan_id,))
        return self.cursor.fetchall()
    
    # Knowledge Base Management
    def get_knowledge_base(self) -> Dict:
        """Get nutrition knowledge base from MySQL (example: just return all rows from knowledge_base table)"""
        self.cursor.execute("SELECT * FROM knowledge_base")
        rows = self.cursor.fetchall()
        return {str(row['kb_id']): row for row in rows}

    def save_knowledge_base(self, pdf_memories, uploaded_pdfs):
        """Save updated knowledge base to MySQL"""
        sql = "INSERT INTO knowledge_base (pdf_memories, uploaded_pdfs, created_at) VALUES (%s, %s, %s)"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (pdf_memories, uploaded_pdfs, now))
        self.conn.commit()
        return str(self.cursor.lastrowid)

    def add_filipino_recipe(self, nutritionist_id: str, recipe_name: str, ingredients: str, 
                           nutrition_facts: str, instructions: str) -> str:
        """Add a Filipino recipe to knowledge base (example: insert into a filipino_recipes table)"""
        sql = """
            INSERT INTO filipino_recipes (name, ingredients, nutrition_facts, instructions, added_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (recipe_name, ingredients, nutrition_facts, instructions, nutritionist_id, now))
        self.conn.commit()
        return str(self.cursor.lastrowid)

# Initialize global data manager
data_manager = DataManager()
