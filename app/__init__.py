from flask import Flask, request, jsonify, render_template
from flask_login import LoginManager
from flask_dance.contrib.google import make_google_blueprint
from flask_migrate import Migrate
from app.extensions import db, login_manager
import os
from app.payment import payment_bp  # Ensure correct import path


migrate = Migrate()
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

def create_app():
    app = Flask(__name__)

    # Config
    app.config['SECRET_KEY'] = 'e1b8c3b7e3f14c1abde223f1241c39ea'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

     #unauthorized user leads to login page
    
    login_manager.login_view = "main.login"  # Redirects to login page if not logged in

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Google OAuth
    google_bp = make_google_blueprint(
        client_id="...",
        client_secret="...",
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ]
    )
    app.register_blueprint(google_bp, url_prefix="/login")
    app.register_blueprint(payment_bp)



    return app
