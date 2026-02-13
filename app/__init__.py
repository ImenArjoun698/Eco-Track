from flask import Flask
import os
from app.routes.auth import auth

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

    # Register auth blueprint
    app.register_blueprint(auth)

    @app.route('/')
    def index():
        return "Eco-Track is running"

    return app
