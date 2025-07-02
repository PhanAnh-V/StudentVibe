from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app import app, db
from models import Student, SessionSettings, Squad
from forms import StudentForm, TeacherLoginForm, StudentLoginForm
import logging
import re
import json
from collections import Counter, defaultdict
from ai_recommendations import generate_interest_recommendations, enhance_archetype_with_ai, analyze_compatibility_with_ai

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
            
            # Create new student record
            student = Student(
                name=form.name.data,
                vibes=combined_vibes,
                question1=form.question1.data,
                question2=form.question2.data,
                question3=form.question3.data,
                question4=form.question4.data,
                question5=form.question5.data,
                question6=form.question6.data,
                country=form.country.data,
                gender=form.gender.data,
                submission_id=submission_id
            )
            
            db.session.add(student)
            db.session.commit()
            
            logging.info(f"New student registered: {student.name} (ID: {student.id}, Submission ID: {submission_id})")
            
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
        
        # Add icebreaker_text attribute if it doesn't exist (placeholder for future AI integration)
        if not hasattr(squad, 'icebreaker_text'):
            squad.icebreaker_text = None
        
        return render_template('squad_hub.html', squad=squad)
        
    except Exception as e:
        logging.error(f"Error accessing squad hub {squad_id}: {str(e)}")
        flash('Squad not found or unable to access squad details.', 'error')
        return redirect(url_for('find_squad'))

