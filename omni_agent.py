import os
import gradio as gr
import pandas as pd
import json
import logging
from dotenv import load_dotenv
from typing import Optional, List

# --- Constants ---
EMBEDDING_MODEL = "text-embedding-3-small"
MEMORY_COLLECTION = "memory"
DEFAULT_SESSION_ID = "default"
MAX_RETRIES = 3

# --- Custom Exceptions ---
class AgentError(Exception):
    pass

class EmbeddingError(AgentError):
    pass

class MemoryError(AgentError):
    pass

# --- Configuration ---
class Config:
    def __init__(self):
        self.embedding_model = EMBEDDING_MODEL
        self.memory_collection = MEMORY_COLLECTION
        self.session_id = DEFAULT_SESSION_ID
        self.api_key = os.getenv("OPENAI_API_KEY")
        
    def validate(self):
        if not self.api_key:
            raise ValueError("API key is not set")
        return True

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Load .env first (critical for API keys) ---
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set! Add it to your .env file.")

# --- LLM/Embedding imports (AFTER loading .env) ---
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from langchain.tools import Tool

# --- Agent Core Components ---
from agent_tools.task_manager import TaskManager, with_retry
from agent_tools.utils import stream_progress_update
from agent_tools.memory_store import MemoryStore
from agent_tools.memory_retriever import MemoryRetriever
from agent_tools.ragis_logger import RagisLogger

# --- File Operations Tools ---
from agent_tools.files import read_any_file, edit_or_create_file, handle_pending_file_change, list_file_backups, restore_file_backup
from agent_tools.code_exec import exec_python_code, exec_node_code
from agent_tools.ux_sandbox import (
    write_ui_file, handle_pending_ui_file, start_ui_sandbox_server, 
    vivaldi_ui_screenshot, test_ui_button
)
from agent_tools.shell import (
    run_shell_command, handle_pending_shell_cmd, run_pip_install, handle_pending_pip_install,
    run_npm_install, handle_pending_npm_install
)
from agent_tools.github_tools import (
    github_clone, handle_pending_github_clone, github_push, handle_pending_github_push
)
from agent_tools.api_requests import api_get, api_post, handle_pending_api_call
from agent_tools.doc_gen import generate_docstrings, handle_pending_doc_gen
from agent_tools.pip_audit import pip_audit, handle_pending_pip_audit
from agent_tools.universal_installer import (
    suggest_installer, handle_pending_installer, handle_pending_installer_run
)
from agent_tools.search import code_search_ripgrep, handle_pending_code_search, symbol_search_ctags
from agent_tools.restore import list_file_backups as restore__list_file_backups, handle_pending_backup_restore
from secure_vault import set_secret, get_secret, delete_secret, change_pin, load_vault

# --- Command Line Arguments ---
def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='Omni Agent')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--test', action='store_true', help='Run tests only')
    return parser.parse_args()

# --- Environment Check ---
def check_environment():
    required_env_vars = ['OPENAI_API_KEY', 'MEMORY_DB_PATH']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# --- System Checks ---
def check_system():
    """Run comprehensive system checks"""
    logger.info("\n=== System Check ===")
    logger.info(f"OpenAI API Key set: {'OPENAI_API_KEY' in os.environ}")
    logger.info(f"Current directory: {os.getcwd()}")
    
    # Check required directories
    required_dirs = ['datastore', 'agent_tools']
    dir_status = {d: os.path.exists(d) for d in required_dirs}
    logger.info("\n=== Directory Check ===")
    for d, exists in dir_status.items():
        logger.info(f"Directory {d} exists: {exists}")
    
    # Check required files
    required_files = ['synonyms.json', 'ragis_events.log']
    file_status = {f: os.path.exists(f) for f in required_files}
    logger.info("\n=== File Check ===")
    for f, exists in file_status.items():
        logger.info(f"File {f} exists: {exists}")

