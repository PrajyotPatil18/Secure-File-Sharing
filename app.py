import os
import json
import secrets
import time
import io
import logging
from datetime import datetime, timedelta
from flask import Flask, request, render_template, send_file, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from encryption import crypto

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('file_sharing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ENCRYPTED_FOLDER = 'encrypted'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip', 'rar', 'mp4', 'avi', 'mov'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
DEFAULT_EXPIRY_HOURS = 24

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)

# Metadata storage
LINKS_FILE = 'links.json'

def load_links():
    """Load download links metadata"""
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_links(links):
    """Save download links metadata"""
    with open(LINKS_FILE, 'w') as f:
        json.dump(links, f, indent=2)

def clean_expired_links():
    """Remove expired links"""
    links = load_links()
    current_time = time.time()
    expired_links = []
    
    for link_id, metadata in links.items():
        if metadata.get('expires_at', 0) < current_time:
            expired_links.append(link_id)
            # Remove encrypted file
            encrypted_path = metadata.get('encrypted_path')
            if encrypted_path and os.path.exists(encrypted_path):
                os.remove(encrypted_path)
    
    for link_id in expired_links:
        del links[link_id]
    
    if expired_links:
        save_links(links)
    
    return len(expired_links)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_link_id():
    """Generate secure link ID"""
    return secrets.token_urlsafe(16)

@app.route('/')
def index():
    """Main upload page"""
    logger.info(f"Upload page accessed from {request.remote_addr}")
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and encryption"""
    try:
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(url_for('index'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(url_for('index'))
        
        if not allowed_file(file.filename):
            flash('File type not allowed')
            return redirect(url_for('index'))
        
        # Get filename early for logging
        filename = secure_filename(file.filename)
        
        # Read file data
        file_data = file.read()
        if len(file_data) > MAX_FILE_SIZE:
            flash('File too large (max 100MB)')
            return redirect(url_for('index'))
        
        # Get optional password
        password = request.form.get('password', '').strip()
        expiry_hours = int(request.form.get('expiry_hours', DEFAULT_EXPIRY_HOURS))
        
        logger.info(f"Upload attempt: {filename}, size: {len(file_data)} bytes, password_protected: {bool(password)}")
        
        # Encrypt file
        if password:
            encrypted_data, salt = crypto.encrypt_with_password(file_data, password)
            salt_hex = salt.hex()
        else:
            key = crypto.generate_key()
            encrypted_data = crypto.encrypt_file(file_data, key)
            key_hex = key.hex()
            salt_hex = None
        
        # Save encrypted file
        encrypted_filename = f"{secrets.token_hex(8)}_{filename}"
        encrypted_path = os.path.join(ENCRYPTED_FOLDER, encrypted_filename)
        
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Generate download link
        link_id = generate_link_id()
        expires_at = time.time() + (expiry_hours * 3600)
        
        # Save metadata
        links = load_links()
        links[link_id] = {
            'filename': filename,
            'encrypted_path': encrypted_path,
            'original_size': len(file_data),
            'upload_time': time.time(),
            'expires_at': expires_at,
            'has_password': bool(password),
            'key_hex': key_hex if not password else None,
            'salt_hex': salt_hex,
            'expiry_hours': expiry_hours
        }
        save_links(links)
        
        # Generate download URL with actual server IP
        server_ip = request.host.split(':')[0] if request.host else '10.23.80.198'
        if server_ip == '127.0.0.1' or server_ip == 'localhost':
            server_ip = '10.23.80.198'  # Use actual network IP
        download_url = f"http://{server_ip}:5000/download/{link_id}"
        
        logger.info(f"File uploaded successfully: {filename}, link_id: {link_id}, expires_in: {expiry_hours}h")
        
        return render_template('upload_success.html', 
                             download_url=download_url,
                             filename=filename,
                             expiry_hours=expiry_hours,
                             has_password=bool(password))
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)} from {request.remote_addr}")
        flash('Upload failed. Please try again.')
        return redirect(url_for('index'))

@app.route('/download/<link_id>')
def download_page(link_id):
    """Download page with password protection"""
    logger.info(f"Download page accessed: {link_id} from {request.remote_addr}")
    links = load_links()
    
    # Clean expired links first
    clean_expired_links()
    links = load_links()
    
    if link_id not in links:
        return render_template('error.html', message='Link expired or not found'), 404
    
    metadata = links[link_id]
    
    # Check if expired
    if metadata['expires_at'] < time.time():
        # Remove expired link and file
        if os.path.exists(metadata['encrypted_path']):
            os.remove(metadata['encrypted_path'])
        del links[link_id]
        save_links(links)
        return render_template('error.html', message='Link expired'), 410
    
    return render_template('download.html', 
                         link_id=link_id,
                         filename=metadata['filename'],
                         has_password=metadata['has_password'],
                         expiry_hours=metadata['expiry_hours'])

@app.route('/download/<link_id>/file', methods=['POST'])
def download_file(link_id):
    """Handle actual file download and decryption"""
    logger.info(f"Download requested: {link_id} from {request.remote_addr}")
    links = load_links()
    
    if link_id not in links:
        return jsonify({'error': 'Link not found'}), 404
    
    metadata = links[link_id]
    
    # Check if expired
    if metadata['expires_at'] < time.time():
        return jsonify({'error': 'Link expired'}), 410
    
    try:
        # Read encrypted file
        with open(metadata['encrypted_path'], 'rb') as f:
            encrypted_data = f.read()
        
        # Decrypt file
        if metadata['has_password']:
            password = request.form.get('password', '')
            if not password:
                return jsonify({'error': 'Password required'}), 400
            
            salt = bytes.fromhex(metadata['salt_hex'])
            decrypted_data = crypto.decrypt_with_password(encrypted_data, password, salt)
        else:
            key = bytes.fromhex(metadata['key_hex'])
            decrypted_data = crypto.decrypt_file(encrypted_data, key)
        
        # Send file
        logger.info(f"File decrypted and sent: {metadata['filename']} to {request.remote_addr}")
        return send_file(
            io.BytesIO(decrypted_data),
            as_attachment=True,
            download_name=metadata['filename'],
            mimetype='application/octet-stream'
        )
    
    except Exception as e:
        logger.error(f"Download error: {str(e)} for {link_id} from {request.remote_addr}")
        if metadata['has_password']:
            return jsonify({'error': 'Invalid password'}), 401
        return jsonify({'error': 'Download failed'}), 500

@app.route('/links')
def list_links():
    """List active download links (admin view)"""
    logger.info(f"Links page accessed from {request.remote_addr}")
    links = load_links()
    clean_expired_links()
    links = load_links()
    
    active_links = []
    for link_id, metadata in links.items():
        if metadata['expires_at'] > time.time():
            active_links.append({
                'link_id': link_id,
                'filename': metadata['filename'],
                'download_url': url_for('download_page', link_id=link_id, _external=True),
                'expires_at': datetime.fromtimestamp(metadata['expires_at']).strftime('%Y-%m-%d %H:%M:%S'),
                'has_password': metadata['has_password']
            })
    
    return render_template('links.html', links=active_links)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)