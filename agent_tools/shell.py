import os
import subprocess
import datetime
from agent_tools.ragis_logger import RagisLogger

MAX_STDOUT = 1800
MAX_STDERR = 800

# Central logger for all shell/npm/pip actions
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=['cmd', 'cwd', 'package'])

def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def is_affirmative(msg):
    affirm = ["yes", "ok", "allow", "approve", "go ahead"]
    return any(word in msg.lower() for word in affirm)

def run_shell_command(args, session_state):
    cmd = args.get("cmd", "")
    cwd = args.get("cwd", os.path.expanduser("~"))
    safe_cmds = [
        "ls", "dir", "npm install", "npm run", "npm build", "pip install", "pip list",
        "python", "pytest", "make", "echo", "pip freeze", "npm start", "node", "which", "where"
    ]
    blocklist = ["rm -rf", "del /f", "shutdown", "format", "dd ", "mkfs", "poweroff"]

    if any(bad in cmd.lower() for bad in blocklist):
        logger.log("blocked_shell_command", {"cmd": cmd, "cwd": cwd})
        return "[BLOCKED] That command is not permitted for safety."
    if not any(cmd.lower().startswith(prefix) for prefix in safe_cmds):
        session_state['pending_shell_cmd'] = (cmd, cwd)
        return f"Agent wants to run shell command:\n`{cmd}` in `{cwd}` — ok to run? (yes/ok/approve)"
    try:
        if cmd.startswith("npm install"):
            parts = cmd.split()
            result = subprocess.run(parts, cwd=cwd, capture_output=True, text=True, timeout=60)
        elif cmd.startswith("pip install"):
            parts = cmd.split()
            result = subprocess.run(parts, cwd=cwd, capture_output=True, text=True, timeout=60)
        else:
            result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=60)
        logger.log("run_shell", {"action": "RUN_SHELL", "cwd": cwd, "cmd": cmd})
        output = result.stdout[:2200] + "\n" + result.stderr[:600]
        return f"Shell output (clipped):\n{output}"
    except Exception as e:
        logger.log("run_shell_fail", {"action": "RUN_SHELL_FAIL", "cwd": cwd, "cmd": cmd, "error": str(e)})
        return f"Shell command error: {e}"

def handle_pending_shell_cmd(user_message, session_state):
    if session_state.get('pending_shell_cmd'):
        cmd, cwd = session_state.pop('pending_shell_cmd')
        auto_approve = session_state.get("global_approval", False)

        if auto_approve or is_affirmative(user_message):
            try:
                if cmd.startswith("npm install"):
                    parts = cmd.split()
                    result = subprocess.run(parts, cwd=cwd, capture_output=True, text=True, timeout=60)
                elif cmd.startswith("pip install"):
                    parts = cmd.split()
                    result = subprocess.run(parts, cwd=cwd, capture_output=True, text=True, timeout=60)
                else:
                    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=60)
                logger.log("run_shell", {"action": "RUN_SHELL", "cwd": cwd, "cmd": cmd})
                output = result.stdout[:2000] + "\n" + result.stderr[:800]
                return f"Shell output (approved):\n{output}"
            except Exception as e:
                logger.log("run_shell_fail", {"action": "RUN_SHELL_FAIL", "cwd": cwd, "cmd": cmd, "error": str(e)})
                return f"Shell command error: {e}"
        else:
            logger.log("shell_cmd_cancelled", {"cmd": cmd, "cwd": cwd, "user_message": user_message})
            return "Shell command cancelled."
    return None

def run_pip_install(args, session_state):
    package = args.get("package")
    if not package:
        return "No package specified for pip install."
    session_state['pending_pip_install'] = package
    return f"Agent wants to run `pip install {package}`. Ok to run? (yes/ok/approve)"

def handle_pending_pip_install(user_message, session_state):
    if session_state.get('pending_pip_install'):
        package = session_state.pop('pending_pip_install')
        auto_approve = session_state.get("global_approval", False)

        if auto_approve or is_affirmative(user_message):
            try:
                result = subprocess.run(
                    ["pip", "install", package], capture_output=True, text=True, timeout=60
                )
                logger.log("pip_install", {"action": "PIP_INSTALL", "package": package})
                return f"pip install output:\n{result.stdout[:MAX_STDOUT]}\n{result.stderr[:MAX_STDERR]}"
            except Exception as e:
                logger.log("pip_install_fail", {"action": "PIP_INSTALL_FAIL", "package": package, "error": str(e)})
                return f"pip install error: {e}"
        else:
            logger.log("pip_install_cancelled", {"package": package, "user_message": user_message})
            return "pip install cancelled."
    return None

def run_npm_install(args, session_state):
    package = args.get("package", "")
    cwd = args.get("cwd", os.path.expanduser("~"))
    if not package:
        session_state['pending_npm_install'] = cwd
        return f"Agent wants to run `npm install` in `{cwd}` (no package specified). Ok to run? (yes/ok/approve)"
    else:
        session_state['pending_npm_install'] = (package, cwd)
        return f"Agent wants to run `npm install {package}` in `{cwd}`. Ok to run? (yes/ok/approve)"

def handle_pending_npm_install(user_message: str, session_state: dict) -> str | None:
    """
    Handle approval for pending npm install actions.
    If approved, runs npm install (with or without a package) in the specified directory.
    """
    if session_state.get('pending_npm_install'):
        val = session_state.pop('pending_npm_install')
        auto_approve = session_state.get("global_approval", False)

        if isinstance(val, tuple):
            package, cwd = val
            cmd = ["npm", "install", package]
        else:
            package, cwd = "", val
            cmd = ["npm", "install"]

        if auto_approve or is_affirmative(user_message):
            try:
                result = subprocess.run(
                    cmd, cwd=cwd, capture_output=True, text=True, timeout=120
                )
                logger.log("npm_install", {"action": "NPM_INSTALL", "package": package, "cwd": cwd, "cmd": " ".join(cmd)})
                return f"npm install output:\n{result.stdout[:MAX_STDOUT]}\n{result.stderr[:MAX_STDERR]}"
            except Exception as e:
                logger.log("npm_install_fail", {"action": "NPM_INSTALL_FAIL", "package": package, "cwd": cwd, "cmd": " ".join(cmd), "error": str(e)})
                return f"npm install error: {e}"
        else:
            logger.log("npm_install_cancelled", {"package": package, "cwd": cwd, "cmd": " ".join(cmd), "user_message": user_message})
            return "npm install cancelled."
    return None