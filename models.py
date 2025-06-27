from app import db

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
    question7 = db.Column(db.Text, nullable=False)  # secret superpower
    country = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(50), nullable=False)
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
            'question7': getattr(self, 'question7', ''),
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
            getattr(self, 'question6', '') or '',
            getattr(self, 'question7', '') or ''
        ]
        return ' '.join(filter(None, answers))
