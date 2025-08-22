from db import get_connection
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import json

class DataManager:
    def update_food(self, food_id, food_data):
        """Update a food in the foods table with the allowed columns."""
        sql = """
            UPDATE foods SET
                food_name_and_description = %s,
                scientific_name = %s,
                alternate_common_names = %s,
                energy_kcal = %s,
                nutrition_tags = %s
            WHERE food_id = %s
        """
        params = (
            food_data.get('food_name_and_description', ''),
            food_data.get('scientific_name', ''),
            food_data.get('alternate_common_names', ''),
            food_data.get('energy_kcal', 0),
            food_data.get('nutrition_tags', ''),
            food_id
        )
        self.cursor.execute(sql, params)
        self.conn.commit()
    def get_foods_data(self):
        """Get all foods from the foods table, ordered by food_id."""
        self.cursor.execute("SELECT food_id, food_name_and_description, scientific_name, alternate_common_names, energy_kcal, nutrition_tags FROM foods ORDER BY food_id")
        return self.cursor.fetchall()

    def get_food_by_id(self, food_id):
        """Get a specific food by its ID."""
        self.cursor.execute("SELECT food_id, food_name_and_description, scientific_name, alternate_common_names, energy_kcal, nutrition_tags FROM foods WHERE food_id = %s", (food_id,))
        return self.cursor.fetchone()

    def search_foods(self, search_term=""):
        """Search foods by name, description, or tags."""
        conditions = []
        params = []
        if search_term:
            conditions.append("(food_name_and_description LIKE %s OR scientific_name LIKE %s OR alternate_common_names LIKE %s OR nutrition_tags LIKE %s)")
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"SELECT food_id, food_name_and_description, scientific_name, alternate_common_names, energy_kcal, nutrition_tags FROM foods {where_clause} ORDER BY food_name_and_description"
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()
    def get_nutritionists(self) -> list:
        """Get all nutritionists from MySQL, all columns."""
        self.cursor.execute("SELECT user_id, role_id, first_name, middle_name, last_name, birth_date, sex, email, email_verified_at, password, contact_number, address, is_active, remember_token, license_number, years_experience, qualifications, professional_experience, professional_id_path, verification_status, rejection_reason, verified_at, verified_by, account_status, deleted_at, created_at, updated_at FROM users WHERE role_id = (SELECT role_id FROM roles WHERE role_name = 'nutritionist')")
        return self.cursor.fetchall()
    def get_meal_plan_by_id(self, plan_id: int) -> Optional[Dict]:
        """Get a single meal plan by its plan_id."""
        self.cursor.execute("SELECT plan_id, patient_id, plan_details, generated_at FROM meal_plans WHERE plan_id = %s", (plan_id,))
        return self.cursor.fetchone()

    def get_nutritionist_notes_by_patient(self, patient_id: int) -> List[Dict]:
        """Get all nutritionist notes for a given patient_id from assessments.notes."""
        self.cursor.execute("SELECT assessment_id, nutritionist_id, patient_id, plan_id, assessment_date, notes, treatment, recovery_status, completed_at, created_at, updated_at FROM assessments WHERE patient_id = %s", (patient_id,))
        return self.cursor.fetchall()
    # get_foods_data is now the canonical method for foods
    
    def get_food_nutrition(self, meal_id):
        """Backward compatibility: Get meal nutrition data."""
        meal = self.get_meal_by_id(meal_id)
        if not meal:
            return {}
        
        # Return nutrition data in old format for compatibility
        nutrition = {
            'general': {
                'calories_kcal': meal.get('calories_kcal'),
                'protein_g': meal.get('protein_g'),
                'carbohydrates_g': meal.get('carbohydrates_g'),
                'fat_g': meal.get('fat_g'),
                'fiber_g': meal.get('fiber_g'),
                'sugar_g': meal.get('sugar_g'),
                'sodium_mg': meal.get('sodium_mg'),
                'calcium_mg': meal.get('calcium_mg'),
                'iron_mg': meal.get('iron_mg'),
                'vitamin_c_mg': meal.get('vitamin_c_mg'),
                'saturated_fat_g': meal.get('saturated_fat_g'),
                'polyunsaturated_fat_g': meal.get('polyunsaturated_fat_g'),
                'monounsaturated_fat_g': meal.get('monounsaturated_fat_g'),
                'trans_fat_g': meal.get('trans_fat_g'),
                'cholesterol_mg': meal.get('cholesterol_mg'),
                'potassium_mg': meal.get('potassium_mg'),
                'vitamin_a_iu': meal.get('vitamin_a_iu')
            }
        }
        return nutrition
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

    def add_meal(self, meal_data):
        """Add a new meal to the database."""
        import json
        
        # First, insert into meals table
        meals_sql = """
            INSERT INTO meals (
                meal_name, description, course, keywords, prep_time_minutes, 
                cook_time_minutes, servings, ingredients, instructions, image_url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Convert ingredients list to JSON string if needed
        ingredients = meal_data.get('ingredients', [])
        if isinstance(ingredients, list):
            ingredients = json.dumps(ingredients)
        
        meals_params = (
            meal_data.get('meal_name'),
            meal_data.get('description'),
            meal_data.get('course'),
            meal_data.get('keywords'),
            meal_data.get('prep_time_minutes'),
            meal_data.get('cook_time_minutes'),
            meal_data.get('servings'),
            ingredients,
            meal_data.get('instructions'),
            meal_data.get('image_url')
        )
        
        self.cursor.execute(meals_sql, meals_params)
        meal_id = self.cursor.lastrowid
        
        # Then, insert nutrition facts if any nutrition data is provided
        nutrition_data = {
            'calories_kcal': meal_data.get('calories_kcal'),
            'carbohydrates_g': meal_data.get('carbohydrates_g'),
            'protein_g': meal_data.get('protein_g'),
            'fat_g': meal_data.get('fat_g'),
            'saturated_fat_g': meal_data.get('saturated_fat_g'),
            'polyunsaturated_fat_g': meal_data.get('polyunsaturated_fat_g'),
            'monounsaturated_fat_g': meal_data.get('monounsaturated_fat_g'),
            'trans_fat_g': meal_data.get('trans_fat_g'),
            'cholesterol_mg': meal_data.get('cholesterol_mg'),
            'sodium_mg': meal_data.get('sodium_mg'),
            'potassium_mg': meal_data.get('potassium_mg'),
            'fiber_g': meal_data.get('fiber_g'),
            'sugar_g': meal_data.get('sugar_g'),
            'vitamin_a_iu': meal_data.get('vitamin_a_iu'),
            'vitamin_c_mg': meal_data.get('vitamin_c_mg'),
            'calcium_mg': meal_data.get('calcium_mg'),
            'iron_mg': meal_data.get('iron_mg')
        }
        
        # Only insert nutrition facts if at least one nutrition value is provided
        if any(value is not None for value in nutrition_data.values()):
            nutrition_sql = """
                INSERT INTO nutrition_facts (
                    meal_id, calories_kcal, carbohydrates_g, protein_g, fat_g, saturated_fat_g,
                    polyunsaturated_fat_g, monounsaturated_fat_g, trans_fat_g,
                    cholesterol_mg, sodium_mg, potassium_mg, fiber_g, sugar_g,
                    vitamin_a_iu, vitamin_c_mg, calcium_mg, iron_mg
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            nutrition_params = (
                meal_id,
                nutrition_data['calories_kcal'],
                nutrition_data['carbohydrates_g'],
                nutrition_data['protein_g'],
                nutrition_data['fat_g'],
                nutrition_data['saturated_fat_g'],
                nutrition_data['polyunsaturated_fat_g'],
                nutrition_data['monounsaturated_fat_g'],
                nutrition_data['trans_fat_g'],
                nutrition_data['cholesterol_mg'],
                nutrition_data['sodium_mg'],
                nutrition_data['potassium_mg'],
                nutrition_data['fiber_g'],
                nutrition_data['sugar_g'],
                nutrition_data['vitamin_a_iu'],
                nutrition_data['vitamin_c_mg'],
                nutrition_data['calcium_mg'],
                nutrition_data['iron_mg']
            )
            
            self.cursor.execute(nutrition_sql, nutrition_params)
        
        self.conn.commit()
        return meal_id

    def update_meal(self, meal_id, meal_data):
        """Update an existing meal."""
        import json
        
        # Update meals table
        meals_sql = """
            UPDATE meals SET
                meal_name = %s, description = %s, course = %s, keywords = %s,
                prep_time_minutes = %s, cook_time_minutes = %s, servings = %s,
                ingredients = %s, instructions = %s, image_url = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE meal_id = %s
        """
        
        # Convert ingredients list to JSON string if needed
        ingredients = meal_data.get('ingredients', [])
        if isinstance(ingredients, list):
            ingredients = json.dumps(ingredients)
        
        meals_params = (
            meal_data.get('meal_name'),
            meal_data.get('description'),
            meal_data.get('course'),
            meal_data.get('keywords'),
            meal_data.get('prep_time_minutes'),
            meal_data.get('cook_time_minutes'),
            meal_data.get('servings'),
            ingredients,
            meal_data.get('instructions'),
            meal_data.get('image_url'),
            meal_id
        )
        
        self.cursor.execute(meals_sql, meals_params)
        
        # Update or insert nutrition facts
        nutrition_data = {
            'calories_kcal': meal_data.get('calories_kcal'),
            'carbohydrates_g': meal_data.get('carbohydrates_g'),
            'protein_g': meal_data.get('protein_g'),
            'fat_g': meal_data.get('fat_g'),
            'saturated_fat_g': meal_data.get('saturated_fat_g'),
            'polyunsaturated_fat_g': meal_data.get('polyunsaturated_fat_g'),
            'monounsaturated_fat_g': meal_data.get('monounsaturated_fat_g'),
            'trans_fat_g': meal_data.get('trans_fat_g'),
            'cholesterol_mg': meal_data.get('cholesterol_mg'),
            'sodium_mg': meal_data.get('sodium_mg'),
            'potassium_mg': meal_data.get('potassium_mg'),
            'fiber_g': meal_data.get('fiber_g'),
            'sugar_g': meal_data.get('sugar_g'),
            'vitamin_a_iu': meal_data.get('vitamin_a_iu'),
            'vitamin_c_mg': meal_data.get('vitamin_c_mg'),
            'calcium_mg': meal_data.get('calcium_mg'),
            'iron_mg': meal_data.get('iron_mg')
        }
        
        # Check if nutrition facts exist for this meal
        self.cursor.execute("SELECT meal_id FROM nutrition_facts WHERE meal_id = %s", (meal_id,))
        nutrition_exists = self.cursor.fetchone()
        
        if any(value is not None for value in nutrition_data.values()):
            if nutrition_exists:
                # Update existing nutrition facts
                nutrition_sql = """
                    UPDATE nutrition_facts SET
                        calories_kcal = %s, carbohydrates_g = %s, protein_g = %s, fat_g = %s,
                        saturated_fat_g = %s, polyunsaturated_fat_g = %s, monounsaturated_fat_g = %s,
                        trans_fat_g = %s, cholesterol_mg = %s, sodium_mg = %s, potassium_mg = %s,
                        fiber_g = %s, sugar_g = %s, vitamin_a_iu = %s, vitamin_c_mg = %s,
                        calcium_mg = %s, iron_mg = %s
                    WHERE meal_id = %s
                """
                nutrition_params = tuple(nutrition_data.values()) + (meal_id,)
            else:
                # Insert new nutrition facts
                nutrition_sql = """
                    INSERT INTO nutrition_facts (
                        meal_id, calories_kcal, carbohydrates_g, protein_g, fat_g, saturated_fat_g,
                        polyunsaturated_fat_g, monounsaturated_fat_g, trans_fat_g,
                        cholesterol_mg, sodium_mg, potassium_mg, fiber_g, sugar_g,
                        vitamin_a_iu, vitamin_c_mg, calcium_mg, iron_mg
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                nutrition_params = (meal_id,) + tuple(nutrition_data.values())
            
            self.cursor.execute(nutrition_sql, nutrition_params)
        
        self.conn.commit()

    def delete_meal(self, meal_id):
        """Delete a meal from the database."""
        # Delete nutrition facts first (foreign key constraint)
        self.cursor.execute("DELETE FROM nutrition_facts WHERE meal_id = %s", (meal_id,))
        # Then delete the meal
        self.cursor.execute("DELETE FROM meals WHERE meal_id = %s", (meal_id,))
        self.conn.commit()

    def get_meal_courses(self):
        """Get all unique meal courses."""
        self.cursor.execute("SELECT DISTINCT course FROM meals WHERE course IS NOT NULL ORDER BY course")
        return [row['course'] for row in self.cursor.fetchall()]
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
        self.cursor.execute("SELECT assessment_id, nutritionist_id, patient_id, plan_id, assessment_date, notes, treatment, recovery_status, completed_at, created_at, updated_at FROM assessments")
        rows = self.cursor.fetchall()
        return {str(row['assessment_id']): row for row in rows}

    def save_nutritionist_note(self, plan_id: str, patient_id: str, nutritionist_id: str, note: str) -> str:
        """
        If an assessment exists for the given plan_id, patient_id, and nutritionist_id, append the note to the existing notes field.
        Otherwise, insert a new assessment row.
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Check for existing assessment
        self.cursor.execute(
            "SELECT assessment_id, notes FROM assessments WHERE plan_id = %s AND patient_id = %s AND nutritionist_id = %s",
            (plan_id, patient_id, nutritionist_id)
        )
        row = self.cursor.fetchone()
        if row:
            # Append new note to existing notes (newline separator)
            existing_notes = row.get('notes') or ''
            if existing_notes.strip():
                updated_notes = existing_notes.rstrip() + '\n- ' + note.strip()
            else:
                updated_notes = note.strip()
            self.cursor.execute(
                "UPDATE assessments SET notes = %s, updated_at = %s WHERE assessment_id = %s",
                (updated_notes, now, row['assessment_id'])
            )
            self.conn.commit()
            return str(row['assessment_id'])
        else:
            # Insert new row
            sql = """
                INSERT INTO assessments (plan_id, patient_id, nutritionist_id, notes, assessment_date, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(sql, (plan_id, patient_id, nutritionist_id, note.strip(), now, now))
            self.conn.commit()
            return str(self.cursor.lastrowid)

    def get_notes_for_meal_plan(self, plan_id: str) -> List[Dict]:
        self.cursor.execute("SELECT assessment_id, nutritionist_id, patient_id, plan_id, notes, created_at FROM assessments WHERE plan_id = %s", (plan_id,))
        return self.cursor.fetchall()

    # Knowledge Base Management
    def get_knowledge_base(self) -> Dict:
        self.cursor.execute("SELECT kb_id, ai_summary, pdf_name, pdf_text, added_at FROM knowledge_base")
        rows = self.cursor.fetchall()
        return {str(row['kb_id']): row for row in rows}

    def save_knowledge_base(self, ai_summary, pdf_name, pdf_text=None, uploaded_by=None, uploaded_by_id=None):
        sql = "INSERT INTO knowledge_base (ai_summary, pdf_name, pdf_text, added_at) VALUES (%s, %s, %s, %s)"
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
            now
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
