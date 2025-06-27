# Student Information Collection System

## Overview

This is a Flask-based web application designed to collect and store student information. The system provides a simple form interface where students can submit their name and personal interests/vibes, with data being stored in a database for future reference.

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

## Changelog

- June 27, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.