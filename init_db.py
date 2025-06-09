# -*- coding: utf-8 -*-
from main import create_app, db
from models import User
import gc
import os

def init_db():
    # Set memory optimization flags
    os.environ['PYTHONMALLOC'] = 'debug'
    os.environ['PYTHONMALLOCSTATS'] = '1'
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['PYTHONHASHSEED'] = '0'
    
    app = create_app()
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            
            # Check if we need to create an admin user
            admin = User.query.filter_by(email='admin@example.com').first()
            if not admin:
                admin = User(
                    google_id='admin',
                    email='admin@example.com',
                    name='Admin User'
                )
                db.session.add(admin)
                db.session.commit()
                print("Created admin user")
            else:
                print("Admin user already exists")
            
            # Clean up
            db.session.close()
            gc.collect()
            
        except Exception as e:
            print(f"Error during database initialization: {e}")
            raise
        finally:
            # Ensure cleanup happens even if there's an error
            db.session.close()
            gc.collect()

if __name__ == '__main__':
    init_db() 