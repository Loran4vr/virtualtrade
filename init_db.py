import os
from main import create_app, db
from models import User

def init_db():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we need to create an admin user
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                email='admin@example.com',
                name='Admin User',
                google_id='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Created admin user")
        
        print("Database initialized successfully")

if __name__ == '__main__':
    init_db() 