import os
import json
import pytz
from datetime import datetime
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
from functools import wraps

# 1. INITIALIZE APP (Top-Level)
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "PEC_VECTOR_GATE_2026_SECURE")
CORS(app)

# 2. LAZY INIT HELPER
def get_firebase_app():
    if not firebase_admin._apps:
        firebase_info = os.getenv("FIREBASE_JSON")
        db_url = os.getenv("FIREBASE_DB_URL")
        if firebase_info and db_url:
            cred_dict = json.loads(firebase_info)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': db_url})
    return firebase_admin.get_app()

# 3. ROUTE: LOGIN (Student/Admin)
@app.route('/login', methods=['POST'])
def login():
    get_firebase_app()
    data = request.get_json()
    # Simplified login logic
    session['uid'] = data.get('email')
    session['role'] = data.get('role', 'student')
    return jsonify({"success": True})

# 4. ROUTE: SUBMIT CODE
@app.route('/api/submit_code', methods=['POST'])
def submit_code():
    from api.compiler import run_code
    get_firebase_app()
    data = request.get_json()
    output, error = run_code(data['code'], data['language'], "")
    return jsonify({"output": output, "error": error})

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "Compiler API Active"})
