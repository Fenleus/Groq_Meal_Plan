# 🍎 AI-Powered Child Nutrition Management System

A comprehensive, intelligent nutrition management system for children aged 0-5 years, powered by **Groq AI**, **semantic search**, and **evidence-based nutrition guidelines**. Features modern LangChain integration with advanced embedding capabilities for contextual nutrition guidance.

## 🌟 **System Highlights**

- 🤖 **AI-Driven**: Groq LLaMA 70B for intelligent meal planning and assessment
- 🔍 **Semantic Search**: FAISS-powered similarity search across nutrition knowledge base
- 📚 **Evidence-Based**: WHO nutrition guidelines and Filipino dietary practices
- 🏥 **Medical-Aware**: Handles allergies, medical conditions, and growth parameters
- 🇵🇭 **Filipino-Focused**: Traditional recipes with modern nutrition science
- ⚡ **Modern Architecture**: LangChain core with caching and optimization

---

## 🏗️ **System Architecture**

### **Multi-Role Application Suite**
1. **👨‍👩‍👧‍👦 Parent Interface** (`parent_ui.py`) - Child meal plan management
2. **👩‍⚕️ Nutritionist Interface** (`nutritionist_ui.py`) - Professional assessment and monitoring  
3. **🛠️ Admin Interface** (`admin_ui.py`) - System administration and knowledge base management
4. **🌐 FastAPI Backend** (`fastapi_app.py`) - RESTful API with 12 specialized endpoints

### **AI & Intelligence Layer**
- **Nutrition AI Engine** (`nutrition_ai.py`) - Core AI logic with Groq integration
- **LangChain Meal Planning** (`nutrition_chain.py`) - Advanced prompt engineering
- **Semantic Search** (`embedding_utils.py`) - FAISS vector similarity search
- **Knowledge Management** (`data_manager.py`) - Database operations with text chunking

---

## 🚀 **Quick Start**

### **1. Installation**
```bash
# Clone repository and install dependencies
pip install -r requirements.txt
```

### **2. Environment Setup**
Create `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### **3. Launch Applications**
```bash
# Launch all interfaces (uses different ports)
launch.bat

# Or run individually:
streamlit run parent_ui.py --server.port 8501       # Parents
streamlit run nutritionist_ui.py --server.port 8502 # Nutritionists  
streamlit run admin_ui.py --server.port 8503        # Admins

# FastAPI backend
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```

### **4. Test System**
```bash
# Run comprehensive test suite
python test_MAIN.py
```

---

## 🎯 **Core Features by Role**

### **👨‍👩‍👧‍👦 Parents Can:**
- Generate AI-powered meal plans based on child's age, BMI, allergies, and medical conditions
- View all children's meal plans with nutritionist notes and recommendations
- Input available ingredients for customized meal suggestions
- Access 6-month meal plan history and progress tracking
- Contribute family recipes for nutritionist review

### **👩‍⚕️ Nutritionists Can:**
- Review comprehensive patient assessments with AI-generated insights
- Add professional notes to meal plans with clinical observations
- Upload and manage nutrition knowledge base (PDFs, guidelines)
- Monitor multiple families and children with advanced filtering
- Access food database with complete nutrition information

### **🛠️ Admins Can:**
- Manage comprehensive food database with nutrition facts
- Monitor system logs and user activities
- Process and manage knowledge base embeddings
- Oversee meal plan quality and system performance
- Configure system settings and user access

---

## 🧠 **AI & Technology Stack**

### **Language Models**
- **Primary LLM**: Meta LLaMA 70B via Groq API
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
- **Framework**: LangChain Core with RunnableSequence patterns

### **Semantic Search Engine**
- **Vector Database**: FAISS IndexFlatIP (cosine similarity)
- **Text Processing**: RecursiveCharacterTextSplitter with overlap
- **Caching**: Automatic disk caching for 60x speed improvement
- **Knowledge Base**: 3,732+ chunks from nutrition guidelines

### **Modern Architecture**
```python
# Modern LangChain pattern used throughout
chain = prompt_template | llm
result = chain.invoke(variables)

# Smart caching and embedding
embedding_searcher.search_similar_chunks(query, k=4)
```

---

## 📊 **Database Structure**

### **Core Tables**
- **`patients`** - Child profiles with growth metrics and medical data
- **`users`** - Parents, nutritionists, and admins with role-based access
- **`foods`** - Comprehensive food database with nutrition facts
- **`meal_plans`** - AI-generated meal plans with parent and nutritionist input
- **`assessments`** - Professional evaluations and recommendations
- **`knowledge_base`** - PDF documents with AI-extracted insights

### **Key Features**
- Medical condition tracking and allergy management
- Growth parameter monitoring (BMI, height-for-age, weight-for-age)
- Religious and cultural dietary preferences
- Parent recipe integration and nutritionist feedback

---

## 🔍 **Semantic Search & Embeddings**

### **Advanced Search Capabilities**
```python
# Age-appropriate nutrition guidance
results = embedding_searcher.search_similar_chunks(
    "iron requirements 18 month toddler", k=4
)

