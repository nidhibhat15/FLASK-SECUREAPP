from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from ..forms import ComposeForm
from ..utils import get_cipher
from ..extensions import db
from ..models import Message, User
from datetime import datetime, timedelta

messages_bp = Blueprint('messages', __name__, template_folder='templates', url_prefix='')

@messages_bp.route('/messages/compose', methods=['GET','POST'])
@login_required
def compose():
    form = ComposeForm()
    form.recipient.choices = [(u.id, u.username) for u in User.query.filter(User.id != current_user.id).all()]
    if form.validate_on_submit():
        recipient_id = int(form.recipient.data)
        one_time = form.one_time.data
        ttl = form.ttl.data
        expires_at = None
        if ttl:
            expires_at = datetime.utcnow() + timedelta(seconds=int(ttl))
        cipher = get_cipher()
        token = cipher.encrypt(form.message.data.encode()).decode()
        msg = Message(sender_id=current_user.id, recipient_id=recipient_id, token=token, one_time=one_time, expires_at=expires_at)
        db.session.add(msg)
        db.session.commit()
        current_app.logger.info(f"{current_user.username} sent message to {recipient_id}")
        flash('Message sent', 'success')
        return redirect(url_for('messages.inbox'))
    return render_template('messages/compose.html', form=form)

@messages_bp.route('/messages/inbox')
@login_required
def inbox():
    if current_user.is_admin:
        msgs = Message.query.order_by(Message.created_at.desc()).all()
    else:
        msgs = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.created_at.desc()).all()
    return render_template('messages/inbox.html', messages=msgs)

@messages_bp.route('/messages/view/<int:message_id>')
@login_required
def view_message(message_id):
    msg = Message.query.get_or_404(message_id)
    if not (current_user.id == msg.recipient_id or current_user.is_admin or current_user.id == msg.sender_id):
        flash('Access denied', 'danger')
        return redirect(url_for('messages.inbox'))
    if msg.is_expired():
        db.session.delete(msg)
        db.session.commit()
        flash('Message expired', 'warning')
        return redirect(url_for('messages.inbox'))
    cipher = get_cipher()
    try:
        plain = cipher.decrypt(msg.token.encode()).decode()
    except Exception:
        flash('Decryption failed', 'danger')
        return redirect(url_for('messages.inbox'))
    msg.read = True
    if msg.one_time and current_user.id == msg.recipient_id:
        db.session.delete(msg)
    else:
        db.session.commit()
    return render_template('messages/view.html', message=msg, plaintext=plain)
