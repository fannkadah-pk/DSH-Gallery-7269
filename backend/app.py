from __future__ import annotations

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from flask_talisman import Talisman
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from pathlib import Path
import os
import sqlite3
import shutil
import json
from typing import Dict, Any, List, Optional, Tuple
import html

app: Flask = Flask(__name__)
CORS(app)
Talisman(app, content_security_policy=None)  # Disable CSP for now to avoid blocking

auth = HTTPBasicAuth()

users = {
    "admin": "securepassword123"  # Change this to a strong password
}

@auth.verify_password
def verify_password(username, password):
    """Verify user credentials against database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT password_hash, status FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password_hash'], password) and user['status'] == 'approved':
            return username
        return None
    except Exception:
        return None
    finally:
        conn.close()

def get_current_user():
    """Get current authenticated user info."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '):
        return None
    
    import base64
    try:
        credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
        username, password = credentials.split(':', 1)
        
        if verify_password(username, password):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, full_name, username, email, role, status FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            conn.close()
            return user
        return None
    except:
        return None

# Configuration
UPLOAD_FOLDER = 'uploads'
BACKUP_FOLDER = 'backups'
TRASH_FOLDER = 'trash'
ALLOWED_EXTENSIONS = {
    # Images
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp',
    # Videos
    'mp4', 'avi', 'mov', 'mkv', 'webm',
    # Audio
    'mp3', 'wav', 'ogg', 'm4a', 'flac',
    # Documents
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['BACKUP_FOLDER'] = BACKUP_FOLDER
app.config['TRASH_FOLDER'] = TRASH_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Create required directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)
os.makedirs(TRASH_FOLDER, exist_ok=True)

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename: str) -> str:
    """Determine file type based on extension."""
    ext: str = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    image_exts: set[str] = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
    video_exts: set[str] = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    audio_exts: set[str] = {'mp3', 'wav', 'ogg', 'm4a', 'flac'}
    
    if ext in image_exts:
        return 'image'
    elif ext in video_exts:
        return 'video'
    elif ext in audio_exts:
        return 'audio'
    else:
        return 'document'

@auth.login_required
@app.route('/api/upload', methods=['POST'])
def upload_files() -> Tuple[Dict[str, Any], int | None]:
    """Handle file uploads."""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files: list = request.files.getlist('files')
    uploaded_files: list[Dict[str, Any]] = []
    
    conn: sqlite3.Connection = get_db_connection()
    
    for file in files:
        if file and allowed_file(file.filename):
            filename: str = secure_filename(file.filename)
            timestamp: str = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename: str = f"{timestamp}_{filename}"
            filepath: str = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            file.save(filepath)
            
            file_type: str = get_file_type(filename)
            file_size: int = os.path.getsize(filepath)
            
            # Save to database
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO files (filename, originalname, filepath, file_type, size, mimetype, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (unique_filename, filename, filepath, file_type, file_size, file.mimetype, datetime.now()))
            
            file_id = cursor.lastrowid
            conn.commit()
            
            uploaded_files.append({
                'id': file_id,
                'filename': unique_filename,
                'originalname': filename,
                'type': file_type
            })
    
    conn.close()
    
    return jsonify({
        'message': f'Successfully uploaded {len(uploaded_files)} files',
        'files': uploaded_files
    })

