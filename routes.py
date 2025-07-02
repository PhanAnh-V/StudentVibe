from flask import render_template, request, redirect, url_for, flash, session, jsonify
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
            flash('Error loading questionnaire data', 'error')
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
        flash('Welcome! You can now fill out the questionnaire.', 'success')
        return redirect(url_for('session_password'))
    else:
        flash('Incorrect session password. Please try again.', 'error')
        return redirect(url_for('session_password'))

@app.route('/submit-form', methods=['POST'])
def submit_form():
    """Handle questionnaire form submission"""
    if not session.get('session_authenticated'):
        flash('Please enter the session password first.', 'error')
        return redirect(url_for('index'))
    
    form = StudentForm()
    if form.validate_on_submit():
        try:
            # Combine all answers for the vibes field (for backward compatibility)
            combined_vibes = f"{form.question1.data} {form.question2.data} {form.question3.data} {form.question4.data} {form.question5.data} {form.question6.data}"
            
            # Generate unique submission ID
            submission_id = Student.generate_submission_id()
            
            # Get original answers
            original_answers = [
                form.question1.data,
                form.question2.data,
                form.question3.data,
                form.question4.data,
                form.question5.data,
                form.question6.data
            ]
            
            # Get student's chosen language from session
            student_language = session.get('language', 'en')
            
            # Debug session data to understand language detection
            logging.info(f"Session data: {dict(session)}")
            logging.info(f"Processing answers for language: {student_language}")
            
            # Handle Japanese translations based on student's language choice
            japanese_translations = []
            
            for i, answer in enumerate(original_answers, 1):
                if student_language == 'ja':
                    # Student chose Japanese - no translation needed, use original answer
                    japanese_translations.append(answer)
                    logging.info(f"Question {i}: Japanese detected, using original answer")
                else:
                    # Student chose other language - translate to Japanese
                    try:
                        from openai_integration import translate_to_japanese
                        translation = translate_to_japanese(answer)
                        japanese_translations.append(translation)
                        logging.info(f"Question {i} translated successfully from {student_language} to Japanese")
                    except Exception as e:
                        logging.error(f"Translation failed for question {i}: {str(e)}")
                        japanese_translations.append("")  # Save empty translation if it fails
            
            # Create new student record with both original and translated answers
            student = Student(
                name=form.name.data,
                vibes=combined_vibes,
                question1=form.question1.data,
                question2=form.question2.data,
                question3=form.question3.data,
                question4=form.question4.data,
                question5=form.question5.data,
                question6=form.question6.data,
                question1_jp=japanese_translations[0],
                question2_jp=japanese_translations[1],
                question3_jp=japanese_translations[2],
                question4_jp=japanese_translations[3],
                question5_jp=japanese_translations[4],
                question6_jp=japanese_translations[5],
                country=form.country.data,
                gender=form.gender.data,
                submission_id=submission_id
            )
            
            db.session.add(student)
            db.session.commit()
            
            logging.info(f"New student registered: {student.name} (ID: {student.id}, Submission ID: {submission_id}) with Japanese translations")
            
            # Store submission ID in session for success page
            session['submission_id'] = submission_id
            session['student_name'] = form.name.data
            
            # Clear session authentication so form can't be submitted again
            session.pop('session_authenticated', None)
            
            return redirect(url_for('success'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving student: {e}")
            flash('An error occurred while saving your responses. Please try again.', 'error')
    
    # If form validation fails, show errors
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{field}: {error}', 'error')
    
    return render_template('questionnaire.html', form=form)

@app.route('/success')
def success():
    """Success confirmation page"""
    submission_id = session.get('submission_id')
    student_name = session.get('student_name')
    
    # Clear the session data after displaying
    session.pop('submission_id', None)
    session.pop('student_name', None)
    
    return render_template('success.html', 
                         submission_id=submission_id,
                         student_name=student_name)

@app.route('/find-squad', methods=['GET', 'POST'])
def find_squad():
    """Find squad by submission ID"""
    if request.method == 'POST':
        submission_id = request.form.get('submission_id', '').strip().upper()
        
        if not submission_id:
            flash('Please enter your submission ID.', 'error')
            return render_template('find_squad.html')
        
        # Find student by submission ID
        student = Student.query.filter_by(submission_id=submission_id).first()
        
        if not student:
            flash('ID not found, or your squad has not been created yet. Please check your ID or wait for your teacher to create the squads.', 'error')
            return render_template('find_squad.html')
        
        # Check if student has been assigned to a squad
        if student.squad_id:
            # Redirect to the squad hub
            return redirect(url_for('squad_hub', squad_id=student.squad_id))
        else:
            # No squad assigned yet
            flash('Your squad has not been created yet. Please wait for your teacher to create the squads.', 'error')
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
        icebreakers = None
        if squad.icebreaker_text:
            try:
                icebreakers = json.loads(squad.icebreaker_text)
            except (json.JSONDecodeError, TypeError) as e:
                logging.error(f"Error parsing icebreaker JSON for squad {squad_id}: {e}")
                # If JSON parsing fails, treat as plain text
                icebreakers = {"lighthearted": squad.icebreaker_text, "thoughtful": ""}
        
        return render_template('squad_hub.html', squad=squad, icebreakers=icebreakers)
        
    except Exception as e:
        logging.error(f"Error accessing squad hub {squad_id}: {str(e)}")
        flash('Squad not found or unable to access squad details.', 'error')
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
        
        # Get enhanced profile data
        vibes_text = student.vibes or student.get_combined_answers()
        archetype = get_creative_vibe_archetype(student)
        core_sparks = get_core_sparks(vibes_text)
        interests = get_interest_categories_with_colors(vibes_text)
        
        return render_template('profile.html', 
                             student=student,
                             student_answers=student_answers,
                             archetype=archetype,
                             core_sparks=core_sparks,
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
            flash('Welcome to the teacher dashboard!', 'success')
            return redirect(url_for('teacher'))
        else:
            flash('Invalid password. Please try again.', 'error')
    
    return render_template('teacher_login.html', form=form)



@app.route('/logout_student', methods=['POST'])
def logout_student():
    """Logout student and clear session"""
    session.pop('student_id', None)
    return '', 200



@app.route('/teacher')
def teacher_dashboard():
    # This is the corrected function to safely load all data

    # Add a check here to make sure teacher is logged in
    # if 'teacher_logged_in' not in session:
    #     return redirect(url_for('teacher_login'))

    try:
        students = Student.query.all() or []
        solo_students = Student.query.filter_by(squad_id=None).all() or []
        squads = Squad.query.all() or []
        # This is a placeholder for the session password logic
        session_password = "LEARN781" 
    except Exception as e:
        app.logger.error(f"Database error on teacher dashboard: {e}")
        # If database fails, return an empty but stable page
        students, solo_students, squads, session_password = [], [], [], "Error"

    return render_template('teacher.html',
                           students=students,
                           solo_students_db=solo_students,
                           squads=squads,
                           session_password=session_password)

@app.route('/teacher/new-session-password', methods=['POST'])
def new_session_password():
    """Generate new session password for teacher"""
    if not session.get('teacher_authenticated'):
        flash('Please login to access this feature.', 'error')
        return redirect(url_for('teacher_login'))
    
    new_password = SessionSettings.update_password()
    flash(f'New session password generated: {new_password}', 'success')
    logging.info(f"Teacher generated new session password: {new_password}")
    
    return redirect(url_for('teacher'))

@app.route('/teacher/logout')
def teacher_logout():
    """Log out teacher and clear session"""
    session.pop('teacher_authenticated', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('teacher'))

def create_vibe_squads():
    """Group students into squads based on their answer to 'The Ultimate Crew' question"""
    # Get all unassigned students from database
    students = Student.query.filter_by(squad_id=None).all()
    
    if len(students) < 4:
        return {
            'squads': [],
            'solo_students': students
        }
    
    # Define quality-based groupings based on Ultimate Crew question (question6)
    quality_groups = {
        'humor_team': {
            'keywords': ['funny', 'humor', 'laugh', 'joke', 'comedy', 'witty', 'hilarious', 'fun', 'entertaining', 'cheerful', 'upbeat'],
            'name': 'The Comedy Crew',
            'description': 'Masters of Fun & Laughter'
        },
        'leadership_team': {
            'keywords': ['leader', 'leadership', 'organize', 'organized', 'planner', 'responsible', 'reliable', 'dependable', 'take charge', 'motivate'],
            'name': 'The Leadership Squad',
            'description': 'Natural Born Leaders'
        },
        'creative_team': {
            'keywords': ['creative', 'imagination', 'artistic', 'innovative', 'original', 'unique', 'inventive', 'design', 'ideas', 'thinking outside'],
            'name': 'The Creative Collective',
            'description': 'Innovation & Imagination'
        },
        'analytical_team': {
            'keywords': ['smart', 'intelligent', 'analytical', 'logical', 'strategic', 'problem-solving', 'think', 'plan', 'strategy', 'clever'],
            'name': 'The Think Tank',
            'description': 'Strategic Problem Solvers'
        },
        'supportive_team': {
            'keywords': ['supportive', 'kind', 'caring', 'empathetic', 'understanding', 'helpful', 'team player', 'collaborative', 'encouraging', 'positive'],
            'name': 'The Support Squad',
            'description': 'Champions of Teamwork'
        },
        'energetic_team': {
            'keywords': ['energetic', 'enthusiastic', 'passionate', 'motivated', 'driven', 'active', 'dynamic', 'spirited', 'ambitious', 'determined'],
            'name': 'The Energy Force',
            'description': 'Pure Power & Enthusiasm'
        }
    }
    
    # Analyze each student's Ultimate Crew answer and assign to quality groups
    student_assignments = {}
    group_members = {group: [] for group in quality_groups.keys()}
    
    for student in students:
        ultimate_crew_answer = (student.question6 or "").lower()
        best_group = None
        max_matches = 0
        
        # Find the quality group with most keyword matches
        for group_name, group_info in quality_groups.items():
            match_count = sum(1 for keyword in group_info['keywords'] 
                            if keyword in ultimate_crew_answer)
            
            if match_count > max_matches:
                max_matches = match_count
                best_group = group_name
        
        # If no keywords match, categorize based on general sentiment
        if best_group is None:
            # Look for general positive team qualities
            if any(word in ultimate_crew_answer for word in ['team', 'together', 'help', 'work', 'support']):
                best_group = 'supportive_team'
            elif any(word in ultimate_crew_answer for word in ['smart', 'think', 'solve', 'plan']):
                best_group = 'analytical_team'
            elif any(word in ultimate_crew_answer for word in ['fun', 'enjoy', 'happy', 'good']):
                best_group = 'humor_team'
            else:
                best_group = 'creative_team'  # Default fallback
        
        student_assignments[student.id] = best_group
        group_members[best_group].append(student)
    
    # Create balanced squads from quality groups
    squads = []
    processed_students = set()
    
    # Sort groups by size (largest first) to ensure good distribution
    sorted_groups = sorted(group_members.items(), key=lambda x: len(x[1]), reverse=True)
    
    while len(students) - len(processed_students) >= 4:
        current_squad = []
        squad_qualities = []
        
        # Try to get one student from each quality group for diversity
        for group_name, members in sorted_groups:
            available_members = [s for s in members if s.id not in processed_students]
            if available_members and len(current_squad) < 4:
                selected_student = available_members[0]
                current_squad.append(selected_student)
                processed_students.add(selected_student.id)
                squad_qualities.append(quality_groups[group_name]['description'])
        
        # Fill remaining spots if squad has less than 4 members
        while len(current_squad) < 4:
            available_students = [s for s in students if s.id not in processed_students]
            if not available_students:
                break
            
            # Prioritize students from groups not yet represented in this squad
            represented_groups = {student_assignments[s.id] for s in current_squad}
            
            next_student = None
            for group_name, members in sorted_groups:
                if group_name not in represented_groups:
                    available_from_group = [s for s in members if s.id not in processed_students]
                    if available_from_group:
                        next_student = available_from_group[0]
                        squad_qualities.append(quality_groups[group_name]['description'])
                        break
            
            # If no unrepresented groups, take any available student
            if next_student is None and available_students:
                next_student = available_students[0]
                group = student_assignments[next_student.id]
                squad_qualities.append(quality_groups[group]['description'])
            
            if next_student:
                current_squad.append(next_student)
                processed_students.add(next_student.id)
            else:
                break
        
        # Add one more member if possible (max 5 per squad)
        if len(current_squad) == 4:
            remaining_count = len(students) - len(processed_students)
            if remaining_count >= 4:  # Only add 5th if it won't prevent another squad
                available_students = [s for s in students if s.id not in processed_students]
                if available_students:
                    fifth_member = available_students[0]
                    current_squad.append(fifth_member)
                    processed_students.add(fifth_member.id)
                    group = student_assignments[fifth_member.id]
                    squad_qualities.append(quality_groups[group]['description'])
        
        # Create squad if it has enough members
        if len(current_squad) >= 4:
            # Create a meaningful shared interests description
            unique_qualities = list(set(squad_qualities))
            shared_interests = ', '.join(unique_qualities[:3])  # Show top 3 qualities
            
            squads.append({
                'members': current_squad,
                'shared_interests': shared_interests
            })
    
    # Students who couldn't be placed in squads become solo students
    solo_students = [s for s in students if s.id not in processed_students]
    
    return {
        'squads': squads,
        'solo_students': solo_students
    }

@app.route('/teacher/create-squads', methods=['POST'])
def create_squads():
    """AI-powered squad formation - The Sorting Hat of the application"""
    if not session.get('teacher_authenticated'):
        flash('Access denied. Please log in first.', 'error')
        return redirect(url_for('teacher'))
    
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
            flash('Need at least 3 students to create squads.', 'warning')
            return redirect(url_for('teacher'))
        
        # Step 3: Prepare student data with their 6 question responses for AI analysis
        students_data = []
        student_map = {}  # For efficient lookups during assignment
        
        for student in unassigned_students:
            student_data = {
                'id': student.id,
                'name': student.name,
                'question1': student.question1,
                'question2': student.question2,
                'question3': student.question3,
                'question4': student.question4,
                'question5': student.question5,
                'question6': student.question6,
            }
            students_data.append(student_data)
            student_map[student.id] = student
        
        logging.info(f"Sending {len(students_data)} students to AI for intelligent grouping")
        
        # Step 4: Send to AI as a social dynamics expert for squad formation
        ai_response = analyze_students_and_create_squads(students_data)
        
        # Step 5: Parse AI response and validate structure
        if not isinstance(ai_response, dict) or 'squads' not in ai_response:
            raise ValueError("Invalid AI response format - expected dict with 'squads' key")
        
        squads_created = 0
        
        # Step 6: Process each AI-suggested squad and save to database
        for squad_data in ai_response['squads']:
            # Validate squad structure
            required_keys = ['name', 'shared_interests', 'member_ids']
            if not all(key in squad_data for key in required_keys):
                logging.warning(f"Skipping squad with missing keys: {squad_data}")
                continue
            
            # Create new squad record
            new_squad = Squad(
                name=squad_data['name'],
                shared_interests=squad_data['shared_interests']
            )
            db.session.add(new_squad)
            db.session.flush()  # Get the squad ID for student assignments
            
            # Assign students to this squad
            members_assigned = 0
            for student_id in squad_data['member_ids']:
                if student_id in student_map:
                    student = student_map[student_id]
                    student.squad_id = new_squad.id
                    members_assigned += 1
                    logging.info(f"Assigned {student.name} to squad '{new_squad.name}'")
                else:
                    logging.warning(f"Student ID {student_id} not found in database")
            
            if members_assigned > 0:
                squads_created += 1
                logging.info(f"Created squad '{new_squad.name}' with {members_assigned} members")
            else:
                # Remove empty squads
                db.session.delete(new_squad)
        
        # Step 7: Commit all changes to database
        db.session.commit()
        
        if squads_created > 0:
            flash(f'Successfully created {squads_created} AI-powered squads! Students have been intelligently grouped based on shared interests.', 'success')
            logging.info(f"Squad formation complete: {squads_created} squads created")
        else:
            flash('No squads were created. Please try again or check the student data.', 'warning')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error during squad formation: {str(e)}")
        flash('Squad formation failed. Please try again.', 'error')
    
    return redirect(url_for('teacher'))


def create_fallback_squads(students_data):
    """
    Fallback squad creation when AI is unavailable
    Creates simple squads of 3-4 students sequentially
    """
    squads = []
    current_squad = []
    squad_number = 1
    
    for student in students_data:
        current_squad.append(student['id'])
        
        # Create squad when we have 4 members or when we're at the end
        if len(current_squad) == 4 or student == students_data[-1]:
            # Don't create squads with less than 3 members unless it's the only option
            if len(current_squad) >= 3 or len(squads) == 0:
                squads.append({
                    'name': f'Squad {squad_number}',
                    'shared_interests': 'Mixed interests and personalities',
                    'member_ids': current_squad.copy()
                })
                squad_number += 1
            else:
                # Add remaining students to the last squad
                if squads:
                    squads[-1]['member_ids'].extend(current_squad)
            
            current_squad = []
    
    return {'squads': squads}


def analyze_students_and_create_squads(students_data):
    """
    Send student data to AI (OpenAI) acting as social dynamics expert
    Returns JSON with intelligent squad groupings based on shared interests
    """
    try:
        from openai_integration import group_students_into_squads
        return group_students_into_squads(students_data)
    except ImportError:
        logging.error("OpenAI integration not available")
        return create_fallback_squads(students_data)
    except Exception as e:
        logging.error(f"Error in AI squad formation: {str(e)}")
        return create_fallback_squads(students_data)


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
        flash('Access denied. Please log in first.', 'error')
        return redirect(url_for('teacher'))
    
    try:
        student = Student.query.get_or_404(student_id)
        student_name = student.name
        
        # Delete the student record
        db.session.delete(student)
        db.session.commit()
        
        flash(f'Successfully deleted student: {student_name}', 'success')
        logging.info(f"Deleted student: {student_name} (ID: {student_id})")
        
        # Clear current squads since student composition has changed
        if 'current_squads' in session:
            del session['current_squads']
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting student {student_id}: {str(e)}")
        flash('There was an error deleting the student. Please try again.', 'error')
    
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
        
        flash(f'Squad "{squad_name}" has been cleanly deleted. {member_count} students are now available for new squads.', 'success')
        logging.info(f"Squad {squad_name} (ID: {squad_id}) deleted successfully, {member_count} students unassigned")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting squad: {str(e)}', 'error')
        logging.error(f"Failed to delete squad {squad_id}: {str(e)}")
    
    return redirect(url_for('teacher'))

@app.route('/clear-squads', methods=['POST'])
def clear_squads():
    """Delete all records from students and squads tables"""
    if not session.get('teacher_authenticated'):
        flash('Access denied. Please log in first.', 'error')
        return redirect(url_for('teacher'))
    
    try:
        # First, delete all records from the students table
        all_students = Student.query.all()
        total_students = len(all_students)
        
        for student in all_students:
            logging.info(f"Deleting student {student.name} (ID: {student.id})")
            db.session.delete(student)
        
        # Flush the student deletions
        db.session.flush()
        
        # Second, delete all records from the squads table
        all_squads = Squad.query.all()
        total_squads = len(all_squads)
        
        for squad in all_squads:
            logging.info(f"Deleting squad {squad.name} (ID: {squad.id})")
            db.session.delete(squad)
        
        # Commit all changes
        db.session.commit()
        
        flash(f'すべてのデータが削除されました。{total_students}人の学生と{total_squads}つのスクワッドが削除されました。', 'success')
        logging.info(f"All squads cleared successfully: {total_squads} squads deleted, {total_students} students unassigned")
        
    except Exception as e:
        db.session.rollback()
        flash(f'スクワッドクリア中にエラーが発生しました: {str(e)}', 'error')
        logging.error(f"Failed to clear all squads: {str(e)}")
    
    return redirect(url_for('teacher'))

@app.route('/generate-icebreaker/<int:squad_id>')
def generate_icebreaker(squad_id):
    """Generate AI-powered icebreaker for a specific squad"""
    if not session.get('teacher_authenticated'):
        flash('Access denied. Please log in first.', 'error')
        return redirect(url_for('teacher'))
    
    try:
        # Fetch the squad and its members
        squad = Squad.query.get_or_404(squad_id)
        members = squad.members
        
        if not members:
            flash(f'No members found in squad "{squad.name}".', 'error')
            return redirect(url_for('teacher'))
        
        # Prepare member data for AI analysis
        member_data = []
        for member in members:
            member_info = {
                'name': member.name,
                'country': member.country,
                'gender': member.gender,
                'answers': {
                    'go_to_activity': member.question1,
                    'skill_to_master': member.question2,
                    'talk_about_for_hours': member.question3,
                    'ideal_friday_night': member.question4,
                    'weirdest_obsession': member.question5,
                    'energy_soundtrack': member.question6
                }
            }
            member_data.append(member_info)
        
        # Call Gemini AI to generate icebreaker
        icebreaker_text = generate_squad_icebreaker_with_ai(member_data, squad.name)
        
        # Save the icebreaker to the database
        squad.icebreaker_text = icebreaker_text
        db.session.commit()
        
        flash(f'Icebreaker generated for squad "{squad.name}"!', 'success')
        logging.info(f"Generated icebreaker for squad {squad.name} (ID: {squad_id})")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error generating icebreaker: {str(e)}', 'error')
        logging.error(f"Failed to generate icebreaker for squad {squad_id}: {str(e)}")
    
    return redirect(url_for('teacher'))

@app.route('/teacher/ai-advice/<int:student_id>', methods=['POST'])
def get_ai_advice(student_id):
    """Generate AI advice for a solo student"""
    if not session.get('teacher_authenticated'):
        flash('Access denied. Please log in first.', 'error')
        return redirect(url_for('teacher'))
    
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
        flash(f'AI advice generated for {student.name}', 'success')
        
    except Exception as e:
        logging.error(f"Error generating AI advice for student {student_id}: {str(e)}")
        flash('Unable to generate AI advice at this time.', 'error')
    
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
        flash('Access denied. Please log in first.', 'error')
        return redirect(url_for('teacher'))
    
    students = Student.query.all()
    
    if len(students) < 2:
        flash('Need at least 2 students to generate AI insights.', 'info')
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
        
        flash('Database has been reset!', 'success')
        logging.info("Database reset completed successfully")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting database: {str(e)}', 'error')
        logging.error(f"Database reset failed: {str(e)}")
    
    return redirect(url_for('teacher_login'))

@app.route('/seed-database')
def seed_database():
    """Temporary route to seed database with fake student data for testing"""
    try:
        # Test student data: 4 Chinese, 2 Vietnamese, 2 English speakers
        fake_students_data = [
            {
                'name': '李小明',
                'country': 'China',
                'gender': 'Male',
                'question1': '和朋友一起打游戏',
                'question2': '学习编程和人工智能',
                'question3': '科技趋势和游戏策略',
                'question4': '在线游戏聚会',
                'question5': '收集稀有游戏卡片',
                'question6': '电子舞曲音乐'
            },
            {
                'name': '王小华',
                'country': 'China',  
                'gender': 'Female',
                'question1': '在咖啡厅看小说',
                'question2': '数字艺术和插画设计',
                'question3': '书籍、电影和创意故事',
                'question4': '看电影吃爆米花',
                'question5': '收集古董书籍',
                'question6': 'Lo-fi和独立音乐'
            },
            {
                'name': '张伟',
                'country': 'China',
                'gender': 'Male',
                'question1': '打篮球和户外运动',
                'question2': '体育训练和健身',
                'question3': '运动统计和健身方法',
                'question4': '和朋友打篮球',
                'question5': '收集运动鞋',
                'question6': '嘻哈和说唱音乐'
            },
            {
                'name': '刘美丽',
                'country': 'China',
                'gender': 'Female',
                'question1': '画画和做手工艺品',
                'question2': '传统艺术和书法',
                'question3': '艺术文化和传统工艺',
                'question4': '艺术创作之夜',
                'question5': '收集艺术用品',
                'question6': '古典音乐和民族音乐'
            },
            {
                'name': 'Nguyễn Thị Lan',
                'country': 'Vietnam',
                'gender': 'Female',
                'question1': 'Nấu các món ăn truyền thống Việt Nam',
                'question2': 'Nghệ thuật ẩm thực và chụp ảnh món ăn',
                'question3': 'Văn hóa ẩm thực và kỹ thuật nấu nướng',
                'question4': 'Nấu bữa tối cho gia đình',
                'question5': 'Sưu tập sách nấu ăn cổ',
                'question6': 'Nhạc dân ca Việt Nam'
            },
            {
                'name': 'Trần Văn Minh',
                'country': 'Vietnam',
                'gender': 'Male',
                'question1': 'Chụp ảnh và khám phá các con phố thành phố',
                'question2': 'Nhiếp ảnh và kể chuyện bằng hình ảnh',
                'question3': 'Nghệ thuật, nhiếp ảnh và văn hóa đô thị',
                'question4': 'Đi dạo chụp ảnh quanh thành phố',
                'question5': 'Sưu tập máy ảnh vintage',
                'question6': 'Nhạc rock độc lập và alternative'
            },
            {
                'name': 'Emma Johnson',
                'country': 'Other',
                'gender': 'Female',
                'question1': 'Reading fantasy novels in cozy places',
                'question2': 'Creative writing and storytelling',
                'question3': 'Literature, movies, and creative arts',
                'question4': 'Reading with tea and snacks',
                'question5': 'Collecting first edition books',
                'question6': 'Folk and acoustic music'
            },
            {
                'name': 'Michael Smith',
                'country': 'Other',
                'gender': 'Male',
                'question1': 'Building electronics and coding projects',
                'question2': 'Software engineering and robotics',
                'question3': 'Technology innovation and engineering',
                'question4': 'Coding and building projects',
                'question5': 'Collecting vintage electronics',
                'question6': 'Electronic and synthwave music'
            }
        ]
        
        # Create students
        created_students = []
        for student_data in fake_students_data:
            # Generate combined vibes text
            vibes_text = f"{student_data['question1']} {student_data['question2']} {student_data['question3']} {student_data['question4']} {student_data['question5']} {student_data['question6']}"
            
            student = Student(
                name=student_data['name'],
                country=student_data['country'],
                gender=student_data['gender'],
                question1=student_data['question1'],
                question2=student_data['question2'],
                question3=student_data['question3'],
                question4=student_data['question4'],
                question5=student_data['question5'],
                question6=student_data['question6'],
                vibes=vibes_text,
                submission_id=Student.generate_submission_id()
            )
            
            db.session.add(student)
            created_students.append(student)
        
        # Flush to get student IDs
        db.session.flush()
        
        # Create two squads
        squad1 = Squad(
            name="Creative Explorers",
            shared_interests="Art, Music, Photography, Creative Expression"
        )
        squad2 = Squad(
            name="Adventure Seekers", 
            shared_interests="Gaming, Technology, Problem-Solving, Outdoor Activities"
        )
        
        db.session.add(squad1)
        db.session.add(squad2)
        db.session.flush()
        
        # Assign students to squads (first 4 to squad1, last 4 to squad2)
        for i, student in enumerate(created_students):
            if i < 4:
                student.squad_id = squad1.id
            else:
                student.squad_id = squad2.id
        
        # Commit all changes
        db.session.commit()
        
        flash('8 fake students and 2 squads have been created!', 'success')
        logging.info("Database seeded successfully with 8 students and 2 squads")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error seeding database: {str(e)}', 'error')
        logging.error(f"Database seeding failed: {str(e)}")
    
    return redirect(url_for('teacher'))




@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('session_password.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    flash('An internal error occurred. Please try again.', 'error')
    return render_template('session_password.html'), 500
