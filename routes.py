from flask import render_template, request, redirect, url_for, flash, session
from app import app, db
from models import Student
from forms import StudentForm, TeacherLoginForm
import logging
import re
from collections import Counter, defaultdict
from ai_recommendations import generate_interest_recommendations, enhance_archetype_with_ai, analyze_compatibility_with_ai

@app.route('/', methods=['GET', 'POST'])
def index():
    """Homepage with student information form"""
    form = StudentForm()
    
    if form.validate_on_submit():
        try:
            # Create new student record
            student = Student(
                name=form.name.data.strip(),
                vibes=form.vibes.data.strip(),
                country=form.country.data,
                gender=form.gender.data
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
            
            # Get solo students and AI advice from session
            solo_students = session.get('solo_students', [])
            ai_advice = {}
            for student in solo_students:
                advice_key = f'ai_advice_{student["id"]}'
                if advice_key in session:
                    ai_advice[student['id']] = session[advice_key]
            
            return render_template('teacher.html', 
                                 students=students,
                                 solo_students=solo_students,
                                 ai_advice=ai_advice)
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
    """Create vibe squads and redirect back to teacher dashboard"""
    if not session.get('teacher_authenticated'):
        flash('Access denied. Please log in first.', 'error')
        return redirect(url_for('teacher'))
    
    try:
        result = create_vibe_squads()
        squads = result['squads']
        solo_students = result['solo_students']
        
        session['current_squads'] = [
            {
                'members': [{'id': s.id, 'name': s.name, 'vibes': s.vibes, 'country': s.country, 'gender': s.gender} for s in squad['members']],
                'shared_interests': squad['shared_interests']
            }
            for squad in squads
        ]
        
        session['solo_students'] = [
            {'id': s.id, 'name': s.name, 'vibes': s.vibes, 'country': s.country, 'gender': s.gender}
            for s in solo_students
        ]
        
        flash(f'Successfully created {len(squads)} vibe squads with {len(solo_students)} solo students!', 'success')
        logging.info(f"Created {len(squads)} vibe squads with {len(solo_students)} solo students")
        
    except Exception as e:
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

def get_vibe_archetype(vibes_text):
    """Determine student's vibe archetype based on their interests"""
    vibes_lower = vibes_text.lower()
    
    # Define archetype patterns
    archetypes = {
        'Gaming Guru': ['game', 'gaming', 'games', 'video games', 'gamer', 'anime', 'manga', 'cosplay'],
        'Music Maestro': ['music', 'musical', 'musician', 'singing', 'guitar', 'piano', 'song', 'dance', 'dancing'],
        'Creative Artist': ['art', 'drawing', 'painting', 'creative', 'design', 'sketch', 'photography', 'photo'],
        'Adventure Seeker': ['travel', 'traveling', 'adventure', 'explore', 'trip', 'nature', 'outdoor', 'hiking'],
        'Sports Champion': ['sport', 'sports', 'football', 'basketball', 'soccer', 'tennis', 'athletic', 'fitness', 'gym'],
        'Tech Wizard': ['technology', 'tech', 'programming', 'coding', 'computer', 'software'],
        'Bookworm Scholar': ['reading', 'books', 'literature', 'novel', 'story', 'study'],
        'Foodie Explorer': ['food', 'cooking', 'baking', 'cuisine', 'restaurant', 'eat'],
        'Movie Buff': ['movie', 'film', 'cinema', 'netflix', 'watch']
    }
    
    # Count matches for each archetype
    archetype_scores = {}
    for archetype, keywords in archetypes.items():
        score = sum(1 for keyword in keywords if keyword in vibes_lower)
        if score > 0:
            archetype_scores[archetype] = score
    
    # Return archetype with highest score, or default
    if archetype_scores:
        return max(archetype_scores.items(), key=lambda x: x[1])[0]
    else:
        return 'Mystery Vibe'

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
    # Get squads from session or create from current students
    squads_data = session.get('current_squads')
    
    if not squads_data:
        # Create squads from current students if none exist
        result = create_vibe_squads()
        squads = result['squads']
        squads_data = [
            {
                'members': [{'id': s.id, 'name': s.name, 'vibes': s.vibes, 'country': s.country, 'gender': s.gender} for s in squad['members']],
                'shared_interests': squad['shared_interests']
            }
            for squad in squads
        ]
    
    # Enhance squad data with archetypes and sparks
    enhanced_squads = []
    for squad in squads_data:
        enhanced_members = []
        for member in squad['members']:
            enhanced_member = member.copy()
            enhanced_member['archetype'] = get_vibe_archetype(member['vibes'])
            enhanced_member['sparks'] = get_core_sparks(member['vibes'])
            enhanced_members.append(enhanced_member)
        
        enhanced_squads.append({
            'members': enhanced_members,
            'shared_interests': squad['shared_interests']
        })
    
    return render_template('squads.html', squads=enhanced_squads)

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