def test_embeddings():
    """Test embedding generation with various cases"""
    logger.info("\n=== Embedding System Test ===")
    test_cases = [
        ("Short test", "This is a short test message"),
        ("Longer test", "This is a longer test message that should generate a proper embedding"),
        ("Empty test", ""),
        ("Special chars", "Test with special characters: !@#$%^&*()_+")
    ]
    
    for name, text in test_cases:
        logger.info(f"\nTesting {name}:")
        embedding = get_embedding(text)
        if embedding:
            logger.info(f"✅ Success - Embedding length: {len(embedding)}")
        else:
            logger.error(f"❌ Failed for {name}")

def get_embedding(text: str) -> Optional[List[float]]:
    """Generate an embedding for the given text.
    
    Args:
        text (str): Input text to generate embedding for
        
    Returns:
        Optional[List[float]]: The generated embedding or None if failed
    """
    try:
        embedding = embed_fn.embed_query(text)
        logger.info(f"Generated embedding of length: {len(embedding)}")
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None

# --- Main Execution ---
def main():
    """Main entry point for the Omni Agent"""
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Check environment
        check_environment()
        
        # Run system checks
        check_system()
        
        if args.test:
            test_embeddings()
            return
            
        # Initialize configuration
        config = Config()
        config.validate()
        
        # Initialize embeddings
        embed_fn = OpenAIEmbeddings(
            model=config.embedding_model,
            openai_api_key=config.api_key
        )
        
        # Initialize agent components
        llm = ChatOpenAI(
            model="gpt-4.1-2025-04-14",
            temperature=0.4,
        )
        agent = create_react_agent(llm, [])
        
        # Initialize tools
        tools = [
            Tool(
                name="read_file",
                description="Read content from any file",
                func=read_any_file
            ),
            Tool(
                name="edit_file",
                description="Edit or create a file",
                func=edit_or_create_file
            ),
            Tool(
                name="run_code",
                description="Execute Python code",
                func=exec_python_code
            )
        ]
        
        # Initialize memory system
        memory_store = MemoryStore(
            db_path='datastore',
            collection_name=config.memory_collection,
            synonyms_path="synonyms.json",
            log_path="ragis_events.log"
        )
        
        # Initialize task manager
        from agent_tools.task_manager import TaskManager
        task_manager = TaskManager()
        
        # Initialize session state
        session_state = {
            'global_approval': False,
            'session_id': config.session_id
        }
        
        # Start the Gradio interface
        with gr.Blocks() as app:
            # ... Gradio interface code ...
            app.launch()
            
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise

if __name__ == "__main__":
    main()
    

# --- Session and agent state ---
session_unlocked = False
session_pin = None
session_state = {}
task_manager = TaskManager()

# --- Memory, Retriever, Logger ---
memory_store = MemoryStore(
    db_path='datastore',
    collection_name='memory',
    synonyms_path="synonyms.json",
    log_path="ragis_events.log"
)
memory_retriever = MemoryRetriever(
    db_path='datastore',
    collection_name='memory',
    synonyms_path="synonyms.json",
    log_path="ragis_events.log"
)
logger = RagisLogger(log_path="ragis_events.log", pii_mask_fields=['raw_text', 'query_text'])

# --- Main agent brain ---
llm = ChatOpenAI(
    model="gpt-4.1-2025-04-14",
    temperature=0.4,
)
agent = create_react_agent(llm, [])

def split_text_chunks(text, chunk_size=500):
    for i in range(0, len(text), chunk_size):
        yield text[i:i+chunk_size]

