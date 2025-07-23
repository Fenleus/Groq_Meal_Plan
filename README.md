# Family Nutrition Management System

A comprehensive nutrition management system with separate interfaces for parents and nutritionists, powered by Groq AI.

## 🏗️ System Overview

### **Two Separate Applications:**
1. **Parent Interface** (`parent_ui.py`) - Manage children's meal plans and family recipes
2. **Nutritionist Interface** (`nutritionist_ui.py`) - Review plans, add notes, manage knowledge base

### **Key Features:**
- 👨‍👩‍👧‍👦 **For Parents**: Child meal plan management, family recipe input
- 👩‍⚕️ **For Nutritionists**: Client overview, meal plan notes, knowledge base management
- 🧠 **AI-Powered**: Groq API for personalized meal recommendations
- 📄 **Data Storage**: JSON-based storage for simplicity
- 🇵🇭 **Filipino-Focused**: Built-in Filipino nutrition knowledge

## 📋 Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
Your `.env` file should contain:
```
GROQ_API_KEY=your_actual_api_key_here
```

### 3. Run Applications
```bash
# For Parents
streamlit run parent_ui.py --server.port 8501

# For Nutritionists (different port)  
streamlit run nutritionist_ui.py --server.port 8502

# Or use the launcher
launch.bat
```

## 📁 Project Structure

- **`parent_ui.py`** - Parent interface for meal planning
- **`nutritionist_ui.py`** - Nutritionist interface for client management
- **`nutrition_ai.py`** - Core AI logic with Groq
- **`data_manager.py`** - JSON data management utilities
- **`launch.bat`** - Easy launcher script
- **`data/`** - JSON storage directory
  - `children.json` - Children profiles and BMI data
  - `meal_plans.json` - Historical meal plans  
  - `family_recipes.json` - Parent-uploaded recipes
  - `nutritionist_notes.json` - Nutritionist notes on plans
  - `knowledge_base.json` - Filipino nutrition knowledge
- **`requirements.txt`** - Dependencies
- **`.env`** - API keys

## 🎯 Features by User Type

### **Parents Can:**
- View all their children's meal plans
- Generate new meal plans based on child's BMI, allergies, conditions
- Input family recipes (simple text area format)
- View historical meal plans (6 months)
- See nutritionist notes on their meal plans

### **Nutritionists Can:**
- View all families and their meal plans
- Add notes to any meal plan (simple note-taking, no approval workflow)
- Upload and manage Filipino nutrition knowledge
- Upload Filipino recipes with nutrition facts
- Review family-uploaded recipes with professional notes

## 📊 Data Flow

1. **Parent** generates meal plan → AI considers child's BMI, allergies, medical conditions
2. **System** uses Filipino nutrition knowledge + family recipes for recommendations
3. **Nutritionist** reviews and adds notes to meal plans
4. **Parent** can view updated meal plans with nutritionist notes

---

## Data Sources

Food composition and nutrition facts in this system are based on the Philippine Food Composition Tables from [FNRI DOST](https://i.fnri.dost.gov.ph/).

**Start with either interface based on your role!** 👨‍👩‍👧‍👦 or 👩‍⚕️
