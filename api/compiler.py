import subprocess
import os
import tempfile
import signal

# Define resources for the sandbox
TIMEOUT_SECONDS = 5  # Prevents infinite loops

def run_code(code, lang, input_data=""):
    """
    Executes code in a secure, temp directory.
    Returns: (output, error)
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        
        # 1. Prepare files based on language
        if lang == "python":
            file_path = os.path.join(tmpdirname, "script.py")
            cmd = ["python3", file_path]
            with open(file_path, "w") as f: f.write(code)
            
        elif lang == "java":
            file_path = os.path.join(tmpdirname, "Main.java")
            # Assumes class is named Main
            with open(file_path, "w") as f: f.write(code)
            # Compile first
            compile_proc = subprocess.run(["javac", file_path], capture_output=True, text=True)
            if compile_proc.returncode != 0:
                return "", compile_proc.stderr
            cmd = ["java", "-cp", tmpdirname, "Main"]
            
        elif lang == "sql":
            # Uses sqlite3 (in-memory)
            import sqlite3
            try:
                conn = sqlite3.connect(":memory:")
                cur = conn.cursor()
                cur.execute(code)
                output = str(cur.fetchall())
                conn.close()
                return output, ""
            except Exception as e:
                return "", str(e)
        else:
            return "", "Language not supported"

        # 2. Execute with constraints
        try:
            result = subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                # Enforce no shell=True for security
                shell=False 
            )
            return result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return "", "Execution Timed Out (Security Limit)"
        except Exception as e:
            return "", str(e)
