import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app
from flask_login import login_required, current_user
from ..forms import UploadForm
from ..utils import save_encrypted_file, load_decrypted_file
from ..extensions import db
from ..models import File
from io import BytesIO

files_bp = Blueprint('files', __name__, template_folder='templates', url_prefix='')

@files_bp.route('/vault')
@login_required
def vault():
    if current_user.is_admin:
        files = File.query.order_by(File.created_at.desc()).all()
    else:
        files = File.query.filter_by(user_id=current_user.id).order_by(File.created_at.desc()).all()
    form = UploadForm()
    return render_template('files/vault.html', files=files, form=form)

@files_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        f = request.files.get('file')
        if not f:
            flash('No file selected', 'warning')
            return redirect(url_for('files.vault'))
        try:
            stored_name, size, mimetype, original = save_encrypted_file(f)
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('files.vault'))
        rec = File(user_id=current_user.id, filename=original, stored_name=stored_name, mimetype=mimetype, size=size)
        db.session.add(rec)
        db.session.commit()
        flash('Uploaded and encrypted successfully', 'success')
    return redirect(url_for('files.vault'))

@files_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    rec = File.query.get_or_404(file_id)
    if not (current_user.is_admin or rec.user_id == current_user.id):
        flash('Access denied', 'danger')
        return redirect(url_for('files.vault'))
    try:
        data = load_decrypted_file(rec.stored_name)
    except FileNotFoundError:
        flash('File missing', 'danger')
        return redirect(url_for('files.vault'))
    return send_file(BytesIO(data), download_name=rec.filename, mimetype=rec.mimetype, as_attachment=True)

@files_bp.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    rec = File.query.get_or_404(file_id)
    if not (current_user.is_admin or rec.user_id == current_user.id):
        flash('Access denied', 'danger')
        return redirect(url_for('files.vault'))
    try:
        upload_folder = os.path.join(current_app.instance_path, 'uploads')
        path = os.path.join(upload_folder, rec.stored_name)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    db.session.delete(rec)
    db.session.commit()
    flash('Deleted successfully', 'info')
    return redirect(url_for('files.vault'))
