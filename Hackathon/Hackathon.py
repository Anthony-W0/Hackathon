#Hackathon File Project 

"""
Docstring for Hackathon FIle
Routing & Setup (Flask): 3 to 4 hours

File Handling (Upload/Download): 3 to 4 hours

Encryption Logic: 3 to 4 hours

UI/Cyberpunk Styling: 2 to 3 hours

Debugging & Buffer: 2 to 3 hours
"""

from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
import os
import io
import tempfile
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json
import hashlib
from datetime import datetime

app = Flask(__name__)
# SECURITY: Change this secret key for production!
app.secret_key = os.environ.get('SECRET_KEY', 'CHANGE_ME_IN_PRODUCTION_' + os.urandom(24).hex())
UPLOAD_FOLDER = 'drop_zone'
KEYS_FOLDER = 'keys'

# Message-based dead drops (from friend's code)
# WARNING: In-memory storage - will reset on server restart!
# For production, use a database instead
dead_drops = {}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(KEYS_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['KEYS_FOLDER'] = KEYS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Friend's Message Encryption Functions
def generate_key_simple(password: str) -> bytes:
    """Simple key generation for messages (friend's method)"""
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def encrypt_message(message, password):
    """Encrypt text message (friend's method)"""
    f = Fernet(generate_key_simple(password))
    return f.encrypt(message.encode()).decode()

def decrypt_message(ciphertext, password):
    """Decrypt text message (friend's method)"""
    f = Fernet(generate_key_simple(password))
    return f.decrypt(ciphertext.encode()).decode()

# Encryption Functions
def generate_key_from_password(password: str, salt: bytes = None) -> tuple:
    """Generate encryption key from password"""
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_file(file_path: str, password: str = "DEFAULT_DEAD_DROP_KEY") -> dict:
    """Encrypt file and return metadata"""
    try:
        # Generate encryption key
        key, salt = generate_key_from_password(password)
        fernet = Fernet(key)
        
        # Read and encrypt file
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        encrypted_data = fernet.encrypt(file_data)
        
        # Save encrypted file
        encrypted_path = file_path + '.enc'
        with open(encrypted_path, 'wb') as encrypted_file:
            encrypted_file.write(encrypted_data)
        
        # Remove original file (security)
        os.remove(file_path)
        
        # Create metadata
        metadata = {
            'original_name': os.path.basename(file_path),
            'encrypted_name': os.path.basename(encrypted_path),
            'salt': base64.b64encode(salt).decode(),
            'encryption_time': datetime.now().isoformat(),
            'size': len(encrypted_data)
        }
        
        # Save metadata
        metadata_path = file_path + '.meta'
        with open(metadata_path, 'w') as meta_file:
            json.dump(metadata, meta_file, indent=2)
        
        return metadata
        
    except Exception as e:
        raise Exception(f"Encryption failed: {str(e)}")

@app.route('/')
def index():
    # This will load your cyberpunk UI
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file:
        # Secure the filename to prevent directory traversal attacks
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # ENCRYPTION LOGIC - The core feature!
        try:
            metadata = encrypt_file(filepath)
            return render_template('success.html', 
                                 filename=metadata['encrypted_name'],
                                 original_name=metadata['original_name'],
                                 encrypted=True,
                                 size=metadata['size'])
        except Exception as e:
            flash(f'Encryption failed: {str(e)}')
            return redirect(url_for('index'))

@app.route('/files')
def list_files():
    """List all encrypted files in the drop zone"""
    try:
        encrypted_files = []
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename.endswith('.enc'):
                # Load metadata
                base_name = filename.replace('.enc', '')
                meta_path = os.path.join(app.config['UPLOAD_FOLDER'], base_name + '.meta')
                
                if os.path.exists(meta_path):
                    with open(meta_path, 'r') as meta_file:
                        metadata = json.load(meta_file)
                        encrypted_files.append({
                            'encrypted_name': filename,
                            'original_name': metadata['original_name'],
                            'encryption_time': metadata['encryption_time'],
                            'size': metadata['size']
                        })
        
        return render_template('files.html', files=encrypted_files)
    except Exception as e:
        flash(f'Error loading files: {str(e)}')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """Decrypt and download a file"""
    try:
        encrypted_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(encrypted_path):
            flash('File not found')
            return redirect(url_for('list_files'))
        
        # Load metadata to get original filename
        base_path = encrypted_path.replace('.enc', '')
        metadata_path = base_path + '.meta'
        
        if not os.path.exists(metadata_path):
            flash('Metadata file not found')
            return redirect(url_for('list_files'))
        
        with open(metadata_path, 'r') as meta_file:
            metadata = json.load(meta_file)
        
        # Decrypt file directly in memory for download
        password = "DEFAULT_DEAD_DROP_KEY"
        salt = base64.b64decode(metadata['salt'].encode())
        
        # Generate key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        fernet = Fernet(key)
        
        # Decrypt data
        with open(encrypted_path, 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()
        
        decrypted_data = fernet.decrypt(encrypted_data)
        
        # Create temporary file for download
        import tempfile
        import io
        
        # Use BytesIO to serve file directly from memory
        file_stream = io.BytesIO(decrypted_data)
        file_stream.seek(0)
        
        return send_file(file_stream, 
                        as_attachment=True, 
                        download_name=metadata['original_name'],
                        mimetype='application/octet-stream')
                        
    except Exception as e:
        flash(f'Download failed: {str(e)}')
        return redirect(url_for('list_files'))

# Friend's Message-Based Dead Drop Routes
@app.route('/create-drop', methods=['POST'])
def create_drop():
    """Create encrypted message drop (friend's feature)"""
    try:
        data = request.json
        msg, pw = data.get('message'), data.get('password')
        
        if not msg or not pw:
            return jsonify({"error": "Missing message or password"}), 400

        drop_id = str(len(dead_drops) + 1)
        dead_drops[drop_id] = encrypt_message(msg, pw)
        
        return jsonify({"dropId": drop_id, "message": "Drop created successfully"})
    except Exception as e:
        return jsonify({"error": f"Encryption failed: {str(e)}"}), 500

@app.route('/retrieve-drop', methods=['POST'])
def retrieve_drop():
    """Retrieve and burn message drop (friend's feature)"""
    try:
        data = request.json
        d_id, pw = data.get('drop_id'), data.get('password')

        encrypted = dead_drops.get(d_id)
        if not encrypted:
            return jsonify({"error": "Drop not found or already burned"}), 404

        decrypted = decrypt_message(encrypted, pw)
        del dead_drops[d_id]  # 💣 Burn After Reading
        return jsonify({"message": decrypted})
    except Exception as e:
        return jsonify({"error": "Invalid password or decryption failed"}), 401

@app.route('/messages')
def message_interface():
    """Interface for message-based dead drops"""
    return render_template('messages.html')

if __name__ == '__main__':
    # Development mode - change for production!
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0' if not debug_mode else '127.0.0.1'
    
    app.run(debug=debug_mode, port=port, host=host)

    

