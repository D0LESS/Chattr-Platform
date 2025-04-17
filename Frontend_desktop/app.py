import customtkinter as ctk
from auth import authenticate_user, add_user, session
from ui_components import themed_button, themed_entry
from preferences import get_pref, save_pref
from chroma_db import query_documents, add_document

ctk.set_appearance_mode(get_pref("THEME", "dark"))
ctk.set_default_color_theme("blue")

class Chattr(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry('950x650')
        self.title('Chattr - AOL Inspired Chat')
        self.user_email = None
        
        self.login_frame = ctk.CTkFrame(self)
        self.chat_frame