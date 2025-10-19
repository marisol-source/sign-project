# ui.py

import tkinter as tk
from tkinter import scrolledtext

def setup_tkinter_window():
    root = tk.Tk()
    root.title("Texto Reconocido - Original y Corregido Automáticamente")
    root.geometry("800x300")
    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=90, height=15)
    text_area.pack(padx=10, pady=10)
    text_area.insert(tk.END, "Presiona 'I' para iniciar/pausar la interpretación...\n\n")
    text_area.config(state=tk.DISABLED)
    return root, text_area

def overwrite_text(text_area, original_text, corrected_text, live_word, live_letter, live_confidence):
    text_area.config(state=tk.NORMAL)
    text_area.delete("1.0", tk.END)
    
    if original_text.strip():
        text_area.insert(tk.END, "TEXTO ORIGINAL:\n")
        text_area.insert(tk.END, original_text)
        text_area.insert(tk.END, "\n\n")
    
    if corrected_text.strip():
        text_area.insert(tk.END, "TEXTO CORREGIDO (Automático):\n")
        text_area.insert(tk.END, corrected_text)
        text_area.insert(tk.END, "\n\n")
    
    status_line = f"[Palabra actual] = {live_word if live_word else '—'}"
    if live_letter:
        status_line += f"    |    [Letra en vivo] = {live_letter} ({live_confidence*100:.1f}%)"
    else:
        status_line += "    |    [Letra en vivo] = —"
    
    text_area.insert(tk.END, status_line)
    text_area.see(tk.END)
    text_area.config(state=tk.DISABLED)
