# Student Information Collection System

## Overview

This is a Flask-based web application designed to collect and store student information with teacher management capabilities. The system provides a simple form interface where students can submit their name and personal interests/vibes, with data being stored in a database. Teachers can access a protected dashboard to view submissions and automatically create student groups based on shared interests.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database ORM**: SQLAlchemy with Flask-SQLAlchemy extension
- **Form Handling**: WTForms with Flask-WTF for CSRF protection
- **Web Server**: Gunicorn for production deployment
- **Template Engine**: Jinja2 (built into Flask)

### Frontend Architecture
- **Styling**: Bootstrap 5 for responsive design
- **Icons**: Font Awesome for UI icons
- **Fonts**: Google Fonts (Roboto and Open Sans)
- **Layout**: Mobile-first responsive design with Google Forms-inspired styling

### Database Architecture
- **Primary Database**: PostgreSQL (production) with psycopg2-binary driver
- **Development Database**: SQLite as fallback
- **ORM**: SQLAlchemy 2.0+ with declarative base model

## Key Components

### Models (models.py)
- **Student Model**: Core data model with fields for id, name, vibes, country, gender, and created_at timestamp
- **Database Integration**: SQLAlchemy ORM with automatic table creation and PostgreSQL support

### Forms (forms.py)
- **StudentForm**: WTForms-based form with validation including name, interests, country, and gender fields
- **Dropdown Fields**: SelectField implementation for country (China, Vietnam, Japan, Other) and gender (Male, Female, Prefer not to say)
- **Validation Rules**: Required fields, length constraints, and user-friendly error messages
- **CSRF Protection**: Built-in security through Flask-WTF

### Routes (routes.py)
- **Index Route** (`/`): Main form display and submission handling
- **Success Route** (`/success`): Confirmation page after successful submission
- **Teacher Route** (`/teacher`): Password-protected teacher dashboard with filtering and management features
- **Teacher Login**: Authentication with hardcoded password "1234"
- **Vibe Squads** (`/teacher/create-squads`): Automatic grouping based on shared interests
- **Student Deletion** (`/teacher/delete-student/<id>`): Secure student record removal with confirmation
- **AI Recommendations** (`/recommendations/<student_id>`): Personalized AI-powered activity suggestions
- **AI Insights** (`/teacher/ai-insights`): Advanced teacher dashboard with AI analysis
- **Error Handling**: 404 error handler and form validation error management

### Templates
- **Base Template**: Common layout with Bootstrap integration
- **Index Template**: Main form interface with flash message support
- **Success Template**: Confirmation page with submission details

## Data Flow

1. **User Access**: User visits the homepage (`/`)
2. **Form Display**: StudentForm is rendered with validation rules
3. **Form Submission**: POST request validates form data
4. **Data Processing**: Valid data creates Student model instance
5. **Database Storage**: Student record saved to database
6. **Success Redirect**: User redirected to success page
7. **Error Handling**: Validation errors displayed with flash messages

## External Dependencies

### Python Packages
- **Flask**: Web framework and core functionality
- **SQLAlchemy**: Database ORM and connection management
- **WTForms**: Form handling and validation
- **Gunicorn**: WSGI HTTP server for production
- **psycopg2-binary**: PostgreSQL database adapter

### Frontend Dependencies (CDN)
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library for UI elements
- **Google Fonts**: Typography (Roboto and Open Sans)

### Infrastructure Dependencies
- **PostgreSQL**: Primary database system
- **OpenSSL**: SSL/TLS support for secure connections

## Deployment Strategy

### Development Environment
- **Local Server**: Flask development server with debug mode
- **Database**: SQLite for local development
- **Hot Reload**: Automatic code reloading for development

### Production Environment
- **Web Server**: Gunicorn with autoscale deployment target
- **Database**: PostgreSQL with connection pooling
- **Process Management**: Multiple worker processes with port reuse
- **Proxy Setup**: ProxyFix middleware for proper header handling

### Configuration Management
- **Environment Variables**: Database URL and session secrets
- **Database Settings**: Connection pooling and health checks
- **Security**: CSRF protection and secure session handling

## New Features

### AI-Powered Interest Recommendation Engine
- **Personalized Recommendations**: OpenAI GPT-4o analyzes student interests to suggest 5 tailored activities
- **Smart Archetype Enhancement**: AI-driven personality analysis beyond keyword matching
- **Growth Opportunities**: Suggests areas for personal development and skill expansion
- **Connection Insights**: Recommends ways to connect with like-minded peers
- **Compatibility Analysis**: AI evaluates student pairing potential for optimal squad formation

