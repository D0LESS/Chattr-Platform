import customtkinter as ctk

def themed_button(master, text, command):
    return ctk.CTkButton(master, text=text, command=command)

def themed_entry(master, placeholder=''):
    return ctk.CTkEntry(master, placeholder_text=placeholder)