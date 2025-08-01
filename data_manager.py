
from db import get_connection
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

class DataManager:
    # Admin Logs Management
    def save_admin_log(self, action: str, details):
        """Insert a new admin log into the admin_logs table."""
        import json
        sql = "INSERT INTO admin_logs (timestamp, action, details) VALUES (%s, %s, %s)"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (now, action, json.dumps(details)))
        self.conn.commit()

    def get_admin_logs(self):
        """Fetch all admin logs from the admin_logs table."""
        self.cursor.execute("SELECT log_id, timestamp, action, details FROM admin_logs ORDER BY timestamp DESC")
        rows = self.cursor.fetchall()
        import json
        for row in rows:
            if isinstance(row.get('details'), str):
                try:
                    row['details'] = json.loads(row['details'])
                except Exception:
                    pass
        return rows
    # Food Database Management
    def get_foods_data(self):
        """Get all foods from the foods table, with basic info."""
        self.cursor.execute("SELECT food_id, food_name_and_description, scientific_name, alternate_common_names, edible_portion FROM foods")
        rows = self.cursor.fetchall()

        for row in rows:
            if isinstance(row.get('alternate_common_names'), (list, tuple)):
                row['alternate_common_names'] = ', '.join(row['alternate_common_names'])
        return rows

    def get_food_nutrition(self, food_id):
        """Get all nutrition facts for a food from all related tables."""
        nutrition = {}
        # Proximates
        self.cursor.execute("SELECT water_g, energy_kcal, protein_g, total_fat_g, carbohydrate_total_g, ash_g FROM proximates WHERE food_id = %s", (food_id,))
        row = self.cursor.fetchone()
        if row:
            nutrition['proximates'] = row
        # Other Carbohydrates
        self.cursor.execute("SELECT fiber_total_dietary_g, sugars_total_g FROM other_carbohydrates WHERE food_id = %s", (food_id,))
        row = self.cursor.fetchone()
        if row:
            nutrition['other_carbohydrates'] = row
        # Minerals
        self.cursor.execute("SELECT calcium_mg, phosphorus_mg, iron_mg, sodium_mg FROM minerals WHERE food_id = %s", (food_id,))
        row = self.cursor.fetchone()
        if row:
            nutrition['minerals'] = row
        # Vitamins
        self.cursor.execute("SELECT retinol_vitamin_a_ug, beta_carotene_ug, retinol_activity_equivalent_rae_ug, thiamin_vitamin_b1_mg, riboflavin_vitamin_b2_mg, niacin_mg, niacin_from_tryptophan_mg, ascorbic_acid_vitamin_c_mg FROM vitamins WHERE food_id = %s", (food_id,))
        row = self.cursor.fetchone()
        if row:
            nutrition['vitamins'] = row
        # Lipids
        self.cursor.execute("SELECT fatty_acids_saturated_total_g, fatty_acids_monounsaturated_total_g, fatty_acids_polyunsaturated_total_g, cholesterol_mg FROM lipids WHERE food_id = %s", (food_id,))
        row = self.cursor.fetchone()
        if row:
            nutrition['lipids'] = row
        return nutrition
    """
    Manages MySQL-based data storage for the nutrition system
    """
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor(dictionary=True)

    # Parents Data Management

    def get_parents_data(self) -> Dict:
        """Get all parents data from MySQL, including all columns as per schema."""
        self.cursor.execute("SELECT parent_id, full_name, contact_number, barangay, religion, created_at, updated_at FROM parents")
        rows = self.cursor.fetchall()
        return {str(row['parent_id']): row for row in rows}


    def get_parent_by_id(self, parent_id: str) -> Optional[Dict]:
        """Get specific parent data from MySQL, all columns."""
        self.cursor.execute("SELECT parent_id, full_name, contact_number, barangay, religion, created_at, updated_at FROM parents WHERE parent_id = %s", (parent_id,))
        row = self.cursor.fetchone()
        return row

    def get_religion_by_parent(self, parent_id: str) -> Optional[str]:
        parent = self.get_parent_by_id(parent_id)
        if parent:
            return parent.get('religion')
        return None

    # Children Data Management

    def get_children_data(self) -> Dict:
        """Get all children data from MySQL (patients table), all columns."""
        self.cursor.execute("SELECT patient_id, first_name, last_name, date_of_birth, age_in_months, gender, bmi, bmi_category, allergies, medical_conditions, address, contact_number, created_at, updated_at, parent_id FROM patients")
        rows = self.cursor.fetchall()
        return {str(row['patient_id']): row for row in rows}


    def get_children_by_parent(self, parent_id: str) -> List[Dict]:
        """Get all children for a specific parent from MySQL, all columns."""
        self.cursor.execute("SELECT patient_id, first_name, last_name, date_of_birth, age_in_months, gender, bmi, bmi_category, allergies, medical_conditions, address, contact_number, created_at, updated_at, parent_id FROM patients WHERE parent_id = %s", (parent_id,))
        return self.cursor.fetchall()


    def get_children_ids_by_parent(self, parent_id: str) -> List[str]:
        """Get all children IDs for a specific parent from MySQL"""
        self.cursor.execute("SELECT patient_id FROM patients WHERE parent_id = %s", (parent_id,))
        rows = self.cursor.fetchall()
        return [str(row['patient_id']) for row in rows]


    def get_patient_by_id(self, patient_id: str) -> Optional[Dict]:
        """Get specific patient data from MySQL, all columns."""
        self.cursor.execute("SELECT patient_id, first_name, last_name, date_of_birth, age_in_months, gender, bmi, bmi_category, allergies, medical_conditions, address, contact_number, created_at, updated_at, parent_id FROM patients WHERE patient_id = %s", (patient_id,))
        row = self.cursor.fetchone()
        return row

    # Meal Plans Management
    def get_meal_plans(self) -> Dict:
        """Get all meal plans from MySQL, all columns."""
        self.cursor.execute("SELECT plan_id, patient_id, plan_details, created_at FROM meal_plans")
        rows = self.cursor.fetchall()
        return {str(row['plan_id']): row for row in rows}

    def save_meal_plan(self, patient_id: str, meal_plan: str, duration_days: int, parent_id: str) -> str:
        """Save a new meal plan to MySQL"""
        sql = """
            INSERT INTO meal_plans (patient_id, plan_details, created_at)
            VALUES (%s, %s, %s)
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (patient_id, meal_plan, now))
        self.conn.commit()
        return str(self.cursor.lastrowid)

    def get_meal_plans_by_patient(self, patient_id: str, months_back: int = 6) -> List[Dict]:
        """Get meal plans for a patient within the last X months from MySQL, all columns."""
        cutoff_date = (datetime.now() - timedelta(days=months_back * 30)).strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(
            "SELECT plan_id, patient_id, plan_details, created_at FROM meal_plans WHERE patient_id = %s AND created_at >= %s ORDER BY created_at DESC",
            (patient_id, cutoff_date)
        )
        return self.cursor.fetchall()

    def get_meal_plans_by_parent(self, parent_id: str) -> List[Dict]:
        """Get all recent meal plans for a parent's children from MySQL, all columns."""
        self.cursor.execute("SELECT plan_id, patient_id, plan_details, created_at FROM meal_plans WHERE patient_id IN (SELECT id FROM patients WHERE parent_id = %s) ORDER BY created_at DESC", (parent_id,))
        return self.cursor.fetchall()

    # Parent Recipes Management

    def get_parent_recipes(self) -> Dict:
        self.cursor.execute("SELECT id, parent_id, name, description, created_at FROM parent_recipes")
        rows = self.cursor.fetchall()
        return {str(row['id']): row for row in rows}

    def save_parent_recipe(self, parent_id: str, recipe_name: str, recipe_description: str) -> str:
        sql = """
            INSERT INTO parent_recipes (parent_id, name, description, created_at)
            VALUES (%s, %s, %s, %s)
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (parent_id, recipe_name, recipe_description, now))
        self.conn.commit()
        return str(self.cursor.lastrowid)

    def get_recipes_by_parent(self, parent_id: str) -> List[Dict]:
        self.cursor.execute("SELECT id, parent_id, name, description, created_at FROM parent_recipes WHERE parent_id = %s", (parent_id,))
        return self.cursor.fetchall()

    # Nutritionist Notes Management
    def get_nutritionist_notes(self) -> Dict:
        self.cursor.execute("SELECT note_id, nutritionist_id, patient_id, note, created_at FROM nutritionist_notes")
        rows = self.cursor.fetchall()
        return {str(row['note_id']): row for row in rows}

    def save_nutritionist_note(self, meal_plan_id: str, nutritionist_id: str, note: str) -> str:
        sql = """
            INSERT INTO nutritionist_notes (meal_plan_id, nutritionist_id, note, created_at)
            VALUES (%s, %s, %s, %s)
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (meal_plan_id, nutritionist_id, note, now))
        self.conn.commit()
        return str(self.cursor.lastrowid)

    def get_notes_for_meal_plan(self, meal_plan_id: str) -> List[Dict]:
        self.cursor.execute("SELECT note_id, nutritionist_id, patient_id, note, created_at FROM nutritionist_notes WHERE meal_plan_id = %s", (meal_plan_id,))
        return self.cursor.fetchall()

    # Knowledge Base Management
    def get_knowledge_base(self) -> Dict:
        self.cursor.execute("SELECT kb_id, pdf_memories, uploaded_pdfs, created_at FROM knowledge_base")
        rows = self.cursor.fetchall()
        return {str(row['kb_id']): row for row in rows}

    def save_knowledge_base(self, pdf_memories, uploaded_pdfs):
        sql = "INSERT INTO knowledge_base (pdf_memories, uploaded_pdfs, created_at) VALUES (%s, %s, %s)"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (pdf_memories, uploaded_pdfs, now))
        self.conn.commit()
        return str(self.cursor.lastrowid)

data_manager = DataManager()
