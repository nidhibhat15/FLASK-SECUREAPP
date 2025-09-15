import os
from cryptography.fernet import Fernet
from flask import current_app
import logging
from werkzeug.utils import secure_filename
import uuid

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.pdf', '.txt', '.csv', '.json', '.zip'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def ensure_fernet_key(app):
    keyfile = os.path.join(app.instance_path, 'fernet.key')
    # if key exists in config and file doesn't exist, write it
    if 'FERNET_KEY' in app.config:
        if not os.path.exists(keyfile):
            with open(keyfile, 'wb') as f:
                f.write(app.config['FERNET_KEY'])
        return

    # if file exists, read key
    if os.path.exists(keyfile):
        with open(keyfile, 'rb') as f:
            app.config['FERNET_KEY'] = f.read()
    else:
        # generate new key
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(keyfile), exist_ok=True)
        with open(keyfile, 'wb') as f:
            f.write(key)
        app.config['FERNET_KEY'] = key

def get_cipher():
    key = current_app.config.get('FERNET_KEY')
    if not key:
        raise RuntimeError('FERNET_KEY is not set')
    if isinstance(key, str):
        key = key.encode()  # ensure bytes
    return Fernet(key)

def save_encrypted_file(file_storage):
    filename = secure_filename(file_storage.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("File type not allowed")

    data = file_storage.read()
    if len(data) > MAX_FILE_SIZE:
        raise ValueError("File too large")

    cipher = get_cipher()
    encrypted_data = cipher.encrypt(data)

    stored_name = f"{uuid.uuid4().hex}{ext}.enc"
    upload_folder = os.path.join(current_app.instance_path, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, stored_name)

    with open(path, 'wb') as f:
        f.write(encrypted_data)

    return stored_name, len(data), file_storage.mimetype, filename

def load_decrypted_file(stored_name):
    upload_folder = os.path.join(current_app.instance_path, 'uploads')
    path = os.path.join(upload_folder, stored_name)
    if not os.path.exists(path):
        raise FileNotFoundError

    with open(path, 'rb') as f:
        ciphertext = f.read()

    cipher = get_cipher()
    data = cipher.decrypt(ciphertext)
    return data
