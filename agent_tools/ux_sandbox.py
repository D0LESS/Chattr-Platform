import os
import shutil
import tempfile
import subprocess
import sys
import datetime
from agent_tools.ragis_logger import RagisLogger

# Central logger for all UI sandbox actions
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=['abs_path', 'backup_path', 'temp_path', 'script_path', 'url', 'filename'])

def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def write_ui_file(args, session_state):
    """Prepare to write a UI file, requiring user approval and making a backup if needed."""
    rel_path = args.get("path", "")
    content = args.get("content", "")
    user_home = os.path.expanduser("~")
    sandbox_dir = os.path.join(user_home, "ui_sandbox")
    os.makedirs(sandbox_dir, exist_ok=True)
    abs_path = os.path.abspath(os.path.join(sandbox_dir, rel_path))
    # Always backup before overwrite
    if os.path.exists(abs_path):
        backup_path = f"{abs_path}.bak.{get_timestamp()}"
        shutil.copy2(abs_path, backup_path)
        logger.log("ui_file_backup", {"abs_path": abs_path, "backup_path": backup_path})
    else:
        backup_path = None
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmpf:
        tmpf.write(content)
        temp_path = tmpf.name
    session_state['pending_ui_file'] = (abs_path, content, backup_path, temp_path)
    logger.log("ui_file_prepare", {
        "abs_path": abs_path,
        "backup_path": backup_path,
        "temp_path": temp_path,
        "snippet": content[:80]
    })
    return (
        f"I'm about to create/update:\n{abs_path}\n"
        f"Here's the beginning: {content[:80]}...\n"
        f"Backup: {backup_path if backup_path else 'New file.'}\n"
        "Is this OK? (yes/ok/approve or no)"
    )

def handle_pending_ui_file(user_message, session_state):
    """Handle user approval or denial for a pending UI file write."""
    def is_affirmative(msg):
        affirm = ["yes", "ok", "allow", "approve", "go ahead"]
        return any(word in msg.lower() for word in affirm)
    if session_state.get('pending_ui_file'):
        abs_path, content, backup_path, temp_path = session_state['pending_ui_file']
        if is_affirmative(user_message):
            try:
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.log("ui_file_written", {
                    "abs_path": abs_path, "backup_path": backup_path
                })
            except Exception as e:
                logger.log("ui_file_write_fail", {
                    "abs_path": abs_path, "backup_path": backup_path, "error": str(e)
                })
                session_state.pop('pending_ui_file')
                try:
                    os.remove(temp_path)
                except Exception as cleanup_err:
                    logger.log("tempfile_remove_fail", {"file": temp_path, "error": str(cleanup_err)})
                return f"Error writing UI file: {e}"
            session_state.pop('pending_ui_file')
            try:
                os.remove(temp_path)
            except Exception as cleanup_err:
                logger.log("tempfile_remove_fail", {"file": temp_path, "error": str(cleanup_err)})
            return f"UI file '{abs_path}' saved. (Backup: {backup_path})"
        else:
            session_state.pop('pending_ui_file')
            try:
                os.remove(temp_path)
            except Exception as cleanup_err:
                logger.log("tempfile_remove_fail", {"file": temp_path, "error": str(cleanup_err)})
            logger.log("ui_file_cancelled", {"abs_path": abs_path})
            return "UI file write not approved. Cancelling."
    return None

def start_ui_sandbox_server(sandbox_dir=None, port=7847):
    """Start a local HTTP server for the UI sandbox directory."""
    sandbox_dir = sandbox_dir or os.path.join(os.path.expanduser("~"), "ui_sandbox")
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        s.close()
        subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--directory", sandbox_dir],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.log("ui_sandbox_server_start", {"sandbox_dir": sandbox_dir, "port": port})
    except OSError:
        s.close()
        logger.log("ui_sandbox_server_launch_error", {"sandbox_dir": sandbox_dir, "port": port})
    url = f"http://127.0.0.1:{port}/"
    return url

def vivaldi_ui_screenshot(url="http://127.0.0.1:7847/", filename="ui_screenshot.png", vivaldi_path="C:\\Program Files\\Vivaldi\\Application\\vivaldi.exe"):
    """Take a screenshot of the UI sandbox using Vivaldi in headless mode."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    options = Options()
    options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    if not os.path.exists(vivaldi_path):
        return f"Vivaldi not found at {vivaldi_path}."
    options.binary_location = vivaldi_path
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        driver.save_screenshot(filename)
        logger.log("ui_screenshot", {"filename": filename, "url": url})
        return f"Vivaldi screenshot taken and saved as {filename}."
    except Exception as e:
        logger.log("ui_screenshot_error", {"filename": filename, "url": url, "error": str(e)})
        return f"Screenshot error: {e}"
    finally:
        if driver:
            driver.quit()

def test_ui_button(args, session_state):
    """Test clicking a button in the UI sandbox using Selenium."""
    selector = args.get("button_selector") or "button"
    url = args.get("sandbox_url") or "http://127.0.0.1:7847/"
    vivaldi_path = args.get("vivaldi_path", "C:\\Program Files\\Vivaldi\\Application\\vivaldi.exe")
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    options = Options()
    options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    if not os.path.exists(vivaldi_path):
        return f"Vivaldi not found at {vivaldi_path}."
    options.binary_location = vivaldi_path
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        btn = driver.find_element("css selector", selector)
        btn.click()
        result_text = driver.page_source
        screenshot_path = f"test_btn_{get_timestamp()}.png"
        driver.save_screenshot(screenshot_path)
        logger.log("ui_btn_test", {
            "url": url, "selector": selector, "screenshot": screenshot_path
        })
        return f"Button '{selector}' clicked. Screenshot: {screenshot_path}\nPost-click HTML (truncated):\n{result_text[:900]}"
    except Exception as e:
        logger.log("ui_btn_test_error", {
            "url": url, "selector": selector, "error": str(e)
        })
        return f"Button test error: {e}"
    finally:
        if driver:
            driver.quit()