@app.route('/api/files', methods=['GET'])
def get_files() -> Dict[str, Any]:
    """Get all non-deleted files organized by type."""
    conn: sqlite3.Connection = get_db_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    
    # Get files by type
    cursor.execute("SELECT * FROM files WHERE file_type = 'image' AND deleted = 0")
    images: list = cursor.fetchall()
    
    cursor.execute("SELECT * FROM files WHERE file_type = 'video' AND deleted = 0")
    videos: list = cursor.fetchall()
    
    cursor.execute("SELECT * FROM files WHERE file_type = 'audio' AND deleted = 0")
    audio: list = cursor.fetchall()
    
    cursor.execute("SELECT * FROM files WHERE file_type = 'document' AND deleted = 0")
    documents: list = cursor.fetchall()
    
    conn.close()
    
    # include any static images from frontend/assets/data-dsh
    asset_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'assets', 'data-dsh'))
    asset_images: list[Dict[str, Any]] = []
    if os.path.isdir(asset_dir):
        for fname in os.listdir(asset_dir):
            lower = fname.lower()
            if any(lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
                asset_images.append({
                    'id': f'asset-{fname}',
                    'filename': f'assets/data-dsh/{fname}',
                    'originalname': fname,
                    'size': os.path.getsize(os.path.join(asset_dir, fname)),
                    'file_type': 'image',
                    'mimetype': 'image/' + lower.split('.')[-1]
                })
    
    # Escape HTML in filenames for security
    images_list = [dict(row) for row in images] + asset_images
    for item in images_list:
        item['originalname'] = html.escape(item['originalname'])
    
    videos_list = [dict(row) for row in videos]
    for item in videos_list:
        item['originalname'] = html.escape(item['originalname'])
    
    audio_list = [dict(row) for row in audio]
    for item in audio_list:
        item['originalname'] = html.escape(item['originalname'])
    
    documents_list = [dict(row) for row in documents]
    for item in documents_list:
        item['originalname'] = html.escape(item['originalname'])
    
    return jsonify({
        'images': images_list,
        'videos': videos_list,
        'audio': audio_list,
        'documents': documents_list
    })

@auth.login_required
@app.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id: int) -> Dict[str, str]:
    """Move file to trash."""
    conn: sqlite3.Connection = get_db_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    
    # Get file info
    cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
    file: Optional[sqlite3.Row] = cursor.fetchone()
    
    if file:
        # Move to trash
        trash_path: str = os.path.join(app.config['TRASH_FOLDER'], file['filename'])
        shutil.move(file['filepath'], trash_path)
        
        # Update database
        cursor.execute('''
            UPDATE files 
            SET deleted = 1, deleted_at = ?, trash_path = ? 
            WHERE id = ?
        ''', (datetime.now(), trash_path, file_id))
        
        conn.commit()
    
    conn.close()
    
    return jsonify({'message': 'File moved to trash'})

@app.route('/api/download/<int:file_id>', methods=['GET'])
def download_file(file_id: int):
    """Download a file by ID."""
    conn: sqlite3.Connection = get_db_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
    file: Optional[sqlite3.Row] = cursor.fetchone()
    
    conn.close()
    
    if file:
        return send_file(file['filepath'], as_attachment=True, download_name=file['originalname'])
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/counts', methods=['GET'])
def get_counts() -> Dict[str, int]:
    """Get file counts by type."""
    conn: sqlite3.Connection = get_db_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM files WHERE file_type = 'image' AND deleted = 0")
    image_count: int = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM files WHERE file_type = 'video' AND deleted = 0")
    video_count: int = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM files WHERE file_type = 'audio' AND deleted = 0")
    audio_count: int = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM files WHERE file_type = 'document' AND deleted = 0")
    document_count: int = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'images': image_count,
        'videos': video_count,
        'audio': audio_count,
        'documents': document_count
    })

@auth.login_required
@app.route('/api/backup', methods=['POST'])
def create_backup() -> Dict[str, str]:
    """Create backup of uploads folder."""
    timestamp: str = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file: str = os.path.join(app.config['BACKUP_FOLDER'], f'backup_{timestamp}.zip')
    
    # Create backup of uploads folder and database
    shutil.make_archive(backup_file.replace('.zip', ''), 'zip', app.config['UPLOAD_FOLDER'])
    
    return jsonify({
        'message': 'Backup created successfully',
        'filename': f'backup_{timestamp}.zip'
    })

@auth.login_required
@app.route('/api/restore', methods=['POST'])
def restore_data() -> Tuple[Dict[str, str], int] | Dict[str, str]:
    """Restore from latest backup."""
    # Find latest backup
    backups: list[str] = sorted([f for f in os.listdir(app.config['BACKUP_FOLDER']) if f.endswith('.zip')])
    
    if not backups:
        return jsonify({'error': 'No backup found'}), 404
    
    latest_backup: str = os.path.join(app.config['BACKUP_FOLDER'], backups[-1])
    
    # Restore files
    shutil.unpack_archive(latest_backup, app.config['UPLOAD_FOLDER'])
    
    return jsonify({'message': 'Data restored successfully'})

