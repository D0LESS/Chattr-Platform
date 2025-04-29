import os
import shutil
import glob
from datetime import datetime
from typing import Dict, Any, Optional
from agent_tools.ragis_logger import RagisLogger

# Central logger for restore actions
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=['target_path', 'backup_path'])

def list_file_backups(args: Dict[str, Any], session_state: dict) -> str:
    """
    List all backup files (timestamped .bak.*) for a given file.
    """
    target = args.get("target_path", "")
    target = os.path.abspath(os.path.expanduser(target))
    pattern = f"{target}.bak.*"
    found = sorted(glob.glob(pattern), reverse=True)
    if not found:
        return f"No backups found for {target}."
    session_state['pending_backup_restore'] = found
    backup_msg = "\n".join(f"[{i}] {os.path.basename(fp)} ({fp})" for i, fp in enumerate(found))
    logger.log("list_file_backups", {"target_path": target, "backups_found": found[:10]})
    return (
        f"Backups for {target}:\n{backup_msg}\n"
        "Reply with the index number to restore, or 'cancel' to skip."
    )

def handle_pending_backup_restore(user_message: str, session_state: dict) -> Optional[str]:
    """
    Restore a selected backup file over its original.
    """
    if session_state.get('pending_backup_restore'):
        found = session_state.pop('pending_backup_restore')

        if user_message.strip().lower() == "cancel":
            logger.log("restore_cancelled", {})
            return "Restore cancelled."

        try:
            idx = int(user_message.strip())
            if idx < 0 or idx >= len(found):
                logger.log("restore_invalid_index", {"index": idx, "max": len(found)-1})
                return f"Invalid index. Please provide an integer 0-{len(found)-1} or type 'cancel'."
            backup_path = found[idx]
            orig_path = backup_path.rsplit(".bak.", 1)[0]
            # Always restore if a valid index is chosen, since user must select the backup.
            shutil.copy2(backup_path, orig_path)
            logger.log("restore_file_backup", {
                "action": "RESTORE_FILE_BACKUP",
                "orig_path": orig_path,
                "backup_path": backup_path
            })
            return f"Restored {orig_path} from backup {backup_path}."
        except Exception as e:
            logger.log("restore_error", {"error": str(e)})
            return f"Restore error: {e}"
    return None