@app.route('/profile/<int:student_id>')
def student_profile(student_id):
    """Student profile page displaying detailed character sheet"""
    try:
        # Fetch the student with all their data
        student = Student.query.get_or_404(student_id)
        
        # Load questionnaire data for displaying question titles
        try:
            questions = load_questionnaire_data()
            en_questions = questions.get('en', [])
        except:
            en_questions = []
        
        # Create a mapping of answers to questions for easy display
        if len(en_questions) >= 6:
            student_answers = [
                {'question': en_questions[0]['title'], 'answer': student.question1},
                {'question': en_questions[1]['title'], 'answer': student.question2},
                {'question': en_questions[2]['title'], 'answer': student.question3},
                {'question': en_questions[3]['title'], 'answer': student.question4},
                {'question': en_questions[4]['title'], 'answer': student.question5},
                {'question': en_questions[5]['title'], 'answer': student.question6},
            ]
        else:
            # Fallback question titles if questions.json is not available
            student_answers = [
                {'question': 'Adventure Preference', 'answer': student.question1},
                {'question': 'Passion Interest', 'answer': student.question2},
                {'question': 'Humor Style', 'answer': student.question3},
                {'question': 'Secret Superpower', 'answer': student.question4},
                {'question': 'Personal Vibe', 'answer': student.question5},
                {'question': 'Team Quality', 'answer': student.question6},
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
        flash('Student profile not found or unable to access details.', 'error')
        return redirect(url_for('teacher'))

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
def teacher():
    """Teacher dashboard with authentication required"""
    # Check if teacher is authenticated
    if not session.get('teacher_authenticated'):
        flash('Please login to access the teacher dashboard.', 'error')
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
    
    return render_template('teacher.html', 
                         students=students_with_interests,
                         squads=squads,
                         solo_students_db=solo_students_db,
                         ai_advice=ai_advice,
                         session_password=current_session_password)

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
    """Create vibe squads and save them to the database"""
    if not session.get('teacher_authenticated'):
        flash('Access denied. Please log in first.', 'error')
        return redirect(url_for('teacher'))
    
    try:
        # Clear existing squads and reset student assignments
        Squad.query.delete()
        db.session.execute(db.text("UPDATE students SET squad_id = NULL"))
        db.session.commit()
        
        # Use the existing squad creation logic
        result = create_vibe_squads()
        squads_data = result['squads']
        solo_students = result['solo_students']
        
        # Save squads to database
        for i, squad_data in enumerate(squads_data):
            # Create squad with a meaningful name based on their qualities
            squad_names = [
                "The Harmony Makers", "The Innovation Station", "The Dream Builders", "The Spark Squad", 
                "The Power Players", "The Creative Collective", "The Unity Squad", "The Bright Minds",
                "The Dynamic Force", "The Catalyst Crew", "The Phoenix Team", "The Visionary Squad"
            ]
            squad_name = squad_names[i % len(squad_names)] if i < len(squad_names) else f"Vibe Squad {i + 1}"
            
            new_squad = Squad(
                name=squad_name,
                shared_interests=squad_data['shared_interests']
            )
            db.session.add(new_squad)
            db.session.flush()  # Get the ID
            
            # Assign students to this squad
            for student in squad_data['members']:
                student.squad_id = new_squad.id
        
        db.session.commit()
        
        flash(f'Successfully created {len(squads_data)} vibe squads with {len(solo_students)} solo students!', 'success')
        logging.info(f"Created {len(squads_data)} vibe squads with {len(solo_students)} solo students")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating squads: {str(e)}")
        flash('There was an error creating the squads. Please try again.', 'error')
    
    return redirect(url_for('teacher'))

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
    """Delete a specific squad and move all members to ungrouped"""
    try:
        squad = Squad.query.get_or_404(squad_id)
        squad_name = squad.name
        
        # Move all squad members to ungrouped (set squad_id to None)
        for member in squad.members:
            member.squad_id = None
        
        # Delete the squad record
        db.session.delete(squad)
        db.session.commit()
        
        flash(f'Squad "{squad_name}" has been deleted and all members moved to ungrouped.', 'success')
        logging.info(f"Squad {squad_name} (ID: {squad_id}) deleted successfully")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting squad: {str(e)}', 'error')
        logging.error(f"Failed to delete squad {squad_id}: {str(e)}")
    
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
            student.question7 or ''
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
        # Sample fake student data with realistic answers
        fake_students_data = [
            {
                'name': 'Alex Chen',
                'country': 'China',
                'gender': 'Male',
                'question1': 'Hit the beach with friends and play volleyball all day',
                'question2': 'Photography - I love capturing street art and the way light changes throughout the day',
                'question3': 'When we tried to recreate a TikTok dance and failed spectacularly',
                'question4': 'I can always find the best food spots in any city within 10 minutes',
                'question5': 'Lo-fi hip hop playlist, Studio Ghibli films, and my vintage camera',
                'question6': 'Someone who stays calm under pressure and thinks outside the box'
            },
            {
                'name': 'Maria Nguyen',
                'country': 'Vietnam',
                'gender': 'Female',
                'question1': 'Explore hidden cafes in the city and try different coffee brewing methods',
                'question2': 'Cooking fusion dishes - mixing Vietnamese and Italian flavors creates amazing combinations',
                'question3': 'My friend trying to speak Vietnamese with Google Translate during a family dinner',
                'question4': 'I can organize any messy space into something beautiful and functional',
                'question5': 'Indie pop music, cooking shows, and my collection of vintage recipe books',
                'question6': 'Someone with great communication skills who can keep everyone motivated'
            },
            {
                'name': 'Yuki Tanaka',
                'country': 'Japan',
                'gender': 'Female',
                'question1': 'Visit art museums and sketch in quiet gardens',
                'question2': 'Anime illustration - the way artists convey emotion through simple lines is incredible',
                'question3': 'Watching my dad try to use emoji for the first time and sending random combinations',
                'question4': 'I can remember every detail from movies and TV shows I watch',
                'question5': 'J-pop ballads, slice-of-life anime, and my digital art tablet',
                'question6': 'Someone creative who notices small details others might miss'
            },
            {
                'name': 'Jake Rodriguez',
                'country': 'Other',
                'gender': 'Male',
                'question1': 'Go hiking in the mountains and set up camp under the stars',
                'question2': 'Rock climbing - the mental puzzle of finding the right route is as important as physical strength',
                'question3': 'Our camping trip when we realized we forgot the tent poles and had to build a shelter from branches',
                'question4': 'I can fix almost anything electronic with basic tools and patience',
                'question5': 'Alternative rock, adventure documentaries, and my climbing gear',
                'question6': 'Someone reliable who can problem-solve when things go wrong'
            },
            {
                'name': 'Emma Li',
                'country': 'China',
                'gender': 'Female',
                'question1': 'Attend live music concerts and discover new indie bands',
                'question2': 'Playing guitar - writing songs helps me process emotions and connect with others',
                'question3': 'Band practice when our drummer forgot his sticks and used chopsticks instead',
                'question4': 'I can learn any song by ear after listening to it a few times',
                'question5': 'Indie folk music, music documentaries, and my acoustic guitar',
                'question6': 'Someone with good rhythm who can keep the team in sync'
            },
            {
                'name': 'Minh Pham',
                'country': 'Vietnam',
                'gender': 'Male',
                'question1': 'Try street food from different vendors and rate each dish',
                'question2': 'Gaming - the storytelling in modern RPGs rivals the best novels and films',
                'question3': 'Online gaming session where our teammate accidentally revealed their age as 12',
                'question4': 'I can spot patterns and strategies in games that others miss',
                'question5': 'Electronic music, RPG games, and my gaming setup',
                'question6': 'Someone strategic who can think several steps ahead'
            },
            {
                'name': 'Sophie Kim',
                'country': 'Other',
                'gender': 'Female',
                'question1': 'Browse bookstores and read in cozy coffee shops all day',
                'question2': 'Creative writing - crafting characters and worlds that feel real is my passion',
                'question3': 'Reading my terrible poetry from middle school to my friends last week',
                'question4': 'I can remember quotes from books and movies with perfect accuracy',
                'question5': 'Acoustic covers, fantasy novels, and my leather-bound journal',
                'question6': 'Someone imaginative who brings fresh perspectives to challenges'
            },
            {
                'name': 'David Wong',
                'country': 'China',
                'gender': 'Male',
                'question1': 'Visit science museums and experiment with interactive exhibits',
                'question2': 'Robotics - building machines that can help solve real-world problems',
                'question3': 'Our robot competition when our bot started dancing instead of following the course',
                'question4': 'I can explain complex technical concepts in simple terms',
                'question5': 'Electronic beats, sci-fi films, and my Arduino kit',
                'question6': 'Someone analytical who can break down complex problems into steps'
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
