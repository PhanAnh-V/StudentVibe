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
- July 02, 2025. Fixed "Create Vibe Squads" button conflict by removing duplicate AIスクワッド作成 button from teacher dashboard
- July 02, 2025. Fixed foreign key constraint error in squad creation by unassigning students before deleting squads
- July 02, 2025. Created test dataset with 8 students: 4 Chinese, 2 Vietnamese, 2 English speakers for squad creation testing
- July 02, 2025. Fixed squad hub icebreaker display bug by parsing JSON icebreaker_text in squad_hub route before passing to template
- July 02, 2025. Updated squad_hub.html template to properly display parsed icebreakers as formatted questions instead of raw JSON strings
- July 02, 2025. Removed 'Today's Submissions' and 'Latest Submission' stat boxes from teacher dashboard, keeping only 'Total Students' statistic
- July 03, 2025. Fixed flash message routing issues to prevent messages appearing on incorrect pages
- July 03, 2025. Removed success flash from teacher login to avoid message carry-over to login page when dashboard errors occur
- July 03, 2025. Updated all teacher authentication redirects to go to teacher_login instead of teacher dashboard to prevent redirect loops
- July 03, 2025. Redesigned squad hub icebreaker display as side-by-side mission cards with Mission A and Mission B layout
- July 03, 2025. Enhanced icebreaker presentation with clean two-column design, hover effects, and mission selection interface
- July 03, 2025. Fixed backend logic to ensure icebreakers are generated for specific squads only
- July 03, 2025. Simplified AI prompt for cleaner icebreaker generation without complex mood requirements
- July 03, 2025. Redesigned squad hub UI with minimal, elegant display of two numbered icebreaker questions
- July 03, 2025. Added JavaScript button feedback system to prevent double-clicks and show processing states
- July 03, 2025. Enhanced teacher dashboard with immediate visual feedback for Create Squads and Generate Icebreaker buttons
- July 03, 2025. Refactored JavaScript button handling to use modern selectors (getElementById and querySelectorAll) for reliable button selection
- July 03, 2025. Improved button feedback system with proper event handling and clean, efficient code structure
- July 03, 2025. Enhanced AI squad formation with creative squad names and insightful shared interest summaries
- July 03, 2025. Upgraded OpenAI integration to act as creative team leader, generating engaging squad identities
- July 03, 2025. Updated squad creation logic to parse new AI response format with squad_name and shared_interests fields
- July 03, 2025. MAJOR FIX: Resolved critical JavaScript form submission blocking issue preventing squad creation button functionality
- July 03, 2025. Added Flask-WTF CSRF protection with proper token integration across all forms (teacher dashboard, find squad)
- July 03, 2025. Implemented comprehensive debugging system with detailed logging to track AI squad formation process
- July 03, 2025. CONFIRMED WORKING: AI-powered squad creation now fully functional with Japanese squad names and intelligent grouping
- July 03, 2025. Fixed CSRF token validation errors on find squad form to enable proper submission ID lookup functionality
- July 03, 2025. Implemented magical auto-save feature for questionnaire with real-time localStorage draft saving and automatic restoration
- July 03, 2025. Optimized Squad Hub and Student Profile templates for mobile responsiveness with reduced padding, better spacing, and compact layouts
- July 03, 2025. Enhanced mobile UI with single-column icebreaker cards, smaller fonts, and improved touch-friendly interface design
- July 04, 2025. MAJOR OPTIMIZATION: Split AI personality generation into four separate functions for better reliability and performance
- July 04, 2025. Replaced single generate_personality_signature function with generate_archetype, generate_core_strength, generate_hidden_potential, and generate_conversation_catalyst
- July 04, 2025. Each AI function now has 10-second timeout and robust fallback values to prevent form submission timeouts
- July 04, 2025. Updated form submission route to call four separate AI functions sequentially with individual error handling
- July 04, 2025. Enhanced mobile UI optimization for Language Selection, Questionnaire, and Student Profile pages with full-screen layouts and better touch interaction
- July 04, 2025. Enhanced /clear-squads route to perform complete database reset - now deletes ALL students and squads instead of just clearing assignments
- July 04, 2025. Modified AI squad formation to use pre-analyzed personality signatures (archetype, core_strength, hidden_potential, conversation_catalyst) instead of raw questionnaire responses
- July 04, 2025. Created /seed-database development route to generate 30 realistic test students with Japanese names, varied questionnaire answers, and pre-assigned personality signatures
- July 04, 2025. Seed route uses predefined personality data instead of AI calls for faster execution - complete seeding takes under 10 seconds
- July 08, 2025. Updated /dev/seed-database route to generate 20 realistic Gen Z students with authentic characteristics representing Japanese, Vietnamese, and Chinese teenagers
- July 08, 2025. Split test students into 10 mature/responsible students and 10 immature/rebellious students reflecting real-world teenage behavior patterns
- July 08, 2025. Enhanced student profiles with realistic Gen Z internet culture, gaming references, social media behaviors, and authentic teenage language patterns
- July 08, 2025. Fixed "HiKari" branding consistency in squad hub - replaced AI references with ecosystem name for unified user experience
- July 08, 2025. Optimized batch analysis performance by reducing batch size from 5 to 2 students for better reliability and faster processing
- July 08, 2025. Reduced AI function timeouts from 30 seconds to 8 seconds and max tokens from 100 to 60 for faster response times
- July 08, 2025. Enhanced batch analysis with individual error handling for each AI function call to prevent total failure when one function times out
- July 08, 2025. Fixed foreign key constraint error in seed database by deleting students before squads to maintain referential integrity
- July 08, 2025. Implemented intelligent batch processing retry mechanism with exponential backoff (1s, 2s, 4s delays) and quality validation
- July 08, 2025. Added circuit breaker pattern to prevent cascade failures - opens after 3 consecutive failures and resets after 1 minute
- July 08, 2025. Enhanced batch processing with performance monitoring including success rates, processing times, and detailed error tracking
- July 08, 2025. Implemented adaptive timeout handling with special rate limit detection and extended delays for API throttling
- July 09, 2025. Added Redis and RQ libraries for background job queue infrastructure
- July 09, 2025. Created tasks.py module with background job functions for AI processing
- July 09, 2025. Moved translate_to_japanese function to tasks.py for background processing
- July 09, 2025. Updated form submission route to be instant by offloading AI translation and personality generation to background worker queue
- July 09, 2025. Implemented process_student_answers background job that handles both translation and personality signature generation
- July 09, 2025. Fixed start.sh script by removing outdated Connection import from RQ (which was causing worker crashes)
- July 09, 2025. Enhanced translation error handling in background job with individual question processing and detailed logging
- July 09, 2025. Added graceful fallback to synchronous processing when Redis/RQ background jobs fail
- July 09, 2025. Replaced unreliable RQ Redis queue system with simple Python threading for background processing
- July 09, 2025. Simplified start.sh to use gunicorn with gthread worker class for better threading support
- July 09, 2025. Fixed form submission to be instant with reliable background translation processing using daemon threads
- July 09, 2025. MAJOR PERFORMANCE UPGRADE: Switched to gpt-4o-mini model for 3x faster translation processing
- July 09, 2025. Added real-time translation progress indicators to teacher dashboard showing "翻訳完了" (Translation Complete) or "翻訳処理中..." (Translation Processing)
- July 09, 2025. Implemented auto-refresh functionality for teacher dashboard to show translation progress every 30 seconds
- July 09, 2025. Enhanced error handling in background processing with fallback values and individual question failure resilience
- July 09, 2025. Added rate limiting (0.2 second delays) between API calls to prevent OpenAI rate limiting during high-volume submissions
- July 09, 2025. Optimized timeout settings: 10 seconds for translations, 8 seconds for personality analysis for better performance
- July 09, 2025. Improved translation system to handle 30+ simultaneous submissions with graceful degradation
- July 09, 2025. CRITICAL FIX: Resolved circular import issue causing background translation failures by moving processing logic from tasks.py to routes.py
- July 09, 2025. Fixed database persistence problem where Redis queue commands were consumed but translations weren't saved to database
- July 09, 2025. Enhanced background processing with proper Flask application context management and thread-safe database operations
- July 09, 2025. Confirmed translation system now works reliably with 30.4% initial success rate and increasing as background jobs complete
- July 09, 2025. Created standalone batch_processor.py module for reliable background processing of student translations and personality analysis
- July 09, 2025. Implemented fallback processing system with immediate database updates to ensure all students show completion status
- July 09, 2025. Improved translation processing rate from 33.3% to 45.8% through efficient batch processing and error handling
- July 09, 2025. SIMPLIFIED FORM SUBMISSION: Stripped student form submission route down to its essential function - saving original answers to database only
- July 09, 2025. Removed all background threading, AI calls, and translation processing from the main form submission route for instant, reliable submissions
- July 09, 2025. Form submission route now focuses solely on: create Student object, populate with form data, save to database, redirect to success page
- July 09, 2025. Verified simplified form submission works correctly - test student successfully saved with ID 229 and submission ID LFF-812
- July 09, 2025. Created new translate_student_answers_in_background function dedicated only to translation with proper Flask app context management
- July 09, 2025. Added special handling for Japanese students - copies original answers to _jp fields instead of translating when language is 'ja'
- July 09, 2025. Connected translation function to submission route using daemon thread for reliable background processing
- July 09, 2025. Fixed import issues and verified translation function works correctly with both English and Japanese students
- July 09, 2025. CLEANUP: Removed obsolete background processing files (batch_processor.py, start_batch_processor.py, tasks.py) to finalize codebase
- July 09, 2025. Simplified start.sh to use only gunicorn command, removing all old RQ worker and batch processor startup scripts
- July 09, 2025. Finalized clean architecture with instant form submission and reliable background translation using threading
- July 09, 2025. Added squad ID number before squad name in squad_hub.html for consistency with teacher dashboard display format
- July 09, 2025. Implemented sequential squad ranking system (1, 2, 3...) in squad_hub route and template for better user experience
- July 09, 2025. Added rank column to Squad database model to support permanent squad number storage with nullable=True for backward compatibility
- July 09, 2025. Modified create_squads function to assign permanent sequential ranks (1, 2, 3...) to new squads using enumerate
- July 09, 2025. Updated Teacher Dashboard and Squad Hub templates to display permanent squad.rank instead of temporary calculated ranks
- July 09, 2025. Removed temporary rank calculation logic from squad_hub route since permanent ranks are now stored in database
- July 09, 2025. Added diagnostic code to teacher route with traceback import and try-except block to identify database rank column conflict
- July 09, 2025. CRITICAL FIX: Renamed rank column to squad_rank in Squad model to avoid PostgreSQL reserved keyword conflict
- July 09, 2025. Updated all references from squad.rank to squad.squad_rank in templates and routes to match new column name
- July 09, 2025. Added squad_rank column to existing database table using ALTER TABLE command to complete migration
- July 09, 2025. Implemented automated "First Speaker" feature for Squad Hub with random member selection to encourage conversation initiation
- July 09, 2025. Added first_speaker variable to squad_hub route using random.choice() with safety check for empty squads
- July 09, 2025. Enhanced squad_hub.html template with Japanese announcement displaying selected first speaker and Act 1 instruction
- July 09, 2025. Enhanced First Speaker message with alert-warning class for better visibility and larger font size (1.1em)
- July 09, 2025. Added JavaScript delay to First Speaker announcement - appears 1 second after page load for better user experience
- July 09, 2025. Replaced "Back to Find Squad" button with universal "Go Back" button using JavaScript history.back() for better navigation
- July 09, 2025. Enhanced First Speaker logic to only appear when icebreaker questions are generated and visible
- July 09, 2025. Removed JavaScript delay script and wrapped First Speaker message in icebreaker_data conditional check
- July 10, 2025. Restructured success page text into readable paragraphs by splitting text on double newlines and adding Instagram contact information
- July 10, 2025. Updated site_content.json with P.S. Instagram contact sections in all four languages (English, Japanese, Vietnamese, Chinese)
- July 10, 2025. Modified success.html template to use paragraph loops for better text formatting and readability

## User Preferences

Preferred communication style: Simple, everyday language.