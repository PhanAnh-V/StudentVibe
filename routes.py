from flask import render_template, request, redirect, url_for, session, jsonify, flash
from app import app, db
from models import Student, SessionSettings, Squad
from forms import StudentForm, TeacherLoginForm, StudentLoginForm
import logging
import re
import json
import random
from collections import Counter, defaultdict
# AI recommendations functions will be imported where needed

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
            
            # Handle Japanese translations based on student's language choice
            japanese_translations = []
            print('--- Starting translation process ---')
            
            for i, answer in enumerate(original_answers, 1):
                if student_language == 'ja':
                    # Student chose Japanese - no translation needed, use original answer
                    japanese_translations.append(answer)
                    print(f"Question {i}: Japanese detected, using original answer")
                    logging.info(f"Question {i}: Japanese detected, using original answer")
                else:
                    # Student chose other language - translate to Japanese
                    try:
                        print(f"Question {i}: Attempting translation from {student_language} to Japanese")
                        from openai_integration import translate_to_japanese
                        translation = translate_to_japanese(answer)
                        japanese_translations.append(translation)
                        print(f"Question {i}: Translation successful")
                        print(f"Original: {answer[:50]}...")
                        print(f"Translated: {translation[:50]}...")
                        logging.info(f"Question {i} translated successfully from {student_language} to Japanese")
                    except Exception as e:
                        print(f"Translation failed for question {i}: {str(e)}")
                        logging.error(f"Translation failed for question {i}: {str(e)}")
                        japanese_translations.append("")  # Save empty translation if it fails
            
            print('--- Creating student record ---')
            # Create new student record with both original and translated answers
            student = Student()
            student.name = form.name.data
            student.vibes = combined_vibes
            student.question1 = form.question1.data
            student.question2 = form.question2.data
            student.question3 = form.question3.data
            student.question4 = form.question4.data
            student.question5 = form.question5.data
            student.question6 = form.question6.data
            student.question1_jp = japanese_translations[0]
            student.question2_jp = japanese_translations[1]
            student.question3_jp = japanese_translations[2]
            student.question4_jp = japanese_translations[3]
            student.question5_jp = japanese_translations[4]
            student.question6_jp = japanese_translations[5]
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
            
            logging.info(f"New student registered: {student.name} (ID: {student.id}, Submission ID: {submission_id}) with Japanese translations")
            
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
    
    # Clear the session data after displaying
    session.pop('submission_id', None)
    session.pop('student_name', None)
    
    return render_template('success.html', 
                         submission_id=submission_id,
                         student_name=student_name,
                         site_content=site_content)

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
        
        return render_template('squad_hub.html', squad=squad, icebreaker_data=icebreaker_data)
        
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



@app.route('/teacher')
def teacher():
    """Teacher dashboard with authentication required"""
    # Check if teacher is authenticated
    if not session.get('teacher_authenticated'):
        return redirect(url_for('teacher_login'))
    
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

