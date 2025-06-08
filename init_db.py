from flask import Flask # Import Flask directly
import os # Import os for environment variables
from main import db # Import db from main

# Create a minimal Flask app instance for database context
app = Flask(__name__)

# Explicitly set database URI for this minimal app instance
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Recommended setting for Flask-SQLAlchemy

# Initialize db with this app
db.init_app(app)

with app.app_context():
    db.create_all()
    print("Database tables created successfully!") 