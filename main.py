from flask import Flask, render_template, send_from_directory, jsonify
import os
from dotenv import load_dotenv
from src.routes.auth import auth_bp, init_google_oauth
from src.routes.market_data import market_data_bp
from src.routes.portfolio import portfolio_bp
from config import config

# Load environment variables
load_dotenv()

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize Google OAuth
    init_google_oauth(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(market_data_bp, url_prefix='/api/market')
    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
    
    # Serve static files (frontend)
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    # API routes
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'ok'})
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    # Use production config if FLASK_ENV is set to production
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

