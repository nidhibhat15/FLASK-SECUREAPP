from .extensions import db
from datetime import datetime
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages_sent = db.relationship(
        'Message',
        backref='sender',
        foreign_keys='Message.sender_id',
        lazy=True
    )
    messages_received = db.relationship(
        'Message',
        backref='recipient',
        foreign_keys='Message.recipient_id',
        lazy=True
    )
    files = db.relationship('File', backref='owner', lazy=True)

    def is_locked(self):
        return self.locked_until and datetime.utcnow() < self.locked_until


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    one_time = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=True)

    def is_expired(self):
        return self.expires_at and datetime.utcnow() > self.expires_at


class File(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(260), nullable=False)
    stored_name = db.Column(db.String(260), nullable=False)
    mimetype = db.Column(db.String(120), nullable=True)
    size = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