# Medical condition support
allergy_guidance = embedding_searcher.search_similar_chunks(
    "food allergies children alternatives", k=6
)
```

### **Performance Features**
- **Instant Search**: 2-second response time with caching
- **Smart Updates**: Automatic cache invalidation on knowledge base changes
- **Batch Processing**: Efficient embedding creation for large documents
- **Quality Filtering**: Similarity threshold (>0.4) for relevant results

---

## 🧪 **Testing & Quality Assurance**

### **Comprehensive Test Suite** ✅ 18/18 Tests Passing
- **Chunk Overlapping**: Text processing with context preservation
- **Top-K Similarity Search**: Embedding-based information retrieval
- **End-to-End Functionality**: Complete API workflow testing
- **Performance & Caching**: Large-scale operation validation

### **Test Coverage**
```bash
# Run all tests
python test_MAIN.py

# Individual test categories
pytest test_comprehensive_embedding_system.py -k TestChunkOverlapping
pytest test_comprehensive_embedding_system.py -k TestTopKSimilaritySearch
```

---

## 📁 **Project Structure**

```
📂 Groq_Meal_Plan/
├── 🎯 Core Applications
│   ├── parent_ui.py              # Parent dashboard
│   ├── nutritionist_ui.py        # Professional interface
│   ├── admin_ui.py              # System administration
│   └── fastapi_app.py           # REST API backend
├── 🤖 AI & Intelligence
│   ├── nutrition_ai.py          # Core AI engine
│   ├── nutrition_chain.py       # LangChain meal planning
│   ├── embedding_utils.py       # Semantic search
│   └── data_manager.py          # Database operations
├── 🧪 Testing & Quality
│   ├── test_MAIN.py             # Main test runner
│   ├── test_comprehensive_embedding_system.py
│   ├── test_embedding_ui.py     # Interactive test interface
│   └── TEST_SUMMARY.md          # Test results documentation
├── 📚 Documentation
│   ├── README.md                # This file
│   ├── USAGE_GUIDE.md           # Semantic search guide
│   └── IMPLEMENTATION_SUMMARY.md
├── ⚙️ Configuration
│   ├── requirements.txt         # Dependencies
│   ├── launch.bat              # Easy launcher
│   └── .env                    # API keys
└── 💾 Data & Cache
    ├── embeddings_cache/        # Vector embeddings
    └── __pycache__/            # Python cache
```

---

## 🔧 **API Endpoints**

### **Role-Based Endpoint Organization**

#### **👤 User Endpoints**
- `GET /` - Health check and API information
- `POST /get_foods_data` - Food database access

#### **👨‍👩‍👧‍👦 Parent Endpoints**  
- `POST /generate_meal_plan` - AI meal plan generation
- `POST /get_children_by_parent` - Child information
- `POST /get_meal_plans_by_child` - Meal plan history
- `POST /get_meal_plan_detail` - Detailed plan view

#### **👩‍⚕️ Nutritionist Endpoints**
- `POST /nutrition/analysis` - AI nutrition analysis
- `POST /assessment` - Comprehensive patient assessment

#### **🛠️ Admin Endpoints**
- `POST /process_embeddings` - Knowledge base processing
- `POST /embedding_status` - System status check
- `POST /get_knowledge_base` - Knowledge management
- `POST /upload_pdf` - Document upload with AI processing

---

## 📋 **Dependencies**

### **Core Requirements**
```txt
groq                      # Groq API integration
python-dotenv            # Environment management
langchain                # LLM framework
langchain-core           # Modern LangChain components
langchain-groq           # Groq LLM integration
langchain-text-splitters # Text processing
```

### **Web & API**
```txt
streamlit               # User interfaces
fastapi                 # REST API framework
uvicorn                 # ASGI server
pydantic               # Data validation
python-multipart       # File upload support
```

### **AI & Data Processing**
```txt
sentence-transformers   # Embedding models
faiss-cpu              # Vector similarity search
numpy                  # Numerical operations
pdfplumber             # PDF processing
mysql-connector-python # Database connectivity
```

---

## 🌍 **Evidence-Based Nutrition**

### **Knowledge Sources**
- **WHO Guidelines**: Child nutrition standards and recommendations
- **Philippine FNRI**: Local food composition and dietary practices
- **Medical Literature**: Evidence-based nutrition interventions
- **Cultural Practices**: Traditional Filipino feeding practices

### **AI Integration**
- Automatic PDF processing and insight extraction
- Context-aware nutrition guidance based on patient profiles
- Cultural and religious dietary accommodation
- Age-appropriate feeding recommendations (0-6, 6-12, 12-24, 24+ months)

---

## 🎉 **Getting Started Tips**

1. **First Time Setup**: Run `test_MAIN.py` to verify system functionality
2. **Knowledge Base**: Upload WHO guidelines and local nutrition documents via admin interface
3. **Embedding Processing**: Use `/process_embeddings` to build searchable knowledge base
4. **Test Generation**: Create sample meal plans to verify AI functionality
5. **Monitor Performance**: Check embedding cache status for optimal performance

---

## 📞 **Support & Documentation**

- **Usage Guide**: See `USAGE_GUIDE.md` for semantic search usage
- **Test Results**: View `TEST_SUMMARY.md` for system validation
- **API Testing**: Use interactive test UI in `test_embedding_ui.py`

---

**🚀 Start with any interface based on your role and begin providing intelligent, evidence-based nutrition care for children!**

*Built with ❤️ for better child nutrition outcomes*
````