tools = [
    Tool("ReadAnyFile", lambda args: read_any_file(args, session_state), "Read any file under your user directory."),
    Tool("EditOrCreateFile", lambda args: edit_or_create_file(args, session_state), "Edit/create files in your user directory with approval."),
    Tool("ExecPythonCode", lambda args: exec_python_code(args, session_state), "Execute Python code in a sandbox, with approval."),
    Tool("ExecNodeCode", lambda args: exec_node_code(args, session_state), "Execute Node.js code with approval."),
    Tool("WriteUIFile", lambda args: write_ui_file(args, session_state), "Write or update HTML/CSS/JS in the UI sandbox."),
    Tool("RunShell", lambda args: run_shell_command(args, session_state), "Run shell commands, approval and safety-gated."),
    Tool("RunPipInstall", lambda args: run_pip_install(args, session_state), "Install Python packages via pip, approval required."),
    Tool("RunNpmInstall", lambda args: run_npm_install(args, session_state), "Install Node packages via npm, approval required."),
    Tool("GitHubClone", lambda args: github_clone(args, session_state, get_secret), "Clone repo to your user directory, approval/vault required."),
    Tool("GitHubPush", lambda args: github_push(args, session_state, get_secret), "Push repo to GitHub, approval/vault required."),
    Tool("APIGet", lambda args: api_get(args, session_state), "Approval-gated GET API call."),
    Tool("APIPost", lambda args: api_post(args, session_state), "Approval-gated POST API call."),
    Tool("CodeGenerateDocs", lambda args: generate_docstrings(args, session_state), "Generate HTML docs (pdoc3), approval required."),
    Tool("DocstringCoverage", lambda args: handle_pending_doc_gen(args, session_state), "Check docstring coverage/project health."),
    Tool("PipAudit", lambda args: pip_audit(args, session_state), "Audit for vulnerable dependencies, approval required."),
    Tool("SuggestInstaller", lambda args: suggest_installer(args, session_state), "Suggest/generate a universal install script."),
    Tool("CodeSearchRipgrep", lambda args: code_search_ripgrep(args, session_state), "Fuzzy, regex, and symbol project search, approval required."),
    Tool("ListFileBackups", lambda args: list_file_backups(args, session_state), "List backups for a given file."),
    Tool("RestoreFileBackup", lambda args: restore_file_backup(args, session_state), "Restore a file from backup, approval required."),
    Tool("VivaldiScreenshot", lambda args: vivaldi_ui_screenshot(**args), "Snapshot the UI sandbox via Vivaldi/Selenium."),
    Tool("TestUIButton", lambda args: test_ui_button(args, session_state), "Test/interact with sandboxed UI, log output & screenshots."),
]

def handle_pending_all(user_message, session_state, get_secret):
    auto_approve = session_state.get("global_approval", False)
    for handler in [
        handle_pending_file_change,
        handle_pending_ui_file,
        handle_pending_shell_cmd,
        handle_pending_pip_install,
        handle_pending_npm_install,
        handle_pending_github_clone,
        handle_pending_github_push,
        handle_pending_api_call,
        handle_pending_doc_gen,
        handle_pending_pip_audit,
        handle_pending_installer,
        handle_pending_installer_run,
        handle_pending_code_search,
        handle_pending_backup_restore,
    ]:
        try:
            result = handler(user_message, session_state)
            if result:
                return result
        except Exception as e:
            logger.log("handler_error", {"handler": handler.__name__, "error": str(e), "user_message": user_message})
    return None