@app.route('/api/trash', methods=['GET'])
def get_trash() -> Dict[str, list]:
    """Get all deleted files organized by type."""
    conn: sqlite3.Connection = get_db_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM files WHERE deleted = 1")
    trash_files: list = cursor.fetchall()
    
    conn.close()
    
    # Organize by type
    trash: Dict[str, list] = {
        'images': [],
        'videos': [],
        'audio': [],
        'documents': []
    }
    
    for file in trash_files:
        file_dict: Dict[str, Any] = dict(file)
        file_dict['originalname'] = html.escape(file_dict['originalname'])
        trash[file_dict['file_type'] + 's'].append(file_dict)
    
    return jsonify(trash)

@auth.login_required
@app.route('/api/trash/<int:file_id>/restore', methods=['POST'])
def restore_from_trash(file_id: int) -> Dict[str, str]:
    """Restore file from trash."""
    conn: sqlite3.Connection = get_db_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
    file: Optional[sqlite3.Row] = cursor.fetchone()
    
    if file:
        # Move back from trash
        original_path: str = file['filepath']
        trash_path: str = file['trash_path']
        
        if os.path.exists(trash_path):
            shutil.move(trash_path, original_path)
        
        # Update database
        cursor.execute('''
            UPDATE files 
            SET deleted = 0, deleted_at = NULL, trash_path = NULL 
            WHERE id = ?
        ''', (file_id,))
        
        conn.commit()
    
    conn.close()
    
    return jsonify({'message': 'File restored'})

@auth.login_required
@app.route('/api/trash/<int:file_id>', methods=['DELETE'])
def delete_permanently(file_id: int) -> Dict[str, str]:
    """Permanently delete file from trash."""
    conn: sqlite3.Connection = get_db_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
    file: Optional[sqlite3.Row] = cursor.fetchone()
    
    if file and file['trash_path'] and os.path.exists(file['trash_path']):
        os.remove(file['trash_path'])
    
    cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
    conn.commit()
    
    conn.close()
    
    return jsonify({'message': 'File deleted permanently'})

@auth.login_required
@app.route('/api/trash/restore-all', methods=['POST'])
def restore_all_trash() -> Dict[str, str]:
    """Restore all files from trash."""
    conn: sqlite3.Connection = get_db_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM files WHERE deleted = 1")
    trash_files: list = cursor.fetchall()
    
    for file in trash_files:
        if file['trash_path'] and os.path.exists(file['trash_path']):
            shutil.move(file['trash_path'], file['filepath'])
    
    cursor.execute('''
        UPDATE files 
        SET deleted = 0, deleted_at = NULL, trash_path = NULL 
        WHERE deleted = 1
    ''')
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'All files restored'})

# Routes for serving frontend pages
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/index.html')
def index_page():
    return send_from_directory('../frontend', 'index.html')

@app.route('/gallery.html')
def gallery():
    return send_from_directory('../frontend', 'gallery.html')

@app.route('/about.html')
def about():
    return send_from_directory('../frontend', 'about.html')

@app.route('/settings.html')
def settings():
    return send_from_directory('../frontend', 'settings.html')

@app.route('/login.html')
def login():
    return send_from_directory('../frontend', 'login.html')

