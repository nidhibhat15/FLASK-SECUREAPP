from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from .forms import EncryptForm
from ..utils import get_cipher
from ..extensions import db
from ..models import Message, User

main_bp = Blueprint('main', __name__, template_folder='templates', url_prefix='')

# ✅ New root route
@main_bp.route('/')
@login_required
def home():
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    messages = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.created_at.desc()).all()
    cipher = get_cipher()

    # Decrypt messages for display
    for msg in messages:
        try:
            msg.plaintext = cipher.decrypt(msg.token.encode()).decode()
        except Exception:
            msg.plaintext = "[Cannot decrypt]"

    return render_template('dashboard.html', messages=messages)

@main_bp.route('/encrypt', methods=['GET', 'POST'])
@login_required
def encrypt():
    form = EncryptForm()

    # Populate recipient dropdown
    users = [(u.id, u.username) for u in User.query.all() if u.id != current_user.id]
    users.insert(0, (0, 'Self Note'))
    form.recipient.choices = users

    if form.validate_on_submit():
        cipher = get_cipher()
        token = cipher.encrypt(form.message.data.encode()).decode()

        recipient_id = form.recipient.data
        if recipient_id == 0:
            recipient_id = current_user.id  # self note

        msg = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            token=token
        )
        db.session.add(msg)
        db.session.commit()
        flash('Message encrypted and saved', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('encrypt.html', form=form)

@main_bp.route('/decrypt', methods=['POST'])
@login_required
def decrypt():
    token = request.form.get('token')
    cipher = get_cipher()
    try:
        plaintext = cipher.decrypt(token.encode()).decode()
        flash(f'Decrypted message: {plaintext}', 'info')
    except Exception:
        flash('Invalid token or wrong key', 'danger')
    return redirect(url_for('main.dashboard'))