def agent_chat(message: str, history: list = []):
    global session_unlocked, session_pin

    pin_entry = message.strip()
    if not session_unlocked:
        if pin_entry.lower().startswith("pin:"):
            pin_entry = pin_entry[4:].strip()
        if pin_entry.isdigit() and 5 <= len(pin_entry) <= 6:
            if load_vault(pin_entry) is not None:
                session_unlocked = True
                session_pin = pin_entry
                session_state["pin"] = pin_entry
                yield "🔓 PIN accepted! Vault unlocked. Ready to roll."
                return
            else:
                yield "❌ Incorrect PIN. Try again."
                return
        else:
            yield "🔒 Enter your 5-6 digit PIN:"
            return

    user_lc = message.lower()

    if user_lc in ("trust session", "enable global approval", "approve all"):
        session_state["global_approval"] = True
        yield "✅ Global approval enabled. No more confirmation prompts this session."
        return
    if user_lc in ("lock agent", "revoke global approval", "disable trust"):
        session_state["global_approval"] = False
        yield "🔒 Global approval disabled. Manual approvals required again."
        return

    if user_lc.startswith(('view file', 'show file', 'read file', 'cat ')):
        parts = message.split(' ', 2)
        if len(parts) < 3 or not parts[-1].strip():
            yield "❓ Please specify a file path to view."
            return
        file_path = parts[-1]
        yield read_any_file({"path": file_path}, session_state)
        return

    if user_lc.startswith(('search ', 'find ', 'grep ', 'symbol ')):
        parts = message.split(' ', 1)
        if len(parts) < 2 or not parts[1].strip():
            yield "❓ Please specify a search pattern."
            return
        pattern = parts[1]
        args = {"pattern": pattern, "project_dir": os.path.expanduser("~")}
        yield code_search_ripgrep(args, session_state)
        return

    if user_lc.startswith(("list backups", "show backups")):
        parts = message.split(' ', 2)
        if len(parts) < 3 or not parts[-1].strip():
            yield "❓ Please specify a file path to list backups for."
            return
        target_file = parts[-1]
        yield list_file_backups({"target_path": target_file}, session_state)
        return

    pending_result = handle_pending_all(message, session_state, lambda name, pin=None: get_secret(name, pin or session_pin))
    if pending_result:
        yield pending_result
        return

    secret_result = handle_pending_secret_workflow(message, session_state)
    if secret_result:
        yield secret_result
        return

    while task_manager.has_tasks():
        task = task_manager.next_task()
        yield f"🛠 Executing queued task: {task['action']}..."
        try:
            task_func = task["action"]
            task_args = task.get("params", {})
            output = task_func(task_args, session_state)
            yield output
        except Exception as e:
            logger.log("task_error", {"action": task['action'], "error": str(e), "params": task.get("params", {})})
            yield f"⚠️ Task {task['action']} failed: {e}"

    try:
        # --- MemoryStore: add only real embedding
        embedding = embed_fn.embed_query(message)
        if not isinstance(embedding, (list, tuple)) or not all(isinstance(x, (float, int)) for x in embedding):
            logger.log("embedding_error", {"input": message, "bad_embedding": str(embedding)})
            raise ValueError("Embedding must be a list of floats/ints. Got: " + str(embedding))
        memory_store.add_memory(
            raw_text=message,
            embedding=embedding,
            major_category="general",
            metatags=["user"],
            session_id=session_state.get("session_id", "default"),
        )

        context_metatags = []
        if history:
            for m in history[-25:]:
                if hasattr(m, "metatags"):
                    context_metatags.extend(m.metatags)
                elif isinstance(m, dict) and "metatags" in m:
                    context_metatags.extend(m["metatags"])

        recall_docs, metadatas, scores = memory_retriever.retrieve_memories(
            query_embedding=embedding,
            context_window_metatags=context_metatags,
            query_text=message,
        )

        messages = [{
            "role": "system",
            "content": (
                "You are Astrid, a witty, bold, clever AI dev/ops co-pilot. "
                "Collaborate confidently and directly. Secrets must use vaults only. "
                "Act decisively if authorized. Stream progress. Be transparent but upbeat on errors."
            )
        }]
        if history:
            messages.extend(history[-20:])
        messages.append({"role": "user", "content": message})

        result = agent.invoke({"messages": messages, "input": message})
        if isinstance(result, dict) and "messages" in result:
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    for chunk in split_text_chunks(msg.content, chunk_size=500):
                        yield chunk
                    logger.log("agent_response", {"input": message, "output": msg.content})
                    return
                elif isinstance(msg, dict) and msg.get("role") == "assistant":
                    for chunk in split_text_chunks(msg.get("content", ""), chunk_size=500):
                        yield chunk
                    logger.log("agent_response", {"input": message, "output": msg.get("content", "")})
                    return
        if isinstance(result, AIMessage):
            for chunk in split_text_chunks(result.content, chunk_size=500):
                yield chunk
            logger.log("agent_response", {"input": message, "output": result.content})
            return
        logger.log("agent_response", {"input": message, "output": str(result)})
        yield str(result)
    except Exception as e:
        logger.log("agent_error", {"input": message, "error": str(e)})
        yield f"🔥 Agent error: {e}"

