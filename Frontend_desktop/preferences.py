import os
from dotenv import load_dotenv, set_key

pref_file = ".env"

def save_pref(key, value):
    set_key(pref_file, key, value)

def get_pref(key, default=None):
    load_dotenv(pref_file)
    return os.getenv(key, default)