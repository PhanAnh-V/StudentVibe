from flask import render_template, request, redirect, url_for, flash
from app import app, db
from models import Student
from forms import StudentForm
import logging

@app.route('/', methods=['GET', 'POST'])
def index():
    """Homepage with student information form"""
    form = StudentForm()
    
    if form.validate_on_submit():
        try:
            # Create new student record
            student = Student(
                name=form.name.data.strip(),
                vibes=form.vibes.data.strip()
            )
            
            # Add to database
            db.session.add(student)
            db.session.commit()
            
            logging.info(f"New student added: {student.name}")
            
            # Redirect to success page
            return redirect(url_for('success'))
            
        except Exception as e:
            # Handle database errors
            db.session.rollback()
            logging.error(f"Database error: {str(e)}")
            flash('There was an error saving your information. Please try again.', 'error')
    
    elif request.method == 'POST':
        # Handle form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'error')
    
    return render_template('index.html', form=form)

@app.route('/success')
def success():
    """Success confirmation page"""
    return render_template('success.html')

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('index.html', form=StudentForm()), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    flash('An internal error occurred. Please try again.', 'error')
    return render_template('index.html', form=StudentForm()), 500
