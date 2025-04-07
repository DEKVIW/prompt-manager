from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(db.String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(db.String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(db.String(128))
    is_admin: Mapped[bool] = mapped_column(db.Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    
    # 一对多关系
    prompts = relationship('Prompt', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    invite_codes = relationship('InviteCode', foreign_keys='InviteCode.creator_id', 
                                backref='creator', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def password(self):
        raise AttributeError('密码不可读')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class InviteCode(db.Model):
    __tablename__ = 'invite_codes'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(db.String(16), unique=True, index=True)
    is_used: Mapped[bool] = mapped_column(db.Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    used_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    creator_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'))
    used_by: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def use(self, user_id):
        if not self.is_used:
            self.is_used = True
            self.used_at = datetime.utcnow()
            self.used_by = user_id
            return True
        return False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) 