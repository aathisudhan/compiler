import os
import json
import pytz
from datetime import datetime
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db, auth
from functools import wraps

# 1. INITIALIZE APP (Top-Level)
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "PEC_VECTOR_GATE_2026_SECURE")
CORS(app)

# 2. FIREBASE INIT (Handles empty/missing env vars safely)
firebase_info = os.getenv("FIREBASE_JSON")
db_url = os.getenv("FIREBASE_DB_URL")

if firebase_info and db_url:
    try:
        if not firebase_admin._apps:
            cred_dict = json.loads(firebase_info)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': db_url})
    except Exception as e:
        print(f"Firebase Init Error: {e}")

# 3. HELPERS
def get_ist_now():
    return datetime.now(pytz.timezone('Asia/Kolkata'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'uid' not in session:
            return jsonify({"success": False, "message": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# 4. ROUTES
@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "Compiler API Active"})

@app.route('/api/submit_code', methods=['POST'])
@login_required
def submit_code():
    from api.compiler import run_code
    
    data = request.get_json()
    code = data.get('code', '')
    lang = data.get('language', '').lower()
    q_id = data.get('question_id')
    
    if not q_id or not code or not lang:
        return jsonify({"success": False, "message": "Invalid input"}), 400
    
    # Fetch from Firebase
    q_data = db.reference(f'Compiler/Questions/{q_id}').get()
    if not q_data:
        return jsonify({"success": False, "message": "Question not found"}), 404
        
    expected = str(q_data.get('expected_output', '')).strip()
    
    # Run in sandbox
    output, error = run_code(code, lang, q_data.get('testcase_input', ''))
    
    # Mark logic
    marks = 0
    if not error and output.strip() == expected:
        marks = q_data.get('points', 10)
    
    # Save submission
    db.reference(f'Compiler/Submissions/{session["uid"]}/{q_id}').set({
        "code": code,
        "marks": marks,
        "timestamp": get_ist_now().isoformat()
    })
    
    return jsonify({"output": output, "error": error, "marks": marks})

# 5. ADMIN ROUTE
@app.route('/api/admin/save_question', methods=['POST'])
@login_required
def save_question():
    # Add check for Admin role here if needed
    data = request.get_json()
    q_id = data.get('q_id')
    db.reference(f'Compiler/Questions/{q_id}').set(data)
    return jsonify({"success": True})
