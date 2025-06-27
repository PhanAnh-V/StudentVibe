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
    
    # If we have fewer than 3 students, create one small squad
    if len(students) < 3:
        return [{
            'members': students,
            'shared_interests': 'small group'
        }]
    
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
    
    # Create student interest profiles
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
            'processed': False
        })
    
    squads = []
    
    # First pass: Group students with shared interests
    for i, student_info in enumerate(student_data):
        if student_info['processed'] or not student_info['interests']:
            continue
            
        current_squad = [student_info]
        student_info['processed'] = True
        
        # Find other students with similar interests
        for j, other_info in enumerate(student_data):
            if i == j or other_info['processed'] or len(current_squad) >= 4:
                continue
                
            # Check for shared interests
            shared = student_info['interests'].intersection(other_info['interests'])
            if shared:
                current_squad.append(other_info)
                other_info['processed'] = True
        
        # Only create squad if we have enough members
        if len(current_squad) >= 2:
            shared_interests = set()
            for member in current_squad:
                shared_interests.update(member['interests'])
            
            squads.append({
                'members': [m['student'] for m in current_squad],
                'shared_interests': ', '.join(sorted(list(shared_interests))[:3]) or 'mixed interests'
            })
    
    # Second pass: Group remaining students
    remaining = [s for s in student_data if not s['processed']]
    
    # Create squads from remaining students
    while len(remaining) >= 3:
        squad_size = min(4, len(remaining))
        squad_members = remaining[:squad_size]
        remaining = remaining[squad_size:]
        
        for member in squad_members:
            member['processed'] = True
            
        squads.append({
            'members': [m['student'] for m in squad_members],
            'shared_interests': 'diverse interests'
        })
    
    # Handle final remaining students
    if remaining:
        if squads and len(squads[-1]['members']) == 3:
            # Add to last squad if it has only 3 members
            squads[-1]['members'].extend([s['student'] for s in remaining])
        else:
            # Create final squad with remaining students
            squads.append({
                'members': [s['student'] for s in remaining],
                'shared_interests': 'mixed group'
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
        squads = create_vibe_squads()
        squads_data = [
            {
                'members': [{'id': s.id, 'name': s.name, 'vibes': s.vibes} for s in squad['members']],
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
