from db import get_connection
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import json

class DataManager:
    def get_nutritionists(self) -> list:
        """Get all nutritionists from MySQL, all columns."""
        self.cursor.execute("SELECT user_id, role_id, first_name, middle_name, last_name, birth_date, sex, email, email_verified_at, password, contact_number, address, is_active, remember_token, license_number, years_experience, qualifications, professional_experience, professional_id_path, verification_status, rejection_reason, verified_at, verified_by, account_status, deleted_at, created_at, updated_at FROM users WHERE role_id = (SELECT role_id FROM roles WHERE role_name = 'nutritionist')")
        return self.cursor.fetchall()
    def get_meal_plan_by_id(self, plan_id: int) -> Optional[Dict]:
        """Get a single meal plan by its plan_id."""
        self.cursor.execute("SELECT plan_id, patient_id, plan_details, generated_at FROM meal_plans WHERE plan_id = %s", (plan_id,))
        return self.cursor.fetchone()

    def get_nutritionist_notes_by_patient(self, patient_id: int) -> List[Dict]:
        """Get all nutritionist notes for a given patient_id."""
        self.cursor.execute("SELECT note_id, nutritionist_id, patient_id, plan_id, note, created_at FROM nutritionist_notes WHERE patient_id = %s", (patient_id,))
        return self.cursor.fetchall()
    def update_food_nutrition(self, food_id, category, field, value):
        """Update a single nutrition fact for a food entry."""
        # Map category to table name
        table_map = {
            'proximates': 'proximates',
            'other_carbohydrates': 'other_carbohydrates',
            'minerals': 'minerals',
            'vitamins': 'vitamins',
            'lipids': 'lipids'
        }
        table = table_map.get(category)
        if not table:
            raise ValueError(f"Unknown nutrition category: {category}")
        # Compose SQL
        sql = f"UPDATE {table} SET {field} = %s WHERE food_id = %s"
        self.cursor.execute(sql, (value, food_id))
        self.conn.commit()
    # Admin Logs Management
    def save_admin_log(self, action: str, details):
        """Insert a new admin log into the audit_logs table."""
        sql = "INSERT INTO audit_logs (log_timestamp, action, description) VALUES (%s, %s, %s)"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (now, action, json.dumps(details)))
        self.conn.commit()

    def get_admin_logs(self):
        """Fetch all admin logs from the audit_logs table."""
        self.cursor.execute("SELECT log_id, log_timestamp, action, description FROM audit_logs ORDER BY log_timestamp DESC")
        rows = self.cursor.fetchall()
        for row in rows:
            if isinstance(row.get('description'), str):
                try:
                    row['description'] = json.loads(row['description'])
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

    def update_food(self, food_id, food_name_and_description, scientific_name, alternate_common_names, edible_portion):
        """Update a food entry in the foods table."""
        sql = """
            UPDATE foods
            SET food_name_and_description = %s,
                scientific_name = %s,
                alternate_common_names = %s,
                edible_portion = %s
            WHERE food_id = %s
        """
        self.cursor.execute(sql, (
            food_name_and_description,
            scientific_name,
            alternate_common_names,
            edible_portion,
            food_id
        ))
        self.conn.commit()
    """
    Manages MySQL-based data storage for the nutrition system
    """
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor(dictionary=True)

    def get_barangay_name(self, barangay_id: int) -> str:
        """Get barangay name by barangay_id."""
        try:
            self.cursor.execute("SELECT barangay_name FROM barangays WHERE barangay_id = %s", (barangay_id,))
            result = self.cursor.fetchone()
            return result['barangay_name'] if result else f"Barangay {barangay_id}"
        except Exception:
            return f"Barangay {barangay_id}"

    def get_all_barangays(self) -> Dict:
        """Get all barangays as a dictionary {barangay_id: barangay_name}."""
        try:
            self.cursor.execute("SELECT barangay_id, barangay_name FROM barangays ORDER BY barangay_name")
            rows = self.cursor.fetchall()
            return {row['barangay_id']: row['barangay_name'] for row in rows}
        except Exception:
            return {}

    @staticmethod
    def format_full_name(first_name: str = '', middle_name: str = '', last_name: str = '') -> str:
        """Format a full name properly, excluding empty/None middle names."""
        parts = []
        
        if first_name and first_name.strip():
            parts.append(first_name.strip())
        
        if middle_name and middle_name.strip() and middle_name.strip().lower() not in ['none', 'null', '']:
            parts.append(middle_name.strip())
        
        if last_name and last_name.strip():
            parts.append(last_name.strip())
        
        return ' '.join(parts)

    # Parents Data Management

    def get_parents_data(self) -> Dict:
        """Get all parents data from MySQL, including all columns as per schema."""
        self.cursor.execute("SELECT user_id, role_id, first_name, middle_name, last_name, birth_date, sex, email, email_verified_at, password, contact_number, address, is_active, remember_token, license_number, years_experience, qualifications, professional_experience, professional_id_path, verification_status, rejection_reason, verified_at, verified_by, account_status, deleted_at, created_at, updated_at FROM users WHERE role_id = (SELECT role_id FROM roles WHERE role_name = 'parent')")
        rows = self.cursor.fetchall()
        return {str(row['user_id']): row for row in rows}


    def get_parent_by_id(self, parent_id: str) -> Optional[Dict]:
        """Get specific parent data from MySQL, all columns."""
        self.cursor.execute("SELECT user_id, role_id, first_name, middle_name, last_name, birth_date, sex, email, email_verified_at, password, contact_number, address, is_active, remember_token, license_number, years_experience, qualifications, professional_experience, professional_id_path, verification_status, rejection_reason, verified_at, verified_by, account_status, deleted_at, created_at, updated_at FROM users WHERE user_id = %s AND role_id = (SELECT role_id FROM roles WHERE role_name = 'parent')", (parent_id,))
        row = self.cursor.fetchone()
        return row

    def get_religion_by_parent(self, parent_id: str) -> Optional[str]:
        parent = self.get_parent_by_id(parent_id)
        if parent:
            # Religion is not stored in users table, so return None for now
            return None
        return None

    # Children Data Management

    def get_children_data(self) -> Dict:
        """Get all children data from MySQL (patients table), all columns."""
        self.cursor.execute("SELECT patient_id, first_name, middle_name, last_name, barangay_id, contact_number, age_months, sex, date_of_admission, total_household_adults, total_household_children, total_household_twins, is_4ps_beneficiary, weight_kg, height_cm, weight_for_age, height_for_age, bmi_for_age, breastfeeding, allergies, religion, other_medical_problems, edema, created_at, updated_at, parent_id FROM patients")
        rows = self.cursor.fetchall()
        return {str(row['patient_id']): row for row in rows}


    def get_children_by_parent(self, parent_id: str) -> List[Dict]:
        """Get all children for a specific parent from MySQL, all columns."""
        self.cursor.execute("SELECT patient_id, first_name, middle_name, last_name, barangay_id, contact_number, age_months, sex, date_of_admission, total_household_adults, total_household_children, total_household_twins, is_4ps_beneficiary, weight_kg, height_cm, weight_for_age, height_for_age, bmi_for_age, breastfeeding, allergies, religion, other_medical_problems, edema, created_at, updated_at, parent_id FROM patients WHERE parent_id = %s", (parent_id,))
        return self.cursor.fetchall()


    def get_children_ids_by_parent(self, parent_id: str) -> List[str]:
        """Get all children IDs for a specific parent from MySQL"""
        self.cursor.execute("SELECT patient_id FROM patients WHERE parent_id = %s", (parent_id,))
        rows = self.cursor.fetchall()
        return [str(row['patient_id']) for row in rows]


    def get_patient_by_id(self, patient_id: str) -> Optional[Dict]:
        """Get specific patient data from MySQL, all columns."""
        self.cursor.execute("SELECT patient_id, first_name, middle_name, last_name, barangay_id, contact_number, age_months, sex, date_of_admission, total_household_adults, total_household_children, total_household_twins, is_4ps_beneficiary, weight_kg, height_cm, weight_for_age, height_for_age, bmi_for_age, breastfeeding, allergies, religion, other_medical_problems, edema, created_at, updated_at, parent_id FROM patients WHERE patient_id = %s", (patient_id,))
        row = self.cursor.fetchone()
        return row

    # Meal Plans Management
    def get_meal_plans(self) -> Dict:
        """Get all meal plans from MySQL, all columns."""
        self.cursor.execute("SELECT plan_id, patient_id, plan_details, generated_at FROM meal_plans")
        rows = self.cursor.fetchall()
        return {str(row['plan_id']): row for row in rows}

    def save_meal_plan(self, patient_id: str, meal_plan: str, duration_days: int, parent_id: str) -> str:
        """Save a new meal plan to MySQL"""
        sql = """
            INSERT INTO meal_plans (patient_id, plan_details, generated_at)
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
            "SELECT plan_id, patient_id, plan_details, generated_at FROM meal_plans WHERE patient_id = %s AND generated_at >= %s ORDER BY generated_at DESC",
            (patient_id, cutoff_date)
        )
        return self.cursor.fetchall()

    def get_meal_plans_by_parent(self, parent_id: str) -> List[Dict]:
        """Get all recent meal plans for a parent's children from MySQL, all columns."""
        self.cursor.execute("SELECT plan_id, patient_id, plan_details, generated_at FROM meal_plans WHERE patient_id IN (SELECT patient_id FROM patients WHERE parent_id = %s) ORDER BY generated_at DESC", (parent_id,))
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
        self.cursor.execute("SELECT note_id, nutritionist_id, patient_id, plan_id, note, created_at FROM nutritionist_notes")
        rows = self.cursor.fetchall()
        return {str(row['note_id']): row for row in rows}

    def save_nutritionist_note(self, plan_id: str, nutritionist_id: str, note: str) -> str:
        sql = """
            INSERT INTO nutritionist_notes (plan_id, nutritionist_id, note, created_at)
            VALUES (%s, %s, %s, %s)
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (plan_id, nutritionist_id, note, now))
        self.conn.commit()
        return str(self.cursor.lastrowid)

    def get_notes_for_meal_plan(self, plan_id: str) -> List[Dict]:
        self.cursor.execute("SELECT note_id, nutritionist_id, patient_id, plan_id, note, created_at FROM nutritionist_notes WHERE plan_id = %s", (plan_id,))
        return self.cursor.fetchall()

    # Knowledge Base Management
    def get_knowledge_base(self) -> Dict:
        self.cursor.execute("SELECT kb_id, ai_summary, pdf_name, pdf_text, uploaded_by, added_at, uploaded_by_id FROM knowledge_base")
        rows = self.cursor.fetchall()
        return {str(row['kb_id']): row for row in rows}

    def save_knowledge_base(self, ai_summary, pdf_name, pdf_text=None, uploaded_by=None, uploaded_by_id=None):
        sql = "INSERT INTO knowledge_base (ai_summary, pdf_name, pdf_text, uploaded_by, added_at, uploaded_by_id) VALUES (%s, %s, %s, %s, %s, %s)"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert ai_summary to plain text if it's a list
        if isinstance(ai_summary, list):
            ai_summary_text = "\n".join(ai_summary)
        else:
            ai_summary_text = str(ai_summary) if ai_summary else ""
            
        self.cursor.execute(sql, (
            ai_summary_text,
            pdf_name,
            pdf_text,
            uploaded_by,
            now,
            uploaded_by_id
        ))
        self.conn.commit()
        return str(self.cursor.lastrowid)

    def delete_knowledge_base_entry(self, kb_id):
        """Delete a knowledge base entry by its ID"""
        sql = "DELETE FROM knowledge_base WHERE kb_id = %s"
        self.cursor.execute(sql, (kb_id,))
        self.conn.commit()
        return True

data_manager = DataManager()
