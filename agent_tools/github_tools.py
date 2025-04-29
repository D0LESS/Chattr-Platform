import os
import subprocess
from datetime import datetime
from .utils import stream_progress_update  # if you want to show streaming later
from .task_manager import with_retry
from agent_tools.ragis_logger import RagisLogger

MAX_CLONE_STDOUT = 2000
MAX_CLONE_STDERR = 800
MAX_PUSH_LOG = 2500

# Central logger for all git actions
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=['repo_url', 'dest_dir', 'local_dir', 'commit_msg'])

def is_affirmative(msg: str) -> bool:
    """Return True if the message is an affirmative/approval."""
    affirm = ["yes", "ok", "allow", "approve", "go ahead"]
    return any(word in msg.lower() for word in affirm)

def github_clone(args, session_state, get_secret):
    """
    Prepare to clone a GitHub repo, approval required.
    """
    repo_url = args.get("url")
    dest_dir = os.path.abspath(os.path.expanduser(args.get("dest", "myrepo_clone")))
    user_home = os.path.expanduser("~")
    if not dest_dir.startswith(user_home):
        return "Permission denied: Only clone under your user directory."
    session_state['pending_github_clone'] = (repo_url, dest_dir)
    return f"Clone repo {repo_url} to {dest_dir}? (yes/ok/approve)"

def handle_pending_github_clone(user_message, session_state, get_secret):
    """
    Handle approval and execution of a pending GitHub clone.
    """
    if session_state.get('pending_github_clone'):
        repo_url, dest_dir = session_state.pop('pending_github_clone')
        auto_approve = session_state.get("global_approval", False)

        if auto_approve or is_affirmative(user_message):
            try:
                result = with_retry(lambda: subprocess.run(
                    ["git", "clone", repo_url, dest_dir], capture_output=True, text=True, timeout=90
                ))
                logger.log("github_clone", {
                    "action": "GITHUB_CLONE",
                    "dest_dir": dest_dir,
                    "repo_url": repo_url,
                    "stdout_sample": result.stdout[:500],
                    "stderr_sample": result.stderr[:300]
                })
                return f"Cloned {repo_url} to {dest_dir}.\n{result.stdout[:MAX_CLONE_STDOUT]}\n{result.stderr[:MAX_CLONE_STDERR]}"
            except Exception as e:
                logger.log("github_clone_error", {
                    "action": "GITHUB_CLONE",
                    "repo_url": repo_url,
                    "dest_dir": dest_dir,
                    "error": str(e)
                })
                return f"Clone error: {e}"
        else:
            logger.log("github_clone_cancelled", {
                "repo_url": repo_url, "dest_dir": dest_dir, "user_message": user_message
            })
            return "GitHub clone not approved. Cancelling."
    return None

def github_push(args, session_state, get_secret):
    """
    Prepare to push a local repo to GitHub, approval required.
    """
    local_dir = os.path.abspath(os.path.expanduser(args.get("dir", "")))
    commit_msg = args.get("message", "Agent commit")
    remote = args.get("remote", "origin")
    branch = args.get("branch", "main")
    user_home = os.path.expanduser("~")
    if not local_dir.startswith(user_home):
        return "Permission denied: Only push from user directory."
    session_state['pending_github_push'] = (local_dir, commit_msg, remote, branch)
    return f"Push {local_dir} with commit '{commit_msg}' to {remote}/{branch}? (yes/ok/approve)"

def handle_pending_github_push(user_message, session_state, get_secret):
    """
    Handle approval and execution of a pending GitHub push.
    """
    if session_state.get('pending_github_push'):
        local_dir, commit_msg, remote, branch = session_state.pop('pending_github_push')
        auto_approve = session_state.get("global_approval", False)

        if auto_approve or is_affirmative(user_message):
            try:
                cmds = [
                    ["git", "add", "."],
                    ["git", "commit", "-m", commit_msg],
                    ["git", "push", remote, branch]
                ]
                outputs = []
                for cmd in cmds:
                    try:
                        result = with_retry(lambda: subprocess.run(cmd, capture_output=True, text=True, cwd=local_dir, timeout=90))
                        outputs.append(result.stdout + "\n" + result.stderr)
                    except Exception as e:
                        # Special handling for "nothing to commit" on git commit
                        if "commit" in cmd and "nothing to commit" in str(e):
                            outputs.append("Nothing to commit.\n")
                        else:
                            outputs.append(f"Error running {' '.join(cmd)}: {e}\n")
                logger.log("github_push", {
                    "action": "GITHUB_PUSH",
                    "local_dir": local_dir,
                    "commit_msg": commit_msg,
                    "remote": remote,
                    "branch": branch,
                    "log_excerpt": ''.join(outputs)[:700]
                })
                return f"Git push done. Log:\n{''.join(outputs)[:MAX_PUSH_LOG]}"
            except Exception as e:
                logger.log("github_push_error", {
                    "action": "GITHUB_PUSH",
                    "local_dir": local_dir,
                    "commit_msg": commit_msg,
                    "remote": remote,
                    "branch": branch,
                    "error": str(e)
                })
                return f"Push error: {e}"
        else:
            logger.log("github_push_cancelled", {
                "local_dir": local_dir, "commit_msg": commit_msg,
                "remote": remote, "branch": branch, "user_message": user_message
            })
            return "GitHub push not approved. Cancelling."
    return None