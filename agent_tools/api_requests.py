# api_requests.py

import requests
import datetime
from typing import Any, Dict, Optional
from agent_tools.ragis_logger import RagisLogger

MAX_API_RESPONSE = 2500

# Instantiate a central logger for this module (adjust path/PII as needed)
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=['payload', 'url'])

def is_affirmative(msg: str) -> bool:
    """Return True if the message is an affirmative/approval."""
    affirm = ["yes", "ok", "allow", "approve", "go ahead"]
    return any(word in msg.lower() for word in affirm)

def api_get(args: Dict[str, Any], session_state: dict) -> str:
    """
    Prepare a GET API call, approval required.
    """
    url = args.get("url", "")
    if not url:
        return "No URL provided."
    session_state['pending_api_call'] = ("GET", url)
    return f"Agent wants to call GET {url} — ok to run? (yes/ok/approve)"

def api_post(args: Dict[str, Any], session_state: dict) -> str:
    """
    Prepare a POST API call, approval required.
    """
    url = args.get("url", "")
    payload = args.get("payload", {})
    if not url:
        return "No URL provided."
    session_state['pending_api_call'] = ("POST", url, payload)
    return f"Agent wants to call POST {url} with payload {payload} — ok to run? (yes/ok/approve)"

def handle_pending_api_call(user_message: str, session_state: dict) -> Optional[str]:
    """
    Handle approval and execution of a pending API call (GET or POST).
    """
    if session_state.get('pending_api_call'):
        auto_approve = session_state.get("global_approval", False)
        call_info = session_state.pop('pending_api_call')

        if auto_approve or is_affirmative(user_message):
            try:
                if call_info[0] == "GET":
                    method, url = call_info
                    result = requests.get(url, timeout=20)
                    logger.log("api_get", {
                        "url": url,
                        "status_code": result.status_code,
                        "response_excerpt": result.text[:300]
                    })
                    return f"GET {url} response:\n{result.text[:MAX_API_RESPONSE]}"
                elif call_info[0] == "POST":
                    method, url, payload = call_info
                    result = requests.post(url, json=payload, timeout=20)
                    logger.log("api_post", {
                        "url": url,
                        "status_code": result.status_code,
                        "payload": payload,
                        "response_excerpt": result.text[:300]
                    })
                    return f"POST {url} response:\n{result.text[:MAX_API_RESPONSE]}"
                else:
                    logger.log("api_error", {
                        "action": call_info,
                        "error": "Unknown API call format."
                    })
                    return "Unknown API call format."
            except Exception as e:
                logger.log("api_error", {
                    "action": call_info,
                    "error": str(e)
                })
                return f"API call error: {e}"
        else:
            logger.log("api_cancelled", {
                "action": call_info,
                "user_message": user_message
            })
            return "API call not approved. Cancelling."
    return None