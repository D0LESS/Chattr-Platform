# 🧩 OmniThreads Agent Tools

This folder contains the **modular toolkit** powering the OmniThreads agent platform.  
Each tool is designed for **explicit, conversational approval**, robust centralized logging (using `RagisLogger`), and safe automation for developers, DevOps, and UX/UI workflows.

---

## 📦 Tool Modules Overview

<details>
<summary><strong>files.py</strong></summary>

- **read_any_file:** Read files under your user directory with path validation and robust logging.
- **edit_or_create_file:** Edit/create files under your directory (approval, backup, diff preview), logs all actions.
- **handle_pending_file_change:** Conversational approval handler for file changes, logs all events.
- **list_file_backups:** List timestamped backups for a file, formatted and logged.
- **restore_file_backup:** Restore a file from any backup with approval, all actions logged.
</details>

<details>
<summary><strong>code_exec.py</strong></summary>

- **exec_python_code:** Approval-gated, syntax-checked Python execution with detailed event logging.
- **exec_node_code:** Approval-gated Node.js code execution, robustly logged.
</details>

<details>
<summary><strong>ux_sandbox.py</strong></summary>

- **write_ui_file:** Safely add/edit HTML/CSS/JS/React files in the `ui_sandbox` folder, with backup/diff and robust logging.
- **handle_pending_ui_file:** Conversational approval for UI file changes, logs approvals, denials, and backups.
- **start_ui_sandbox_server:** Launches a local server for UI preview, server events logged.
- **vivaldi_ui_screenshot:** Takes browser screenshots using Vivaldi and Selenium, screenshot actions logged.
- **test_ui_button:** Automates UI sandbox button interaction for test automation with logging.
</details>

<details>
<summary><strong>shell.py</strong></summary>

- **run_shell_command:** Approval-gated shell command execution (safe-list + blocklist), commands and outputs logged.
- **handle_pending_shell_cmd:** Waits for explicit approval before executing any command not on the safe-list, logs all results.
- **run_pip_install:** Approval and logging for pip install actions.
- **handle_pending_pip_install:** Gated, logged execution of pip install.
- **run_npm_install:** Approval and logging for npm installs.
- **handle_pending_npm_install:** Gated, logged execution of npm installs.
</details>

<details>
<summary><strong>github_tools.py</strong></summary>

- **github_clone:** Approval and directory-checking for git repo clone, events are logged.
- **handle_pending_github_clone:** Conversational approval and detailed logging.
- **github_push:** Approval-gated git pushes, commit message/remote/branch logged.
- **handle_pending_github_push:** Approval and output logging for git push activity.
</details>

<details>
<summary><strong>api_requests.py</strong></summary>

- **api_get:** Approval-gated GET API call, actions and responses logged.
- **api_post:** Approval-gated POST API call, actions and responses logged.
- **handle_pending_api_call:** Approves and logs all outbound API calls and their results.
</details>

<details>
<summary><strong>doc_gen.py</strong></summary>

- **generate_docstrings:** Approval-gated docformatter run, results and errors logged.
- **handle_pending_doc_gen:** Approval and error logging for doc auto-generation.
- **docstring_coverage:** Returns codebase docstring coverage stats (not logged unless extended).
</details>

<details>
<summary><strong>pip_audit.py</strong></summary>

- **pip_audit:** Approval-gated dependency auditing for CVEs, audit results centrally logged.
- **handle_pending_pip_audit:** Waits for user approval, results are event-logged and error-logged.
- **handle_pip_audit_upgrade:** (Placeholder for automated dependency upgrades, to be approval-logged if implemented.)
</details>

<details>
<summary><strong>universal_installer.py</strong></summary>

- **suggest_installer:** Inspects project for installer files, offers to build a unified installer, event logged.
- **handle_pending_installer:** Builds script after approval, logs all script creation actions.
- **handle_pending_installer_run:** Runs installer script only with approval, run results logged.
</details>

<details>
<summary><strong>search.py</strong></summary>

- **code_search_ripgrep:** Approval-gated searches using ripgrep, context and results logged.
- **handle_pending_code_search:** Gated execution/printing for code search, all activity logged.
- **symbol_search_ctags:** (Optional) ctags-based search for symbols/functions, logs result summary.
</details>

<details>
<summary><strong>restore.py</strong></summary>

- **list_file_backups:** Central listing of all backups for a file, properly logged.
- **handle_pending_backup_restore:** Restores chosen backup on approval and logs restore activity.
</details>

<details>
<summary><strong>utils.py</strong></summary>

- **stream_progress_update:** Formats progress updates for streaming or interactive reporting.
- **split_text_chunks:** Splits large text into manageable chunked output (no logging needed).
</details>

---

## 🛡️ Best Practices

- **All destructive, sensitive, or potentially unsafe actions** (edit, install, run, call, restore) require explicit conversational approval.
- **All events, edits, errors, API calls, and executions** are centrally, securely logged via `RagisLogger` (timestamp, file/target, action, summary, with PII masking as configured).
- **No secrets, keys, tokens, or credentials** are written to log or file—use the `secure_vault.py` module (outside this folder) for secure PIN-locked storage and retrieval.
- **All tools are modular, auditable, and designed for continuous improvement and easy extension.**

---

## 🤝 Contributing & Support

For support, upgrades, or to suggest new tools:  
**Open an issue or submit a PR!**

---