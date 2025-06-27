from flask import render_template, request, redirect, url_for, flash, session
from app import app, db
from models import Student
from forms import StudentForm, TeacherLoginForm
import logging
import re
from collections import Counter, defaultdict

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

@app.route('/teacher', methods=['GET', 'POST'])
def teacher():
    """Teacher dashboard with password protection"""
    form = TeacherLoginForm()
    
    # Check if user is already authenticated
    if session.get('teacher_authenticated'):
        # Fetch all students from database
        students = Student.query.order_by(Student.created_at.desc()).all()
        return render_template('teacher.html', students=students)
    
    # Handle password submission
    if form.validate_on_submit():
        if form.password.data == "1234":
            # Set session flag for authentication
            session['teacher_authenticated'] = True
            session.permanent = True
            
            # Fetch all students from database
            students = Student.query.order_by(Student.created_at.desc()).all()
            logging.info(f"Teacher accessed dashboard. Found {len(students)} students.")
            
            return render_template('teacher.html', students=students)
        else:
            flash('Incorrect password. Please try again.', 'error')
    
    # Show login form
    return render_template('teacher_login.html', form=form)

@app.route('/teacher/logout')
def teacher_logout():
    """Log out teacher and clear session"""
    session.pop('teacher_authenticated', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('teacher'))

def create_vibe_squads():
    """Group students into squads based on shared interests"""
    # Get all students
    students = Student.query.all()
    
    if len(students) < 2:
        return []
    
    # Define interest keywords to look for
    interest_keywords = [
        'game', 'gaming', 'games', 'video games',
        'music', 'musical', 'musician', 'singing', 'guitar', 'piano',
        'anime', 'manga', 'japanese', 'cosplay',
        'travel', 'traveling', 'adventure', 'explore',
        'food', 'cooking', 'baking', 'cuisine', 'restaurant',
        'sport', 'sports', 'football', 'basketball', 'soccer', 'tennis',
        'art', 'drawing', 'painting', 'creative', 'design',
        'reading', 'books', 'literature', 'novel',
        'technology', 'tech', 'programming', 'coding', 'computer',
        'fitness', 'gym', 'workout', 'exercise', 'running',
        'photography', 'photo', 'camera',
        'dance', 'dancing', 'ballet', 'hip hop'
    ]
    
    # Create student interest profiles
    student_interests = {}
    for student in students:
        interests = set()
        vibes_lower = student.vibes.lower()
        
        # Find matching keywords in student's vibes
        for keyword in interest_keywords:
            if keyword in vibes_lower:
                interests.add(keyword)
        
        student_interests[student.id] = {
            'student': student,
            'interests': interests
        }
    
    # Group students by shared interests
    interest_groups = defaultdict(list)
    processed_students = set()
    
    for student_id, data in student_interests.items():
        if student_id in processed_students:
            continue
            
        current_group = [data]
        processed_students.add(student_id)
        
        # Find other students with similar interests
        for other_id, other_data in student_interests.items():
            if other_id in processed_students or len(current_group) >= 4:
                continue
                
            # Check for shared interests
            shared_interests = data['interests'].intersection(other_data['interests'])
            if shared_interests:
                current_group.append(other_data)
                processed_students.add(other_id)
        
        if len(current_group) >= 2:
            # Create a group key based on shared interests
            all_interests = set()
            for member in current_group:
                all_interests.update(member['interests'])
            group_key = ', '.join(sorted(list(all_interests))[:3]) or 'general'
            interest_groups[group_key].extend(current_group)
    
    # Handle remaining students (those without shared interests)
    remaining_students = []
    for student_id, data in student_interests.items():
        if student_id not in processed_students:
            remaining_students.append(data)
    
    # Create squads with optimal sizes (3-4 members)
    squads = []
    
    # Process interest groups
    for interest, members in interest_groups.items():
        while len(members) >= 3:
            if len(members) >= 4:
                # Create squad of 4
                squad = members[:4]
                members = members[4:]
            else:
                # Create squad of 3
                squad = members[:3]
                members = members[3:]
            
            squads.append({
                'members': [m['student'] for m in squad],
                'shared_interests': interest
            })
        
        # Add remaining members to the pool
        remaining_students.extend(members)
    
    # Group remaining students into squads
    while len(remaining_students) >= 3:
        if len(remaining_students) >= 4:
            squad_size = 4
        else:
            squad_size = 3
            
        squad_members = remaining_students[:squad_size]
        remaining_students = remaining_students[squad_size:]
        
        squads.append({
            'members': [m['student'] for m in squad_members],
            'shared_interests': 'mixed interests'
        })
    
    # Handle final remaining students (less than 3)
    if remaining_students:
        if squads and len(squads[-1]['members']) == 3:
            # Add to last squad if it has only 3 members
            squads[-1]['members'].extend([m['student'] for m in remaining_students])
        elif len(remaining_students) >= 2:
            # Create a small squad if there are at least 2 students
            squads.append({
                'members': [m['student'] for m in remaining_students],
                'shared_interests': 'mixed interests'
            })
    
    return squads

@app.route('/teacher/create-squads', methods=['POST'])
def create_squads():
    """Create vibe squads and redirect back to teacher dashboard"""
    if not session.get('teacher_authenticated'):
        flash('Access denied. Please log in first.', 'error')
        return redirect(url_for('teacher'))
    
    try:
        squads = create_vibe_squads()
        session['current_squads'] = [
            {
                'members': [{'id': s.id, 'name': s.name, 'vibes': s.vibes} for s in squad['members']],
                'shared_interests': squad['shared_interests']
            }
            for squad in squads
        ]
        
        flash(f'Successfully created {len(squads)} vibe squads!', 'success')
        logging.info(f"Created {len(squads)} vibe squads")
        
    except Exception as e:
        logging.error(f"Error creating squads: {str(e)}")
        flash('There was an error creating the squads. Please try again.', 'error')
    
    return redirect(url_for('teacher'))

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
