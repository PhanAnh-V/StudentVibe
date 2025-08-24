import logging
from flask import render_template, request, redirect, url_for, session, jsonify, flash
from app import app, db, csrf
from models import Student, SessionSettings, Squad
from forms import StudentForm, TeacherLoginForm, StudentLoginForm

# Health check route for Firebase App Hosting
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'message': 'VibeCheck is running'}, 200

import firebase_admin
from firebase_admin import credentials, auth
# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
except Exception as e:
    logging.error(f"Failed to initialize Firebase Admin SDK: {e}")
# Removed RQ queue import - using threading instead
import logging
import re
import json
import random
import traceback
from collections import Counter, defaultdict
# AI recommendations functions will be imported where needed

# Health check endpoint for Firebase App Hosting
@app.route('/health')
def health_check():
    """Health check endpoint for Firebase App Hosting"""
    return jsonify({"status": "healthy", "message": "VibeCheck is running"}), 200

def load_questionnaire_data():
    """Load questionnaire data from questions.json file"""
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("questions.json file not found")
        return None
    except json.JSONDecodeError:
        logging.error("Error decoding questions.json")
        return None

@app.route('/')
def index():
    """Language selection homepage"""
    return render_template('language_select.html')

@app.route('/select-language/<lang>')
def select_language(lang):
    """Handle language selection and redirect to session password"""
    # Validate language choice
    valid_languages = ['en', 'vi', 'zh', 'ja']
    if lang not in valid_languages:
        lang = 'en'  # Default to English for invalid choices
    
    # Store language choice in session
    session['selected_language'] = lang
    session.permanent = True
    
    # Redirect to session password page
    return redirect(url_for('session_password'))

@app.route('/session-password')
def session_password():
    """Session password page that shows questionnaire when authenticated"""
    # If already authenticated, show the questionnaire form
    if session.get('session_authenticated'):
        # Load questionnaire data
        questionnaire_data = load_questionnaire_data()
        if not questionnaire_data:

            return render_template('session_password.html')
        
        # Get selected language from session, default to English
        selected_language = session.get('selected_language', 'en')
        
        # Get questions for the selected language
        questions = questionnaire_data['questions'].get(selected_language, questionnaire_data['questions']['en'])
        form_labels = questionnaire_data['form_labels']
        
        # Log question descriptions to verify full text is loading
        print(f"=== QUESTIONNAIRE DEBUG INFO ===")
        print(f"Selected language: {selected_language}")
        print(f"Number of questions loaded: {len(questions)}")
        for i, question in enumerate(questions):
            print(f"Question {i+1} - Title: {question.get('title', 'N/A')}")
            print(f"Question {i+1} - Description: {question.get('description', 'N/A')}")
            print(f"Question {i+1} - Description length: {len(question.get('description', ''))}")
            print("---")
        print("=== END DEBUG INFO ===")
        
        form = StudentForm()
        return render_template('questionnaire.html', form=form, questions=questions, form_labels=form_labels, selected_language=selected_language)
    
    # Otherwise show session password entry
    return render_template('session_password.html')

@app.route('/session-auth', methods=['POST'])
def session_auth():
    """Handle session password authentication"""
    entered_password = request.form.get('session_password', '').strip().upper()
    current_password = SessionSettings.get_current_password()
    
    if entered_password == current_password:
        session['session_authenticated'] = True
        print(f"Session password SET successfully: {session['session_authenticated']}")
        return redirect(url_for('session_password'))
    else:
        print(f"Session password validation FAILED: entered={entered_password}, current={current_password}")
        return redirect(url_for('session_password'))

def translate_student_answers_in_background(student_id, student_language):
    """
    Background function dedicated only to translation - including special handling for Japanese students
    """
    with app.app_context():
        try:
            from openai_integration import translate_to_japanese
            
            student = Student.query.get(student_id)
            if not student:
                logging.error(f"Could not find student with ID {student_id} to translate.")
                return
                
            logging.info(f"Starting translation for student {student_id} ({student.name}) in language: {student_language}")
            
            # Special handling for Japanese students
            if student_language == 'ja':
                # Student chose Japanese - copy original answers to _jp fields
                student.question1_jp = student.question1
                student.question2_jp = student.question2
                student.question3_jp = student.question3
                student.question4_jp = student.question4
                student.question5_jp = student.question5
                student.question6_jp = student.question6
                logging.info(f"Japanese detected for student {student_id}, copied original answers")
            else:
                # Student chose other language - translate to Japanese
                logging.info(f"Translating answers for student {student_id} from {student_language} to Japanese")
                
                # Translate each answer individually with error handling and rate limiting
                translations = []
                import time
                for i, answer in enumerate([student.question1, student.question2, student.question3, 
                                          student.question4, student.question5, student.question6], 1):
                    try:
                        translation = translate_to_japanese(answer)
                        translations.append(translation)
                        logging.info(f"Question {i} translated successfully for student {student_id}")
                        # Add small delay to prevent rate limiting
                        time.sleep(0.2)
                    except Exception as e:
                        logging.error(f"Translation failed for question {i} of student {student_id}: {str(e)}")
                        translations.append("翻訳エラー")  # Use error message for failed translations
                
                # Assign translations to student
                student.question1_jp = translations[0]
                student.question2_jp = translations[1]
                student.question3_jp = translations[2]
                student.question4_jp = translations[3]
                student.question5_jp = translations[4]
                student.question6_jp = translations[5]
                
                logging.info(f"Successfully processed translations for student {student_id}")
            
            # Save changes to database
            db.session.commit()
            logging.info(f"Translation completed and saved for student {student_id}")
            
        except Exception as e:
            logging.error(f"Translation error for student {student_id}: {str(e)}")
            db.session.rollback()

@app.route('/submit-form', methods=['POST'])
def submit_form():
    """Handle questionnaire form submission"""
    print('=== FORM SUBMISSION ROUTE STARTED ===')
    print(f'Form submission initiated. Current session content: {dict(session)}')
    print(f'Session authenticated: {session.get("session_authenticated")}')
    
    if not session.get('session_authenticated'):
        print('Session not authenticated, redirecting to session password')
        return redirect(url_for('session_password'))
    
    print('Creating StudentForm instance...')
    form = StudentForm()
    print('Form created, validating...')
    
    if form.validate_on_submit():
        print('Form validation PASSED')
        try:
            print('--- Starting form submission ---')
            print(f'Form data received: name={form.name.data}, country={form.country.data}, gender={form.gender.data}')
            
            # Combine all answers for the vibes field (for backward compatibility)
            combined_vibes = f"{form.question1.data} {form.question2.data} {form.question3.data} {form.question4.data} {form.question5.data} {form.question6.data}"
            print(f'Combined vibes created: {len(combined_vibes)} characters')
            
            # Generate unique submission ID
            submission_id = Student.generate_submission_id()
            print(f'Generated submission ID: {submission_id}')
            
            # Get original answers
            original_answers = [
                form.question1.data,
                form.question2.data,
                form.question3.data,
                form.question4.data,
                form.question5.data,
                form.question6.data
            ]
            print(f'Original answers collected: {len(original_answers)} answers')
            
            # Get student's chosen language from session
            student_language = session.get('language', 'en')
            print(f'Student language detected: {student_language}')
            
            # Debug session data to understand language detection
            logging.info(f"Session data: {dict(session)}")
            logging.info(f"Processing answers for language: {student_language}")
            
            print('--- Creating student record ---')
            # Create new student record with original answers only
            student = Student()
            student.name = form.name.data
            student.vibes = combined_vibes
            student.question1 = form.question1.data
            student.question2 = form.question2.data
            student.question3 = form.question3.data
            student.question4 = form.question4.data
            student.question5 = form.question5.data
            student.question6 = form.question6.data
            student.country = form.country.data
            student.gender = form.gender.data
            student.submission_id = submission_id
            print('Student record created with basic info')
            
            print('--- Data prepared, attempting to save to database ---')
            try:
                db.session.add(student)
                print('Student added to database session')
                db.session.commit()
                print('--- Database save successful ---')
            except Exception as db_error:
                print(f'DATABASE ERROR during commit: {db_error}')
                raise db_error
                
            logging.info(f"New student registered: {student.name} (ID: {student.id}, Submission ID: {submission_id})")
            
            # Start background translation in a separate thread
            import threading
            student_language = session.get('selected_language', 'en')
            translation_thread = threading.Thread(
                target=translate_student_answers_in_background,
                args=(student.id, student_language),
                daemon=True
            )
            translation_thread.start()
            logging.info(f"Started background translation for student {student.id} in language {student_language}")
            
            # Store submission ID in session for success page
            session['submission_id'] = submission_id
            session['student_name'] = form.name.data
            
            # Clear session authentication so form can't be submitted again
            session.pop('session_authenticated', None)
            
            print('--- Form submission completed successfully ---')
            return redirect(url_for('success'))
        except Exception as e:
            print(f'FORM SUBMISSION FAILED WITH ERROR: {e}')
            print(f'Error type: {type(e).__name__}')
            print(f'Error args: {e.args}')
            import traceback
            print(f'Full traceback:')
            traceback.print_exc()
            db.session.rollback()
            logging.error(f"Form submission failed with error: {e}")
            logging.error(f"Full traceback: {traceback.format_exc()}")
            flash('エラーが発生しました。もう一度お試しください。', 'error')
            return redirect(url_for('session_password'))
    
    # If form validation fails, render form with errors
    print('Form validation FAILED')
    print(f'Form errors: {form.errors}')
    print('Rendering questionnaire with validation errors')
    return render_template('questionnaire.html', form=form)

