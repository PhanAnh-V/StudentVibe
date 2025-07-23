from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import random
import string

class Base(DeclarativeBase):
    pass

# Create database instance
db = SQLAlchemy(model_class=Base)

class SessionSettings(db.Model):
    """Model for storing session-wide settings like password"""
    __tablename__ = 'session_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    session_password = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    @staticmethod
    def generate_password():
        """Generate a random session password like VIBE123"""
        prefixes = ['VIBE', 'COOL', 'QUIZ', 'FORM', 'TEAM', 'STAR', 'WORK', 'LEARN']
        numbers = ''.join(random.choices(string.digits, k=3))
        return f"{random.choice(prefixes)}{numbers}"
    
    @staticmethod
    def get_current_password():
        """Get the current session password"""
        settings = SessionSettings.query.first()
        if not settings:
            # Create default password if none exists
            password = SessionSettings.generate_password()
            settings = SessionSettings(session_password=password)
            db.session.add(settings)
            db.session.commit()
        return settings.session_password
    
    @staticmethod
    def update_password():
        """Generate and update to a new session password"""
        new_password = SessionSettings.generate_password()
        settings = SessionSettings.query.first()
        if settings:
            settings.session_password = new_password
            settings.updated_at = db.func.current_timestamp()
        else:
            settings = SessionSettings(session_password=new_password)
            db.session.add(settings)
        db.session.commit()
        return new_password

class Student(db.Model):
    """Student model for storing student information"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Legacy field for backward compatibility
    vibes = db.Column(db.Text, nullable=True)
    # New mystery generator questions
    question1 = db.Column(db.Text, nullable=False)  # go-to activity
    question2 = db.Column(db.Text, nullable=False)  # skill to master
    question3 = db.Column(db.Text, nullable=False)  # talk about for hours
    question4 = db.Column(db.Text, nullable=False)  # ideal Friday night
    question5 = db.Column(db.Text, nullable=False)  # weirdest obsession
    question6 = db.Column(db.Text, nullable=False)  # energy soundtrack
    # Japanese translations for each question
    question1_jp = db.Column(db.Text, nullable=True)  # Japanese translation of question1
    question2_jp = db.Column(db.Text, nullable=True)  # Japanese translation of question2
    question3_jp = db.Column(db.Text, nullable=True)  # Japanese translation of question3
    question4_jp = db.Column(db.Text, nullable=True)  # Japanese translation of question4
    question5_jp = db.Column(db.Text, nullable=True)  # Japanese translation of question5
    question6_jp = db.Column(db.Text, nullable=True)  # Japanese translation of question6
    country = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    submission_id = db.Column(db.String(7), unique=True, nullable=True)
    squad_id = db.Column(db.Integer, db.ForeignKey('squads.id'), nullable=True)
    archetype = db.Column(db.String(100), nullable=True)  # AI-generated Japanese archetype nickname
    # Personality signature fields
    core_strength = db.Column(db.Text, nullable=True)  # Core strength/talent
    hidden_potential = db.Column(db.Text, nullable=True)  # Hidden potential/untapped abilities
    conversation_catalyst = db.Column(db.Text, nullable=True)  # Conversation starter/catalyst
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<Student {self.name}>'
    
    def to_dict(self):
        """Convert student object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'vibes': self.vibes or self.get_combined_answers(),  # Backward compatibility
            'question1': getattr(self, 'question1', ''),
            'question2': getattr(self, 'question2', ''),
            'question3': getattr(self, 'question3', ''),
            'question4': getattr(self, 'question4', ''),
            'question5': getattr(self, 'question5', ''),
            'question6': getattr(self, 'question6', ''),
            'country': self.country,
            'gender': self.gender,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_combined_answers(self):
        """Combine all mystery generator answers for analysis"""
        answers = [
            getattr(self, 'question1', '') or '',
            getattr(self, 'question2', '') or '',
            getattr(self, 'question3', '') or '',
            getattr(self, 'question4', '') or '',
            getattr(self, 'question5', '') or '',
            getattr(self, 'question6', '') or ''
        ]
        return ' '.join(filter(None, answers))
    
    @staticmethod
    def generate_submission_id():
        """Generate a unique submission ID like VIB-482"""
        while True:
            # Generate 3 random letters
            letters = ''.join(random.choices(string.ascii_uppercase, k=3))
            # Generate 3 random numbers
            numbers = ''.join(random.choices(string.digits, k=3))
            # Combine with dash
            submission_id = f"{letters}-{numbers}"
            
            # Check if this ID already exists
            existing = Student.query.filter_by(submission_id=submission_id).first()
            if not existing:
                return submission_id

class Squad(db.Model):
    """Model for storing student squads"""
    __tablename__ = 'squads'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    shared_interests = db.Column(db.Text, nullable=True)
    icebreaker_text = db.Column(db.Text, nullable=True)
    squad_icon = db.Column(db.String(50), nullable=True)
    squad_number = db.Column(db.Integer, nullable=True)
    squad_rank = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationship to students
    members = db.relationship('Student', backref='squad', lazy=True)
    
    def __repr__(self):
        return f'<Squad {self.name}>'
