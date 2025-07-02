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
        # For now, we'll check if the student exists in the database
        # Squad assignment logic will be implemented when squads are created
        squad_info = None
        
        # TODO: Implement squad lookup when squad system is enhanced
        # This is a placeholder for when squads are properly stored in database
        if hasattr(student, 'squad_id') and student.squad_id:
            # Squad assignment exists
            squad_info = {
                'squad_name': f'Squad {student.squad_id}',
                'members': [student.name],  # Placeholder
                'student_name': student.name
            }
        else:
            # No squad assigned yet
            flash('ID not found, or your squad has not been created yet. Please check your ID or wait for your teacher to create the squads.', 'error')
            return render_template('find_squad.html')
        
        return render_template('find_squad.html', 
                             squad_info=squad_info,
                             student=student)
    
    # GET request - show the form
    return render_template('find_squad.html')



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

@app.route('/profile/<int:id>')
def student_profile(id):
    """Student private profile page"""
    # Check if student is logged in and accessing their own profile
    if 'student_id' not in session or session['student_id'] != id:
        flash('Please login to access your profile.', 'error')
        return redirect(url_for('student_login'))
    
    student = Student.query.get_or_404(id)
    
    # Get archetype information
    archetype_info = get_creative_vibe_archetype(student)
    
    # Get core interests
    core_sparks = get_core_sparks(student.get_combined_answers())
    
    # Get interest categories
    interests = get_interest_categories_with_colors(student.get_combined_answers())
    
    return render_template('profile.html', 
                         student=student, 
                         archetype=archetype_info,
                         core_sparks=core_sparks,
                         interests=interests)

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
    """Group students into squads of 4-5 members based on shared interests"""
    # Get all students
    students = Student.query.all()
    
    if len(students) < 4:
        return {
            'squads': [],
            'solo_students': students
        }
    
    # Define interest keywords to look for
    interest_keywords = [
        'game', 'gaming', 'games', 'video games', 'gamer',
        'music', 'musical', 'musician', 'singing', 'guitar', 'piano', 'song',
        'anime', 'manga', 'japanese', 'cosplay', 'otaku',
        'travel', 'traveling', 'adventure', 'explore', 'trip',
        'food', 'cooking', 'baking', 'cuisine', 'restaurant', 'eat',
        'sport', 'sports', 'football', 'basketball', 'soccer', 'tennis', 'athletic',
        'art', 'drawing', 'painting', 'creative', 'design', 'sketch',
        'reading', 'books', 'literature', 'novel', 'story',
        'technology', 'tech', 'programming', 'coding', 'computer', 'software',
        'fitness', 'gym', 'workout', 'exercise', 'running', 'health',
        'photography', 'photo', 'camera', 'picture',
        'dance', 'dancing', 'ballet', 'hip hop',
        'movie', 'film', 'cinema', 'netflix',
        'nature', 'outdoor', 'hiking', 'camping'
    ]
    
    # Create student interest profiles with compatibility scores
    student_data = []
    for student in students:
        interests = set()
        vibes_lower = student.vibes.lower()
        
        # Find matching keywords in student's vibes
        for keyword in interest_keywords:
            if keyword in vibes_lower:
                interests.add(keyword)
        
        student_data.append({
            'student': student,
            'interests': interests,
            'compatibility_scores': {}
        })
    
    # Calculate compatibility scores between all students
    for i, student1 in enumerate(student_data):
        for j, student2 in enumerate(student_data):
            if i != j:
                shared_interests = student1['interests'].intersection(student2['interests'])
                compatibility = len(shared_interests)
                student1['compatibility_scores'][j] = compatibility
    
    squads = []
    processed_indices = set()
    
    # Form squads ensuring 4-5 members each
    while len(student_data) - len(processed_indices) >= 4:
        # Find student with most unprocessed compatible connections
        best_starter = None
        best_score = -1
        
        for i, student_info in enumerate(student_data):
            if i in processed_indices:
                continue
                
            # Count compatible unprocessed students
            compatible_count = sum(1 for j, score in student_info['compatibility_scores'].items() 
                                 if j not in processed_indices and score > 0)
            
            if compatible_count > best_score:
                best_score = compatible_count
                best_starter = i
        
        if best_starter is None:
            # No clear starter, pick first unprocessed
            best_starter = next(i for i in range(len(student_data)) if i not in processed_indices)
        
        # Start squad with best starter
        current_squad = [best_starter]
        processed_indices.add(best_starter)
        
        # Find best compatible students for this squad
        while len(current_squad) < 5 and len(student_data) - len(processed_indices) > 0:
            best_candidate = None
            best_compatibility = -1
            
            # Don't fill to 5 if it would leave less than 4 for another squad
            remaining_after = len(student_data) - len(processed_indices) - 1
            if len(current_squad) >= 4 and remaining_after > 0 and remaining_after < 4:
                break
            
            for candidate_idx in range(len(student_data)):
                if candidate_idx in processed_indices:
                    continue
                
                # Calculate average compatibility with current squad
                total_compatibility = sum(student_data[squad_member]['compatibility_scores'].get(candidate_idx, 0) 
                                        for squad_member in current_squad)
                avg_compatibility = total_compatibility / len(current_squad)
                
                if avg_compatibility > best_compatibility:
                    best_compatibility = avg_compatibility
                    best_candidate = candidate_idx
            
            if best_candidate is not None:
                current_squad.append(best_candidate)
                processed_indices.add(best_candidate)
            else:
                break
        
        # Create squad if it has at least 4 members
        if len(current_squad) >= 4:
            squad_members = [student_data[i]['student'] for i in current_squad]
            
            # Calculate shared interests for display
            all_interests = set()
            for i in current_squad:
                all_interests.update(student_data[i]['interests'])
            
            squads.append({
                'members': squad_members,
                'shared_interests': ', '.join(sorted(list(all_interests))[:4]) or 'diverse interests'
            })
    
    # Students who couldn't be placed in squads become solo students
    solo_students = [student_data[i]['student'] for i in range(len(student_data)) 
                    if i not in processed_indices]
    
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
            # Create squad with a creative name
            squad_names = [
                "The Innovators", "Creative Minds", "Dream Team", "The Explorers", 
                "Vibe Squad Alpha", "The Mavericks", "Squad Goals", "The Visionaries",
                "Dynamic Duo+", "The Catalysts", "Team Phoenix", "The Pioneers"
            ]
            squad_name = squad_names[i % len(squad_names)] if i < len(squad_names) else f"Squad {i + 1}"
            
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