@app.route('/success')
def success():
    """Success confirmation page"""
    print("--- DEBUG: Success route has been called. ---")
    submission_id = session.get('submission_id')
    student_name = session.get('student_name')
    
    # Load site content for multilingual support
    site_content = None
    try:
        with open('site_content.json', 'r', encoding='utf-8') as f:
            site_content = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading site_content.json: {e}")
        site_content = {}
    
    # Get user's selected language, default to English
    lang = session.get('selected_language', 'en')
    print(f"--- DEBUG: Language selected is: {lang} ---")
    
    # Create dictionary with language-specific text
    success_text = {}
    if site_content and 'success_page' in site_content:
        success_page = site_content['success_page']
        
        # Get text for user's language, fallback to English
        success_text['thank_you'] = success_page.get('thank_you', {}).get(lang, 
            success_page.get('thank_you', {}).get('en', 'Thank you, {name}!'))
        success_text['id_reminder'] = success_page.get('id_reminder', {}).get(lang,
            success_page.get('id_reminder', {}).get('en', 'Please save this ID.'))
        success_text['scroll_prompt'] = success_page.get('scroll_prompt', {}).get(lang,
            success_page.get('scroll_prompt', {}).get('en', 'Scroll down for a surprise!'))
        
        # Format the thank_you message with student name, or default
        if student_name:
            success_text['thank_you'] = success_text['thank_you'].format(name=student_name)
        else:
            # Remove {name} placeholder if no name available
            success_text['thank_you'] = success_text['thank_you'].replace(', {name}', '').replace('{name}', '')
    
    # Default fallback values if no site_content
    if not success_text:
        success_text = {
            'thank_you': 'ありがとうございました！',
            'id_reminder': 'このIDを保存してください。',
            'scroll_prompt': 'スクロールしてみてください！'
        }
    
    # Default submission_id if missing
    if not submission_id:
        submission_id = 'TEST-123'
    
    print(f"--- DEBUG: Prepared success_text object: {success_text} ---")
    print(f"--- DEBUG: submission_id: {submission_id}, student_name: {student_name} ---")
    
    # Get app explanation for all languages (for template flexibility)
    app_explanation = site_content.get('success_page', {}).get('app_explanation', {})
    
    # Clear the session data after displaying
    session.pop('submission_id', None)
    session.pop('student_name', None)
    
    print("--- DEBUG: Now attempting to render success.html template. ---")
    
    return render_template('success.html', 
                         submission_id=submission_id,
                         student_name=student_name,
                         success_text=success_text,
                         app_explanation=app_explanation)

@app.route('/find-squad', methods=['GET', 'POST'])
def find_squad():
    """Find squad by submission ID"""
    if request.method == 'POST':
        submission_id = request.form.get('submission_id', '').strip().upper()
        
        if not submission_id:
            return render_template('find_squad.html')
        
        # Find student by submission ID
        student = Student.query.filter_by(submission_id=submission_id).first()
        
        if not student:
            return render_template('find_squad.html')
        
        # Check if student has been assigned to a squad
        if student.squad_id:
            # Redirect to the squad hub
            return redirect(url_for('squad_hub', squad_id=student.squad_id))
        else:
            # No squad assigned yet
            return render_template('find_squad.html')
    
    # GET request - show the form
    return render_template('find_squad.html')

@app.route('/squad-hub/<int:squad_id>')
def squad_hub(squad_id):
    """Display the squad hub for a specific squad"""
    try:
        # Fetch the squad with all its members
        squad = Squad.query.get_or_404(squad_id)
        
        # Randomly select a first speaker from squad members
        first_speaker = random.choice(squad.members) if squad.members else None
        
        # Parse the JSON icebreaker_text into a Python object
        icebreaker_data = None
        if squad.icebreaker_text:
            try:
                icebreaker_data = json.loads(squad.icebreaker_text)
                logging.info(f"Successfully parsed icebreaker data for squad {squad_id}: {icebreaker_data}")
            except (json.JSONDecodeError, TypeError) as e:
                logging.error(f"Error parsing icebreaker JSON for squad {squad_id}: {e}")
                # If JSON parsing fails, create a fallback structure
                icebreaker_data = None
        
        return render_template('squad_hub.html', squad=squad, icebreaker_data=icebreaker_data, first_speaker=first_speaker)
        
    except Exception as e:
        logging.error(f"Error accessing squad hub {squad_id}: {str(e)}")
        return redirect(url_for('find_squad'))

@app.route('/profile/<int:student_id>')
def student_profile(student_id):
    """Student profile page displaying detailed character sheet"""
    try:
        # Fetch the student with all their data
        student = Student.query.get(student_id)
        
        if not student:
            # Student not found - show error on profile page itself
            return render_template('profile.html', 
                                 student=None,
                                 error_message="Profile not found")
        
        # Load questionnaire data for displaying question titles
        try:
            questions = load_questionnaire_data()
            en_questions = questions.get('en', [])
        except:
            en_questions = []
        
        # Create a mapping of answers to questions for easy display (including Japanese translations)
        if len(en_questions) >= 6:
            student_answers = [
                {'question': en_questions[0]['title'], 'answer': student.question1, 'answer_jp': getattr(student, 'question1_jp', '')},
                {'question': en_questions[1]['title'], 'answer': student.question2, 'answer_jp': getattr(student, 'question2_jp', '')},
                {'question': en_questions[2]['title'], 'answer': student.question3, 'answer_jp': getattr(student, 'question3_jp', '')},
                {'question': en_questions[3]['title'], 'answer': student.question4, 'answer_jp': getattr(student, 'question4_jp', '')},
                {'question': en_questions[4]['title'], 'answer': student.question5, 'answer_jp': getattr(student, 'question5_jp', '')},
                {'question': en_questions[5]['title'], 'answer': student.question6, 'answer_jp': getattr(student, 'question6_jp', '')},
            ]
        else:
            # Fallback question titles if questions.json is not available
            student_answers = [
                {'question': 'Adventure Preference', 'answer': student.question1, 'answer_jp': getattr(student, 'question1_jp', '')},
                {'question': 'Passion Interest', 'answer': student.question2, 'answer_jp': getattr(student, 'question2_jp', '')},
                {'question': 'Humor Style', 'answer': student.question3, 'answer_jp': getattr(student, 'question3_jp', '')},
                {'question': 'Secret Superpower', 'answer': student.question4, 'answer_jp': getattr(student, 'question4_jp', '')},
                {'question': 'Personal Vibe', 'answer': student.question5, 'answer_jp': getattr(student, 'question5_jp', '')},
                {'question': 'Team Quality', 'answer': student.question6, 'answer_jp': getattr(student, 'question6_jp', '')},
            ]
        
        # Get enhanced profile data (legacy compatibility)
        vibes_text = student.vibes or student.get_combined_answers()
        interests = get_interest_categories_with_colors(vibes_text)
        
        # Personality Signature data (new AI-generated fields)
        personality_signature = {
            'archetype': getattr(student, 'archetype', '個性豊かな学生'),
            'core_strength': getattr(student, 'core_strength', ''),
            'hidden_potential': getattr(student, 'hidden_potential', ''),
            'conversation_catalyst': getattr(student, 'conversation_catalyst', '')
        }
        
        return render_template('profile.html', 
                             student=student,
                             student_answers=student_answers,
                             personality_signature=personality_signature,
                             interests=interests)
        
    except Exception as e:
        logging.error(f"Error accessing student profile {student_id}: {str(e)}")
        # Show error on profile page itself instead of redirecting
        return render_template('profile.html', 
                             student=None,
                             error_message="Profile not found")

@app.route('/login/teacher', methods=['GET', 'POST'])
def teacher_login():
    """Teacher login with password authentication"""
    form = TeacherLoginForm()
    
    if form.validate_on_submit():
        password = form.password.data
        if password == "1234":  # Teacher password
            session['teacher_authenticated'] = True
            session.permanent = True  # Make session permanent
            logging.info(f"Teacher login successful. Session set: {session.get('teacher_authenticated')}")
            # No flash message here - redirect directly to avoid message carry-over
            return redirect(url_for('teacher'))
        else:
            pass  # Invalid password, form will show validation errors
    
    return render_template('teacher_login.html', form=form)



@app.route('/logout_student', methods=['POST'])
def logout_student():
    """Logout student and clear session"""
    session.pop('student_id', None)
    return '', 200


@app.route('/organizer-dashboard')
def organizer_dashboard():
    # This is a protected route.
    # If the user's Firebase UID is not in the session, they are not logged in.
    if 'firebase_uid' not in session:
        return redirect(url_for('login'))

    # The rest of this code is the same as your old /teacher route.
    try:
        students = Student.query.order_by(Student.created_at.desc()).all()
        current_session_password = SessionSettings.get_current_password()
        squads = Squad.query.all()
        solo_students_db = Student.query.filter_by(squad_id=None).all()

        squads_exist = Squad.query.count() > 0
        unanalyzed_students_count = Student.query.filter(
            db.or_(Student.archetype.is_(None), Student.archetype == "")
        ).count()
        analysis_complete = unanalyzed_students_count == 0

        return render_template('teacher.html', 
                             students=students,
                             squads=squads,
                             solo_students_db=solo_students_db,
                             session_password=current_session_password,
                             squads_exist=squads_exist,
                             analysis_complete=analysis_complete)
    except Exception as e:
        logging.error(f"Error in organizer_dashboard: {e}")
        traceback.print_exc()
        return "The dashboard encountered an error. Check the console for details.", 500
        
@app.route('/logout')
def logout():
    """Organizer logout: clear firebase_uid from session and redirect to home."""
    session.pop('firebase_uid', None)
    return redirect(url_for('index'))

@app.route('/teacher')
def teacher():
    """Teacher dashboard with authentication required"""
    # Check if teacher is authenticated
    if not session.get('teacher_authenticated'):
        return redirect(url_for('teacher_login'))
    
    try:
        # Fetch all students from database
        students = Student.query.order_by(Student.created_at.desc()).all()
        logging.info(f"Teacher accessed dashboard. Found {len(students)} students.")
        
        # Get solo students and AI advice from session
        solo_students = session.get('solo_students', [])
        ai_advice = {}
        for student in solo_students:
            advice_key = f'ai_advice_{student["id"]}'
            if advice_key in session:
                ai_advice[student['id']] = session[advice_key]
        
        # Add interest visualization data to students
        students_with_interests = []
        for student in students:
            student_dict = {
                'id': student.id,
                'name': student.name,
                'vibes': student.vibes or student.get_combined_answers(),
                'country': student.country,
                'gender': student.gender,
                'created_at': student.created_at,
                'interests': get_interest_categories_with_colors(student.vibes or student.get_combined_answers())
            }
            students_with_interests.append(student_dict)
        
        # Get current session password
        current_session_password = SessionSettings.get_current_password()
        
        # Fetch all squads from database with their members
        squads = Squad.query.all()
        solo_students_db = Student.query.filter_by(squad_id=None).all()
        
        # Check completion status for Squad Creation and Batch Analysis
        # Squad Creation: Check if any Squad records exist
        squads_exist = Squad.query.count() > 0
        
        # Batch Analysis: Check if there are students that still need analysis (archetype field is empty/null)
        unanalyzed_students_count = Student.query.filter(
            db.or_(Student.archetype.is_(None), Student.archetype == "")
        ).count()
        analysis_complete = unanalyzed_students_count == 0
        
        return render_template('teacher.html', 
                             students=students_with_interests,
                             squads=squads,
                             solo_students_db=solo_students_db,
                             ai_advice=ai_advice,
                             session_password=current_session_password,
                             squads_exist=squads_exist,
                             analysis_complete=analysis_complete)
    
    except Exception as e:
        print("!!! TEACHER DASHBOARD CRASHED !!!")
        print(f"ERROR: {e}")
        traceback.print_exc()
        # Return a simple error message instead of crashing
        return "The teacher dashboard encountered an error. Check the console for details.", 500

