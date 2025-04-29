from cryptography.fernet import Fernet, InvalidToken
import os
import base64
import json
import hashlib
from datetime import datetime
from agent_tools.ragis_logger import RagisLogger

VAULT_FILE = "secrets.vault"
VAULT_SALT_FILE = "secrets.salt"
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=['name', 'value', 'pin'])

def get_salt():
    if os.path.exists(VAULT_SALT_FILE):
        with open(VAULT_SALT_FILE, "rb") as f:
            return f.read()
    else:
        new_salt = os.urandom(16)
        with open(VAULT_SALT_FILE, "wb") as f:
            f.write(new_salt)
        return new_salt

def get_fernet(pin: str) -> Fernet:
    salt = get_salt()
    key = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 200_000, dklen=32)
    return Fernet(base64.urlsafe_b64encode(key))

def load_vault(pin):
    f = get_fernet(pin)
    if not os.path.exists(VAULT_FILE):
        logger.log("vault_load_empty", {"pin": pin})
        return {}
    with open(VAULT_FILE, "rb") as vf:
        enc = vf.read()
    try:
        dec = f.decrypt(enc)
        logger.log("vault_load", {"pin": pin, "status": "success"})
        return json.loads(dec)
    except InvalidToken:
        logger.log("vault_load_failed", {"pin": pin, "error": "InvalidToken"})
        print("Error: Invalid PIN provided.")
        return None
    except Exception as e:
        logger.log("vault_load_failed", {"pin": pin, "error": str(e)})
        print(f"Error loading vault: {e}")
        return None

def save_vault(secrets, pin):
    f = get_fernet(pin)
    try:
        enc = f.encrypt(json.dumps(secrets).encode())
        with open(VAULT_FILE, "wb") as vf:
            vf.write(enc)
        logger.log("vault_save", {"pin": pin, "status": "success", "keys": list(secrets.keys())})
    except Exception as e:
        logger.log("vault_save_failed", {"pin": pin, "error": str(e)})
        print(f"Error saving vault: {e}")

def set_secret(name, value, pin):
    if not name or not isinstance(name, str):
        logger.log("set_secret_failed", {"name": name, "pin": pin, "error": "invalid name"})
        print("Error: Secret name must be a non-empty string.")
        return
    if not value or not isinstance(value, str):
        logger.log("set_secret_failed", {"name": name, "pin": pin, "error": "invalid value"})
        print("Error: Secret value must be a non-empty string.")
        return
    secrets = load_vault(pin) or {}
    timestamp = datetime.now().isoformat()
    entry = secrets.get(name)
    if entry and 'current' in entry:
        # Move current value to archive before updating
        if 'archive' not in entry:
            entry['archive'] = []
        entry['archive'].insert(0, {"value": entry['current'], "timestamp": entry.get("last_update", timestamp)})
    else:
        entry = {"archive": []}
    entry['current'] = value
    entry['last_update'] = timestamp
    secrets[name] = entry
    save_vault(secrets, pin)
    logger.log("set_secret", {"name": name, "pin": pin, "status": "set", "timestamp": timestamp})

def get_secret(name, pin, archived=False, version=0):
    secrets = load_vault(pin) or {}
    entry = secrets.get(name)
    if not entry:
        logger.log("get_secret_failed", {"name": name, "pin": pin, "error": "not found"})
        return None
    if not archived:
        logger.log("get_secret", {"name": name, "pin": pin, "archived": archived, "status": "found"})
        return entry.get('current')
    if 'archive' in entry and len(entry['archive']) > version:
        logger.log("get_secret_archive", {"name": name, "pin": pin, "version": version, "status": "found"})
        return entry['archive'][version]['value']
    logger.log("get_secret_archive_failed", {"name": name, "pin": pin, "version": version, "error": "not found"})
    return None

def get_secret_archive_list(name, pin):
    secrets = load_vault(pin) or {}
    entry = secrets.get(name)
    if entry and 'archive' in entry:
        logger.log("get_secret_archive_list", {"name": name, "pin": pin, "status": "found"})
        return entry['archive']
    logger.log("get_secret_archive_list_failed", {"name": name, "pin": pin, "error": "not found"})
    return []

def restore_secret(name, pin, version=0):
    secrets = load_vault(pin) or {}
    entry = secrets.get(name)
    if not entry or 'archive' not in entry or len(entry['archive']) <= version:
        logger.log("restore_secret_failed", {"name": name, "pin": pin, "version": version, "error": "invalid archive"})
        print("Error: Invalid archive version or secret does not exist.")
        return False
    timestamp = datetime.now().isoformat()
    # Swap archive[version] to 'current', move current to archive[0]
    archive_entry = entry['archive'].pop(version)
    if 'current' in entry:
        entry['archive'].insert(0, {"value": entry['current'], "timestamp": entry.get("last_update", timestamp)})
    entry['current'] = archive_entry['value']
    entry['last_update'] = timestamp
    secrets[name] = entry
    save_vault(secrets, pin)
    logger.log("restore_secret", {"name": name, "pin": pin, "version": version, "status": "restored", "timestamp": timestamp})
    return True

def delete_secret(name, pin, erase_archive=False):
    secrets = load_vault(pin) or {}
    if name in secrets:
        if erase_archive:
            del secrets[name]
            logger.log("delete_secret", {"name": name, "pin": pin, "erase_archive": True})
        else:
            # Just mark as deleted but retain archive for possible restore
            entry = secrets[name]
            entry['deleted'] = True
            entry['deleted_date'] = datetime.now().isoformat()
            secrets[name] = entry
            logger.log("delete_secret", {"name": name, "pin": pin, "erase_archive": False})
        save_vault(secrets, pin)
        return True
    logger.log("delete_secret_failed", {"name": name, "pin": pin, "error": "not found"})
    return False

def change_pin(old_pin, new_pin):
    if not new_pin.isdigit() or not (5 <= len(new_pin) <= 6):
        logger.log("pin_change_failed", {"old_pin": old_pin, "new_pin": new_pin, "error": "invalid pin"})
        print("Error: New PIN must be numeric and 5-6 digits long.")
        return False
    secrets = load_vault(old_pin)
    if secrets is None:
        logger.log("pin_change_failed", {"old_pin": old_pin, "new_pin": new_pin, "error": "invalid old pin"})
        print("Error: Invalid old PIN.")
        return False
    save_vault(secrets, new_pin)
    logger.log("pin_change", {"old_pin": old_pin, "new_pin": new_pin, "status": "success"})
    return True