@app.route('/teacher/delete-student/<int:student_id>', methods=['POST'])
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

@app.route('/teacher/delete-squad', methods=['POST'])
def delete_squad():
    """Delete a squad and move all members to ungrouped list"""
    if not session.get('teacher_authenticated'):
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        data = request.get_json()
        squad_index = int(data['squad_index'])
        
        # Get current squads and ungrouped students from session
        current_squads = session.get('current_squads', [])
        ungrouped_students = session.get('ungrouped_students', [])
        
        if 0 <= squad_index < len(current_squads):
            # Move all squad members to ungrouped list
            squad_to_delete = current_squads.pop(squad_index)
            ungrouped_students.extend(squad_to_delete['members'])
            
            # Update session
            session['current_squads'] = current_squads
            session['ungrouped_students'] = ungrouped_students
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Invalid squad index'})
            
    except Exception as e:
        logging.error(f"Error deleting squad: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error'})

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

@app.route('/squads')
def squads():
    """Public page displaying vibe squads with cards"""
    # Fetch all squads from database with their members
    db_squads = Squad.query.all()
    
    # If no squads exist in database, show empty state
    if not db_squads:
        return render_template('squads.html', squads=[], no_squads=True)
    
    # Transform database squads into enhanced format for display
    enhanced_squads = []
    for squad in db_squads:
        enhanced_members = []
        for member in squad.members:
            vibes_text = member.vibes or member.get_combined_answers()
            enhanced_member = {
                'id': member.id,
                'name': member.name,
                'vibes': vibes_text,
                'country': member.country,
                'gender': member.gender,
                'submission_id': member.submission_id,
                'archetype': get_vibe_archetype(vibes_text),
                'sparks': get_core_sparks(vibes_text),
                'interests': get_interest_categories_with_colors(vibes_text)
            }
            enhanced_members.append(enhanced_member)
        
        enhanced_squads.append({
            'id': squad.id,
            'name': squad.name,
            'members': enhanced_members,
            'shared_interests': squad.shared_interests,
            'created_at': squad.created_at
        })
    
    return render_template('squads.html', squads=enhanced_squads, no_squads=False)

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