@app.route('/teacher/new-session-password', methods=['POST'])
def new_session_password():
    """Generate new session password for teacher"""
    if not session.get('teacher_authenticated'):
        return redirect(url_for('teacher_login'))
    
    new_password = SessionSettings.update_password()
    logging.info(f"Teacher generated new session password: {new_password}")
    
    return redirect(url_for('teacher'))

@app.route('/teacher/logout')
def teacher_logout():
    """Log out teacher and clear session"""
    session.pop('teacher_authenticated', None)
    return redirect(url_for('teacher'))

# Global circuit breaker state for AI functions
circuit_breaker_state = {
    'failure_count': 0,
    'last_failure_time': None,
    'circuit_open': False,
    'success_count': 0
}

def intelligent_ai_call_with_retry(ai_function, student_answers, function_name, fallback_value, max_retries=3):
    """
    Intelligent retry mechanism with circuit breaker pattern and adaptive timeout
    """
    import time
    
    # Circuit breaker check
    if circuit_breaker_state['circuit_open']:
        if time.time() - circuit_breaker_state['last_failure_time'] > 60:  # Reset after 1 minute
            circuit_breaker_state['circuit_open'] = False
            circuit_breaker_state['failure_count'] = 0
            print(f"🔄 Circuit breaker reset for {function_name}")
        else:
            print(f"⚡ Circuit breaker open for {function_name}, using fallback")
            return fallback_value
    
    start_time = time.time()
    
    for attempt in range(max_retries):
        try:
            # Calculate delay with exponential backoff (1s, 2s, 4s)
            if attempt > 0:
                delay = min(2 ** (attempt - 1), 8)  # Cap at 8 seconds
                print(f"⏳ Retrying {function_name} in {delay}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            
            # Call the AI function with timeout monitoring
            attempt_start = time.time()
            result = ai_function(student_answers)
            attempt_duration = time.time() - attempt_start
            
            # Validate result quality
            if result and result.strip() and result != fallback_value and len(result.strip()) > 5:
                # Success - reset circuit breaker
                circuit_breaker_state['failure_count'] = 0
                circuit_breaker_state['success_count'] += 1
                circuit_breaker_state['circuit_open'] = False
                
                total_duration = time.time() - start_time
                print(f"✓ {function_name} succeeded on attempt {attempt + 1} ({attempt_duration:.1f}s, total: {total_duration:.1f}s)")
                return result
            else:
                print(f"⚠ {function_name} returned low-quality result on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    circuit_breaker_state['failure_count'] += 1
                    return fallback_value
                    
        except Exception as e:
            error_type = type(e).__name__
            print(f"✗ {function_name} failed on attempt {attempt + 1}: {error_type} - {str(e)}")
            
            # Handle different error types
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                print(f"🕐 Timeout error for {function_name}")
            elif "rate limit" in str(e).lower():
                print(f"⏱ Rate limit error for {function_name}, extending delay")
                if attempt < max_retries - 1:
                    time.sleep(10)  # Extended delay for rate limits
            
            if attempt == max_retries - 1:
                circuit_breaker_state['failure_count'] += 1
                circuit_breaker_state['last_failure_time'] = time.time()
                
                # Open circuit breaker after 3 consecutive failures
                if circuit_breaker_state['failure_count'] >= 3:
                    circuit_breaker_state['circuit_open'] = True
                    print(f"⚡ Circuit breaker opened for {function_name}")
                
                return fallback_value
    
    return fallback_value

@app.route('/teacher/analyze-batch', methods=['POST'])
def analyze_batch():
    """Analyze the next batch of students with intelligent retry mechanism"""
    print("--- User clicked 'Analyze Batch'. Route was called. ---")
    
    # Check if teacher is authenticated
    if not session.get('teacher_authenticated'):
        return redirect(url_for('teacher_login'))
    
    try:
        # Find all students who have not yet been analyzed (archetype field is empty or null)
        # Reduced batch size to 2 for better reliability and faster processing
        unanalyzed_students = Student.query.filter(
            db.or_(Student.archetype.is_(None), Student.archetype == "")
        ).limit(2).all()
        
        print(f"Found {len(unanalyzed_students)} students to analyze.")
        
        if not unanalyzed_students:
            flash("すべての学生の分析が完了しました。", "info")
            return redirect(url_for('teacher'))
        
        # Import AI personality generation functions
        from openai_integration import generate_archetype, generate_core_strength, generate_hidden_potential, generate_conversation_catalyst
        
        import time
        successfully_analyzed = 0
        total_ai_calls = 0
        successful_ai_calls = 0
        fallback_used = 0
        batch_start_time = time.time()
        
        # Process each student in the batch with enhanced monitoring
        for student_idx, student in enumerate(unanalyzed_students):
            try:
                student_start_time = time.time()
                print(f"🔄 Processing student {student_idx + 1}/{len(unanalyzed_students)}: {student.name}")
                
                # Prepare student answers for AI analysis
                student_answers = {
                    'question1': student.question1,
                    'question2': student.question2,
                    'question3': student.question3,
                    'question4': student.question4,
                    'question5': student.question5,
                    'question6': student.question6
                }
                
                # Generate personality signature using intelligent retry mechanism
                ai_functions = [
                    (generate_archetype, "archetype", "個性豊かな学生"),
                    (generate_core_strength, "core_strength", "創造的な思考力と独自の視点を持っています。"),
                    (generate_hidden_potential, "hidden_potential", "リーダーシップの才能が眠っている可能性があります。"),
                    (generate_conversation_catalyst, "conversation_catalyst", "趣味や興味のあることについて話すと、とても輝いて見えます。")
                ]
                
                student_results = {}
                
                for ai_func, field_name, fallback in ai_functions:
                    total_ai_calls += 1
                    result = intelligent_ai_call_with_retry(ai_func, student_answers, field_name, fallback)
                    
                    if result != fallback:
                        successful_ai_calls += 1
                    else:
                        fallback_used += 1
                    
                    student_results[field_name] = result
                
                # Assign results to student
                student.archetype = student_results['archetype']
                student.core_strength = student_results['core_strength']
                student.hidden_potential = student_results['hidden_potential']
                student.conversation_catalyst = student_results['conversation_catalyst']
                
                # Save changes to database after each student
                db.session.commit()
                successfully_analyzed += 1
                
                student_duration = time.time() - student_start_time
                print(f"✅ Completed {student.name} in {student_duration:.1f}s")
                
                logging.info(f"Successfully analyzed student {student.name} (ID: {student.id})")
                
            except Exception as e:
                logging.error(f"Error analyzing student {student.name}: {str(e)}")
                # Set fallback values for this student
                student.archetype = "個性豊かな学生"
                student.core_strength = "創造的な思考力と独自の視点を持っています。"
                student.hidden_potential = "リーダーシップの才能が眠っている可能性があります。"
                student.conversation_catalyst = "趣味や興味のあることについて話すと、とても輝いて見えます。"
                db.session.commit()
                successfully_analyzed += 1
                fallback_used += 4
        
        # Count remaining unanalyzed students
        remaining_count = Student.query.filter(
            db.or_(Student.archetype.is_(None), Student.archetype == "")
        ).count()
        
        # Calculate batch performance metrics
        batch_duration = time.time() - batch_start_time
        success_rate = (successful_ai_calls / total_ai_calls * 100) if total_ai_calls > 0 else 0
        
        # Create enhanced status message with performance metrics
        if remaining_count == 0:
            flash(f"🎉 {successfully_analyzed}人の学生を分析しました。すべての分析が完了しました！ (成功率: {success_rate:.1f}%, 処理時間: {batch_duration:.1f}s)", "success")
        else:
            flash(f"📊 {successfully_analyzed}人の学生を分析しました。残り{remaining_count}人の学生が分析待ちです。 (成功率: {success_rate:.1f}%, フォールバック使用: {fallback_used}回)", "info")
        
        # Log detailed performance metrics
        print(f"📈 Batch Performance Summary:")
        print(f"   Students processed: {successfully_analyzed}")
        print(f"   Total AI calls: {total_ai_calls}")
        print(f"   Successful AI calls: {successful_ai_calls}")
        print(f"   Fallback used: {fallback_used}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Total time: {batch_duration:.1f}s")
        print(f"   Average time per student: {batch_duration/successfully_analyzed:.1f}s")
        print(f"   Circuit breaker state: {'Open' if circuit_breaker_state['circuit_open'] else 'Closed'}")
        
    except Exception as e:
        logging.error(f"Error in analyze_batch: {str(e)}")
        flash("分析中にエラーが発生しました。もう一度お試しください。", "error")
    
    return redirect(url_for('teacher'))



def assign_squad_icon(squad_name):
    """
    Assign Font Awesome icon based on keywords in squad name
    """
    squad_name_lower = squad_name.lower()
    
    # Icon mapping based on common keywords
    icon_keywords = {
        'explorer': 'fa-compass',
        'adventure': 'fa-compass',
        'travel': 'fa-compass',
        '探検': 'fa-compass',
        'アドベンチャー': 'fa-compass',
        
        'creative': 'fa-palette',
        'art': 'fa-palette',
        'design': 'fa-palette',
        'クリエイティブ': 'fa-palette',
        'アート': 'fa-palette',
        
        'music': 'fa-music',
        'sound': 'fa-music',
        'ミュージック': 'fa-music',
        '音楽': 'fa-music',
        
        'tech': 'fa-laptop-code',
        'coding': 'fa-laptop-code',
        'digital': 'fa-laptop-code',
        'テック': 'fa-laptop-code',
        'コーディング': 'fa-laptop-code',
        
        'sports': 'fa-running',
        'fitness': 'fa-running',
        'active': 'fa-running',
        'スポーツ': 'fa-running',
        
        'stars': 'fa-star',
        'dream': 'fa-star',
        'future': 'fa-star',
        'スター': 'fa-star',
        'ドリーム': 'fa-star',
        
        'unity': 'fa-users',
        'team': 'fa-users',
        'harmony': 'fa-users',
        'ユニティ': 'fa-users',
        'チーム': 'fa-users',
        'ハーモニー': 'fa-users',
        
        'gaming': 'fa-gamepad',
        'game': 'fa-gamepad',
        'ゲーム': 'fa-gamepad',
        
        'book': 'fa-book',
        'reading': 'fa-book',
        'study': 'fa-book',
        '本': 'fa-book',
        
        'fire': 'fa-fire',
        'energy': 'fa-fire',
        'power': 'fa-fire',
        'パワー': 'fa-fire',
        
        'rocket': 'fa-rocket',
        'space': 'fa-rocket',
        'innovation': 'fa-rocket',
        'ロケット': 'fa-rocket',
    }
    
    # Check for keywords in squad name
    for keyword, icon in icon_keywords.items():
        if keyword in squad_name_lower:
            return icon
    
    # Default icon if no keywords match
    return 'fa-users'

def create_simple_japanese_squads(students_data):
    """
    Fallback squad creation with Japanese names when AI is unavailable
    Creates simple squads of 3-4 students with Japanese styling
    """
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
        "様々な興味と個性を持つ多様なグループです",  # Diverse group with various interests and personalities
        "創造性と協力の精神で結ばれた仲間です",  # Companions united by creativity and cooperation
        "新しい冒険と学びを追求するチームです",  # Team pursuing new adventures and learning
        "お互いの強みを活かし合う素晴らしいグループです",  # Wonderful group that brings out each other's strengths
        "共に成長し、夢を実現するパートナーです",  # Partners who grow together and realize dreams
        "協力と友情で繋がった特別なチームです"  # Special team connected by cooperation and friendship
    ]
    
    squad_number = 0
    
    for student in students_data:
        current_squad.append(student['id'])
        
        # Create squad when we have 4 members or when we're at the end
        if len(current_squad) == 4 or student == students_data[-1]:
            # Don't create squads with less than 3 members unless it's the only option
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
                # Add remaining students to the last squad
                if squads:
                    squads[-1]['member_ids'].extend(current_squad)
            
            current_squad = []
    
    return {'squads': squads}


@app.route('/teacher/create-squads', methods=['POST'])
def create_squads():
    """AI-powered squad formation - The Sorting Hat of the application"""
    
    # Debug session authentication
    teacher_auth = session.get('teacher_authenticated')
    logging.info(f"🎯 CREATE SQUADS ROUTE CALLED! Teacher authenticated: {teacher_auth}")
    logging.info(f"Request method: {request.method}")
    logging.info(f"Form data: {dict(request.form)}")
    logging.info(f"Session contents: {dict(session)}")
    
    if not teacher_auth:
        logging.warning("Authentication failed in create_squads route")
        return redirect(url_for('teacher_login'))
    
    try:
        # Step 1: Clean slate - Reset all existing squad assignments
        # First unassign all students from squads
        db.session.execute(db.text("UPDATE students SET squad_id = NULL"))
        # Then delete all squads
        Squad.query.delete()
        db.session.commit()
        
        # Step 2: Fetch all unassigned student submissions from database
        unassigned_students = Student.query.filter_by(squad_id=None).all()
        
        if len(unassigned_students) < 3:
            return redirect(url_for('teacher'))
        
        # Step 3: Prepare student data with their pre-analyzed personality signatures for AI analysis
        students_data = []
        student_map = {}  # For efficient lookups during assignment
        
        for student in unassigned_students:
            student_data = {
                'id': student.id,
                'name': student.name,
                'archetype': student.archetype,
                'core_strength': student.core_strength,
                'hidden_potential': student.hidden_potential,
                'conversation_catalyst': student.conversation_catalyst,
            }
            students_data.append(student_data)
            student_map[student.id] = student
        
        logging.info(f"Sending {len(students_data)} students to AI for intelligent grouping")
        
        # Step 4: Send to AI for intelligent squad formation with Japanese names
        try:
            from openai_integration import group_students_into_squads
            # Add timeout handling for AI request
            logging.info("🤖 Calling AI for squad formation...")
            ai_response = group_students_into_squads(students_data)
            logging.info("🎯 AI squad formation completed successfully")
            logging.info(f"AI Response: {ai_response}")
        except Exception as ai_error:
            logging.error(f"❌ AI squad formation failed: {str(ai_error)}")
            # Create a simple fallback grouping in Japanese style
            logging.info("🔄 Using fallback Japanese squad creation...")
            ai_response = create_simple_japanese_squads(students_data)
            logging.info(f"Fallback Response: {ai_response}")
        
        # Step 5: Parse AI response and validate structure
        if not isinstance(ai_response, dict) or 'squads' not in ai_response:
            raise ValueError("Invalid AI response format - expected dict with 'squads' key")
        
        squads_created = 0
        
        # Step 6: Process each AI-suggested squad and save to database
        for i, squad_data in enumerate(ai_response['squads'], 1):
            # Validate squad structure
            required_keys = ['squad_name', 'shared_interests', 'member_ids']
            if not all(key in squad_data for key in required_keys):
                logging.warning(f"Skipping squad with missing keys: {squad_data}")
                continue
            
            # Create new squad record with creative name and shared interests
            new_squad = Squad()
            new_squad.squad_rank = i
            new_squad.name = squad_data['squad_name']
            new_squad.shared_interests = squad_data['shared_interests']
            new_squad.squad_icon = assign_squad_icon(squad_data['squad_name'])
            db.session.add(new_squad)
            db.session.flush()  # Get the squad ID for student assignments
            
            # Assign students to this squad
            members_assigned = 0
            for student_id in squad_data['member_ids']:
                if student_id in student_map:
                    student = student_map[student_id]
                    student.squad_id = new_squad.id
                    members_assigned += 1
                    logging.info(f"Assigned {student.name} to squad '{squad_data['squad_name']}'")
                else:
                    logging.warning(f"Student ID {student_id} not found in database")
            
            if members_assigned > 0:
                squads_created += 1
                logging.info(f"Created squad '{squad_data['squad_name']}' with {members_assigned} members")
            else:
                # Remove empty squads
                db.session.delete(new_squad)
        
        # Step 7: Orphan Adoption - Add unassigned students to existing squads
        logging.info("🔍 Checking for unassigned students...")
        
        # Get all student IDs that were successfully assigned to squads by AI
        assigned_student_ids = set()
        for student in Student.query.all():
            if student.squad_id is not None:
                assigned_student_ids.add(student.id)
        
        # Get all student IDs that should have been assigned
        all_student_ids = set(student_map.keys())
        
        # Find students that were missed by AI
        unassigned_students = all_student_ids - assigned_student_ids
        
        if unassigned_students:
            logging.warning(f"🚨 Found {len(unassigned_students)} unassigned students: {unassigned_students}")
            
            # Orphan Adoption Algorithm - Add each orphan to the smallest existing squad
            for student_id in unassigned_students:
                student = student_map[student_id]
                
                # Find the squad with the fewest members
                squads_with_counts = db.session.query(
                    Squad,
                    db.func.count(Student.id).label('member_count')
                ).outerjoin(Student, Squad.id == Student.squad_id).group_by(Squad.id).all()
                
                if squads_with_counts:
                    # Find the squad with minimum members
                    best_squad, min_count = min(squads_with_counts, key=lambda x: x.member_count)
                    
                    # Add the orphan to this squad
                    student.squad_id = best_squad.id
                    
                    logging.info(f"✅ Adopted {student.name} (ID: {student_id}) into squad '{best_squad.name}' (was {min_count} members)")
                else:
                    logging.error(f"❌ No existing squads found to adopt {student.name}")
        else:
            logging.info("✅ All students successfully assigned to squads by AI")
        
        # Step 8: Commit all changes to database
        logging.info(f"💾 Committing {squads_created} squads to database...")
        db.session.commit()
        logging.info("✅ Database commit successful!")
        
        if squads_created > 0:
            logging.info(f"🎉 Squad formation complete: {squads_created} squads created")
        else:
            logging.warning("⚠️ No squads were created!")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error during squad formation: {str(e)}")
    
    return redirect(url_for('teacher'))








def generate_squad_icebreaker_with_ai(member_data, squad_name):
    """
    Generate a personalized icebreaker question for a specific squad using OpenAI ChatGPT API
    """
    try:
        from openai_integration import generate_squad_icebreaker
        return generate_squad_icebreaker(member_data, squad_name)
    except ImportError:
        logging.error("OpenAI integration not available")
        return get_fallback_icebreaker()
    except Exception as e:
        logging.error(f"Error generating icebreaker: {str(e)}")
        return get_fallback_icebreaker()

def get_fallback_icebreaker():
    """Fallback icebreaker when AI is unavailable"""
    fallback_icebreakers = [
        "Share something you've learned recently that surprised you, and ask each other follow-up questions about it.",
        "What's one skill or hobby you'd love to try together as a group? Plan how you might actually do it.",
        "If you could create the perfect weekend together, what would you include? Build on each other's ideas.",
        "What's something you're curious about that someone else in the group might know? Teach each other something new.",
        "Share a story about a time you tried something completely new. What would you encourage each other to try next?"
    ]
    return random.choice(fallback_icebreakers)

@app.route('/delete-student/<int:student_id>')
def delete_student(student_id):
    """Delete a student record from the database"""
    if not session.get('teacher_authenticated'):
        return redirect(url_for('teacher_login'))
    
    try:
        student = Student.query.get_or_404(student_id)
        student_name = student.name
        
        # Delete the student record
        db.session.delete(student)
        db.session.commit()
        
        logging.info(f"Deleted student: {student_name} (ID: {student_id})")
        
        # Clear current squads since student composition has changed
        if 'current_squads' in session:
            del session['current_squads']
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting student {student_id}: {str(e)}")
    
    return redirect(url_for('teacher'))

@app.route('/teacher/move-student', methods=['POST'])
def move_student():
    """Handle drag-and-drop student movement between squads"""
    if not session.get('teacher_authenticated'):
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        data = request.get_json()
        student_id = int(data['student_id'])
        from_squad = data['from_squad']
        to_squad = data['to_squad']
        new_index = int(data['new_index'])
        
        # Get current squads and ungrouped students from session
        current_squads = session.get('current_squads', [])
        ungrouped_students = session.get('ungrouped_students', [])
        
        # Find the student to move
        student_to_move = None
        
        # Remove student from source
        if from_squad == 'ungrouped':
            for i, student in enumerate(ungrouped_students):
                if student['id'] == student_id:
                    student_to_move = ungrouped_students.pop(i)
                    break
        else:
            from_squad_idx = int(from_squad)
            if 0 <= from_squad_idx < len(current_squads):
                squad_members = current_squads[from_squad_idx]['members']
                for i, member in enumerate(squad_members):
                    if member['id'] == student_id:
                        student_to_move = squad_members.pop(i)
                        break
        
        if not student_to_move:
            return jsonify({'success': False, 'error': 'Student not found'})
        
        # Add student to destination
        if to_squad == 'ungrouped':
            ungrouped_students.insert(new_index, student_to_move)
        else:
            to_squad_idx = int(to_squad)
            if 0 <= to_squad_idx < len(current_squads):
                current_squads[to_squad_idx]['members'].insert(new_index, student_to_move)
            else:
                return jsonify({'success': False, 'error': 'Invalid destination squad'})
        
        # Update session
        session['current_squads'] = current_squads
        session['ungrouped_students'] = ungrouped_students
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Error moving student: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error'})

@app.route('/delete-squad/<int:squad_id>')
def delete_squad(squad_id):
    """Delete a specific squad and cleanly unassign all members"""
    try:
        # Find the squad to delete
        squad = Squad.query.get_or_404(squad_id)
        squad_name = squad.name
        member_count = len(squad.members)
        
        # First, explicitly unassign all students from this squad
        # Using a direct database update for efficiency and clarity
        students_to_unassign = Student.query.filter_by(squad_id=squad_id).all()
        
        for student in students_to_unassign:
            student.squad_id = None
            logging.info(f"Unassigned student {student.name} (ID: {student.id}) from squad {squad_name}")
        
        # Ensure all changes are flushed before deletion
        db.session.flush()
        
        # Now delete the squad record itself (including icebreaker_text and all associated data)
        db.session.delete(squad)
        db.session.commit()
        
        logging.info(f"Squad {squad_name} (ID: {squad_id}) deleted successfully, {member_count} students unassigned")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to delete squad {squad_id}: {str(e)}")
    
    return redirect(url_for('teacher'))

@app.route('/clear-squads', methods=['POST'])
def clear_squads():
    """Complete reset - delete all records from both Student and Squad tables"""
    if not session.get('teacher_authenticated'):
        return redirect(url_for('teacher_login'))
    
    try:
        # Step 1: Count records before deletion for logging
        students_count = Student.query.count()
        squads_count = Squad.query.count()
        
        # Step 2: Delete all student records
        Student.query.delete()
        
        # Step 3: Delete all squad records
        Squad.query.delete()
        
        # Commit all changes
        db.session.commit()
        
        logging.info(f"Complete database reset: {students_count} students deleted, {squads_count} squads deleted")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to complete database reset: {str(e)}")
    
    return redirect(url_for('teacher'))

@app.route('/generate-icebreaker/<int:squad_id>')
def generate_icebreaker(squad_id):
    """Generate AI-powered icebreaker for a specific squad"""
    if not session.get('teacher_authenticated'):
        return redirect(url_for('teacher_login'))
    
    try:
        # Fetch the squad and its members
        squad = Squad.query.get_or_404(squad_id)
        members = squad.members
        
        if not members:
            return redirect(url_for('teacher'))
        
        # Prepare member data for AI analysis
        member_data = []
        for member in members:
            member_info = {
                'name': member.name,
                'country': member.country,
                'gender': member.gender,
                'question1': member.question1,
                'question2': member.question2,
                'question3': member.question3,
                'question4': member.question4,
                'question5': member.question5,
                'question6': member.question6
            }
            member_data.append(member_info)
        
        # Call Gemini AI to generate icebreaker
        icebreaker_text = generate_squad_icebreaker_with_ai(member_data, squad.name)
        
        # Save the icebreaker to the database
        squad.icebreaker_text = icebreaker_text
        db.session.commit()
        
        logging.info(f"Generated icebreaker for squad {squad.name} (ID: {squad_id})")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to generate icebreaker for squad {squad_id}: {str(e)}")
    
    return redirect(url_for('teacher'))

@app.route('/teacher/ai-advice/<int:student_id>', methods=['POST'])
def get_ai_advice(student_id):
    """Generate AI advice for a solo student"""
    if not session.get('teacher_authenticated'):
        return redirect(url_for('teacher_login'))
    
    try:
        student = Student.query.get_or_404(student_id)
        
        # Generate AI advice for solo student
        advice = {
            'integration_strategies': [
                f'Consider {student.name}\'s interests in building connections with other students',
                'Look for shared activities that align with their passion areas',
                'Encourage participation in group projects related to their interests'
            ],
            'collaboration_opportunities': f'Help {student.name} find peers with complementary skills or shared interests',
            'group_role_suggestion': 'Could serve as a specialist contributor in mixed-interest groups',
            'development_areas': [
                'Practice collaborative communication skills',
                'Explore interdisciplinary connections',
                'Develop leadership potential in their interest areas'
            ]
        }
        
        # Store advice in session for display
        session[f'ai_advice_{student_id}'] = advice
        
    except Exception as e:
        logging.error(f"Error generating AI advice for student {student_id}: {str(e)}")
    
    return redirect(url_for('teacher'))

def get_interest_categories_with_colors(vibes_text):
    """Extract interest categories and assign colors for visualization"""
    vibes_lower = vibes_text.lower()
    
    # Define interest categories with colors and keywords
    interest_categories = {
        'Gaming': {
            'keywords': ['game', 'gaming', 'games', 'video games', 'gamer', 'esports', 'pc', 'console', 'minecraft', 'fortnite'],
            'color': '#E91E63',  # Pink
            'icon': 'fas fa-gamepad'
        },
        'Music': {
            'keywords': ['music', 'musical', 'musician', 'singing', 'guitar', 'piano', 'song', 'instrument', 'band'],
            'color': '#9C27B0',  # Purple
            'icon': 'fas fa-music'
        },
        'Art & Design': {
            'keywords': ['art', 'drawing', 'painting', 'creative', 'design', 'sketch', 'photography', 'photo'],
            'color': '#FF9800',  # Orange
            'icon': 'fas fa-palette'
        },
        'Technology': {
            'keywords': ['technology', 'tech', 'programming', 'coding', 'computer', 'software', 'app'],
            'color': '#2196F3',  # Blue
            'icon': 'fas fa-code'
        },
        'Sports': {
            'keywords': ['sport', 'sports', 'football', 'basketball', 'soccer', 'tennis', 'athletic', 'fitness', 'gym'],
            'color': '#4CAF50',  # Green
            'icon': 'fas fa-running'
        },
        'Anime & Manga': {
            'keywords': ['anime', 'manga', 'cosplay', 'otaku', 'japanese', 'japan'],
            'color': '#FF5722',  # Deep Orange
            'icon': 'fas fa-star'
        },
        'Adventure': {
            'keywords': ['travel', 'traveling', 'adventure', 'explore', 'trip', 'nature', 'outdoor', 'hiking', 'camping'],
            'color': '#795548',  # Brown
            'icon': 'fas fa-mountain'
        },
        'Reading': {
            'keywords': ['reading', 'books', 'literature', 'novel', 'story', 'study', 'academic'],
            'color': '#607D8B',  # Blue Grey
            'icon': 'fas fa-book'
        },
        'Food': {
            'keywords': ['food', 'cooking', 'baking', 'cuisine', 'restaurant', 'eat', 'chef'],
            'color': '#FF9800',  # Amber
            'icon': 'fas fa-utensils'
        },
        'Movies & TV': {
            'keywords': ['movie', 'film', 'cinema', 'netflix', 'watch', 'tv', 'series'],
            'color': '#673AB7',  # Deep Purple
            'icon': 'fas fa-film'
        },
        'Dance': {
            'keywords': ['dance', 'dancing', 'ballet', 'hip hop', 'choreography'],
            'color': '#E91E63',  # Pink
            'icon': 'fas fa-music'
        },
        'Social': {
            'keywords': ['friends', 'social', 'party', 'people', 'community', 'group'],
            'color': '#FFEB3B',  # Yellow
            'icon': 'fas fa-users'
        }
    }
    
    # Find matching categories
    found_interests = []
    for category, data in interest_categories.items():
        matches = sum(1 for keyword in data['keywords'] if keyword in vibes_lower)
        if matches > 0:
            found_interests.append({
                'name': category,
                'color': data['color'],
                'icon': data['icon'],
                'intensity': min(matches / len(data['keywords']) * 2, 1.0),  # Normalize intensity
                'match_count': matches
            })
    
    # Sort by match count (highest first)
    found_interests.sort(key=lambda x: x['match_count'], reverse=True)
    
    return found_interests[:4]  # Return top 4 interests

def get_creative_vibe_archetype(student):
    """Determine student's creative vibe archetype based on mystery generator answers"""
    # Handle both new format and legacy format
    if hasattr(student, 'question1') and student.question1:
        combined_text = ' '.join([
            student.question1 or '',
            student.question2 or '',
            student.question3 or '',
            student.question4 or '',
            student.question5 or '',
            student.question6 or '',

        ]).lower()
    else:
        # Fallback to legacy vibes field
        combined_text = (student.vibes or '').lower()
    
    # Creative archetype detection with meme-worthy titles
    creative_archetypes = {
        'Midnight Philosopher': {
            'keywords': ['thinking', 'deep', 'philosophy', 'existential', 'meaning', 'life', 'questions', 'universe', 'wondering', 'pondering', 'reflect'],
            'icon': 'fas fa-moon',
            'description': 'Deep thinker who ponders life\'s mysteries'
        },
        'Certified Meme Historian': {
            'keywords': ['memes', 'funny', 'internet', 'viral', 'tiktok', 'instagram', 'social media', 'trends', 'jokes', 'humor', 'laugh'],
            'icon': 'fas fa-laugh-squint',
            'description': 'Master of internet culture and digital humor'
        },
        'Low-Key Genius': {
            'keywords': ['smart', 'coding', 'programming', 'math', 'science', 'learning', 'studying', 'tech', 'computer', 'solving', 'intelligent'],
            'icon': 'fas fa-brain',
            'description': 'Brilliant mind hiding behind casual vibes'
        },
        'Chaos Coordinator': {
            'keywords': ['random', 'chaos', 'unpredictable', 'spontaneous', 'weird', 'crazy', 'wild', 'energy', 'hyperactive', 'chaotic'],
            'icon': 'fas fa-bolt',
            'description': 'Thrives in beautiful chaos and spontaneity'
        },
        'Vibe Curator': {
            'keywords': ['music', 'playlist', 'aesthetic', 'vibes', 'mood', 'atmosphere', 'chill', 'lofi', 'beats', 'spotify', 'sound'],
            'icon': 'fas fa-headphones',
            'description': 'Creates the perfect atmosphere for any moment'
        },
        'Digital Nomad': {
            'keywords': ['gaming', 'online', 'virtual', 'digital', 'streaming', 'twitch', 'discord', 'pc', 'console', 'esports', 'game'],
            'icon': 'fas fa-gamepad',
            'description': 'Lives and breathes in digital realms'
        },
        'Snack Connoisseur': {
            'keywords': ['food', 'eating', 'snacks', 'cooking', 'restaurant', 'hungry', 'delicious', 'taste', 'cuisine', 'baking', 'cook'],
            'icon': 'fas fa-cookie-bite',
            'description': 'Finds joy in culinary adventures and treats'
        },
        'Plot Twist Enthusiast': {
            'keywords': ['movies', 'series', 'shows', 'netflix', 'anime', 'drama', 'story', 'plot', 'character', 'binge', 'watch'],
            'icon': 'fas fa-film',
            'description': 'Lives for compelling stories and epic narratives'
        },
        'Energy Drink Personified': {
            'keywords': ['energy', 'hyper', 'active', 'sports', 'running', 'gym', 'fitness', 'workout', 'adrenaline', 'intense', 'fast'],
            'icon': 'fas fa-fire',
            'description': 'Pure kinetic energy in human form'
        },
        'Professional Procrastinator': {
            'keywords': ['sleep', 'lazy', 'procrastinate', 'later', 'tomorrow', 'bed', 'nap', 'chill', 'relaxing', 'nothing', 'rest'],
            'icon': 'fas fa-bed',
            'description': 'Masters the art of strategic delay'
        },
        'Social Algorithm': {
            'keywords': ['friends', 'social', 'people', 'party', 'talking', 'hanging out', 'group', 'together', 'communication', 'connect'],
            'icon': 'fas fa-users',
            'description': 'Naturally connects people and builds communities'
        },
        'Creative Hurricane': {
            'keywords': ['art', 'drawing', 'creative', 'design', 'painting', 'craft', 'making', 'building', 'creating', 'imagination', 'artistic'],
            'icon': 'fas fa-palette',
            'description': 'Creates beauty from pure imagination'
        },
        'Adventure Architect': {
            'keywords': ['adventure', 'explore', 'travel', 'discovery', 'journey', 'new', 'experience', 'outdoor', 'hiking', 'nature'],
            'icon': 'fas fa-compass',
            'description': 'Builds epic quests from everyday moments'
        },
        'Zen Master': {
            'keywords': ['calm', 'peaceful', 'meditation', 'nature', 'quiet', 'serene', 'balance', 'mindful', 'tranquil', 'peace'],
            'icon': 'fas fa-leaf',
            'description': 'Brings inner peace to chaotic worlds'
        }
    }
    
    # Calculate scores for each archetype
    archetype_scores = {}
    for archetype_name, archetype_data in creative_archetypes.items():
        score = sum(1 for keyword in archetype_data['keywords'] if keyword in combined_text)
        if score > 0:
            archetype_scores[archetype_name] = score
    
    # Return the highest scoring archetype or default
    if archetype_scores:
        best_archetype = max(archetype_scores, key=archetype_scores.get)
        return {
            'name': best_archetype,
            'icon': creative_archetypes[best_archetype]['icon'],
            'description': creative_archetypes[best_archetype]['description']
        }
    else:
        return {
            'name': 'Mysterious Entity',
            'icon': 'fas fa-star',
            'description': 'A unique presence that defies categorization'
        }

# Legacy function for backward compatibility
def get_vibe_archetype(vibes_text):
    """Legacy function - returns archetype name only"""
    class FakeStudent:
        def __init__(self, vibes):
            self.vibes = vibes
            self.question1 = None
    
    result = get_creative_vibe_archetype(FakeStudent(vibes_text))
    return result['name']

def get_core_sparks(vibes_text):
    """Extract core interests as hashtags with Japanese translations"""
    vibes_lower = vibes_text.lower()
    
    # Define keywords with Japanese translations
    spark_translations = {
        'gaming': 'ゲーム',
        'music': '音楽',
        'art': 'アート',
        'travel': '旅行',
        'sports': 'スポーツ',
        'technology': 'テクノロジー',
        'reading': '読書',
        'food': '食べ物',
        'movies': '映画',
        'anime': 'アニメ',
        'dance': 'ダンス',
        'photography': '写真',
        'fitness': 'フィットネス',
        'nature': '自然',
        'creative': '創造的',
        'adventure': '冒険'
    }
    
    # Enhanced keyword mapping
    keyword_mapping = {
        'game': 'gaming', 'games': 'gaming', 'gamer': 'gaming', 'video games': 'gaming',
        'musical': 'music', 'musician': 'music', 'singing': 'music', 'song': 'music',
        'drawing': 'art', 'painting': 'art', 'design': 'art', 'sketch': 'art',
        'traveling': 'travel', 'trip': 'travel', 'explore': 'travel',
        'sport': 'sports', 'athletic': 'sports', 'football': 'sports', 'basketball': 'sports',
        'tech': 'technology', 'programming': 'technology', 'coding': 'technology',
        'books': 'reading', 'novel': 'reading', 'literature': 'reading',
        'cooking': 'food', 'baking': 'food', 'cuisine': 'food',
        'movie': 'movies', 'film': 'movies', 'cinema': 'movies',
        'manga': 'anime', 'cosplay': 'anime',
        'dancing': 'dance', 'ballet': 'dance',
        'photo': 'photography', 'camera': 'photography',
        'gym': 'fitness', 'workout': 'fitness', 'exercise': 'fitness',
        'outdoor': 'nature', 'hiking': 'nature', 'camping': 'nature',
        'design': 'creative', 'artist': 'creative'
    }
    
    found_sparks = set()
    
    # Check for direct matches
    for spark in spark_translations.keys():
        if spark in vibes_lower:
            found_sparks.add(spark)
    
    # Check for mapped keywords
    for keyword, spark in keyword_mapping.items():
        if keyword in vibes_lower:
            found_sparks.add(spark)
    
    # Convert to hashtag format with translations
    sparks = []
    for spark in sorted(found_sparks)[:4]:  # Limit to 4 main sparks
        japanese = spark_translations.get(spark, '？')
        sparks.append(f'#{spark} ({japanese})')
    
    return sparks if sparks else ['#unique (ユニーク)']



@app.route('/recommendations/<int:student_id>')
def student_recommendations(student_id):
    """Display AI-powered recommendations for a specific student"""
    student = Student.query.get_or_404(student_id)
    
    # Use basic archetype and fallback recommendations to avoid API timeout issues
    archetype = get_vibe_archetype(student.vibes)
    
    # Create fallback recommendations based on archetype
    recommendations = {
        'recommendations': [
            {
                'activity': f'{archetype} Workshop',
                'category': 'skill development',
                'reason': f'Perfect match for your {archetype.lower()} interests'
            },
            {
                'activity': 'Study Group Formation',
                'category': 'social',
                'reason': 'Connect with peers who share your interests'
            },
            {
                'activity': 'Interest Exploration',
                'category': 'personal growth',
                'reason': 'Expand your current interests into new areas'
            },
            {
                'activity': 'Creative Project',
                'category': 'creative',
                'reason': 'Apply your interests in a hands-on project'
            },
            {
                'activity': 'Mentorship Program',
                'category': 'academic',
                'reason': 'Share your knowledge and learn from others'
            }
        ],
        'growth_opportunities': [
            'Develop leadership skills in your area of interest',
            'Explore interdisciplinary connections'
        ],
        'connection_opportunities': 'Join clubs and activities related to your interests to meet like-minded peers'
    }
    
    # Create enhanced profile
    enhanced_profile = {
        'learning_style': f'{archetype} learner with hands-on approach',
        'strengths': [archetype.split()[0], 'Enthusiastic', 'Dedicated'],
        'ideal_group_role': 'Active contributor',
        'growth_opportunities': recommendations['growth_opportunities']
    }
    
    return render_template('recommendations.html', 
                         student=student, 
                         archetype=archetype,
                         recommendations=recommendations,
                         enhanced_profile=enhanced_profile)

@app.route('/teacher/ai-insights')
def teacher_ai_insights():
    """Teacher page with AI-powered insights about students and squad formation"""
    if not session.get('teacher_authenticated'):
        return redirect(url_for('teacher_login'))
    
    students = Student.query.all()
    
    if len(students) < 2:
        return redirect(url_for('teacher'))
    
    # Generate profiles for all students using fallback to avoid API timeouts
    student_profiles = []
    for student in students:
        archetype = get_vibe_archetype(student.vibes)
        student_profiles.append({
            'student': student,
            'profile': {
                'learning_style': f'{archetype} learner with collaborative approach',
                'strengths': [archetype.split()[0], 'Engaged', 'Curious'],
                'ideal_group_role': 'Active contributor and collaborator',
                'growth_opportunities': [
                    'Develop cross-disciplinary connections',
                    'Enhance communication skills',
                    'Explore leadership opportunities'
                ]
            },
            'basic_archetype': archetype
        })
    
    # Analyze compatibility between students using keyword matching
    compatibility_matrix = []
    for i, profile1 in enumerate(student_profiles):
        for j, profile2 in enumerate(student_profiles[i+1:], i+1):
            # Basic compatibility based on shared keywords and archetypes
            vibes1 = set(profile1['student'].vibes.lower().split())
            vibes2 = set(profile2['student'].vibes.lower().split())
            shared_words = vibes1.intersection(vibes2)
            
            # Calculate compatibility score
            base_score = min(0.9, len(shared_words) * 0.15)
            archetype_bonus = 0.2 if profile1['basic_archetype'] == profile2['basic_archetype'] else 0.0
            compatibility_score = min(0.95, base_score + archetype_bonus)
            
            # Determine shared interests from common keywords
            interest_keywords = ['game', 'music', 'art', 'sport', 'food', 'travel', 'tech', 'read', 'movie', 'dance']
            shared_interests = []
            for keyword in interest_keywords:
                if any(keyword in word for word in shared_words):
                    shared_interests.append(keyword)
            
            if not shared_interests and shared_words:
                shared_interests = list(shared_words)[:3]
            elif not shared_interests:
                shared_interests = ['communication', 'teamwork']
            
            compatibility_matrix.append({
                'student1': profile1['student'],
                'student2': profile2['student'],
                'compatibility': {
                    'compatibility_score': compatibility_score,
                    'shared_interests': shared_interests[:3],
                    'complementary_aspects': f'{profile1["basic_archetype"]} and {profile2["basic_archetype"]} perspectives combine well',
                    'collaboration_potential': f'Strong collaboration potential with {compatibility_score:.0%} compatibility',
                    'potential_conflicts': 'None identified'
                }
            })
    
    return render_template('ai_insights.html', 
                         student_profiles=student_profiles,
                         compatibility_matrix=compatibility_matrix)

@app.route('/reset-database')
def reset_database():
    """Temporary route to reset database for testing"""
    try:
        # Delete all student records first (to handle foreign key constraints)
        Student.query.delete()
        
        # Delete all squad records
        Squad.query.delete()
        
        # Delete all session settings
        SessionSettings.query.delete()
        
        # Commit the changes
        db.session.commit()
        
        logging.info("Database reset completed successfully")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Database reset failed: {str(e)}")
    
    return redirect(url_for('teacher_login'))

@app.route('/dev/seed-database')
def seed_database():
    """Developer tool to seed database with 20 realistic Gen Z students for testing"""
    try:
        import random
        
        # First, delete all existing records from both tables (fix foreign key constraint)
        # Delete students first to avoid foreign key constraint violation
        Student.query.delete()
        Squad.query.delete()
        db.session.commit()
        
        # Realistic Gen Z names from Japan, Vietnam, and China
        student_profiles = [
            # Good/Mature students (10)
            {
                'name': 'Yuki Tanaka',
                'country': 'Japan',
                'gender': 'Female',
                'type': 'good',
                'answers': {
                    'question1': 'I love reading classical literature and exploring hidden cafés in Tokyo. I spend my free time writing poetry and studying different architectural styles around the city.',
                    'question2': 'I would master digital art and animation to create meaningful stories that connect people across cultures. Art has the power to bridge differences.',
                    'question3': 'I can talk for hours about sustainable living and environmental conservation. I believe our generation has a responsibility to protect the planet.',
                    'question4': 'My ideal Friday night is cooking a homemade meal with friends, followed by deep conversations about life goals and watching Studio Ghibli films.',
                    'question5': 'I once became obsessed with learning traditional Japanese calligraphy, practicing for hours to perfect each stroke and understanding the philosophy behind each character.',
                    'question6': 'I want teammates who are genuinely curious about the world, empathetic listeners, and people who can find creative solutions to problems.'
                }
            },
            {
                'name': 'Hiroshi Yamamoto',
                'country': 'Japan',
                'gender': 'Male',
                'type': 'good',
                'answers': {
                    'question1': 'I enjoy building small robots and programming them to solve everyday problems. Technology should make life better for everyone.',
                    'question2': 'I would master multiple programming languages to develop apps that help people connect and learn from each other more effectively.',
                    'question3': 'I love discussing the intersection of technology and society, especially how AI can be used ethically to solve global challenges.',
                    'question4': 'Perfect Friday: attending a tech meetup, then going to a quiet ramen shop to code personal projects while listening to lo-fi music.',
                    'question5': 'I became fascinated with mechanical keyboards and spent months researching different switch types and building my own custom keyboard.',
                    'question6': 'I need teammates who are detail-oriented, patient with explaining complex ideas, and passionate about making a positive impact.'
                }
            },
            {
                'name': 'Linh Nguyen',
                'country': 'Vietnam',
                'gender': 'Female',
                'type': 'good',
                'answers': {
                    'question1': 'I love exploring Vietnamese street food culture and learning traditional recipes from my grandmother. Food connects generations and cultures.',
                    'question2': 'I would master photography to document the stories of everyday people and preserve cultural heritage through visual storytelling.',
                    'question3': 'I can talk endlessly about travel experiences and cultural differences, sharing stories about local customs and the beauty of human diversity.',
                    'question4': 'My ideal Friday involves visiting local markets, trying new foods, and having meaningful conversations with older generations about their life experiences.',
                    'question5': 'I once became obsessed with learning about coffee cultivation and brewing methods, visiting every coffee shop in my city to understand different flavor profiles.',
                    'question6': 'I want teammates who are open-minded, respectful of different perspectives, and enthusiastic about learning from others.'
                }
            },
            {
                'name': 'Duc Tran',
                'country': 'Vietnam',
                'gender': 'Male',
                'type': 'good',
                'answers': {
                    'question1': 'I spend my free time tutoring younger students in math and science, believing that education is the key to breaking cycles of poverty.',
                    'question2': 'I would master renewable energy engineering to help develop sustainable solutions for developing countries like Vietnam.',
                    'question3': 'I love discussing educational inequality and how technology can make quality education accessible to everyone, regardless of economic background.',
                    'question4': 'Perfect Friday: studying at the library, then playing basketball with friends, followed by a family dinner with lots of laughter.',
                    'question5': 'I became fascinated with urban gardening and spent months learning how to grow vegetables in small spaces using hydroponics.',
                    'question6': 'I need teammates who are hardworking, supportive of each other, and committed to making a difference in their communities.'
                }
            },
            {
                'name': 'Wei Chen',
                'country': 'China',
                'gender': 'Male',
                'type': 'good',
                'answers': {
                    'question1': 'I practice traditional Chinese instruments like the guzheng and study classical poetry. I believe preserving cultural heritage is important.',
                    'question2': 'I would master international relations and diplomacy to help build bridges between different cultures and prevent conflicts.',
                    'question3': 'I can talk for hours about philosophy, especially comparing Eastern and Western philosophical traditions and their relevance today.',
                    'question4': 'My ideal Friday is attending a cultural performance, then having tea with friends while discussing literature and current events.',
                    'question5': 'I once became obsessed with learning about traditional Chinese medicine and spent months studying herb properties and holistic healing methods.',
                    'question6': 'I want teammates who are intellectually curious, respectful of traditions, and passionate about cross-cultural understanding.'
                }
            },
            {
                'name': 'Mei Zhang',
                'country': 'China',
                'gender': 'Female',
                'type': 'good',
                'answers': {
                    'question1': 'I love learning languages and currently speak four. I believe communication is the foundation of human connection and understanding.',
                    'question2': 'I would master simultaneous translation to help people from different cultures communicate and understand each other better.',
                    'question3': 'I can discuss language learning strategies for hours, sharing resources and exploring how different languages shape our thinking.',
                    'question4': 'Perfect Friday: language exchange café, then watching foreign films with subtitles to immerse myself in different cultures.',
                    'question5': 'I became fascinated with etymology and spent months tracing the origins of words across different languages and cultures.',
                    'question6': 'I need teammates who are patient, good communicators, and appreciate the beauty of linguistic and cultural diversity.'
                }
            },
            {
                'name': 'Sakura Ito',
                'country': 'Japan',
                'gender': 'Female',
                'type': 'good',
                'answers': {
                    'question1': 'I volunteer at animal shelters and study veterinary science. I believe we have a responsibility to protect and care for all living beings.',
                    'question2': 'I would master veterinary medicine to help animals in need and educate people about responsible pet ownership.',
                    'question3': 'I love talking about animal behavior and conservation efforts, sharing stories about wildlife protection and rehabilitation.',
                    'question4': 'My ideal Friday involves volunteering at the animal shelter, then taking nature walks to observe and photograph wildlife.',
                    'question5': 'I once became obsessed with learning about marine biology and spent months studying ocean ecosystems and conservation efforts.',
                    'question6': 'I want teammates who are compassionate, environmentally conscious, and willing to take action for causes they believe in.'
                }
            },
            {
                'name': 'Anh Pham',
                'country': 'Vietnam',
                'gender': 'Female',
                'type': 'good',
                'answers': {
                    'question1': 'I create educational content on social media to help students with study techniques and motivation. Knowledge should be shared freely.',
                    'question2': 'I would master educational psychology to understand how people learn best and develop more effective teaching methods.',
                    'question3': 'I can talk endlessly about personal development, study strategies, and how to overcome academic challenges through persistence.',
                    'question4': 'Perfect Friday: creating study guides for my followers, then relaxing with friends over Vietnamese coffee and planning future goals.',
                    'question5': 'I became fascinated with memory techniques and spent months learning mnemonics and speed-reading methods to improve my learning efficiency.',
                    'question6': 'I need teammates who are motivated, organized, and supportive of each other\'s academic and personal growth.'
                }
            },
            {
                'name': 'Jun Liu',
                'country': 'China',
                'gender': 'Male',
                'type': 'good',
                'answers': {
                    'question1': 'I practice martial arts and study Chinese philosophy. Physical and mental discipline are equally important for personal growth.',
                    'question2': 'I would master sports psychology to help athletes develop mental strength and overcome performance anxiety.',
                    'question3': 'I love discussing the connection between physical fitness and mental health, and how ancient wisdom applies to modern challenges.',
                    'question4': 'My ideal Friday involves martial arts training, then meditation in nature, followed by reading philosophy books.',
                    'question5': 'I once became obsessed with studying different meditation techniques from various Buddhist traditions and their scientific benefits.',
                    'question6': 'I want teammates who are disciplined, balanced in their approach to life, and committed to continuous self-improvement.'
                }
            },
            {
                'name': 'Ayame Sato',
                'country': 'Japan',
                'gender': 'Female',
                'type': 'good',
                'answers': {
                    'question1': 'I study traditional Japanese crafts like pottery and textile weaving. Preserving artisanal skills is important in our digital age.',
                    'question2': 'I would master traditional craftsmanship to keep cultural heritage alive and teach these skills to future generations.',
                    'question3': 'I can talk for hours about the intersection of tradition and modernity, and how ancient techniques remain relevant today.',
                    'question4': 'Perfect Friday: pottery class, then visiting museums to study traditional art, followed by tea ceremony practice.',
                    'question5': 'I became fascinated with natural dyeing techniques and spent months learning how to create colors from plants and minerals.',
                    'question6': 'I need teammates who appreciate craftsmanship, have patience for detailed work, and respect cultural traditions.'
                }
            },
            
            # Immature/Rebellious students (10)
            {
                'name': 'Takeshi Suzuki',
                'country': 'Japan',
                'gender': 'Male',
                'type': 'immature',
                'answers': {
                    'question1': 'bruh i just play mobile games all day lol. mostly gacha games where i spend my allowance on anime waifus. dont judge me',
                    'question2': 'i wanna be a pro gamer or maybe a youtuber? idk something where i dont have to wake up early or wear a suit',
                    'question3': 'memes. literally just memes. i can quote every tiktok trend and vine compilation. also conspiracy theories about anime plots',
                    'question4': 'gaming until 3am while eating convenience store food and energy drinks. maybe watch some streamers rage quit',
                    'question5': 'i got really into collecting pokemon cards again even though im 18. spent like 50000 yen on booster packs last month',
                    'question6': 'someone who wont judge my lifestyle choices and maybe has good wifi for gaming sessions'
                }
            },
            {
                'name': 'Riku Nakamura',
                'country': 'Japan',
                'gender': 'Male',
                'type': 'immature',
                'answers': {
                    'question1': 'skateboarding and causing minor trouble around shibuya. not illegal stuff just... creative interpretations of rules',
                    'question2': 'honestly? time travel so i can go back and buy bitcoin or prevent embarrassing moments from happening',
                    'question3': 'why adults are so obsessed with \"responsibility\" and \"growing up\" like chill we have our whole lives to be boring',
                    'question4': 'sneaking out to all-night karaoke with friends and singing anime openings until we lose our voices',
                    'question5': 'learning how to do skateboard tricks by watching youtube videos at 2x speed. broke my wrist twice but worth it',
                    'question6': 'someone who knows how to have fun and wont snitch when we bend the rules a little'
                }
            },
            {
                'name': 'Minh Hoang',
                'country': 'Vietnam',
                'gender': 'Male',
                'type': 'immature',
                'answers': {
                    'question1': 'playing mobile legends and arguing with teammates in voice chat. also making tiktoks of me doing stupid dances',
                    'question2': 'super speed so i can finish all my homework in 5 minutes and have more time for gaming',
                    'question3': 'why vietnamese parents always compare you to other kids like \"why cant you be more like duc next door\"',
                    'question4': 'internet cafe gaming session with the boys, then street food and complaining about school',
                    'question5': 'trying to learn guitar to impress girls but gave up after 2 weeks because my fingers hurt',
                    'question6': 'someone who can carry me in team games and doesnt care that i never do group project work'
                }
            },
            {
                'name': 'Thuy Dang',
                'country': 'Vietnam',
                'gender': 'Female',
                'type': 'immature',
                'answers': {
                    'question1': 'scrolling through instagram and tiktok for hours. also online shopping for clothes i dont need with my parents money',
                    'question2': 'mind reading so i can know what people really think about me and also cheat on tests',
                    'question3': 'drama. like who said what about who and why everyone is so fake on social media',
                    'question4': 'boba tea, gossip with friends, and taking 100 selfies until i find the perfect one for instagram',
                    'question5': 'korean skincare routine. i have like 15 different products and watch youtube tutorials religiously',
                    'question6': 'someone who has good style, knows all the trends, and wont judge my online shopping addiction'
                }
            },
            {
                'name': 'Hao Wang',
                'country': 'China',
                'gender': 'Male',
                'type': 'immature',
                'answers': {
                    'question1': 'playing league of legends and raging at noob teammates. also watching anime and reading manga instead of studying',
                    'question2': 'invisibility so i can skip classes without getting caught and also spy on people',
                    'question3': 'why chinese parents have such high expectations like bro i just want to be average and happy',
                    'question4': 'hotpot with friends while watching anime and complaining about our strict teachers',
                    'question5': 'collecting anime figures and hiding them from my parents because they think its childish',
                    'question6': 'someone who shares my interests in anime/gaming and wont lecture me about studying more'
                }
            },
            {
                'name': 'Xiao Li',
                'country': 'China',
                'gender': 'Female',
                'type': 'immature',
                'answers': {
                    'question1': 'watching kdramas and crying over fictional characters. also stalking celebrities on weibo',
                    'question2': 'perfect memory so i can remember every kdrama plot and also never forget embarrassing moments',
                    'question3': 'why kdrama male leads are so perfect but real boys are disappointing. also conspiracy theories about idol groups',
                    'question4': 'binge watching the latest kdrama while eating snacks and texting my friends about plot twists',
                    'question5': 'learning korean through kdramas and kpop lyrics. my pronunciation is terrible but i try',
                    'question6': 'someone who understands my kdrama obsession and maybe knows some korean so we can fangirl together'
                }
            },
            {
                'name': 'Yuta Kobayashi',
                'country': 'Japan',
                'gender': 'Male',
                'type': 'immature',
                'answers': {
                    'question1': 'making weird tiktoks and trying to go viral. also collecting limited edition sneakers i cant afford',
                    'question2': 'teleportation so i can travel anywhere without paying and also escape awkward situations instantly',
                    'question3': 'why school is so boring and pointless. like when am i ever gonna use calculus in real life',
                    'question4': 'convenience store dinner, then wandering around tokyo taking random photos for my instagram aesthetic',
                    'question5': 'trying to learn every tiktok dance trend but im terrible at dancing so i just make meme versions',
                    'question6': 'someone who appreciates my humor and wont judge my questionable life choices'
                }
            },
            {
                'name': 'Khang Tran',
                'country': 'Vietnam',
                'gender': 'Male',
                'type': 'immature',
                'answers': {
                    'question1': 'motorbike racing (illegally) and trying to look cool in front of girls. also gym but just for abs',
                    'question2': 'super strength so i can win every fight and also open stubborn jars',
                    'question3': 'why vietnamese girls only date rich guys and ignore my obvious charm and motorcycle skills',
                    'question4': 'racing motorbikes, then bragging about it while eating street food and planning more dangerous stunts',
                    'question5': 'learning how to do wheelies on my motorbike but crashed into a tree. still have the scar',
                    'question6': 'someone who thinks im cool and maybe a girl who will be impressed by my motorcycle'
                }
            },
            {
                'name': 'Zoe Chen',
                'country': 'China',
                'gender': 'Female',
                'type': 'immature',
                'answers': {
                    'question1': 'taking aesthetic photos for xiaohongshu and buying expensive makeup i dont know how to use properly',
                    'question2': 'perfect skin so i never have to worry about acne or spend money on skincare',
                    'question3': 'why chinese beauty standards are so unrealistic and why everyone is so obsessed with being pale',
                    'question4': 'shopping for clothes i dont need, then taking outfit photos for social media',
                    'question5': 'trying every viral skincare trend from korea but my skin got worse instead of better',
                    'question6': 'someone who takes good photos of me and appreciates my fashion sense'
                }
            },
            {
                'name': 'Daiki Yoshida',
                'country': 'Japan',
                'gender': 'Male',
                'type': 'immature',
                'answers': {
                    'question1': 'sleeping until 2pm and then complaining that the day is too short to do anything productive',
                    'question2': 'not needing sleep so i can game 24/7 and also never miss anime episodes',
                    'question3': 'why adults always say \"when i was your age\" like ok boomer times have changed',
                    'question4': 'ordering uber eats, gaming, and maybe watching netflix if i get bored of gaming',
                    'question5': 'trying to beat dark souls but rage quit after dying to the same boss 50 times',
                    'question6': 'someone who doesnt expect me to be productive and maybe brings snacks'
                }
            }
        ]
        
        # Create 20 students from the profiles
        for profile in student_profiles:
            name = profile['name']
            country = profile['country']
            gender = profile['gender']
            answers = profile['answers']
            
            # Combine all answers for vibes field
            combined_answers = f"{answers['question1']} {answers['question2']} {answers['question3']} {answers['question4']} {answers['question5']} {answers['question6']}"
            
            # Create student object with empty personality fields (to be filled by AI later)
            student = Student(
                name=name,
                country=country,
                gender=gender,
                vibes=combined_answers,
                question1=answers['question1'],
                question2=answers['question2'],
                question3=answers['question3'],
                question4=answers['question4'],
                question5=answers['question5'],
                question6=answers['question6'],
                archetype=None,  # Empty personality fields (to be filled by AI later)
                core_strength=None,
                hidden_potential=None,
                conversation_catalyst=None,
                submission_id=Student.generate_submission_id()
            )
            
            # Add to database session
            db.session.add(student)
        
        # Commit all students to database
        db.session.commit()
        
        logging.info("Successfully seeded database with 20 realistic Gen Z test students")
        flash("Database seeded with 20 new Gen Z test students (10 mature, 10 immature).", "success")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to seed database: {str(e)}")
        flash(f"Failed to seed database: {str(e)}", "error")
    
    return redirect(url_for('teacher'))




@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('session_password.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('session_password.html'), 500

@app.route('/verify-token', methods=['POST'])
@csrf.exempt # Exempt this API route from CSRF checks
def verify_token():
    try:
        token = request.json.get('token')
        if not token:
            return jsonify({'status': 'error', 'message': 'ID token is missing.'}), 400

        decoded_token = auth.verify_id_token(token)
        session['firebase_uid'] = decoded_token['uid']

        return jsonify({'status': 'success', 'uid': decoded_token['uid']})

    except Exception as e:
        # This will print the exact crash details to our terminal
        print(f"--- VERIFY TOKEN CRASHED: {e} ---")
        logging.error(f"Error verifying Firebase token: {e}")
        session.pop('firebase_uid', None)
        # Return a JSON error message, not an HTML page
        return jsonify({'status': 'error', 'message': f'Server error: {e}'}), 500

