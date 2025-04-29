import os
import subprocess
from datetime import datetime
from typing import Any, Dict, Optional
from agent_tools.ragis_logger import RagisLogger

MAX_RIPGREP_LINES = 40
MAX_CTAGS_RESULTS = 30

# Central logger for code/search actions
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=["pattern", "project_dir", "symbol"])

def is_affirmative(msg: str) -> bool:
    affirm = ["yes", "ok", "allow", "approve", "go ahead"]
    return any(word in msg.lower() for word in affirm)

def code_search_ripgrep(args: Dict[str, Any], session_state: dict) -> str:
    """
    Run a ripgrep search for the given pattern in the project directory.
    Approval required.
    """
    pattern = args.get("pattern", "")
    if not pattern.strip():
        return "Please specify a non-empty search pattern."
    project_dir = os.path.abspath(os.path.expanduser(args.get("project_dir", "~")))
    try:
        result = subprocess.run(
            ["rg", pattern, project_dir, "--color", "never", "-n", "-H", "-C1"],
            capture_output=True, text=True, timeout=30
        )
        matches = result.stdout.strip().splitlines()
        matches = matches[:MAX_RIPGREP_LINES]
        formatted = "\n".join(matches)
        logger.log("code_search", {
            "action": "CODE_SEARCH",
            "project_dir": project_dir,
            "pattern": pattern,
            "result_count": len(matches)
        })
        return f"[ripgrep search result]\n{formatted}\n(Results may be clipped...)"
    except Exception as e:
        logger.log("code_search_error", {
            "action": "CODE_SEARCH",
            "project_dir": project_dir,
            "pattern": pattern,
            "error": str(e)
        })
        return f"ripgrep search error: {e}"

def handle_pending_code_search(user_message: str, session_state: dict) -> Optional[str]:
    """
    Handle approval and execution of a pending ripgrep code search.
    """
    if session_state.get('pending_code_search'):
        pattern, project_dir = session_state.pop('pending_code_search')
        auto_approve = session_state.get("global_approval", False)

        if auto_approve or is_affirmative(user_message):
            try:
                result = subprocess.run(
                    ["rg", pattern, project_dir, "--color", "never", "-n", "-H", "-C1"],
                    capture_output=True, text=True, timeout=30
                )
                matches = result.stdout.strip().splitlines()
                matches = matches[:MAX_RIPGREP_LINES]
                formatted = "\n".join(matches)
                logger.log("code_search", {
                    "action": "CODE_SEARCH",
                    "project_dir": project_dir,
                    "pattern": pattern,
                    "result_count": len(matches)
                })
                return f"[ripgrep search result]\n{formatted}\n(Results may be clipped...)"
            except FileNotFoundError:
                logger.log("code_search_error", {
                    "action": "CODE_SEARCH",
                    "project_dir": project_dir,
                    "pattern": pattern,
                    "error": "ripgrep (rg) is not installed or not found in PATH."
                })
                return "ripgrep (rg) is not installed or not found in PATH."
            except Exception as e:
                logger.log("code_search_error", {
                    "action": "CODE_SEARCH",
                    "project_dir": project_dir,
                    "pattern": pattern,
                    "error": str(e)
                })
                return f"ripgrep search error: {e}"
        else:
            logger.log("code_search_cancelled", {
                "project_dir": project_dir,
                "pattern": pattern,
                "user_message": user_message
            })
            return "Code search was not approved."
    return None

def symbol_search_ctags(args: Dict[str, Any], session_state: dict) -> str:
    """
    Use ctags to get a list of symbols (function/class names) in the project.
    """
    symbol = args.get("symbol", "")
    if not symbol:
        return "Please specify a symbol to search for."
    project_dir = os.path.abspath(os.path.expanduser(args.get("project_dir", "~")))
    tags_file = os.path.join(project_dir, "tags")
    if not os.path.exists(tags_file):
        return "No tags file found. Run `ctags -R` in your project directory first."

    results = []
    try:
        with open(tags_file, "r", encoding="utf-8") as f:
            for line in f:
                if symbol in line:
                    results.append(line.strip())
    except Exception as e:
        logger.log("ctags_error", {
            "action": "SYMBOL_SEARCH",
            "tags_file": tags_file,
            "symbol": symbol,
            "error": str(e)
        })
        return f"Error reading tags file: {e}"
    
    if not results:
        return f"No symbols matching '{symbol}' found."

    results = results[:MAX_CTAGS_RESULTS]
    logger.log("symbol_search_ctags", {
        "action": "SYMBOL_SEARCH",
        "tags_file": tags_file,
        "symbol": symbol,
        "result_count": len(results)
    })
    return f"[ctags symbol search for '{symbol}']\n" + "\n".join(results)