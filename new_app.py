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



@app.route('/teacher')
def teacher_dashboard():
    """Teacher dashboard"""
    if not session.get('teacher_authenticated'):
        flash('Please log in as teacher first', 'error')
        return redirect(url_for('teacher_login'))
    
    # Get current class session if any
    current_session = session.get('current_class_session')
    class_session = None
    
    if current_session:
        class_session = ClassSession.query.filter_by(class_code=current_session).first()
    
    return render_template('teacher_dashboard.html', 
                         class_session=class_session)

@app.route('/teacher/new-session', methods=['POST'])
def new_class_session():
    """Generate a new class session"""
    if not session.get('teacher_authenticated'):
        flash('Please log in as teacher first', 'error')
        return redirect(url_for('teacher_login'))
    
    # Generate new class code
    class_code = generate_class_code()
    new_session = ClassSession()
    new_session.class_code = class_code
    
    db.session.add(new_session)
    db.session.commit()
    
    # Set as current session
    session['current_class_session'] = class_code
    
    flash(f'New class session created! Class Code: {class_code}', 'success')
    logging.info(f"New class session created with code: {class_code}")
    
    return redirect(url_for('teacher_dashboard'))





@app.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    flash('Successfully logged out', 'success')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)