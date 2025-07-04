from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange

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
    
    # Mystery Generator Questions
    question1 = TextAreaField(
        'What\'s your go-to activity when you have absolutely nothing planned?',
        validators=[
            DataRequired(message='This question is required'),
            Length(min=1, max=500, message='Please write between 1 and 500 characters')
        ],
        render_kw={
            'class': 'form-control'
        }
    )
    
    question2 = TextAreaField(
        'If you could master any skill instantly, what would it be?',
        validators=[
            DataRequired(message='This question is required'),
            Length(min=1, max=500, message='Please write between 1 and 500 characters')
        ],
        render_kw={
            'class': 'form-control'
        }
    )
    
    question3 = TextAreaField(
        'What\'s something you could talk about for hours without getting bored?',
        validators=[
            DataRequired(message='This question is required'),
            Length(min=1, max=500, message='Please write between 1 and 500 characters')
        ],
        render_kw={
            'class': 'form-control'
        }
    )
    
    question4 = TextAreaField(
        'Describe your ideal Friday night in 5 words or less.',
        validators=[
            DataRequired(message='This question is required'),
            Length(min=1, max=500, message='Please write between 1 and 500 characters')
        ],
        render_kw={
            'class': 'form-control'
        }
    )
    
    question5 = TextAreaField(
        'What\'s the weirdest thing you\'ve ever been obsessed with?',
        validators=[
            DataRequired(message='This question is required'),
            Length(min=1, max=500, message='Please write between 1 and 500 characters')
        ],
        render_kw={
            'class': 'form-control'
        }
    )
    
    question6 = TextAreaField(
        'If your energy had a soundtrack, what genre would it be?',
        validators=[
            DataRequired(message='This question is required'),
            Length(min=1, max=500, message='Please write between 1 and 500 characters')
        ],
        render_kw={
            'class': 'form-control'
        }
    )
    

    
    country = SelectField(
        'Country',
        choices=[
            ('China', '中国'),
            ('Vietnam', 'ベトナム'),
            ('Japan', '日本'),
            ('Other', 'その他')
        ],
        validators=[
            DataRequired(message='Please select your country')
        ],
        render_kw={'class': 'form-control'}
    )
    
    gender = SelectField(
        'Gender',
        choices=[
            ('Male', '男性'),
            ('Female', '女性'),
            ('Prefer not to say', '回答しない')
        ],
        validators=[
            DataRequired(message='Please select your gender')
        ],
        render_kw={'class': 'form-control'}
    )
    
    submit = SubmitField(
        '送信',
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

class StudentLoginForm(FlaskForm):
    """Form for student login using their unique ID"""
    student_id = IntegerField(
        'Your Student ID',
        validators=[
            DataRequired(message='Student ID is required'),
            NumberRange(min=1, message='Please enter a valid Student ID')
        ],
        render_kw={
            'placeholder': 'Enter your unique Student ID',
            'class': 'form-control'
        }
    )
    
    submit = SubmitField(
        'Access My Profile',
        render_kw={'class': 'btn btn-success btn-lg'}
    )