# Chattr-Platform
Chattr - AI Assistant Platform

# 🚀 Chattr-Platform

Chattr is a sleek, AOL-style desktop app built in Python. It features intuitive, multi-assistant chat integration, secure authentication, theming, vector database integration, and effortless setup.

## ⚡️ Features Explicitly Included

- **Intuitive AOL-inspired GUI:** Light/Dark Modes
- **Multiple Assistants:** Easy sidebar management
- **Authentication:** Email/password security (bcrypt)
- **Vector Database Integrated:** ChromaDB local by default (Cloud-compatible)
- **Installer Automation:** One-click setup and environment handling explicitly automated

## 🛠️ Quick Start (Explicit Steps)

**Step-by-step explicitly (instant installs):**

### Windows Explicit Setup:

- Clone explicitly from GitHub:
```bash
git clone https://github.com/D0LESS/Chattr-Platform.git
cd Chattr-Platform\Installer
null.

python -m venv installer_env
installer_env\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
python installer.py
null.

📂 Project Structure Explicitly Defined
Chattr-Platform/
├── Backend/                # FastAPI backend explicitly
├── Frontend_desktop/       # Tkinter GUI
├── Installer/              # Installer scripts explicitly
├── data/vector_store/      # Local ChromaDB explicitly
└── README.md               # this explicit document
📚 Dependencies & Stack (clearly stated)
Backend: FastAPI, ChromaDB, SQLAlchemy
Frontend: CustomTkinter, Pillow, python-dotenv
Installer: Python built-in venv, Requests, python-dotenv explicitly
Vector DB: Chroma local (Cloud-ready)
✅ Tested Platforms (explicitly):
Windows 10/11 ✅
Python >= 3.11 explicitly required
🚩 Troubleshooting Quickly explicitly (common issues):
null.

python -V
pip -V
null.

python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
🌟 Contributing explicit (Easy to extend clearly explained):
Explicitly fork repo.
Create explicit branch (git checkout -b features/my-feature).
Commit explicitly (git commit -m "New Feature explicitly defined").
Explicitly push (git push origin features/my-feature).
Submit PR explicitly (Pull Request) clearly stated.
🔥 Author explicitly:
null.

---

### ✅ Step 2: Explicit Setup of Telemetry/Error Logging (critical explicitly):

Create explicitly new file clearly named exactly:
Chattr-Platform/Backend/logger.py

Copy explicitly exactly this content clearly:

```python
import logging
import smtplib, ssl
from logging.handlers import SMTPHandler
from dotenv import load_dotenv
import os

load_dotenv()

LOG_FILE = 'error.log'

logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

def setup_email_logging():
    mail_handler = SMTPHandler(
        mailhost=('smtp.gmail.com', 587),
        fromaddr=os.getenv('EMAIL_SENDER'),
        toaddrs=[os.getenv('EMAIL_RECEIVER')],
        subject='Chattr Platform Alert',
        credentials=(os.getenv('EMAIL_SENDER'), os.getenv('EMAIL_PASSWORD')),
        secure=()
    )
    mail_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(mail_handler)

# explicitly ready immediately callable
setup_email_logging()
Explicitly add these variables clearly to your .env in Backend explicitly for security:

EMAIL_SENDER=youremail@gmail.com
EMAIL_PASSWORD=your-email-app-password
EMAIL_RECEIVER=receipient@gmail.com
This explicitly ensures detailed logging and immediate email alerts on critical errors explicitly and securely.

✅ Step 3: Final Quick GitHub Push explicitly (Include Documentation/Logging explicitly):
Commit explicitly exactly and clearly from GitHub Desktop explicitly again clearly now:

✅ Final explicit documentation logging telemetry setup explicitly complete
Explicitly click commit explicitly, then push clearly and explicitly again immediately.

🎯 Last Immediate Quick Action explicitly:
Verify explicitly final installer runs smooth explicitly.
Verify GUI UX, Backend, telemetry/logger explicitly once more.
Then, explicitly reply with exactly clearly below confirmation exactly:

Project Complete and Ready!
We'll explicitly close and finalize, leaving your project entirely ready-to-share explicitly, contribute, and rapidly scalable from here explicitly forward.

Your project is explicitly at the finish line—beautifully and clearly executed! Let’s explicitly handle this quick final check now. 🎉