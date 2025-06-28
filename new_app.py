import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///class_system.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app, model_class=Base)

# Database Models
class ClassSession(db.Model):
    __tablename__ = 'class_sessions'
    id = db.Column(db.Integer, primary_key=True)
    class_code = db.Column(db.String(20), unique=True, nullable=False)
    
    # Relationship with students
    students = db.relationship('Student', backref='class_session', lazy=True)

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100))
    country = db.Column(db.String(50))
    gender = db.Column(db.String(20))
    session_id = db.Column(db.Integer, db.ForeignKey('class_sessions.id'), nullable=False)
    has_submitted_form = db.Column(db.Boolean, default=False)
    
    # Relationship with answers
    answers = db.relationship('Answer', backref='student', lazy=True, cascade='all, delete-orphan')

class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    answer_text = db.Column(db.Text, nullable=False)

# Create tables
with app.app_context():
    db.create_all()
    logging.info("Database tables created")

def generate_class_code():
    """Generate a unique class code like 'BLUE-SKY-4'"""
    adjectives = ['BLUE', 'RED', 'GREEN', 'GOLD', 'SILVER', 'BRIGHT', 'COOL', 'WARM', 'FAST', 'SMART']
    nouns = ['SKY', 'OCEAN', 'MOUNTAIN', 'STAR', 'MOON', 'SUN', 'TREE', 'RIVER', 'CLOUD', 'FIRE']
    number = random.randint(1, 99)
    
    while True:
        code = f"{random.choice(adjectives)}-{random.choice(nouns)}-{number}"
        existing = ClassSession.query.filter_by(class_code=code).first()
        if not existing:
            return code
        number = random.randint(1, 99)

# Routes
@app.route('/')
def index():
    """Homepage with login options"""
    return render_template('index.html')

@app.route('/login/teacher', methods=['GET', 'POST'])
def teacher_login():
    """Teacher login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '1234':  # Hardcoded password
            session['teacher_authenticated'] = True
            flash('Successfully logged in as teacher', 'success')
            return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid password', 'error')
    
    return render_template('teacher_login.html')

@app.route('/login/student', methods=['GET', 'POST'])
def student_login():
    """Student login page with student number and class code"""
    if request.method == 'POST':
        student_number = request.form.get('student_number')
        class_code = request.form.get('class_code')
        
        if not student_number or not class_code:
            flash('Both Student Number and Class Code are required', 'error')
            return render_template('student_login.html')
        
        # Find the class session
        class_session = ClassSession.query.filter_by(class_code=class_code.upper()).first()
        if not class_session:
            flash('Invalid Class Code', 'error')
            return render_template('student_login.html')
        
        # Find the student
        student = Student.query.filter_by(
            student_number=student_number,
            session_id=class_session.id
        ).first()
        
        if not student:
            flash('Student Number not found for this class', 'error')
            return render_template('student_login.html')
        
        # Log in the student
        session['student_id'] = student.id
        session['student_number'] = student.student_number
        flash(f'Welcome {student.name or student.student_number}!', 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('student_login.html')

@app.route('/teacher')
def teacher_dashboard():
    """Teacher dashboard"""
    if not session.get('teacher_authenticated'):
        flash('Please log in as teacher first', 'error')
        return redirect(url_for('teacher_login'))
    
    # Get current class session if any
    current_session = session.get('current_class_session')
    class_session = None
    students = []
    
    if current_session:
        class_session = ClassSession.query.filter_by(class_code=current_session).first()
        if class_session:
            students = Student.query.filter_by(session_id=class_session.id).all()
    
    return render_template('teacher_dashboard.html', 
                         class_session=class_session, 
                         students=students)

@app.route('/teacher/new-session', methods=['POST'])
def new_class_session():
    """Generate a new class session"""
    if not session.get('teacher_authenticated'):
        flash('Please log in as teacher first', 'error')
        return redirect(url_for('teacher_login'))
    
    # Generate new class code
    class_code = generate_class_code()
    new_session = ClassSession(class_code=class_code)
    
    db.session.add(new_session)
    db.session.commit()
    
    # Set as current session
    session['current_class_session'] = class_code
    
    flash(f'New class session created! Class Code: {class_code}', 'success')
    logging.info(f"New class session created with code: {class_code}")
    
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/activate-students', methods=['POST'])
def activate_students():
    """Add students to current class session"""
    if not session.get('teacher_authenticated'):
        flash('Please log in as teacher first', 'error')
        return redirect(url_for('teacher_login'))
    
    current_session_code = session.get('current_class_session')
    if not current_session_code:
        flash('Please start a new class session first', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    class_session = ClassSession.query.filter_by(class_code=current_session_code).first()
    if not class_session:
        flash('Class session not found', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    student_numbers_text = request.form.get('student_numbers', '')
    if not student_numbers_text.strip():
        flash('Please enter student numbers', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    # Parse student numbers (one per line)
    student_numbers = [num.strip() for num in student_numbers_text.split('\n') if num.strip()]
    
    added_count = 0
    for student_number in student_numbers:
        # Check if student already exists for this session
        existing = Student.query.filter_by(
            student_number=student_number,
            session_id=class_session.id
        ).first()
        
        if not existing:
            new_student = Student(
                student_number=student_number,
                session_id=class_session.id
            )
            db.session.add(new_student)
            added_count += 1
    
    db.session.commit()
    
    flash(f'Added {added_count} students to class {current_session_code}', 'success')
    logging.info(f"Added {added_count} students to class {current_session_code}")
    
    return redirect(url_for('teacher_dashboard'))

@app.route('/student')
def student_dashboard():
    """Student dashboard"""
    student_id = session.get('student_id')
    if not student_id:
        flash('Please log in as student first', 'error')
        return redirect(url_for('student_login'))
    
    student = Student.query.get(student_id)
    if not student:
        flash('Student not found', 'error')
        return redirect(url_for('student_login'))
    
    return render_template('student_dashboard.html', student=student)

@app.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    flash('Successfully logged out', 'success')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)