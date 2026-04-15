from api.compiler import run_code

@app.route('/api/submit_code', methods=['POST'])
@login_required
def submit_code():
    data = request.get_json()
    code = data.get('code')
    lang = data.get('language')
    q_id = data.get('question_id')
    
    # 1. Fetch testcase from Firebase
    q_data = db.reference(f'Compiler/Questions/{q_id}').get()
    expected = q_data.get('expected_output')
    
    # 2. Execute
    output, error = run_code(code, lang, q_data.get('testcase_input'))
    
    # 3. Evaluate
    marks = 0
    if not error and output.strip() == expected.strip():
        marks = q_data.get('points', 10)
    
    # 4. Save to Firebase
    db.reference(f'Compiler/Submissions/{session["uid"]}/{q_id}').set({
        "code": code,
        "marks": marks,
        "timestamp": get_ist_now().isoformat()
    })
    
    return jsonify({"output": output, "error": error, "marks": marks})
