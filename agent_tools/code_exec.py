import os
import sys
import tempfile
import subprocess
import datetime
from agent_tools.ragis_logger import RagisLogger

MAX_STDOUT = 1500
MAX_STDERR = 800

# Centralized logger for all code execution logs
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=['code'])

def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def syntax_validate_python(code):
    import ast
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
    except Exception as e:
        return False, f"Validation error: {e}"

def exec_python_code(args, session_state):
    """Safely execute Python code with syntax validation and timeout."""
    code = args.get("code", "")
    temp_path = os.path.join(tempfile.gettempdir(), f"temp_agent_run_{get_timestamp()}.py")
    valid, err = syntax_validate_python(code)
    if not valid:
        logger.log("exec_python_syntax_error", {"file": temp_path, "error": err})
        return f"Refused to execute Python: {err}"
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(code)
    try:
        result = subprocess.run([sys.executable, temp_path],
                                capture_output=True, text=True, timeout=12)
        output = result.stdout[:MAX_STDOUT] + "\n" + result.stderr[:MAX_STDERR]
        logger.log("exec_python", {
            "file": temp_path,
            "action": "Ran code",
            "stdout": result.stdout[:500],  # short excerpt
            "stderr": result.stderr[:300],  # short excerpt
            "returncode": result.returncode
        })
        return f"Python run output:\n{output}"
    except subprocess.TimeoutExpired:
        logger.log("exec_python_timeout", {"file": temp_path, "code": code})
        return "Python code execution timed out."
    except Exception as e:
        logger.log("exec_python_error", {"file": temp_path, "error": str(e), "code": code})
        return f"Error running code: {e}"
    finally:
        try:
            os.remove(temp_path)
        except Exception as cleanup_err:
            logger.log("tempfile_remove_fail", {"file": temp_path, "error": str(cleanup_err)})

def exec_node_code(args, session_state):
    """Safely execute Node.js code with timeout."""
    code = args.get("code", "")
    temp_path = os.path.join(tempfile.gettempdir(), f"temp_agent_run_{get_timestamp()}.js")
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(code)
    try:
        result = subprocess.run(["node", temp_path],
                                capture_output=True, text=True, timeout=12)
        output = result.stdout[:MAX_STDOUT] + "\n" + result.stderr[:MAX_STDERR]
        logger.log("exec_node", {
            "file": temp_path,
            "action": "Ran code",
            "stdout": result.stdout[:500],
            "stderr": result.stderr[:300],
            "returncode": result.returncode
        })
        return f"Node.js run output:\n{output}"
    except subprocess.TimeoutExpired:
        logger.log("exec_node_timeout", {"file": temp_path, "code": code})
        return "Node code execution timed out."
    except FileNotFoundError:
        logger.log("exec_node_error", {"file": temp_path, "error": "Node.js is not installed or not found in PATH.", "code": code})
        return "Node.js is not installed or not found in PATH."
    except Exception as e:
        logger.log("exec_node_error", {"file": temp_path, "error": str(e), "code": code})
        return f"Error running code: {e}"
    finally:
        try:
            os.remove(temp_path)
        except Exception as cleanup_err:
            logger.log("tempfile_remove_fail", {"file": temp_path, "error": str(cleanup_err)})