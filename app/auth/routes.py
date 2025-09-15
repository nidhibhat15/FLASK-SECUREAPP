from flask import Blueprint, render_template, redirect, url_for, flash, request
from .forms import RegisterForm, LoginForm
from ..extensions import db, bcrypt
from ..models import User
from flask_login import login_user, logout_user, login_required
from datetime import datetime, timedelta
import re

auth_bp = Blueprint('auth', __name__, template_folder='templates', url_prefix='')

PW_RULES = [
    (lambda s: len(s) >= 8, 'At least 8 characters'),
    (lambda s: re.search(r"[A-Z]", s), 'At least one uppercase letter'),
    (lambda s: re.search(r"[a-z]", s), 'At least one lowercase letter'),
    (lambda s: re.search(r"[0-9]", s), 'At least one digit'),
    (lambda s: re.search(r"[^A-Za-z0-9]", s), 'At least one symbol'),
]

MAX_FAILED = 5
LOCK_MINUTES = 15

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        failed_rules = [msg for check, msg in PW_RULES if not check(password)]
        if failed_rules:
            flash('Password not strong enough: ' + '; '.join(failed_rules), 'warning')
            return render_template('auth/register.html', form=form)
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'warning')
            return render_template('auth/register.html', form=form)
        pw_hash = bcrypt.generate_password_hash(password).decode()
        is_admin = False
        if User.query.count() == 0:
            is_admin = True
        user = User(username=username, password_hash=pw_hash, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Invalid credentials', 'danger')
            return render_template('auth/login.html', form=form)
        if user.is_locked():
            flash(f'Account locked until {user.locked_until.isoformat()} UTC', 'danger')
            return render_template('auth/login.html', form=form)
        if bcrypt.check_password_hash(user.password_hash, form.password.data):
            user.failed_attempts = 0
            user.locked_until = None
            db.session.commit()
            login_user(user)
            flash(f'Welcome {user.username}', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            user.failed_attempts += 1
            if user.failed_attempts >= MAX_FAILED:
                user.locked_until = datetime.utcnow() + timedelta(minutes=LOCK_MINUTES)
            db.session.commit()
            flash('Invalid credentials', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('auth.login'))
