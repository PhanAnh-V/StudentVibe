"""
VibeCheck - Complete Working Application
An AI-powered group formation tool for teachers and club leaders to create meaningful connections among students
"""

import os
import json
import logging
import traceback
import random
import string
import threading
import time
from datetime import datetime

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

# Import our modules
from models import db, Student, Squad, SessionSettings
from forms import StudentForm
from firebase_setup import verify_firebase_token
import firebase_admin

# Set up logging
logging.basicConfig(level=logging.INFO)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure CSRF
app.config['WTF_CSRF_CHECK_DEFAULT'] = False
app.config['WTF_CSRF_SSL_STRICT'] = False
csrf = CSRFProtect(app)

# Initialize database
db.init_app(app)

# Template filter for JSON parsing
@app.template_filter('from_json')
def from_json_filter(value):
    """Parse JSON string in templates"""
    try:
        return json.loads(value) if value else None
    except (json.JSONDecodeError, TypeError):
        return None

def load_site_content():
    """Load site content from JSON file"""
    try:
        with open('site_content.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading site content: {e}")
        return {}

def load_questions():
    """Load questions from JSON file"""
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading questions: {e}")
        return []

def generate_submission_id():
    """Generate a unique submission ID like ABC-123"""
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{letters}-{numbers}"

def register_all_routes():
    """Register all application routes"""
    
    @app.route('/')
    def index():
        """Home page with language selection"""
        return render_template('language_select.html')

    @app.route('/student-login')
    def student_login():
        """Student login - redirect to language selection"""
        return redirect(url_for('index'))

    @app.route('/teacher-login') 
    def teacher_login():
        """Teacher login - redirect to Firebase login"""
        return redirect(url_for('login'))

    @app.route('/select-language/<language>')
    def select_language(language):
        """Set the selected language and redirect to session password"""
        session['selected_language'] = language
        session['language'] = language
        return redirect(url_for('session_password'))

    @app.route('/session-password', methods=['GET', 'POST'])
    def session_password():
        """Session password entry page"""
        if request.method == 'POST':
            password = request.form.get('password', '').strip().upper()
            current_password = SessionSettings.get_current_password()
            
            if password == current_password:
                session['session_authenticated'] = True
                session.permanent = True
                return redirect(url_for('questionnaire'))
            else:
                flash('Incorrect session password. Please try again.', 'error')
        
        return render_template('session_password.html')

    @app.route('/session-auth', methods=['POST'])
    def session_auth():
        """Handle session authentication"""
        password = request.form.get('session_password', '').strip().upper()
        current_password = SessionSettings.get_current_password()
        
        if password == current_password:
            session['session_authenticated'] = True
            session.permanent = True
            return redirect(url_for('questionnaire'))
        else:
            flash('Incorrect session password. Please try again.', 'error')
            return redirect(url_for('session_password'))

    @app.route('/questionnaire')
    def questionnaire():
        """Main questionnaire page"""
        if not session.get('session_authenticated'):
            return redirect(url_for('session_password'))
        
        questions_data = load_questions()
        selected_language = session.get('selected_language', 'en')
        
        # Extract questions for the selected language
        if 'questions' in questions_data:
            questions = questions_data['questions'].get(selected_language, questions_data['questions'].get('en', []))
        else:
            questions = []
        
        # Create form object
        from forms import StudentForm
        form = StudentForm()
        
        
        return render_template('questionnaire.html', 
                             form=form,
                             questions=questions, 
                             selected_language=selected_language)

    @app.route('/submit-form', methods=['POST'])
    def submit_form():
        """Handle questionnaire form submission"""
        
        if not session.get('session_authenticated'):
            flash('Session not authenticated', 'error')
            return redirect(url_for('session_password'))
        
        form = StudentForm()
        
        if form.validate_on_submit():
            
            # Get form data
            name = form.name.data
            country = form.country.data  
            gender = form.gender.data
            
            
            # Collect all question answers
            answers = {}
            for i in range(1, 7):
                answer = request.form.get(f'question{i}', '').strip()
                answers[f'question{i}'] = answer
            
            # Create combined vibes string
            combined_vibes = ' | '.join([f"Q{i}: {answers[f'question{i}']}" for i in range(1, 7)])
            
            # Generate submission ID
            submission_id = generate_submission_id()
            
            # Store student name and submission ID in session
            session['student_name'] = name
            session['submission_id'] = submission_id
            
            # Collect original answers
            original_answers = [answers[f'question{i}'] for i in range(1, 7)]
            
            # Detect student language
            student_language = session.get('selected_language', 'en')
            
            # Debug session data
            logging.info(f"Session data: {dict(session)}")
            logging.info(f"Processing answers for language: {student_language}")
            
            # Create student record
            student = Student(
                name=name,
                country=country,
                gender=gender,
                submission_id=submission_id,
                vibes=combined_vibes,
                question1=answers['question1'],
                question2=answers['question2'],
                question3=answers['question3'],
                question4=answers['question4'],
                question5=answers['question5'],
                question6=answers['question6']
            )
            print("Student record created with basic info")
            
            try:
                db.session.add(student)
                print("Student added to database session")
                db.session.commit()
                
                logging.info(f"New student registered: {name} (ID: {student.id}, Submission ID: {submission_id})")
                
                # Start background translation
                logging.info(f"Started background translation for student {student.id} in language {student_language}")
                threading.Thread(
                    target=translate_student_answers_in_background,
                    args=(student.id, student_language),
                    daemon=True
                ).start()
                
                return redirect(url_for('success'))
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"Database error: {e}")
                flash('Error saving your information. Please try again.', 'error')
                return redirect(url_for('questionnaire'))
        
        else:
            flash('Please fill in all required fields correctly.', 'error')
            return redirect(url_for('questionnaire'))

    @app.route('/success')
    def success():
        """Success page after form submission"""
        
        if not session.get('session_authenticated'):
            return redirect(url_for('session_password'))
        
        submission_id = session.get('submission_id')
        student_name = session.get('student_name')
        
        if not submission_id:
            flash('No submission found.', 'error')
            return redirect(url_for('questionnaire'))
        
        # Load site content
        site_content = load_site_content()
        success_page_content = site_content.get('success_page', {})
        
        # Get selected language
        selected_language = session.get('selected_language', 'en')
        
        # Prepare success text with language-specific content
        success_text = {}
        for key, value in success_page_content.items():
            if isinstance(value, dict) and selected_language in value:
                # Format with student name if needed
                text = value[selected_language]
                if '{name}' in text and student_name:
                    text = text.format(name=student_name)
                success_text[key] = text
        
        return render_template('success.html', 
                             submission_id=submission_id,
                             student_name=student_name,
                             site_content=site_content,
                             success_text=success_text,
                             app_explanation=site_content['success_page']['app_explanation'])

    def translate_student_answers_in_background(student_id, student_language):
        """
        Background function dedicated only to translation - including special handling for Japanese students
        """
        with app.app_context():
            try:
                from openai_integration import translate_to_japanese
                
                student = Student.query.get(student_id)
                if not student:
                    logging.error(f"Student {student_id} not found for translation")
                    return
                
                logging.info(f"Starting translation for student {student_id} ({student.name}) in language: {student_language}")
                
                # For all students, translate their answers to Japanese
                if student_language != 'ja':  # Only translate if not already Japanese
                    logging.info(f"Translating answers for student {student_id} from {student_language} to Japanese")
                    
                    # Translate each question answer
                    questions = [student.question1, student.question2, student.question3, 
                               student.question4, student.question5, student.question6]
                    japanese_fields = ['question1_jp', 'question2_jp', 'question3_jp', 
                                     'question4_jp', 'question5_jp', 'question6_jp']
                    
                    for i, (question_text, jp_field) in enumerate(zip(questions, japanese_fields), 1):
                        if question_text and question_text.strip():
                            try:
                                translated = translate_to_japanese(question_text)
                                setattr(student, jp_field, translated)
                                logging.info(f"Question {i} translated successfully for student {student_id}")
                            except Exception as e:
                                logging.error(f"Translation failed for question {i}, student {student_id}: {e}")
                                setattr(student, jp_field, question_text)  # Fallback to original
                    
                    # Save translations
                    db.session.commit()
                    logging.info(f"Successfully processed translations for student {student_id}")
                else:
                    logging.info(f"Student {student_id} is already in Japanese, skipping translation")
                
                logging.info(f"Translation completed and saved for student {student_id}")
                
            except Exception as e:
                logging.error(f"Translation error for student {student_id}: {e}")
                db.session.rollback()

    @app.route('/login')
    def login():
        """Teacher/organizer login page"""
        return render_template('login.html')

    @app.route('/verify-token', methods=['POST'])
    def verify_token():
        """Verify Firebase token and log in user"""
        data = request.get_json()
        id_token = data.get('idToken') or data.get('token')  # Accept both formats
        
        if not id_token:
            return jsonify({'success': False, 'error': 'No token provided'}), 400
        
        try:
            # Verify the Firebase token
            decoded_token = verify_firebase_token(id_token)
            uid = decoded_token['uid']
            email = decoded_token.get('email', '')
            name = decoded_token.get('name', 'Unknown')
            
            # Store user info in session
            session['firebase_uid'] = uid
            session['user_info'] = {
                'uid': uid,
                'email': email,
                'name': name
            }
            session['teacher_authenticated'] = True  # Add this for compatibility
            session.permanent = True
            
            return jsonify({'status': 'success'})
        except Exception as e:
            logging.error(f"Token verification failed: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 401

    @app.route('/firebase-config')
    def firebase_config():
        """Provide Firebase configuration to frontend"""
        api_key = os.environ.get('FIREBASE_API_KEY')
        
        config = {
            'apiKey': api_key,
            'authDomain': 'studentvibe-b7628.firebaseapp.com',
            'projectId': 'studentvibe-b7628',
            'storageBucket': 'studentvibe-b7628.appspot.com',
            'messagingSenderId': '1041001533067',
            'appId': '1:1041001533067:web:a692ad19d96df88e6da4ae'
        }
        return jsonify(config)

    @app.route('/organizer-dashboard')
    def organizer_dashboard():
        """Main organizer dashboard"""
        if not session.get('teacher_authenticated'):
            return redirect(url_for('teacher_login'))
        
        try:
            # Get session password
            session_settings = SessionSettings.query.first()
            session_password = session_settings.session_password if session_settings else "VIBE123"
            
            # Get all students and squads
            students = Student.query.all()
            squads = Squad.query.all()
            
            # Get students not assigned to any squad
            solo_students_db = Student.query.filter_by(squad_id=None).all()
            
            # Check if squads exist
            squads_exist = len(squads) > 0
            
            # Check if analysis is complete (simplified check)
            analysis_complete = all(student.archetype for student in students) if students else False
            
            return render_template('organizer_dashboard_sophisticated.html',
                                 students=students,
                                 squads=squads,
                                 solo_students_db=solo_students_db,
                                 session_password=session_password,
                                 squads_exist=squads_exist,
                                 analysis_complete=analysis_complete)
                                 
        except Exception as e:
            logging.error(f"Dashboard error: {e}")
            flash('Error loading dashboard', 'error')
            return redirect(url_for('teacher_login'))
            return redirect(url_for('login'))

    @app.route('/student_profile/<int:student_id>')
    def student_profile(student_id):
        """View student profile"""
        if not session.get('user_info'):
            return redirect(url_for('login'))
        
        try:
            student = Student.query.get_or_404(student_id)
            
            # Create personality_signature object for template compatibility
            personality_signature = {
                'archetype': student.archetype,
                'core_strength': student.core_strength,
                'hidden_potential': student.hidden_potential,
                'conversation_catalyst': student.conversation_catalyst
            }
            
            return render_template('profile.html', 
                                 student=student, 
                                 personality_signature=personality_signature)
            
        except Exception as e:
            logging.error(f"Error loading student profile: {e}")
            return f"Error loading profile: {e}", 500

    @app.route('/squad_hub/<int:squad_id>')
    def squad_hub(squad_id):
        """View squad details"""
        try:
            squad = Squad.query.get_or_404(squad_id)
            return render_template('squad_hub.html', squad=squad)
            
        except Exception as e:
            logging.error(f"Error loading squad hub: {e}")
            return f"Error loading squad: {e}", 500

    @app.route('/generate_icebreaker/<int:squad_id>')
    def generate_icebreaker(squad_id):
        """Generate AI-powered icebreaker activities for a squad"""
        try:
            from openai_integration import generate_squad_icebreaker
            
            squad = Squad.query.get_or_404(squad_id)
            members = Student.query.filter_by(squad_id=squad_id).all()
            
            if not members:
                flash('No members found in this squad', 'error')
                return redirect(url_for('organizer_dashboard'))
            
            # Prepare member data for AI analysis
            squad_members_data = []
            for member in members:
                member_data = {
                    'name': member.name,
                    'archetype': member.archetype or '個性豊かな学生',
                    'core_strength': member.core_strength or 'Hidden Strength',
                    'hidden_potential': member.hidden_potential or 'Undiscovered Potential',
                    'conversation_catalyst': member.conversation_catalyst or 'Natural Connector'
                }
                squad_members_data.append(member_data)
            
            # Generate AI-powered icebreakers
            logging.info(f"Generating icebreakers for squad {squad.name} with {len(members)} members")
            icebreakers = generate_squad_icebreaker(squad_members_data, squad.name)
            
            # Store icebreakers in squad
            squad.icebreaker_text = json.dumps(icebreakers) if icebreakers else None
            db.session.commit()
            
            flash(f'Icebreaker activities generated for {squad.name}', 'success')
            return redirect(url_for('organizer_dashboard'))
            
        except Exception as e:
            logging.error(f"Error generating icebreaker: {e}")
            flash('Error generating icebreaker', 'error')
            return redirect(url_for('organizer_dashboard'))

    @app.route('/update_session_password', methods=['POST'])
    def update_session_password():
        """Generate a new session password"""
        if not session.get('user_info'):
            return redirect(url_for('login'))
        
        try:
            new_password = SessionSettings.update_password()
            flash(f'New session password created: {new_password}', 'success')
        except Exception as e:
            logging.error(f"Error updating session password: {e}")
            flash('Error updating session password', 'error')
        
        return redirect(url_for('organizer_dashboard'))

    @app.route('/clear_all_data', methods=['POST'])
    def clear_all_data():
        """Clear all student and squad data"""
        if not session.get('user_info'):
            return redirect(url_for('login'))
        
        try:
            # Delete all squads and students
            Squad.query.delete()
            Student.query.delete()
            db.session.commit()
            flash('All student and squad data cleared successfully', 'success')
        except Exception as e:
            logging.error(f"Error clearing data: {e}")
            flash('Error clearing data', 'error')
            db.session.rollback()
        
        return redirect(url_for('organizer_dashboard'))

    @app.route('/logout')
    def logout():
        """Logout user"""
        session.clear()
        flash('You have been logged out successfully', 'success')
        return redirect(url_for('index'))

    @app.route('/teacher-logout')
    def teacher_logout():
        """Logout teacher and clear session"""
        session.clear()
        return redirect(url_for('teacher_login'))

    # Add missing sophisticated routes here
    
    @app.route('/teacher/create-squads', methods=['POST'])
    def create_squads():
        """AI-powered squad formation - The Sorting Hat of the application"""
        
        # Debug session authentication
        teacher_auth = session.get('teacher_authenticated')
        logging.info(f"🎯 CREATE SQUADS ROUTE CALLED! Teacher authenticated: {teacher_auth}")
        
        if not teacher_auth:
            logging.warning("Authentication failed in create_squads route")
            return redirect(url_for('teacher_login'))
        
        try:
            # Step 1: Clean slate - Reset all existing squad assignments
            db.session.execute(db.text("UPDATE students SET squad_id = NULL"))
            Squad.query.delete()
            db.session.commit()
            
            # Step 2: Fetch all unassigned student submissions from database
            unassigned_students = Student.query.filter_by(squad_id=None).all()
            
            if len(unassigned_students) < 3:
                return redirect(url_for('organizer_dashboard'))
            
            # Step 3: Prepare student data for AI analysis
            students_data = []
            student_map = {}
            
            for student in unassigned_students:
                student_data = {
                    'id': student.id,
                    'name': student.name,
                    'archetype': student.archetype or '個性豊かな学生',
                    'core_strength': student.core_strength or 'Hidden Strength',
                    'hidden_potential': student.hidden_potential or 'Undiscovered Potential',
                    'conversation_catalyst': student.conversation_catalyst or 'Natural Connector',
                }
                students_data.append(student_data)
                student_map[student.id] = student
            
            logging.info(f"Sending {len(students_data)} students to AI for intelligent grouping")
            
            # Step 4: Send to AI for intelligent squad formation
            try:
                from openai_integration import group_students_into_squads
                logging.info("🤖 Calling AI for squad formation...")
                ai_response = group_students_into_squads(students_data)
                logging.info("🎯 AI squad formation completed successfully")
            except Exception as ai_error:
                logging.error(f"❌ AI squad formation failed: {str(ai_error)}")
                # Create a simple fallback grouping
                ai_response = create_simple_japanese_squads(students_data)
                logging.info(f"Fallback Response: {ai_response}")
            
            # Step 5: Parse AI response and validate structure
            if not isinstance(ai_response, dict) or 'squads' not in ai_response:
                raise ValueError("Invalid AI response format")
            
            squads_created = 0
            
            # Step 6: Process each AI-suggested squad and save to database
            for i, squad_data in enumerate(ai_response['squads'], 1):
                required_keys = ['squad_name', 'shared_interests', 'member_ids']
                if not all(key in squad_data for key in required_keys):
                    logging.warning(f"Skipping squad with missing keys: {squad_data}")
                    continue
                
                # Create new squad record
                new_squad = Squad()
                new_squad.squad_rank = i
                new_squad.name = squad_data['squad_name']
                new_squad.shared_interests = squad_data['shared_interests']
                new_squad.squad_icon = 'fa-users'  # Default icon
                db.session.add(new_squad)
                db.session.flush()
                
                # Assign students to this squad
                members_assigned = 0
                for student_id in squad_data['member_ids']:
                    if student_id in student_map:
                        student = student_map[student_id]
                        student.squad_id = new_squad.id
                        members_assigned += 1
                        logging.info(f"Assigned {student.name} to squad '{squad_data['squad_name']}'")
                
                if members_assigned > 0:
                    squads_created += 1
                    logging.info(f"Created squad '{squad_data['squad_name']}' with {members_assigned} members")
                else:
                    db.session.delete(new_squad)
            
            # Step 7: Commit all changes to database
            db.session.commit()
            logging.info(f"✅ Database commit successful! {squads_created} squads created")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error during squad formation: {str(e)}")
        
        return redirect(url_for('organizer_dashboard'))
    
    def create_simple_japanese_squads(students_data):
        """Fallback squad creation with Japanese names when AI is unavailable"""
        squads = []
        current_squad = []
        squad_names = [
            "チームハーモニー",  # Team Harmony
            "クリエイティブスピリッツ",  # Creative Spirits  
            "アドベンチャーフレンズ",  # Adventure Friends
            "ドリームチェイサーズ",  # Dream Chasers
            "フューチャースターズ",  # Future Stars
            "ユニティーパワー"  # Unity Power
        ]
        
        interests_jp = [
            "様々な興味と個性を持つ多様なグループです",
            "創造性と協力の精神で結ばれた仲間です",
            "新しい冒険と学びを追求するチームです",
            "お互いの強みを活かし合う素晴らしいグループです",
            "共に成長し、夢を実現するパートナーです",
            "協力と友情で繋がった特別なチームです"
        ]
        
        squad_number = 0
        
        for student in students_data:
            current_squad.append(student['id'])
            
            if len(current_squad) == 4 or student == students_data[-1]:
                if len(current_squad) >= 3 or len(squads) == 0:
                    squad_name = squad_names[squad_number % len(squad_names)]
                    shared_interest = interests_jp[squad_number % len(interests_jp)]
                    
                    squads.append({
                        'squad_name': squad_name,
                        'shared_interests': shared_interest,
                        'member_ids': current_squad.copy()
                    })
                    squad_number += 1
                else:
                    if squads:
                        squads[-1]['member_ids'].extend(current_squad)
                
                current_squad = []
        
        return {'squads': squads}
    
    @app.route('/new-session-password', methods=['POST'])
    def new_session_password():
        """Generate a new session password"""
        if not session.get('teacher_authenticated'):
            return redirect(url_for('teacher_login'))
        
        try:
            # Generate new password
            import random
            import string
            new_password = 'VIBE' + ''.join(random.choices(string.digits, k=3))
            
            # Update or create session settings
            session_settings = SessionSettings.query.first()
            if not session_settings:
                session_settings = SessionSettings(session_password=new_password)
                db.session.add(session_settings)
            else:
                session_settings.session_password = new_password
            
            db.session.commit()
            logging.info(f"Generated new session password: {new_password}")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error generating new session password: {str(e)}")
        
        return redirect(url_for('organizer_dashboard'))
    
    @app.route('/analyze-batch', methods=['POST'])
    def analyze_batch():
        """Analyze batch of students with AI personality generation"""
        if not session.get('teacher_authenticated'):
            return redirect(url_for('teacher_login'))
        
        try:
            from openai_integration import generate_archetype, generate_core_strength, generate_hidden_potential, generate_conversation_catalyst
            
            students = Student.query.all()
            
            for student in students:
                # Prepare student answers for AI analysis
                student_answers = {
                    'question1': student.question1,
                    'question2': student.question2,
                    'question3': student.question3,
                    'question4': student.question4,
                    'question5': student.question5,
                    'question6': student.question6
                }
                
                # Generate AI-powered personality traits if not already set
                if not student.archetype:
                    logging.info(f"Generating archetype for student {student.name}")
                    student.archetype = generate_archetype(student_answers)
                
                if not student.core_strength:
                    logging.info(f"Generating core strength for student {student.name}")
                    student.core_strength = generate_core_strength(student_answers)
                
                if not student.hidden_potential:
                    logging.info(f"Generating hidden potential for student {student.name}")
                    student.hidden_potential = generate_hidden_potential(student_answers)
                
                if not student.conversation_catalyst:
                    logging.info(f"Generating conversation catalyst for student {student.name}")
                    student.conversation_catalyst = generate_conversation_catalyst(student_answers)
            
            db.session.commit()
            logging.info("Batch analysis completed with AI-generated personality traits")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in batch analysis: {str(e)}")
        
        return redirect(url_for('organizer_dashboard'))
    
    @app.route('/clear-squads', methods=['POST'])
    def clear_squads():
        """Complete reset - delete all records from both Student and Squad tables"""
        if not session.get('teacher_authenticated'):
            return redirect(url_for('teacher_login'))
        
        try:
            students_count = Student.query.count()
            squads_count = Squad.query.count()
            
            Student.query.delete()
            Squad.query.delete()
            db.session.commit()
            
            logging.info(f"Complete database reset: {students_count} students deleted, {squads_count} squads deleted")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to complete database reset: {str(e)}")
        
        return redirect(url_for('organizer_dashboard'))
    
    @app.route('/delete-squad/<int:squad_id>')
    def delete_squad(squad_id):
        """Delete a specific squad and cleanly unassign all members"""
        if not session.get('teacher_authenticated'):
            return redirect(url_for('teacher_login'))
        
        try:
            squad = Squad.query.get_or_404(squad_id)
            squad_name = squad.name
            
            # Unassign all students from this squad
            students_to_unassign = Student.query.filter_by(squad_id=squad_id).all()
            for student in students_to_unassign:
                student.squad_id = None
                logging.info(f"Unassigned student {student.name} from squad {squad_name}")
            
            db.session.flush()
            db.session.delete(squad)
            db.session.commit()
            
            logging.info(f"Deleted squad {squad_name} and unassigned {len(students_to_unassign)} members")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to delete squad {squad_id}: {str(e)}")
        
        return redirect(url_for('organizer_dashboard'))
    
    @app.route('/delete-student/<int:student_id>')
    def delete_student(student_id):
        """Delete a student record from the database"""
        if not session.get('teacher_authenticated'):
            return redirect(url_for('teacher_login'))
        
        try:
            student = Student.query.get_or_404(student_id)
            student_name = student.name
            
            db.session.delete(student)
            db.session.commit()
            
            logging.info(f"Deleted student {student_name} (ID: {student_id})")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to delete student {student_id}: {str(e)}")
        
        return redirect(url_for('organizer_dashboard'))

    @app.route('/find-squad')
    def find_squad():
        """Find squad page for students"""
        return render_template('find_squad.html')

# Initialize the app and configure it immediately at module level
try:
    # Load environment variables from .env file if it exists
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print("✅ Environment variables loaded from .env file")
    except FileNotFoundError:
        print("⚠️ No .env file found, using system environment variables")

    # Create database tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables created")

    # Register all routes
    register_all_routes()
    print("✅ All routes registered")

except Exception as e:
    print(f"❌ Error during app initialization: {e}")
    # Still create app_instance even if there are errors
    pass

# This is the WSGI application that Firebase App Hosting will use
app_instance = app

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_ENV', 'production') == 'development'
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
