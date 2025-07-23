# VibeCheck App - Current Status & Context

## 📱 **What VibeCheck Is**
VibeCheck is an AI-powered group formation tool for teachers and club leaders. It helps create meaningful connections among students through:
- **Personality-based questionnaires** using OpenAI GPT-4
- **Smart squad formation** based on compatibility analysis  
- **Interactive icebreaker activities** for group bonding
- **Multi-language support** (Japanese/English)

## 🏗️ **Technical Architecture**

### **Backend (Flask)**
- **Main App**: `app.py` (906 lines) - complete working application
- **Database**: SQLite with SQLAlchemy (Student, Squad, SessionSettings models)
- **AI Integration**: OpenAI GPT-4o for personality analysis and squad formation
- **Authentication**: Firebase Auth integration
- **Environment**: Manual env vars (bypassed dotenv hanging issue)

### **Frontend Templates**
- **Language Selection**: `language_select.html` - "Vibe Check - Language Selection" 
- **Multi-page Flow**: questionnaire → AI analysis → squad results → teacher dashboard
- **Responsive Design**: Bootstrap-based, mobile-friendly

### **Key Dependencies**
```
Flask, Flask-SQLAlchemy, Flask-WTF
firebase-admin, openai, python-dotenv
gunicorn, requests
pytest, playwright, functions-framework
```

## 🎯 **Current Deployment Status**

### ✅ **Successfully Deployed**
- **Firebase Hosting**: https://vibecheckapp-52d16.web.app
- **Static Files**: Deployed and accessible
- **Firebase Project**: `vibecheckapp-52d16` (authenticated)

### ⚠️ **Pending Issues**
- **Functions Deployment**: Python environment configuration needed
- **Dynamic Routes**: Flask app needs proper Firebase Functions setup
- **Database**: SQLite needs cloud persistence solution

## 🔧 **Recent Development Work**

### **Refactoring Completed**
- ✅ **File Cleanup**: Removed 11+ duplicate/debug files (working_app.py, debug_*.py, etc.)
- ✅ **Naming Update**: Changed "StudentVibe" → "VibeCheck" throughout codebase
- ✅ **Critical Bug Fix**: Routes weren't being registered - fixed `create_app()` initialization

### **Testing Infrastructure**
- ✅ **Playwright E2E Tests**: Installed and configured
- ✅ **Test Server**: `test_server.py` works correctly 
- ✅ **Basic Validation**: 2/2 tests pass (server startup + route functionality)

## 📁 **Current File Structure**
```
/workspaces/StudentVibe/
├── app.py                 # Main Flask application (906 lines)
├── main.py               # Firebase Functions entry point
├── models.py             # Database models (Student, Squad, etc.)
├── forms.py              # WTForms for questionnaire
├── firebase_setup.py     # Firebase authentication 
├── openai_integration.py # AI personality analysis
├── requirements.txt      # Python dependencies
├── firebase.json         # Firebase deployment config
├── templates/            # Jinja2 templates
├── static/              # CSS, JS, images
├── tests/               # Playwright E2E tests
└── public/              # Firebase hosting files
```

## 🔑 **Environment Configuration**
```python
# Working environment variables (manual setup)
SECRET_KEY = 'dev-secret-key-for-flask-sessions'
OPENAI_API_KEY = 'sk-proj-...' (valid key)
FIREBASE_API_KEY = 'AIzaSyCGJgfpKalrm4Sz_bbar-xoZ5-19ojwg1s'
```

## 🚀 **Next Development Priorities**

1. **Fix Firebase Functions**: Complete Python environment setup for dynamic routes
2. **Database Migration**: Move from SQLite to Cloud Firestore/SQL
3. **Production Environment**: Secure API keys and production configuration
4. **Feature Development**: Enhanced UI/UX, admin features, analytics

## 💡 **Key Technical Notes**
- **Routing Issue**: Must use `create_app()` function, not direct `app` import
- **Environment**: Dotenv hangs, use manual env var setting
- **Testing**: Playwright setup complete, ready for comprehensive E2E testing
- **Deployment**: Firebase hosting works, functions need environment fix

## 🎛️ **How to Run the App**

### **Local Development**
```bash
# Start the app locally
cd /workspaces/StudentVibe
python3 test_server.py
# App runs on http://localhost:5001
```

### **Testing**
```bash
# Run basic tests
python -m pytest tests/test_simple.py -v

# Run E2E tests (when server issues resolved)
python -m pytest tests/test_e2e.py -v
```

### **Deployment**
```bash
# Deploy to Firebase
firebase deploy --only hosting  # Static files only (working)
firebase deploy --only functions # Needs environment fix
```

## 🚧 **Known Issues & Workarounds**

1. **Dotenv Hanging**: Use manual environment variable setting instead of `load_dotenv()`
2. **Route Registration**: Always use `create_app()`, never import `app` directly
3. **Firebase Functions**: Python environment needs proper setup for deployment
4. **Database Persistence**: SQLite works locally but needs cloud solution for production

## 📊 **Current App Status**
- **Local Development**: ✅ Fully functional
- **Static Hosting**: ✅ Deployed to Firebase
- **Dynamic Functions**: ⚠️ Needs environment configuration
- **Database**: ✅ Working locally (SQLite)
- **AI Integration**: ✅ OpenAI GPT-4 connected
- **Testing**: ✅ Basic tests pass, E2E infrastructure ready

The app is **functional locally** and **partially deployed**. Core functionality works, deployment pipeline established, ready for iterative development and fixes.