def handle_pending_secret_workflow(message, session_state):
    if "store my github pat" in message.lower() or "add github pat" in message.lower():
        session_state['awaiting_secret_name'] = "GITHUB_PAT"
        return "I'll store your GitHub PAT securely as 'GITHUB_PAT' in the vault. Is that ok?"
    if session_state.get('awaiting_secret_name') and is_affirmative(message):
        secret_name = session_state.pop('awaiting_secret_name')
        pin = session_pin
        if get_secret(secret_name, pin):
            session_state['awaiting_secret_overwrite'] = secret_name
            return f"A secret named '{secret_name}' already exists. Overwrite/replace it? (yes/no)"
        else:
            session_state['pending_secret_store'] = secret_name
            return f"Please enter your PIN to store the secret '{secret_name}'."
    if session_state.get('awaiting_secret_overwrite') and is_affirmative(message):
        secret_name = session_state.pop('awaiting_secret_overwrite')
        session_state['pending_secret_store'] = secret_name
        return f"Please enter your PIN to update the secret '{secret_name}'."
    if session_state.get('pending_secret_store') and message.isdigit():
        session_state['pending_secret_pin'] = message
        secret_name = session_state['pending_secret_store']
        return f"PIN accepted. Now paste the value for '{secret_name}'."
    if session_state.get('pending_secret_pin') and session_state.get('pending_secret_store') and not message.isdigit():
        secret_name = session_state.pop('pending_secret_store')
        pin_code = session_state.pop('pending_secret_pin')
        set_secret(secret_name, message.strip(), pin_code)
        return f"🔐 Secret '{secret_name}' stored securely."
    return None

def is_affirmative(msg):
    affirm = [
        "yes", "ok", "allow", "approve", "go ahead", "sure", "yep", "confirmed",
        "trust it", "affirm", "green light", "make it so", "roger that"
    ]
    msg_low = msg.lower()
    return any(word in msg_low for word in affirm)

def read_action_log(log_file="agent_tools/ragis_events.log", max_rows=100):
    if not os.path.exists(log_file):
        return pd.DataFrame(columns=["Timestamp", "Action", "Target", "Summary"])
    rows = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                ev = json.loads(line)
                ts = ev.get("ts", "")
                action = ev.get("event_type", "")
                data = ev.get("data", {})
                target = (
                    data.get("abs_path") or data.get("file") or data.get("target") or
                    data.get("script_path") or data.get("project_path") or data.get("backup_path") or ""
                )
                summary = (
                    data.get("summary") or data.get("action") or data.get("status") or
                    data.get("cmd") or data.get("commit_msg") or data.get("stdout_excerpt") or data.get("error") or ""
                )
                rows.append([ts, action, target, summary])
            except Exception:
                continue
    return pd.DataFrame(rows[-max_rows:], columns=["Timestamp", "Action", "Target", "Summary"])

with gr.Blocks() as app:
    gr.Markdown("# Omni Agent (Pro Mode 🚀)")
    gr.Markdown(
        "🔒 PIN unlock required.\n\n"
        "✅ Approvals conversationally managed (or globally trusted).\n\n"
        "🛡 Secrets stored in vault only (no plaintext).\n\n"
        "🧠 Omni Agent now streams outputs, manages tasks, and logs actions live."
    )

    with gr.Row():
        with gr.Column(scale=3):
            chat = gr.ChatInterface(
                agent_chat,
                title="Omni Agent",
                description="Conversational AI Dev/UX/DevOps copilot — powered by LangGraph + Astrid brain.",
                type="messages"
            )
        with gr.Column(scale=1):
            action_log = gr.Dataframe(
                value=read_action_log(),
                headers=["Timestamp", "Action", "Target", "Summary"],
                datatype=["str", "str", "str", "str"],
                interactive=False,
                label="🕰 Action Timeline",
                visible=True,
            )

            def refresh_log():
                return read_action_log()

            refresh_btn = gr.Button("🔄 Refresh Action Log")
            refresh_btn.click(fn=refresh_log, outputs=action_log)

app.launch()