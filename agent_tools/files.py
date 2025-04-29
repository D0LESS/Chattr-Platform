import os
import shutil
import tempfile
import datetime
import difflib
import glob
from typing import Optional, Dict, Any
from agent_tools.ragis_logger import RagisLogger

# Central logger for all file actions
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=['content', 'abs_path', 'temp_path', 'backup_path'])

def get_timestamp() -> str:
    """Return a timestamp string for backup filenames."""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def backup_file(abs_path: str) -> Optional[str]:
    """Create a timestamped backup of the file at abs_path."""
    if not os.path.exists(abs_path):
        return None
    bpath = f"{abs_path}.bak.{get_timestamp()}"
    shutil.copy2(abs_path, bpath)
    logger.log("backup_file", {
        "orig": abs_path,
        "backup": bpath
    })
    return bpath

def show_diff(file1: str, file2: str) -> str:
    """Return a unified diff between two files."""
    try:
        with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()
        diff = difflib.unified_diff(lines1, lines2, fromfile=file1, tofile=file2)
        return "".join(diff)
    except Exception as e:
        logger.log("diff_error", {"file1": file1, "file2": file2, "error": str(e)})
        return f"Diff error: {e}"

def is_affirmative(msg: str) -> bool:
    """Return True if the message is an affirmative/approval."""
    affirm = [
        "yes", "ok", "allow", "approve", "go ahead", "sure", "yep", "accepted",
        "affirm", "green light", "do it", "confirmed"
    ]
    msg_low = msg.strip().lower()
    return any(word in msg_low for word in affirm)

def read_any_file(args: Dict[str, Any], session_state: dict) -> str:
    """Read and return the contents of a file under the user's home directory."""
    rel_path = args.get("path")
    abs_path = os.path.abspath(os.path.expanduser(rel_path))
    user_home = os.path.expanduser("~")
    if not abs_path.startswith(user_home):
        return "Permission denied: Only files under your user directory can be read."
    try:
        with open(abs_path, 'r', encoding="utf-8") as f:
            content = f.read()
        logger.log("read_file", {"action": "READ_FILE", "abs_path": abs_path, "summary": "Read by agent."})
        return content
    except Exception as e:
        logger.log("read_file_fail", {"action": "READ_FILE_FAIL", "abs_path": abs_path, "error": str(e)})
        return f"Error: {e}"

def edit_or_create_file(args: Dict[str, Any], session_state: dict) -> str:
    """
    Prepare to edit or create a file, showing a diff and requesting approval.
    Backs up the file if it exists.
    """
    rel_path = args.get("path")
    content = args.get("content", "")
    abs_path = os.path.abspath(os.path.expanduser(rel_path))
    user_home = os.path.expanduser("~")
    if not abs_path.startswith(user_home):
        return "Permission denied: Only files under your user directory can be edited/created."
    op_type = "edit" if os.path.exists(abs_path) else "create"
    backup_path = backup_file(abs_path) if os.path.exists(abs_path) else None
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmpf:
        tmpf.write(content)
        temp_path = tmpf.name
    diff_text = ""
    if backup_path:
        diff_text = show_diff(backup_path, temp_path)
    elif os.path.exists(abs_path):
        diff_text = show_diff(abs_path, temp_path)
    summary = f"Diff preview:\n{diff_text[:2000]}" if diff_text else "(No diff preview available.)"
    session_state['pending_file_change'] = (abs_path, content, op_type, backup_path, temp_path)
    snippet = content if len(content) < 80 else content[:77] + "..."
    logger.log("prepare_edit_or_create", {
        "action": op_type.upper(),
        "abs_path": abs_path,
        "backup_path": backup_path,
        "temp_path": temp_path,
        "diff_text": diff_text[:500]
    })
    return (
        f"I'd like to {op_type} the file:\n{abs_path}\nHere is a snippet: '{snippet}'\n{summary}\n"
        "Is that OK? (Reply yes/ok/approve or similar to allow, or no to cancel.)"
    )

def handle_pending_file_change(user_message: str, session_state: dict) -> Optional[str]:
    """
    Handle approval or rejection of a pending file edit/create.
    Cleans up temp files and logs all actions.
    """
    if session_state.get('pending_file_change'):
        abs_path, content, op_type, backup_path, temp_path = session_state['pending_file_change']
        auto_approve = session_state.get("global_approval", False)

        if auto_approve or is_affirmative(user_message):
            try:
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.log("write_file", {
                    "action": "WRITE_FILE", "abs_path": abs_path,
                    "summary": f"User approved; {op_type} (backup in {backup_path if backup_path else 'N/A'})"
                })
                session_state.pop('pending_file_change')
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logger.log("tempfile_remove_fail", {"file": temp_path, "error": str(e)})
                return f"File '{abs_path}' {op_type}d successfully. (Backup: {backup_path})"
            except Exception as e:
                session_state.pop('pending_file_change')
                try:
                    os.remove(temp_path)
                except Exception as e2:
                    logger.log("tempfile_remove_fail", {"file": temp_path, "error": str(e2)})
                logger.log("write_file_fail", {
                    "action": "WRITE_FILE_FAIL", "abs_path": abs_path, "error": str(e)
                })
                return f"Error editing/creating file: {e}"
        else:
            session_state.pop('pending_file_change')
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.log("tempfile_remove_fail", {"file": temp_path, "error": str(e)})
            logger.log("edit_create_cancel", {"abs_path": abs_path, "op_type": op_type})
            return "File edit/create was not approved. Cancelling."
    return None

def list_file_backups(args: Dict[str, Any], session_state: dict) -> str:
    """
    List all available backups for a given file, formatted with indices for easy selection.
    """
    pattern = args.get("path", "")
    if not pattern:
        return "No target file path specified."
    pattern = os.path.abspath(os.path.expanduser(pattern)) + ".bak.*"
    found = sorted(glob.glob(pattern), reverse=True)
    if not found:
        return f"No backups found for {pattern}."
    backup_msg = "\n".join(f"[{i}] {os.path.basename(fp)} ({fp})" for i, fp in enumerate(found))
    logger.log("list_file_backups", {"pattern": pattern, "files_found": found[:10]})
    return "Available backups:\n" + backup_msg

def restore_file_backup(args: Dict[str, Any], session_state: dict) -> str:
    """
    Restore a file from a selected backup.
    """
    backup_path = args.get("backup_path")
    if not backup_path or not os.path.exists(backup_path):
        return "Backup file not found."
    orig_path = backup_path.rsplit(".bak.", 1)[0]
    try:
        shutil.copy2(backup_path, orig_path)
        logger.log("restore_file_backup", {
            "action": "RESTORE_FILE_BACKUP", "orig_path": orig_path, "backup_path": backup_path
        })
        return f"{orig_path} has been restored from backup {backup_path}."
    except Exception as e:
        logger.log("restore_file_backup_fail", {
            "action": "RESTORE_FILE_BACKUP_FAIL", "orig_path": orig_path, "backup_path": backup_path, "error": str(e)
        })
        return f"Restore error: {e}"