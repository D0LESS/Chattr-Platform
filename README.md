# OmniThreads
<<<<<<< HEAD

OmniThreads is a modern, extensible AI agent platform for developers, power users, and teams.  
It features a secure, multi-assistant chat UI, robust automation and retrieval tools, centralized event logging, vector search, and a modular backend—ready for desktop or cloud.
=======
OmniThreads - AI Assistant Platform

# 🚀 OmniThreads

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
git clone https://github.com/D0LESS/OmniThreads.git
cd OmniThreads\Installer
null.

python -m venv installer_env
installer_env\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
python installer.py
null.

📂 Project Structure Explicitly Defined
OmniThreads/
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
>>>>>>> 731f7590a81fd6ddad368e7945828c757c51f51d

---

## 🚀 Features

<<<<<<< HEAD
- **AOL-inspired Desktop UI:** Light/Dark modes, multi-assistant sidebar, persistent chat history.
- **Secure Authentication:** Email/password login (bcrypt), PIN-gated agent actions, and an encrypted vault for secrets.
- **Centralized Logging:** Every action, edit, install, restore, and run is logged in a central, structured audit log using `RagisLogger`, with PII masking.
- **Approval Gating:** All destructive/sensitive actions require conversational approval.
- **Robust Agent Tools:** Modular file editing, code execution, shell, API, GitHub, doc generation, search, backup/restore, pip/npm/install, and more—each with fine-grained approval and logging.
- **Vector Database:** Local ChromaDB (cloud-ready) with custom retrieval and tagging.
- **Installer Automation:** One-click setup for all dependencies and environments.
- **Extensible:** Add new tools, modules, or agents with minimal effort.
- **Secure Vault:** Secrets (API keys, tokens) are never written to disk—handled only via the encrypted vault module.
=======
Create explicitly new file clearly named exactly:
OmniThreads/Backend/logger.py
>>>>>>> 731f7590a81fd6ddad368e7945828c757c51f51d

---

## 🛠️ Quick Start

### Windows Setup

```sh
git clone https://github.com/D0LESS/OmniThreads.git
cd OmniThreads
python -m venv venv
venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
python omni_agent.py
```

---

## 📁 Project Structure

```
OmniThreads/
├── agent_tools/           # All agent tool modules (files, shell, code_exec, etc.) use RagisLogger
├── secure_vault.py        # PIN and encryption-gated vault storage for secrets (API keys, tokens, etc.)
├── data/vector_store/     # Local ChromaDB vector store (vectors+tags, not secrets)
├── omni_agent.py          # Main agent entrypoint (Gradio desktop/web app)
├── ragis_logger.py        # Central, structured logging for all agent actions
├── requirements.txt       # All Python dependencies
├── README.md              # This document
└── ...                    # Additional backend/frontend/runtime modules
```

---

## 📚 Dependencies & Stack

- **Backend:** Python 3.11+, ChromaDB, FastAPI (optional), SQLAlchemy (optional)
- **Frontend:** Gradio (app), CustomTkinter (optional), Pillow, python-dotenv
- **Agent/AI:** LangChain, LangGraph, OpenAI, ChromaDB
- **Dev Tools:** black, ruff, mypy, pytest, pip-audit, pdoc3, docformatter, pandas
- **Search/Symbols:** ripgrep, universal-ctags
- **Browser Automation:** selenium, chromedriver (for UI sandbox/screenshot features)
- **Other:** cryptography, requests

**Note:**  
For code search/symbol tools, install ripgrep and universal-ctags via your system package manager:

- **Windows:** `choco install ripgrep universal-ctags`
- **Mac:** `brew install ripgrep ctags`
- **Linux:** `apt install ripgrep universal-ctags`

<<<<<<< HEAD
---

## ✅ Tested Platforms

- Windows 10/11
- Python 3.11+

---

## ⚡️ Usage

- **PIN Unlock:** All agent actions require PIN unlock for security.
- **Approval Gating:** All file/code/shell/api/git/install actions require conversational approval (unless global approval enabled).
- **Action Logging:** Every sensitive or stateful action is logged via RagisLogger, with PII masking as appropriate.
- **Secrets:** All API keys/tokens managed only via `secure_vault.py`—never written to logs or disk in plain text.
- **Audit Log:** All significant actions are visible, queryable, and ready for drift/backward analysis.

---

## 🧩 Extending OmniThreads

Add new agent tools by creating a module in `agent_tools/` and registering it in `omni_agent.py`.

All tools must:
- Require explicit approval for destructive/sensitive actions.
- Log every access, edit, install, API call, and restore via RagisLogger.
- Use the secure vault for secrets, never config files or logs.

---

## 🛡 Troubleshooting

- **Python Version:** Ensure Python 3.11+ is installed (`python -V`).
- **ripgrep/ctags:** Use your package manager for search/symbol commands if needed.
- **Chromedriver:** Download and add to PATH for UI sandbox/screenshot tools.
- **.env:** Copy `.env.example` to `.env` and supply all needed OpenAI and system credentials.
- **Vault or PIN issues:** See `secure_vault.py` for vault PIN resets and secret recovery.

---

## 🌟 Contributing

1. Fork the repo.
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to your fork: `git push origin feature/my-feature`
5. Open a Pull Request!

Pull Requests and issues are welcome!

---

## 🔥 Author

Maintained by **D0LESS**.  
Feedback, suggestions, and feature requests are always welcome!

---

> All agent actions, edits, restores, and installs are always gated, logged, and auditable.  
> OmniThreads is ready to use, extend, and trust. 🚀
=======
Your project is explicitly at the finish line—beautifully and clearly executed! Let’s explicitly handle this quick final check now. 🎉
>>>>>>> 731f7590a81fd6ddad368e7945828c757c51f51d
