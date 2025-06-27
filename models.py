from app import db

class Student(db.Model):
    """Student model for storing student information"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    vibes = db.Column(db.Text, nullable=False)
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
            'vibes': self.vibes,
            'country': self.country,
            'gender': self.gender,
            'created_at': self.created_at
        }
