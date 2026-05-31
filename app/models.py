from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用戶模型"""
    id = db.Column(db.Integer, primary_key=True)
    id_number = db.Column(db.String(20), unique=True, nullable=False)  # 學號或教職員編號（用於登錄）
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='student')  # admin, student, staff
    real_name = db.Column(db.String(80), nullable=False)  # 顯示用的真實姓名
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lost_items = db.relationship('LostItem', backref='reporter', lazy=True, foreign_keys='LostItem.reporter_id')
    found_items = db.relationship('FoundItem', backref='finder', lazy=True, foreign_keys='FoundItem.finder_id')
    claims = db.relationship('Claim', backref='claimer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)        
    def get_all_lost_for_admin(self):
        if self.role == 'admin':
            return LostItem.query.order_by(LostItem.created_at.desc()).all()
        return []

class LostItem(db.Model):
    """失物報告"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # phone, wallet, keys, clothes, etc.
    location = db.Column(db.String(200), nullable=False)
    lost_date = db.Column(db.DateTime, nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='lost')  # lost, found, claimed
    image_url = db.Column(db.String(255))
    contact_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    claims = db.relationship('Claim', backref='lost_item', lazy=True, cascade='all, delete-orphan')


class FoundItem(db.Model):
    """拾物報告"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    found_date = db.Column(db.DateTime, nullable=False)
    finder_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='available')  # available, claimed, returned
    image_url = db.Column(db.String(255))
    contact_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    claims = db.relationship('Claim', backref='found_item', lazy=True, cascade='all, delete-orphan')


class Claim(db.Model):
    """認領記錄"""
    id = db.Column(db.Integer, primary_key=True)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_item.id'), nullable=False)
    found_item_id = db.Column(db.Integer, db.ForeignKey('found_item.id'), nullable=False)
    claimer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, returned
    description = db.Column(db.Text)  # 領取人提供的詳細資訊
    claimed_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