### Intelligent Squad Formation System (NEW)
- **Google Gemini AI Integration**: Uses Gemini 2.5 Pro model for intelligent student grouping
- **Smart Squad Creation**: AI analyzes all 6 questionnaire responses to create balanced squads of 3-4 students
- **Personalized Icebreakers**: Each squad receives a unique, AI-generated icebreaker question based on members' specific interests
- **Automatic Squad Naming**: AI generates creative, engaging names for each squad based on member characteristics
- **Graceful Error Handling**: Falls back to default icebreakers if AI service is unavailable

### Vibe Squads System
- **Archetype Detection**: Automatically assigns personality archetypes based on student interests (Gaming Guru, Music Maestro, Creative Artist, etc.)
- **Japanese Translations**: Core interests displayed as hashtags with Japanese translations (#gaming (ゲーム))
- **Visual Identity Cards**: Beautiful vibe cards with gradient borders, avatars, and professional styling
- **Private Squad Hub**: Exclusive `/squad-hub/<squad_id>` route for squad members only
- **AI Recommendation Links**: Direct access to personalized AI suggestions from each vibe card

### Teacher Management
- **Password Protection**: Secure teacher dashboard with hardcoded password "1234"
- **Automatic Grouping**: Smart algorithm creates squads of 3-4 based on shared interests
- **AI Insights Dashboard**: Advanced compatibility analysis and student profiling
- **Student Filtering**: Real-time dropdown filters for country and gender with instant results
- **Student Management**: Delete functionality with confirmation modal for record removal
- **Session Management**: Persistent login and squad data storage

### Enhanced Navigation
- **Unified Interface**: Single navigation bar connecting all sections
- **Responsive Design**: Mobile-first approach with Google Forms inspiration

## Changelog

- June 27, 2025. Initial setup with student form and database
- June 27, 2025. Added teacher dashboard with password protection
- June 27, 2025. Implemented vibe squad grouping algorithm
- June 27, 2025. Created public vibe cards display with archetypes and Japanese translations
- June 27, 2025. Added AI-powered recommendation engine with fallback systems
- June 27, 2025. Enhanced database with country and gender fields, updated forms and UI
- June 27, 2025. Implemented teacher dashboard filtering and student deletion functionality
- June 28, 2025. Implemented secure login system with teacher-controlled student registration
- June 28, 2025. Added auto-generated Student IDs and display badges in teacher dashboard
- June 28, 2025. Changed teacher dashboard from two-column grid to single vertical column layout
- June 28, 2025. Added view toggle buttons with JavaScript tabs for switching between Vibe Squads and All Submissions
- June 28, 2025. Removed "View Squads" navigation link from login pages (student and teacher)
- June 29, 2025. Added session password protection system with randomly generated passwords (e.g., "VIBE123")
- June 29, 2025. Created SessionSettings model to manage session passwords with database persistence
- June 29, 2025. Modified homepage to require session password before accessing questionnaire form
- June 29, 2025. Added Session Control section to teacher dashboard with copy functionality
- June 29, 2025. Removed teacher "Add New Student" functionality - students now only submit through main form
- June 30, 2025. Fixed form submission database error by adding missing vibes field populated from combined question answers
- June 30, 2025. Removed student login functionality - deleted route, template, and link from session password page
- June 30, 2025. Added navigation links throughout app to return to session password page for new sessions
- June 30, 2025. Removed old welcome page template (index.html) with "Ultimate Student Experience" content
- June 30, 2025. Updated error handlers to reference session password page instead of deleted welcome template
- June 30, 2025. Added submission_id column to Student model with unique constraint for tracking submissions
- June 30, 2025. Implemented unique submission ID generation system (format: ABC-123) for student identification
- June 30, 2025. Updated success page to display personal submission ID with clear instruction to save for future use
- June 30, 2025. Created /find-squad route and template for students to locate their squads using submission IDs
- June 30, 2025. Added "Find My Squad" navigation links throughout student portal areas
- June 30, 2025. Implemented form validation and error handling for submission ID lookup functionality
- June 30, 2025. Created multi-language homepage with Japanese welcome message and 4 language options (English, Vietnamese, Chinese, Japanese)
- June 30, 2025. Implemented language selection system storing user preference in browser sessions
- June 30, 2025. Restructured routing: / = language selection, /session-password = questionnaire access
- June 30, 2025. Updated all navigation links throughout app to work with new language selection flow
- June 30, 2025. Added discreet teacher login link (先生ログイン) to language selection homepage
- June 30, 2025. Removed teacher login link from session password page and converted all text to Japanese
- June 30, 2025. Added Japanese font support (Noto Sans JP) to session password page for proper text rendering
- July 01, 2025. Created questions.json file with multilingual questionnaire data (English, Japanese, Vietnamese, Chinese)
- July 01, 2025. Implemented dynamic question loading system using JSON data with language-based question selection
- July 01, 2025. Updated Student model and forms from 7 questions to 6 questions to match new questionnaire structure
- July 01, 2025. Enhanced questionnaire template with dynamic question rendering and multilingual support
- July 01, 2025. Added custom styling for question descriptions with improved visual design and Japanese font support
- July 02, 2025. Created exclusive Squad Hub experience at /squad-hub/<squad_id> serving as private student clubhouse
- July 02, 2025. Deleted public /squads route and squads.html template per user request for privacy
- July 02, 2025. Removed all "View Squads" navigation links from templates (base.html, find_squad.html, profile.html, questionnaire.html, recommendations.html)
- July 02, 2025. Modified /find-squad route to redirect students directly to their private squad hub when submission ID is found
- July 02, 2025. Enhanced Squad Hub with gradient backgrounds, member profile cards, AI mission section, and mobile-responsive design
- July 02, 2025. Created student profile system with game-inspired character sheet design at /profile/<int:student_id>
- July 02, 2025. Made all student names clickable links in teacher dashboard and squad hub, leading to individual profiles
- July 02, 2025. Fixed profile route error handling to display "Profile not found" directly on page without redirects
- July 02, 2025. Removed erroneous question7 reference that was causing profile access errors
- July 02, 2025. Integrated Google Gemini AI for intelligent squad formation using all 6 questionnaire responses
- July 02, 2025. Added icebreaker_text field to Squad model for storing AI-generated personalized icebreakers
- July 02, 2025. Completely rewrote create_squads function to use Gemini AI for both grouping and icebreaker generation
- July 02, 2025. Created gemini_integration.py module with functions for AI-powered squad grouping and icebreaker creation
- July 02, 2025. Enhanced squad creation to include AI-generated creative squad names based on member characteristics
- July 02, 2025. Migrated from Google Gemini API to OpenAI ChatGPT API (gpt-4o model) for improved reliability
- July 02, 2025. Renamed gemini_integration.py to openai_integration.py and updated all API calls to use OpenAI format
- July 02, 2025. Updated routes.py to use openai_integration module for both squad formation and icebreaker generation
- July 02, 2025. Translated all static interface text in HTML templates from English to Japanese for consistent user experience
- July 02, 2025. Redesigned profile.html with bilingual layout structure for displaying both original and Japanese versions of student answers
- July 02, 2025. Fixed JavaScript error in teacher.html by adding null checks before accessing DOM elements with addEventListener
- July 02, 2025. Updated key translations: "Character Attributes" → "キャラクター属性", "Core Abilities" → "コア能力", "Character Traits" → "キャラクター特性"
- July 02, 2025. Enhanced teacher dashboard with Japanese text for all buttons, modals, and confirmation dialogs
- July 02, 2025. Implemented AI-powered Japanese translation system for student answers using OpenAI ChatGPT API
- July 02, 2025. Added 6 new database columns (question1_jp through question6_jp) to store Japanese translations of student responses
- July 02, 2025. Enhanced form submission route with robust translation loop that handles individual question failures gracefully
- July 02, 2025. Updated profile.html to display bilingual answers with original and Japanese versions side-by-side
- July 02, 2025. Added database migration to support new Japanese translation columns in production
- July 02, 2025. Enhanced translation system with intelligent language detection to skip unnecessary AI calls for Japanese students
- July 02, 2025. Optimized form submission performance by preserving original Japanese answers when student language is 'ja'
- July 02, 2025. Added "Clear All Squads" functionality to teacher dashboard with comprehensive database cleanup
- July 02, 2025. Created /clear-squads route that properly unassigns all students before deleting squad records
- July 02, 2025. Fixed browser console errors by improving clipboard functionality with robust fallbacks and CSP error suppression
- July 02, 2025. Enhanced icebreaker system with dual JSON questions (lighthearted & thoughtful) and improved visual styling
- July 02, 2025. Added custom Flask template filter for reliable JSON parsing in squad hub icebreaker display
- July 02, 2025. Modified /clear-squads route to completely delete all student and squad records (total database reset)
- July 02, 2025. Updated teacher dashboard button from "全スクワッドクリア" to "すべて削除" with enhanced confirmation message
- July 02, 2025. Added form submission protection to questionnaire.html with JavaScript to disable submit button and show "送信中..." loading state
- July 02, 2025. Translated all English text in success.html template to friendly Japanese including titles, messages, buttons, and timestamp formatting

## User Preferences

Preferred communication style: Simple, everyday language.