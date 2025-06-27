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
- **Student Model**: Core data model with fields for id, name, vibes, and created_at timestamp
- **Database Integration**: SQLAlchemy ORM with automatic table creation

### Forms (forms.py)
- **StudentForm**: WTForms-based form with validation
- **Validation Rules**: Required fields, length constraints, and user-friendly error messages
- **CSRF Protection**: Built-in security through Flask-WTF

### Routes (routes.py)
- **Index Route** (`/`): Main form display and submission handling
- **Success Route** (`/success`): Confirmation page after successful submission
- **Teacher Route** (`/teacher`): Password-protected teacher dashboard
- **Teacher Login**: Authentication with hardcoded password "1234"
- **Vibe Squads** (`/teacher/create-squads`): Automatic grouping based on shared interests
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

### Vibe Squads System
- **Archetype Detection**: Automatically assigns personality archetypes based on student interests (Gaming Guru, Music Maestro, Creative Artist, etc.)
- **Japanese Translations**: Core interests displayed as hashtags with Japanese translations (#gaming (ゲーム))
- **Visual Identity Cards**: Beautiful vibe cards with gradient borders, avatars, and professional styling
- **Public Display Page**: `/squads` route for students to view their teams
- **AI Recommendation Links**: Direct access to personalized AI suggestions from each vibe card

### Teacher Management
- **Password Protection**: Secure teacher dashboard with hardcoded password "1234"
- **Automatic Grouping**: Smart algorithm creates squads of 3-4 based on shared interests
- **AI Insights Dashboard**: Advanced compatibility analysis and student profiling
- **Session Management**: Persistent login and squad data storage

### Enhanced Navigation
- **Unified Interface**: Single navigation bar connecting all sections
- **Responsive Design**: Mobile-first approach with Google Forms inspiration

## Changelog

- June 27, 2025. Initial setup with student form and database
- June 27, 2025. Added teacher dashboard with password protection
- June 27, 2025. Implemented vibe squad grouping algorithm
- June 27, 2025. Created public vibe cards display with archetypes and Japanese translations

## User Preferences

Preferred communication style: Simple, everyday language.