from flask import Flask # Import Flask directly
from main import db # Import db from main

# Create a minimal Flask app instance for database context
app = Flask(__name__)

# Initialize db with this app
db.init_app(app)

with app.app_context():
    db.create_all()
    print("Database tables created successfully!") 