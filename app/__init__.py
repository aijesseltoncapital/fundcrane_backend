from flask import Flask
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Load configuration
    app.config.from_pyfile('config.py')
    
    # Import and register blueprints
    from app.routes import payments_bp, documents_bp, user_authentication_bp
    
    app.register_blueprint(payments_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(user_authentication_bp)

    return app