# app.py (updated to restrict adding requests to customers)
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from hashlib import sha256
import jwt
import datetime
import os
from functools import wraps
from flask_cors import CORS
import pytz  # Import the pytz library if you don't have it
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in a real application

DATABASE = 'repairs.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create users table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Create repair_requests table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repair_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_serial_number TEXT NOT NULL,
            description TEXT NOT NULL,
            username TEXT NOT NULL,
            status TEXT DEFAULT 'Open'
        )
    ''')

    # Add default users if no users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        hashed_password_repairman = sha256("admin".encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password, api_key, role) VALUES (?, ?, ?, ?)",
                       ('admin', hashed_password_repairman, 'repairman123456', 'repairman'))
        hashed_password_customer = sha256("customer".encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password, api_key, role) VALUES (?, ?, ?, ?)",
                       ('customer', hashed_password_customer, 'cust123456', 'customer'))

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def generate_jwt(username, role):
    utc_now = datetime.datetime.now(pytz.utc)  # Get current UTC time with timezone info
    payload = {
        'exp': utc_now + datetime.timedelta(hours=1),
        'iat': utc_now,
        'sub': username,
        'role': role
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def decode_jwt(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['sub'], payload['role']
    except jwt.ExpiredSignatureError:
        return None, None
    except jwt.InvalidTokenError:
        return None, None

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logging.info("In decorated_function")
        logging.warning("In decorated_function1")
        logging.warning(request.headers)
        jwt_token = request.headers.get('jwt-token') or request.headers.get('Jwt-token')
        api_key = request.args.get('api_key')

        username = None
        role = None

        if jwt_token:
            username, role = decode_jwt(jwt_token)
        elif api_key:
            conn = get_db()
            user = conn.execute("SELECT username, role FROM users WHERE api_key = ?", (api_key,)).fetchone()
            conn.close()
            if user:
                username = user['username']
                role = user['role']

        if not username:
            return jsonify({'message': 'Authentication required'}), 401
        return f(username, role, *args, **kwargs)
    return decorated_function

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/landing')
def landing():
    return send_from_directory('static', 'landing.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400

    conn = get_db()
    user = conn.execute("SELECT username, password, role FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if user and sha256(password.encode()).hexdigest() == user['password']:
        token = generate_jwt(user['username'], user['role'])
        return jsonify({'token': token})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/repair_requests', methods=['GET', 'POST'])
@auth_required
def repair_requests(username, role):
    conn = get_db()
    if request.method == 'GET':
        request_id = request.args.get('request_id')
        if request_id:
            requests = conn.execute("SELECT request_id, device_serial_number, description, username, status FROM repair_requests WHERE request_id = ?", (request_id,)).fetchall()
        else:
            requests = conn.execute("SELECT request_id, device_serial_number, description, username, status FROM repair_requests").fetchall()
        conn.close()
        return jsonify([dict(row) for row in requests])
    elif request.method == 'POST':
        if role != 'customer':
            conn.close()
            return jsonify({'message': 'Only customers can submit repair requests'}), 403
        data = request.get_json()
        device_serial_number = data.get('device_serial_number')
        description = data.get('description')
        if not device_serial_number or not description:
            return jsonify({'message': 'Device serial number and description are required'}), 400
        conn.execute("INSERT INTO repair_requests (device_serial_number, description, username) VALUES (?, ?, ?)",
                     (device_serial_number, description, username))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Repair request added successfully'}), 201

@app.route('/api/close/<int:request_id>', methods=['POST'])
@auth_required
def close_request(username, role, request_id):
    if role != 'repairman':
        return jsonify({'message': 'Only repairmen can close requests'}), 403

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE repair_requests SET status = 'Closed' WHERE request_id = ?", (request_id,))
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return jsonify({'message': f'Repair request {request_id} closed successfully'}), 200
    else:
        conn.close()
        return jsonify({'message': f'Repair request {request_id} not found'}), 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True,host="0.0.0.0",port=5000)
