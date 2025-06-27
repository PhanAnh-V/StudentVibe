from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length

class StudentForm(FlaskForm):
    """Form for collecting student information"""
    name = StringField(
        'Your Name',
        validators=[
            DataRequired(message='Name is required'),
            Length(min=2, max=100, message='Name must be between 2 and 100 characters')
        ],
        render_kw={
            'placeholder': 'Enter your full name',
            'class': 'form-control'
        }
    )
    
    vibes = TextAreaField(
        'Tell us about your interests and vibes',
        validators=[
            DataRequired(message='Please share your interests'),
            Length(min=10, max=500, message='Please write between 10 and 500 characters')
        ],
        render_kw={
            'placeholder': 'Share your hobbies, interests, what makes you unique, or anything you\'d like us to know about you...',
            'class': 'form-control',
            'rows': 4
        }
    )
    
    submit = SubmitField(
        'Submit',
        render_kw={'class': 'btn btn-primary btn-lg'}
    )

class TeacherLoginForm(FlaskForm):
    """Form for teacher authentication"""
    password = PasswordField(
        'Teacher Password',
        validators=[
            DataRequired(message='Password is required')
        ],
        render_kw={
            'placeholder': 'Enter teacher password',
            'class': 'form-control'
        }
    )
    
    submit = SubmitField(
        'Access Teacher Dashboard',
        render_kw={'class': 'btn btn-primary btn-lg'}
    )
