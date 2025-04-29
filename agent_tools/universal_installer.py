import os
import subprocess
import datetime
from agent_tools.ragis_logger import RagisLogger

MAX_STDOUT = 3000
MAX_STDERR = 1000

# Central logger for all installer actions
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=['project_path', 'script_path', 'script_content'])

def is_affirmative(msg):
    affirm = ["yes", "ok", "allow", "approve", "go ahead"]
    return any(word in msg.lower() for word in affirm)

def suggest_installer(args, session_state):
    """
    Scan the project directory and recommend/build universal installer scripts.
    """
    project_path = args.get("project_dir", os.path.expanduser("~"))
    entries = []
    for fname in ["setup.py", "requirements.txt", "pyproject.toml", "package.json", "Dockerfile", "Makefile"]:
        full = os.path.join(project_path, fname)
        if os.path.exists(full):
            entries.append(fname)
    summary = (
        "Detected installer files:\n" +
        "\n".join(f"- {f}" for f in entries) +
        ("\n\nI can combine these into a bash install script or Docker Compose for you." if entries else "\nNo installer files found.")
    )
    session_state['pending_installer'] = project_path
    logger.log("suggest_installer", {
        "project_path": project_path,
        "detected_files": entries
    })
    return summary + "\nWould you like to build the universal installer? (yes/no)"

def handle_pending_installer(user_message, session_state):
    if session_state.get('pending_installer'):
        prj = session_state.pop('pending_installer')
        if is_affirmative(user_message):
            install_lines = []
            if os.path.exists(os.path.join(prj, "requirements.txt")):
                install_lines.append("pip install -r requirements.txt")
            if os.path.exists(os.path.join(prj, "package.json")):
                install_lines.append("npm install")
            if os.path.exists(os.path.join(prj, "setup.py")):
                install_lines.append("pip install .")
            if os.path.exists(os.path.join(prj, "Makefile")):
                install_lines.append("make")
            if os.path.exists(os.path.join(prj, "Dockerfile")):
                install_lines.append("docker build -t myimage .")
            script_content = "\n".join(install_lines)
            script_path = os.path.join(prj, "universal_installer.sh")
            try:
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write("#!/bin/bash\nset -e\n" + script_content)
                os.chmod(script_path, 0o770)
                logger.log("universal_installer_created", {
                    "script_path": script_path,
                    "project_path": prj,
                    "script_content": script_content
                })
            except Exception as e:
                logger.log("universal_installer_error", {
                    "script_path": script_path, "project_path": prj, "error": str(e)
                })
                return f"Error creating installer script: {e}"
            return (
                f"Universal installer created at {script_path}:\n\n"
                f"{script_content}\n\nReady to run the installer? (yes/ok/approve)"
            )
        else:
            logger.log("universal_installer_cancelled", {"project_path": prj})
            return "Universal installer script creation cancelled."
    return None

def handle_pending_installer_run(user_message, session_state):
    if session_state.get('pending_installer_run'):
        script_path = session_state.pop('pending_installer_run')
        if is_affirmative(user_message):
            try:
                result = subprocess.run(
                    ["/bin/bash", script_path],
                    capture_output=True, text=True, timeout=300  # generous for full installs
                )
                logger.log("run_installer", {
                    "script_path": script_path,
                    "stdout_excerpt": result.stdout[:500],
                    "stderr_excerpt": result.stderr[:300]
                })
                output = result.stdout[:MAX_STDOUT] + "\n" + result.stderr[:MAX_STDERR]
                return f"Installer script ran. Output:\n{output}"
            except Exception as e:
                logger.log("run_installer_error", {
                    "script_path": script_path, "error": str(e)
                })
                return f"Installer run error: {e}"
        else:
            logger.log("run_installer_cancelled", {"script_path": script_path})
            return "Universal installer run cancelled."
    return None