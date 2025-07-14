import os
import json
import logging

from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create and configure the app
app = Flask(__name__)
from config import Config
app.config.from_object(Config)

# Initialize the app with the extension
db.init_app(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Add custom template filter for JSON parsing
@app.template_filter('from_json')
def from_json_filter(value):
    """Parse JSON string in templates"""
    try:
        return json.loads(value) if value else None
    except (json.JSONDecodeError, TypeError):
        return None

with app.app_context():
    # Import models to ensure tables are created
    import models  # noqa: F401
    
    # Create all tables
    db.create_all()

# Define the login route at the top level
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/firebase-config')
def firebase_config():
    # This route provides the NON-SECRET keys to the frontend JavaScript
    return jsonify({
        'apiKey': app.config['FIREBASE_API_KEY'],
        'authDomain': "vibecheckapp-52d16.firebaseapp.com",
        'projectId': "vibecheckapp-52d16",
        'storageBucket': "vibecheckapp-52d16.appspot.com",
        'messagingSenderId': "107974419632",
        'appId': "1:107974419632:web:c17312e16ef5ae7f8c4775",
        'measurementId': "G-HQ23WYKND8"
    })

import routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)