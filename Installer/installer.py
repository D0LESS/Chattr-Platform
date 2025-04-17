import subprocess, sys, os, shutil
from pathlib import Path
from dotenv import set_key

BASE_DIR = Path(__file__).resolve().parent.parent
backend_path = BASE_DIR / "Backend"
frontend_path = BASE_DIR / "Frontend_desktop"
installer_path = Path(__file__).resolve().parent

def create_venv(path):
    venv_path = path / "venv"
    python_exec = sys.executable
    subprocess.run([python_exec, "-m", "venv", str(venv_path)], check=True)
    pip_exec = venv_path / "Scripts" / "pip.exe"
    subprocess.run([str(pip_exec), "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(pip_exec), "install", "-r", str(path / "requirements.txt")], check=True)

def setup_backend():
    print("🚀 Setting up backend explicitly...")
    create_venv(backend_path)
    print("✅ Backend setup complete explicitly.")

def setup_frontend():
    print("🎨 Setting up frontend explicitly...")
    create_venv(frontend_path)
    print("✅ Frontend setup complete explicitly.")

def setup_vector_store():
    data_path = BASE_DIR / "data/vector_store"
    print("🔍 Configuring local ChromaDB explicitly at:", data_path)
    data_path.mkdir(parents=True, exist_ok=True)
    print("✅ Local ChromaDB configured explicitly.")

def create_shortcut():
    shortcut_path = Path.home() / "Desktop" / "Chattr-Installer.bat"
    print(f"📌 Creating desktop shortcut explicitly at {shortcut_path}")
    with open(shortcut_path, 'w') as shortcut:
        shortcut.write(f'@echo off\ncd /d "{BASE_DIR}\\Frontend_desktop"\n"{BASE_DIR}\\Frontend_desktop\\venv\\Scripts\\python.exe" app.py\npause')
    print("✅ Shortcut created clearly on Desktop explicitly.")

def main_installer():
    print("🛠️ Chattr Installer explicitly beginning...")
    setup_backend()
    setup_vector_store()
    setup_frontend()
    create_shortcut()

    api_key = input("🔑 Enter your default LLM API Key explicitly: ").strip()
    set_key(str(BASE_DIR / "Frontend_desktop" / ".env"), "API_KEY", api_key)

    print("\n🚀 Installation explicitly and completely successful!")
    input("Press Enter explicitly to finish clearly and exit.")

if __name__ == "__main__":
    main_installer()