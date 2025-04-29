import subprocess
from datetime import datetime
from typing import Any, Dict, Optional
from agent_tools.ragis_logger import RagisLogger

MAX_STDOUT = 1800
MAX_STDERR = 800

# Central logger for pip audit actions
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=['path'])

def is_affirmative(msg: str) -> bool:
    """Return True if the message is an affirmative/approval."""
    affirm = ["yes", "ok", "allow", "approve", "go ahead"]
    return any(word in msg.lower() for word in affirm)

def pip_audit(args: Dict[str, Any], session_state: dict) -> str:
    """
    Prepare to run pip-audit in the given path, approval required.
    """
    path = args.get("path", ".")
    session_state['pending_pip_audit'] = path
    return f"Agent wants to run pip-audit in `{path}` to check dependencies for CVEs. Run audit? (yes/ok/approve)"

def handle_pending_pip_audit(user_message: str, session_state: dict) -> Optional[str]:
    """
    Handle approval and execution of a pending pip-audit.
    """
    if session_state.get('pending_pip_audit'):
        path = session_state.pop('pending_pip_audit')
        auto_approve = session_state.get("global_approval", False)

        if auto_approve or is_affirmative(user_message):
            try:
                result = subprocess.run(
                    ["pip-audit", "--no-deps"], capture_output=True, text=True, cwd=path, timeout=30
                )
                logger.log("pip_audit", {
                    "action": "PIP_AUDIT",
                    "path": path,
                    "stdout_sample": result.stdout[:350],
                    "stderr_sample": result.stderr[:150]
                })
                audit = result.stdout[:MAX_STDOUT] + "\n" + result.stderr[:MAX_STDERR]
                return (
                    f"pip-audit results:\n{audit}\n"
                    "Should I suggest upgrades/patches for any vulnerable packages? (yes/no)"
                )
            except Exception as e:
                logger.log("pip_audit_fail", {
                    "action": "PIP_AUDIT_FAIL",
                    "path": path,
                    "error": str(e)
                })
                return f"pip-audit error: {e}"
        else:
            logger.log("pip_audit_cancelled", {"path": path, "user_message": user_message})
            return "pip-audit cancelled."
    return None

def handle_pip_audit_upgrade(user_message: str, session_state: dict) -> Optional[str]:
    """
    Stub placeholder: you'd add per-package patching here if extending.
    """
    return None