@app.route('/teacher/analyze-batch', methods=['POST'])
def analyze_batch():
    """Analyze the next batch of students (max 5) with AI personality generation"""
    print("--- User clicked 'Analyze Batch'. Route was called. ---")
    
    # Check if teacher is authenticated
    if not session.get('teacher_authenticated'):
        return redirect(url_for('teacher_login'))
    
    try:
        # Find all students who have not yet been analyzed (archetype field is empty or null)
        unanalyzed_students = Student.query.filter(
            db.or_(Student.archetype.is_(None), Student.archetype == "")
        ).limit(5).all()
        
        print(f"Found {len(unanalyzed_students)} students to analyze.")
        
        if not unanalyzed_students:
            flash("すべての学生の分析が完了しました。", "info")
            return redirect(url_for('teacher'))
        
        # Import AI personality generation functions
        from openai_integration import generate_archetype, generate_core_strength, generate_hidden_potential, generate_conversation_catalyst
        
        # Process each student in the batch
        for student in unanalyzed_students:
            try:
                print(f"Now processing student: {student.name}")
                
                # Prepare student answers for AI analysis
                student_answers = {
                    'question1': student.question1,
                    'question2': student.question2,
                    'question3': student.question3,
                    'question4': student.question4,
                    'question5': student.question5,
                    'question6': student.question6
                }
                
                # Generate personality signature using AI functions
                student.archetype = generate_archetype(student_answers)
                student.core_strength = generate_core_strength(student_answers)
                student.hidden_potential = generate_hidden_potential(student_answers)
                student.conversation_catalyst = generate_conversation_catalyst(student_answers)
                
                # Save changes to database
                db.session.commit()
                
                logging.info(f"Successfully analyzed student {student.name} (ID: {student.id})")
                
            except Exception as e:
                logging.error(f"Error analyzing student {student.name}: {str(e)}")
                # Set fallback values for this student
                student.archetype = "個性豊かな学生"
                student.core_strength = "創造的な思考力と独自の視点を持っています。"
                student.hidden_potential = "リーダーシップの才能が眠っている可能性があります。"
                student.conversation_catalyst = "趣味や興味のあることについて話すと、とても輝いて見えます。"
                db.session.commit()
        
        # Count remaining unanalyzed students
        remaining_count = Student.query.filter(
            db.or_(Student.archetype.is_(None), Student.archetype == "")
        ).count()
        
        # Create status message for teacher
        analyzed_count = len(unanalyzed_students)
        if remaining_count == 0:
            flash(f"{analyzed_count}人の学生を分析しました。すべての分析が完了しました！", "success")
        else:
            flash(f"{analyzed_count}人の学生を分析しました。残り{remaining_count}人の学生が分析待ちです。", "info")
        
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
        for squad_data in ai_response['squads']:
            # Validate squad structure
            required_keys = ['squad_name', 'shared_interests', 'member_ids']
            if not all(key in squad_data for key in required_keys):
                logging.warning(f"Skipping squad with missing keys: {squad_data}")
                continue
            
            # Create new squad record with creative name and shared interests
            new_squad = Squad()
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
    """Developer tool to seed database with 10 new test students for testing"""
    try:
        import random
        
        # First, delete all existing records from both tables
        Squad.query.delete()
        Student.query.delete()
        db.session.commit()
        
        # Common Japanese names for testing
        japanese_names = [
            'Kenji Tanaka', 'Yuki Sato', 'Hiroshi Yamamoto', 'Sakura Watanabe', 'Takeshi Suzuki',
            'Ayame Nakamura', 'Daiki Kobayashi', 'Rei Ito', 'Shota Kato', 'Miki Yoshida'
        ]
        
        # Complex, detailed English answers for questionnaire testing
        detailed_answers = {
            'question1': [
                "I love diving deep into video game lore and exploring every hidden secret in RPGs. When I have free time, I spend hours researching the backstory of my favorite characters and creating detailed fan theories about upcoming plot developments.",
                "My go-to activity is planning elaborate trips through Europe, researching historical sites, local cuisines, and cultural festivals. I create detailed itineraries with backup plans and alternative routes, studying train schedules and hidden gems that most tourists never discover.",
                "I'm passionate about learning classical piano, spending hours practicing complex pieces by Chopin and Debussy. I study music theory, analyze compositions, and experiment with different interpretations of the same piece to develop my own unique style.",
                "I enjoy creating intricate digital art using advanced software like Blender and Photoshop. I spend time studying lighting techniques, color theory, and 3D modeling to create photorealistic landscapes and character designs for my personal projects.",
                "My favorite activity is learning new programming languages and building complex applications. I dive deep into frameworks like React and Node.js, creating full-stack web applications while studying algorithms and data structures.",
                "I love exploring urban photography, wandering through city streets at different times of day to capture the perfect lighting and atmosphere. I study composition techniques and post-processing methods to create compelling visual narratives.",
                "I'm deeply interested in studying different cuisines and perfecting complex cooking techniques. I spend hours researching traditional recipes, learning about ingredient sourcing, and experimenting with fusion dishes that combine multiple culinary traditions.",
                "My passion is learning multiple foreign languages simultaneously, studying grammar patterns, cultural contexts, and regional dialects. I practice conversation with native speakers and immerse myself in literature from different countries.",
                "I enjoy building and programming Arduino-based robotics projects, studying electronics, sensor integration, and automation systems. I create detailed documentation and tutorials for my inventions.",
                "My favorite activity is studying film cinematography and creating short documentary films about local communities. I analyze camera angles, editing techniques, and storytelling methods to improve my craft."
            ],
            'question2': [
                "I would love to master advanced 3D animation and visual effects creation, learning software like Maya and After Effects to bring my creative visions to life in professional-quality animations and short films.",
                "I want to become fluent in multiple programming languages including Python, JavaScript, and C++, so I can develop innovative applications that solve real-world problems and contribute to open-source projects.",
                "I dream of mastering classical guitar performance, learning complex fingerpicking techniques and being able to play intricate pieces by masters like Andrés Segovia and Francisco Tárrega with perfect emotional expression.",
                "I would love to master the art of professional photography, learning advanced lighting techniques, composition rules, and post-processing skills to capture stunning portraits and landscapes that tell compelling stories.",
                "I want to become an expert in sustainable urban gardening, learning hydroponics, permaculture principles, and organic farming techniques to create productive food systems in small spaces.",
                "I dream of mastering advanced cooking techniques from multiple cuisines, learning knife skills, fermentation processes, and molecular gastronomy to create innovative dishes that surprise and delight people.",
                "I would love to master the art of storytelling through writing, learning narrative structure, character development, and world-building to create compelling novels that resonate with readers.",
                "I want to become skilled in advanced data analysis and machine learning, learning statistical modeling, neural networks, and AI algorithms to solve complex problems and make meaningful predictions.",
                "I dream of mastering traditional Japanese calligraphy, learning brush techniques, character formation, and the philosophical aspects of this ancient art form to create beautiful, meaningful works.",
                "I would love to master advanced video editing and film production, learning cinematography, sound design, and post-production techniques to create professional-quality documentaries and short films."
            ],
            'question3': [
                "I can talk for hours about the intricate world-building in fantasy novels, analyzing character development, plot structures, and the way authors create believable magic systems and political intrigue.",
                "I'm passionate about discussing the evolution of video game design, from early arcade games to modern open-world experiences, analyzing how technology has shaped storytelling and player engagement.",
                "I love exploring the technical aspects of music production, discussing different recording techniques, mixing strategies, and how various genres have evolved through technological innovations.",
                "I can spend endless time discussing photography techniques, from the basics of composition and lighting to advanced concepts like long exposure, HDR, and the artistic choices behind famous photographers' work.",
                "I'm fascinated by the intersection of technology and society, discussing how artificial intelligence, blockchain, and emerging technologies are reshaping industries and human interactions.",
                "I love talking about travel experiences and cultural differences, sharing stories about local customs, traditional foods, and the unique perspectives gained from immersing yourself in different societies.",
                "I'm passionate about discussing sustainable living practices, from renewable energy and zero-waste lifestyles to permaculture and the ways individuals can reduce their environmental impact.",
                "I can talk endlessly about the craft of filmmaking, analyzing cinematography choices, editing techniques, and how directors use visual storytelling to convey complex emotions and themes.",
                "I'm deeply interested in discussing language learning strategies, comparing different methodologies, sharing resources, and exploring how understanding multiple languages opens up new ways of thinking.",
                "I love exploring the science behind cooking, discussing chemical reactions, fermentation processes, and how understanding food science can improve both flavor and nutrition in home cooking."
            ],
            'question4': [
                "My ideal Friday night would involve gathering close friends for a home-cooked meal, followed by engaging board games, meaningful conversations, and perhaps watching a thought-provoking film together.",
                "I envision spending the evening in a cozy bookstore café, reading an engrossing novel while sipping artisanal coffee, occasionally chatting with fellow book lovers about recent discoveries.",
                "My perfect Friday would be attending a live music performance, whether it's a jazz club, classical concert, or indie rock show, experiencing the energy and connection between artists and audience.",
                "I'd love to spend the evening working on a creative project, whether it's painting, writing, or coding, while listening to inspiring music and losing track of time in the flow of creation.",
                "My ideal Friday involves exploring a new neighborhood or city, discovering hidden restaurants, unique shops, and interesting architecture while documenting the experience through photography.",
                "I envision a quiet evening at home, cooking an elaborate meal from scratch, experimenting with new recipes and techniques while enjoying the meditative process of creating something delicious.",
                "My perfect Friday would be hosting a small gathering where friends share their latest projects, whether it's art, music, writing, or entrepreneurial ventures, celebrating each other's creativity.",
                "I'd love to spend the evening learning something new, whether it's attending a workshop, taking an online course, or practicing a skill I've been developing, feeling the satisfaction of progress.",
                "My ideal Friday involves outdoor activities like hiking, stargazing, or having a picnic in a scenic location, connecting with nature and appreciating the beauty of the natural world.",
                "I envision spending the evening volunteering for a cause I care about, whether it's helping at a community center, participating in environmental cleanup, or mentoring young people."
            ],
            'question5': [
                "I went through a phase where I was completely obsessed with collecting vintage mechanical keyboards, researching switch types, keycap materials, and the history of different manufacturers.",
                "There was a time when I became fascinated with learning about extinct languages, spending hours studying dead scripts and trying to understand how ancient civilizations communicated.",
                "I once became incredibly invested in the world of competitive yo-yo tricks, practicing for hours daily and learning the physics behind different string tensions and weight distributions.",
                "I had a period where I was obsessed with studying the migration patterns of birds, tracking different species through apps and learning to identify them by their songs and flight patterns.",
                "There was a time when I became fascinated with the art of paper folding, not just simple origami but complex modular designs that required hundreds of individual pieces.",
                "I once spent months studying the history and techniques of traditional bookbinding, learning about different paper types, binding methods, and the craftsmanship of historical manuscripts.",
                "I went through a phase of being completely absorbed in learning about urban beekeeping, studying hive management, honey production, and the important role of bees in urban ecosystems.",
                "There was a period where I became obsessed with the mathematics behind music, studying frequency ratios, harmonic series, and how different tuning systems affect emotional perception.",
                "I once became fascinated with the process of making sourdough bread from scratch, studying fermentation science, flour types, and the cultural history of bread-making traditions.",
                "I had a time where I was completely absorbed in learning about the psychology of color, studying how different hues affect mood, behavior, and cultural associations across different societies."
            ],
            'question6': [
                "My energy has the soundtrack of ambient electronic music - thoughtful, atmospheric, with layers of complexity that reveal themselves over time, creating a sense of depth and contemplation.",
                "I'd describe my energy as indie folk - acoustic, authentic, with storytelling elements that connect with people on a personal level, warm and inviting yet introspective.",
                "My energy resembles upbeat jazz - improvisational, collaborative, with unexpected rhythms and harmonies that keep things interesting and encourage creative expression.",
                "I have the energy of classical orchestral music - structured yet dynamic, with moments of quiet reflection balanced by powerful crescendos of passion and intensity.",
                "My energy is like progressive rock - complex, evolving, with intricate patterns that build into something greater than the sum of their parts, always pushing boundaries.",
                "I'd say my energy has the soundtrack of world music - diverse, culturally rich, incorporating different traditions and perspectives into a harmonious whole.",
                "My energy resembles lo-fi hip-hop - calm, steady, perfect for focused work and creative thinking, with subtle complexities that reward careful listening.",
                "I have the energy of acoustic singer-songwriter music - personal, honest, with meaningful lyrics and melodies that create genuine connections with others.",
                "My energy is like post-rock instrumental music - patient, building, with emotional depth that doesn't require words to communicate powerful feelings.",
                "I'd describe my energy as eclectic playlist music - adaptable, surprising, drawing from many genres to create something unique and personally meaningful."
            ]
        }
        
        countries = ['Japan', 'China', 'Vietnam', 'Other']
        genders = ['Male', 'Female', 'Prefer not to say']
        
        # Create 10 students with detailed answers and empty personality fields
        for i in range(10):
            name = japanese_names[i]
            country = random.choice(countries)
            gender = random.choice(genders)
            
            # Select random detailed answers
            question1 = random.choice(detailed_answers['question1'])
            question2 = random.choice(detailed_answers['question2'])
            question3 = random.choice(detailed_answers['question3'])
            question4 = random.choice(detailed_answers['question4'])
            question5 = random.choice(detailed_answers['question5'])
            question6 = random.choice(detailed_answers['question6'])
            
            # Combine all answers for vibes field
            combined_answers = f"{question1} {question2} {question3} {question4} {question5} {question6}"
            
            # Create student object with empty personality fields
            student = Student(
                name=name,
                country=country,
                gender=gender,
                vibes=combined_answers,
                question1=question1,
                question2=question2,
                question3=question3,
                question4=question4,
                question5=question5,
                question6=question6,
                archetype=None,  # Empty personality fields
                core_strength=None,
                hidden_potential=None,
                conversation_catalyst=None,
                submission_id=Student.generate_submission_id()
            )
            
            # Add to database session
            db.session.add(student)
        
        # Commit all students to database
        db.session.commit()
        
        logging.info("Successfully seeded database with 10 test students")
        flash("Database seeded with 10 new test students.", "success")
        
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
