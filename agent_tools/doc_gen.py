# doc_gen.py

import os
import subprocess
import datetime
from typing import Any, Dict, Optional
from agent_tools.ragis_logger import RagisLogger

MAX_DOC_STDOUT = 2000
MAX_DOC_STDERR = 800

# Centralized logger for doc generation actions
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=["target_path"])

def is_affirmative(msg: str) -> bool:
    """Return True if the message is an affirmative/approval."""
    affirm = ["yes", "ok", "allow", "approve", "go ahead"]
    return any(word in msg.lower() for word in affirm)

def generate_docstrings(args: Dict[str, Any], session_state: dict) -> str:
    """
    Prepare to run docformatter or equivalent tool to fix/generate docstrings.
    Approval required.
    """
    target = args.get("target_path", "")
    if not target:
        return "No target path specified."
    abs_target = os.path.abspath(os.path.expanduser(target))
    if not os.path.exists(abs_target):
        return f"Target file does not exist: {abs_target}"

    session_state['pending_doc_gen'] = abs_target
    return f"Agent wants to auto-generate/fix docstrings for {abs_target}. Proceed? (yes/ok/approve)"

def handle_pending_doc_gen(user_message: str, session_state: dict) -> Optional[str]:
    """
    Actually run the docstring generation/fix if approved.
    """
    if session_state.get('pending_doc_gen'):
        abs_target = session_state.pop('pending_doc_gen')
        auto_approve = session_state.get("global_approval", False)

        if auto_approve or is_affirmative(user_message):
            try:
                result = subprocess.run(
                    ["docformatter", "-i", abs_target],
                    capture_output=True, text=True, timeout=30
                )
                logger.log("doc_gen", {
                    "action": "docformatter_run",
                    "target_path": abs_target,
                    "stdout_sample": result.stdout[:250],
                    "stderr_sample": result.stderr[:150]
                })
                return (
                    f"Docstring formatting done for {abs_target}.\n"
                    f"{result.stdout[:MAX_DOC_STDOUT]}\n{result.stderr[:MAX_DOC_STDERR]}"
                )
            except Exception as e:
                logger.log("doc_gen_error", {
                    "action": "docformatter_run",
                    "target_path": abs_target,
                    "error": str(e)
                })
                return f"Docstring generation error: {e}"
        else:
            logger.log("doc_gen_cancelled", {
                "target_path": abs_target,
                "user_message": user_message
            })
            return "Docstring generation cancelled."
    return None