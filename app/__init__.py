from flask import Flask
from flask_login import LoginManager
from app.models import db, User
import os


def create_app():
    app = Flask(__name__)
    
    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lost_found.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Initialize extensions
    db.init_app(app)
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # 創建預設管理員帳號
        if not User.query.filter_by(id_number='admin').first():
            admin_user = User(
                id_number='admin',
                email='admin@school.com',
                real_name='預設管理員',
                role='admin'
            )
            admin_user.set_password('admin')
            db.session.add(admin_user)
            db.session.commit()
            print("初始化：已自動創建預設管理員帳號 (admin/admin)")

    # Register blueprints
    from app.routes import auth_bp, main_bp, lost_items_bp, found_items_bp, claims_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(lost_items_bp)
    app.register_blueprint(found_items_bp)
    app.register_blueprint(claims_bp)
    
    return app
