from api.compiler import run_code
from flask import jsonify, request, session
# Assuming your other imports and firebase_admin init are already at the top

@app.route('/api/submit_code', methods=['POST'])
@login_required
def submit_code():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data received"}), 400
            
        code = data.get('code', '')
        lang = data.get('language', '').lower()
        q_id = data.get('question_id')
        
        if not q_id or not code or not lang:
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        
        # 1. Fetch testcase from Firebase
        q_ref = db.reference(f'Compiler/Questions/{q_id}')
        q_data = q_ref.get()
        
        if not q_data:
            return jsonify({"success": False, "message": "Question not found"}), 404
            
        expected = str(q_data.get('expected_output', '')).strip()
        test_input = str(q_data.get('testcase_input', ''))
        points = q_data.get('points', 10)
        
        # 2. Execute
        # Ensure your compiler.py handles the language safely
        output, error = run_code(code, lang, test_input)
        
        # 3. Evaluate (Strict comparison)
        marks = 0
        status = "Failed"
        if not error and output.strip() == expected:
            marks = points
            status = "Passed"
        
        # 4. Save to Firebase (Student's specific submission node)
        student_uid = session.get('uid')
        submission_ref = db.reference(f'Compiler/Submissions/{student_uid}/{q_id}')
        submission_ref.set({
            "code": code,
            "marks": marks,
            "status": status,
            "output_received": output[:500], # Keep only first 500 chars to save DB space
            "error_log": str(error)[:500],
            "timestamp": get_ist_now().isoformat()
        })
        
        return jsonify({
            "success": True, 
            "output": output, 
            "error": error, 
            "marks": marks,
            "status": status
        })

    except Exception as e:
        print(f">>> Submission Error: {str(e)}")
        return jsonify({"success": False, "message": "Internal Server Error"}), 500