@app.route('/api/signup', methods=['POST'])
def signup_user():
    """Handle user signup."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['fullName', 'username', 'countryCode', 'contact', 'email', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate email format (basic)
    import re
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Check password strength (basic)
    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if username or email already exists
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", 
                      (data['username'], data['email']))
        if cursor.fetchone():
            return jsonify({'error': 'Username or email already exists'}), 409
        
        # Hash password
        password_hash = generate_password_hash(data['password'])
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (full_name, username, contact_country_code, contact_number, email, password_hash, role, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['fullName'], data['username'], data['countryCode'], data['contact'], 
              data['email'], password_hash, 4, 'pending', datetime.now()))
        
        conn.commit()
        
        return jsonify({'message': 'User registered successfully'}), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Registration failed'}), 500
    finally:
        conn.close()

@app.route('/api/check-user', methods=['POST'])
def check_user_status():
    """Check user status without authentication (for login feedback)."""
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT status FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user:
            return jsonify({'status': user['status']})
        else:
            return jsonify({'error': 'User not found'}), 404
    finally:
        conn.close()

@app.route('/api/users', methods=['GET'])
@auth.login_required
def get_users():
    """Get list of users based on current user's role."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if current_user['role'] == 1:  # Admin - full access
            cursor.execute("SELECT id, full_name, username, contact_country_code, contact_number, email, role, status, created_at FROM users")
        elif current_user['role'] == 2:  # Manager - only username, email, status
            cursor.execute("SELECT id, username, email, role, status FROM users")
        elif current_user['role'] == 3:  # Staff - only username, email
            cursor.execute("SELECT id, username, email FROM users")
        else:  # Client - no access
            return jsonify({'error': 'Access denied'}), 403
        
        users = cursor.fetchall()
        return jsonify({'users': users})
    finally:
        conn.close()

@app.route('/api/users/<int:user_id>/approve', methods=['POST'])
@auth.login_required
def approve_user(user_id):
    """Approve a user (Admin and Manager only)."""
    current_user = get_current_user()
    if not current_user or current_user['role'] > 2:  # Only Admin (1) and Manager (2)
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE users SET status = 'approved' WHERE id = ?", (user_id,))
        conn.commit()
        return jsonify({'message': 'User approved successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Failed to approve user'}), 500
    finally:
        conn.close()

@app.route('/api/users/<int:user_id>/reject', methods=['POST'])
@auth.login_required
def reject_user(user_id):
    """Reject a user (Admin and Manager only)."""
    current_user = get_current_user()
    if not current_user or current_user['role'] > 2:  # Only Admin (1) and Manager (2)
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE users SET status = 'rejected' WHERE id = ?", (user_id,))
        conn.commit()
        return jsonify({'message': 'User rejected successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Failed to reject user'}), 500
    finally:
        conn.close()

@app.route('/api/user/profile', methods=['GET'])
@auth.login_required
def get_user_profile():
    """Get current user's profile information."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({'user': current_user})

@app.route('/api/user/change-password', methods=['POST'])
@auth.login_required
def change_user_password():
    """Change current user's password."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current password and new password are required'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verify current password
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (current_user['id'],))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user['password_hash'], current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Update password
        new_password_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, current_user['id']))
        conn.commit()
        
        return jsonify({'message': 'Password changed successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Failed to change password'}), 500
    finally:
        conn.close()

@app.route('/signup.html')
def signup():
    return send_from_directory('../frontend', 'signup.html')

@app.route('/id-info.html')
def id_info():
    return send_from_directory('../frontend', 'id-info.html')

# Routes for static files
@app.route('/css/<path:filename>')
def css_files(filename):
    return send_from_directory('../frontend/css', filename)

@app.route('/js/<path:filename>')
def js_files(filename):
    return send_from_directory('../frontend/js', filename)

@app.route('/assets/<path:filename>')
def assets_files(filename):
    return send_from_directory('../frontend/assets', filename)

def get_db_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn: sqlite3.Connection = sqlite3.connect('../database/gallery.db')
    conn.row_factory = sqlite3.Row
    return conn

def initialize_admin_user():
    """Create admin user if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM users WHERE username = ?", ('admindshalpha123',))
        if not cursor.fetchone():
            password_hash = generate_password_hash('Alpha@#4')
            cursor.execute('''
                INSERT INTO users (full_name, username, contact_country_code, contact_number, email, password_hash, role, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('Admin User', 'admindshalpha123', '+1', '1234567890', 'admin@dshgallery.com', password_hash, 1, 'approved', datetime.now()))
            conn.commit()
            print("Admin user created successfully")
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    initialize_admin_user()
    app.run(debug=True, port=5000)