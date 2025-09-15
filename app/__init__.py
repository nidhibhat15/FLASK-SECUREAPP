import os
from flask import Flask
from .extensions import db, migrate, login_manager, bcrypt
from .utils import ensure_fernet_key
from .models import User

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Config
    app.config['SECRET_KEY'] = 'super-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'security.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Fernet key
    ensure_fernet_key(app)

    # Login
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints
    from .auth.routes import auth_bp
    from .files.routes import files_bp
    from .main.routes import main_bp
    from .messages.routes import messages_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(files_bp, url_prefix='/files')
    app.register_blueprint(main_bp)
    app.register_blueprint(messages_bp)

    # Ensure uploads folder
    os.makedirs(os.path.join(app.instance_path, 'uploads'), exist_ok=True)

    return app
