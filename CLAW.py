import tkinter as tk
from tkinter import filedialog, messagebox, Scrollbar, StringVar, ttk
from collections import defaultdict
from tkinter.font import Font
from PIL import Image, ImageTk
from datetime import datetime
import re
import chardet
import os
import shutil

ERROR_KEYWORDS = [
    "error", "fail", "exception", "critical", "fatal", "alert", "severe",
    "mismatch", "invalid", "break", "damage", "not found", "missing", "unable",
    "expired", "disconnect", "abort", "terminate", "wrong", "out of memory","failed"
]

LANGUAGES = {
    "English": {
        "Choose File": "Choose Log File",
        "No errors found in the selected file.": "No errors found in the selected file.",
        "Search": "Search",
        "Errors Found:": "Errors Found:"
    },
    "German": {
        "Choose File": "Logdatei wählen",
        "No errors found in the selected file.": "Keine Fehler in der ausgewählten Datei gefunden.",
        "Search": "Suche",
        "Errors Found:": "Gefundene Fehler:"
    },
    "Polish": {
        "Choose File": "Wybierz plik z logami",
        "No errors found in the selected file.": "Nie znaleziono błędów w wybranym pliku.",
        "Search": "Szukaj",
        "Errors Found:": "Znalezione błędy:"
    },
    "French": {
        "Choose File": "Choisir le fichier de journal",
        "No errors found in the selected file.": "Aucune erreur trouvée dans le fichier sélectionné.",
        "Search": "Chercher",
        "Errors Found:": "Erreurs trouvées:"
    },
}

current_language = LANGUAGES["English"]
current_file_path = None 



def set_language(lang):
    global current_language
    current_language = LANGUAGES[lang]
    search_button.config(text=current_language["Search"])
    error_count_label.config(text=current_language["Errors Found:"] + " 0")

def highlight_keywords():
    for keyword in ERROR_KEYWORDS:
        start = "1.0"
        while True:
            start = text_area.search(keyword, start, tk.END, nocase=True)
            if not start:
                break
            end = f"{start}+{len(keyword)}c"
            text_area.tag_add("keyword_highlight", start, end)
            start = end

def open_file():
    global current_file_path
    file_path = filedialog.askopenfilename(filetypes=[("All files", "*.*"),("Text files", "*.txt;*.log")])
    if file_path:
        current_file_path = file_path
        
        # Wykrywanie kodowania pliku
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
        
        encoding = result['encoding']
        
        # Czyszczenie zawartości text_area oraz text_file_text_area przed wczytaniem nowego pliku
        text_area.delete("1.0", tk.END)
        text_file_text_area.delete("1.0", tk.END)
        
        # Wczytywanie całego pliku do zakładki "Text File"
        with open(file_path, 'r', encoding=encoding) as file:
            content = file.read()
            text_file_text_area.insert(tk.END, content)
        
        # Filtruj plik za pomocą ERROR_KEYWORDS i wyświetl wyniki w text_area (zakładka "Log File")
        with open(file_path, 'r', encoding=encoding) as file:
            for line in file:
                if any(keyword.lower() in line.lower() for keyword in ERROR_KEYWORDS):
                    text_area.insert(tk.END, line)
                    text_area.insert(tk.END, "----------------\n")  # Dodawanie separatora
            highlight_keywords()

def text_file_search_logs():
    search_term = search_var.get()
    if search_term:
        text_file_text_area.tag_remove("search_highlight", "1.0", tk.END)
        start_idx = "1.0"
        first_occurrence = None
        while True:
            start_idx = text_file_text_area.search(search_term, start_idx, nocase=True, stopindex=tk.END)
            if not start_idx:
                break
            if not first_occurrence:
                first_occurrence = start_idx
            end_idx = f"{start_idx}+{len(search_term)}c"
            text_file_text_area.tag_add("search_highlight", start_idx, end_idx)
            start_idx = end_idx
        if first_occurrence:
            text_file_text_area.see(first_occurrence)
            
def highlight_text_file_criteria(criteria):
    for keyword in criteria:
        start = "1.0"
        while True:
            start = text_file_text_area.search(keyword, start, tk.END, nocase=True)
            if not start:
                break
            end = f"{start}+{len(keyword)}c"
            text_file_text_area.tag_add("criteria_highlight", start, end)
            text_file_text_area.tag_configure("criteria_highlight", foreground="green")  # Konfiguracja stylu dla podświetlenia
            start = end

    text_file_text_area.see("1.0")

def search_logs():
    search_term = search_var.get()
    if search_term:
        text_area.tag_remove("search_highlight", "1.0", tk.END)
        start_idx = "1.0"
        first_occurrence = None
        while True:
            start_idx = text_area.search(search_term, start_idx, nocase=True, stopindex=tk.END)
            if not start_idx:
                break
            if not first_occurrence:
                first_occurrence = start_idx
            end_idx = f"{start_idx}+{len(search_term)}c"
            text_area.tag_add("search_highlight", start_idx, end_idx)
            start_idx = end_idx
        if first_occurrence:
            text_area.see(first_occurrence)

def search_logs_by_criteria():
    global current_file_path
    if not current_file_path:
        messagebox.showwarning("Warning", "Please select a log file first.")
        return

    start_date = start_date_var.get()
    end_date = end_date_var.get()
    selected_levels = [level for level, var in level_vars.items() if var.get()]

    text_area.delete("1.0", tk.END)

    # Wykrywanie kodowania pliku
    with open(current_file_path, 'rb') as log_file:
        result = chardet.detect(log_file.read(10000))  # wczytuje tylko pierwsze 10 000 bajtów do wykrycia kodowania
    
    encoding = result['encoding']

    with open(current_file_path, 'r', encoding=encoding) as log_file:
        for line in log_file:
            if any(keyword.lower() in line.lower() for keyword in selected_levels):
                if start_date and end_date:
                    date_pattern = r"\d{4}-\d{2}-\d{2}"  # Assuming the date format is YYYY-MM-DD
                    date_matches = re.findall(date_pattern, line)
                    if date_matches:
                        log_date = date_matches[0]
                        if start_date <= log_date <= end_date:
                            text_area.insert(tk.END, line)
                            insert_divider()
                else:
                    text_area.insert(tk.END, line)
                    insert_divider()

    highlight_keywords()
    highlight_criteria(selected_levels)
    
    
def search_logs_by_datetime():
    global current_file_path
    if not current_file_path:
        messagebox.showwarning("Warning", "Please select a log file first.")
        return

    search_date = start_date_var.get()
    search_time = end_date_var.get()
    selected_levels = [level for level, var in level_vars.items() if var.get()]

    text_area.delete("1.0", tk.END)

    # Wykrywanie kodowania pliku
    with open(current_file_path, 'rb') as log_file:
        result = chardet.detect(log_file.read(10000))  # wczytuje tylko pierwsze 10 000 bajtów do wykrycia kodowania
    
    encoding = result['encoding']

    with open(current_file_path, 'r', encoding=encoding) as log_file:
        for line in log_file:
            if any(keyword.lower() in line.lower() for keyword in selected_levels):
                if search_date and search_time:
                    date_pattern = r"\d{4}-\d{2}-\d{2}"
                    time_pattern = r"\d{2}:\d{2}"
                    date_matches = re.findall(date_pattern, line)
                    time_matches = re.findall(time_pattern, line)
                    if date_matches and time_matches:
                        log_date = date_matches[0]
                        log_time = time_matches[0]
                        if search_date == log_date and search_time == log_time:
                            text_area.insert(tk.END, line)
                            insert_divider()

                            start_date_pos = text_area.search(log_date, "1.0", tk.END)
                            end_date_pos = f"{start_date_pos}+{len(log_date)}c"
                            text_area.tag_add("date_highlight", start_date_pos, end_date_pos)

                            start_time_pos = text_area.search(log_time, "1.0", tk.END)
                            end_time_pos = f"{start_time_pos}+{len(log_time)}c"
                            text_area.tag_add("time_highlight", start_time_pos, end_time_pos)

                elif search_date:
                    date_pattern = r"\d{4}-\d{2}-\d{2}"
                    date_matches = re.findall(date_pattern, line)
                    if date_matches:
                        log_date = date_matches[0]
                        if search_date == log_date:
                            text_area.insert(tk.END, line)
                            insert_divider()

                            start_date_pos = text_area.search(log_date, "1.0", tk.END)
                            end_date_pos = f"{start_date_pos}+{len(log_date)}c"
                            text_area.tag_add("date_highlight", start_date_pos, end_date_pos)

                elif search_time:
                    time_pattern = r"\d{2}:\d{2}"
                    time_matches = re.findall(time_pattern, line)
                    if time_matches:
                        log_time = time_matches[0]
                        if search_time == log_time:
                            text_area.insert(tk.END, line)
                            insert_divider()

                            start_time_pos = text_area.search(log_time, "1.0", tk.END)
                            end_time_pos = f"{start_time_pos}+{len(log_time)}c"
                            text_area.tag_add("time_highlight", start_time_pos, end_time_pos)

                else:
                    text_area.insert(tk.END, line)
                    insert_divider()

    highlight_keywords()
    highlight_criteria(selected_levels)
        
def text_file_search_logs_by_datetime():
    global current_file_path
    if not current_file_path:
        messagebox.showwarning("Warning", "Please select a log file first.")
        return

    search_date = start_date_var.get()
    search_time = end_date_var.get()
    selected_levels = [level for level, var in level_vars.items() if var.get()]

    text_file_text_area.delete("1.0", tk.END)

    # Wykrywanie kodowania pliku
    with open(current_file_path, 'rb') as log_file:
        result = chardet.detect(log_file.read(10000))  # wczytuje tylko pierwsze 10 000 bajtów do wykrycia kodowania
    
    encoding = result['encoding']

    with open(current_file_path, 'r', encoding=encoding) as log_file:
        for line in log_file:
            if any(keyword.lower() in line.lower() for keyword in selected_levels):
                if search_date and search_time:
                    date_pattern = r"\d{4}-\d{2}-\d{2}"
                    time_pattern = r"\d{2}:\d{2}"
                    date_matches = re.findall(date_pattern, line)
                    time_matches = re.findall(time_pattern, line)
                    if date_matches and time_matches:
                        log_date = date_matches[0]
                        log_time = time_matches[0]
                        if search_date == log_date and search_time == log_time:
                            text_file_text_area.insert(tk.END, line)
                            insert_divider()

                            start_date_pos = text_file_text_area.search(log_date, "1.0", tk.END)
                            end_date_pos = f"{start_date_pos}+{len(log_date)}c"
                            text_file_text_area.tag_add("date_highlight", start_date_pos, end_date_pos)

                            start_time_pos = text_file_text_area.search(log_time, "1.0", tk.END)
                            end_time_pos = f"{start_time_pos}+{len(log_time)}c"
                            text_file_text_area.tag_add("time_highlight", start_time_pos, end_time_pos)

                elif search_date:
                    date_pattern = r"\d{4}-\d{2}-\d{2}"
                    date_matches = re.findall(date_pattern, line)
                    if date_matches:
                        log_date = date_matches[0]
                        if search_date == log_date:
                            text_file_text_area.insert(tk.END, line)
                            insert_divider()

                            start_date_pos = text_file_text_area.search(log_date, "1.0", tk.END)
                            end_date_pos = f"{start_date_pos}+{len(log_date)}c"
                            text_file_text_area.tag_add("date_highlight", start_date_pos, end_date_pos)

                elif search_time:
                    time_pattern = r"\d{2}:\d{2}"
                    time_matches = re.findall(time_pattern, line)
                    if time_matches:
                        log_time = time_matches[0]
                        if search_time == log_time:
                            text_file_text_area.insert(tk.END, line)
                            insert_divider()

                            start_time_pos = text_file_text_area.search(log_time, "1.0", tk.END)
                            end_time_pos = f"{start_time_pos}+{len(log_time)}c"
                            text_file_text_area.tag_add("time_highlight", start_time_pos, end_time_pos)

                else:
                    text_file_text_area.insert(tk.END, line)
                    insert_divider()

    highlight_text_file_criteria(selected_levels)


def highlight_criteria(criteria):
    for keyword in criteria:
        start = "1.0"
        while True:
            start = text_area.search(keyword, start, tk.END, nocase=True)
            if not start:
                break
            end = f"{start}+{len(keyword)}c"
            text_area.tag_add("criteria_highlight", start, end)
            start = end
def insert_divider():
    text_area.insert(tk.END, "\n" + "-" * 50 + "\n\n")


def find_errors_in_log(file_path):
    error_counts = defaultdict(int)
    
    # Wykrywanie kodowania pliku
    with open(file_path, 'rb') as log_file:
        result = chardet.detect(log_file.read(10000))  # wczytuje tylko pierwsze 10 000 bajtów do wykrycia kodowania
    
    encoding = result['encoding']
    
    with open(file_path, 'r', encoding=encoding) as log_file:
        for line in log_file:  # Czytanie linia po linii
            for keyword in ERROR_KEYWORDS:
                if keyword.lower() in line.lower():
                    error_counts[keyword] += 1
                    text_area.insert(tk.END, line)
                    insert_divider()
                    break

    highlight_keywords()

    total_errors = sum(error_counts.values())
    error_count_label.config(text=f"{current_language['Errors Found:']} {total_errors}")




def export_errors_to_file(errors):
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if file_path:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(errors)
def select_all_levels():
    for var in level_vars.values():
        var.set(True)

def unselect_all_levels():
    for var in level_vars.values():
        var.set(False)

def show_levels_popup():
    popup = tk.Toplevel(root)
    popup.title("Select Keywords")
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = 400
    window_height = 300   # Zmieniłem wysokość na 300
    x_coordinate = int((screen_width / 2) - (window_width / 2))
    y_coordinate = int((screen_height / 2) - (window_height / 2))
    popup.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")
    
    select_all_button = tk.Button(popup, text="Select All", command=select_all_levels)
    select_all_button.grid(row=0, column=0, padx=10, pady=2, sticky='w', columnspan=3)

    unselect_all_button = tk.Button(popup, text="Unselect All", command=unselect_all_levels)
    unselect_all_button.grid(row=1, column=0, padx=10, pady=2, sticky='w', columnspan=3)

    COLUMN_COUNT = 3
    for idx, (level, var) in enumerate(level_vars.items()):
        row = (idx // COLUMN_COUNT) + 2  # +2 to account for the select/unselect buttons
        col = idx % COLUMN_COUNT
        checkbutton = tk.Checkbutton(popup, text=level, variable=var, onvalue=True, offvalue=False)
        checkbutton.grid(row=row, column=col, padx=10, pady=2, sticky='w')
    
    search_popup_button = tk.Button(popup, text="Search", command=search_logs_by_criteria)
    search_popup_button.grid(row=row+2, column=0, columnspan=3, pady=10)
    
    popup.grab_set()
    popup.mainloop()     

root = tk.Tk()
root.title("Cooperative Log Analyzer by WINFOXes")
root.state("zoomed")

font_regular = Font(family="Arial", size=12)
font_bold = Font(family="Arial", size=12, weight='bold')
search_var = tk.StringVar(root)
start_date_var = tk.StringVar(root)
end_date_var = tk.StringVar(root)
level_vars = {level: tk.BooleanVar(value=True) for level in ERROR_KEYWORDS}
menu = tk.Menu(root)
root.config(menu=menu)

file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Choose Log File", command=open_file)
file_menu.add_separator()
file_menu.add_command(label="Export Errors", command=lambda: export_errors_to_file(text_area.get("1.0", tk.END)))


notebook = ttk.Notebook(root)
notebook.pack(pady=10, padx=10, expand=1, fill=tk.BOTH)

# Zakładka dla błędów
log_errors_tab = tk.Frame(notebook)
notebook.add(log_errors_tab, text="Log Errors")


# Zakładka dla całego pliku tekstowego
text_file_tab = tk.Frame(notebook)
notebook.add(text_file_tab, text="Text File")
bottom_frame_text_file = tk.Frame(text_file_tab)
bottom_frame_text_file.pack(side=tk.TOP, fill=tk.X)

# Obszar tekstowy dla zakładki "Text File"
text_file_text_area = tk.Text(text_file_tab, wrap=tk.WORD, font=font_regular)
text_file_text_area.pack(side=tk.LEFT, expand=1, fill=tk.BOTH)
text_file_scrollbar = Scrollbar(text_file_tab, command=text_file_text_area.yview)
text_file_text_area.config(yscrollcommand=text_file_scrollbar.set)
text_file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Ramka dla wyszukiwania w zakładce "Text File"
search_frame_text_file = tk.Frame(bottom_frame_text_file)
search_frame_text_file.pack(side=tk.LEFT, padx=10)

search_entry_text_file = tk.Entry(search_frame_text_file, textvariable=search_var, font=font_regular)
search_entry_text_file.pack(side=tk.LEFT, pady=5)

search_button_text_file = tk.Button(search_frame_text_file, text=current_language["Search"],
                                    command=text_file_search_logs, font=font_regular)
search_button_text_file.pack(side=tk.LEFT, padx=5)

# Główna ramka dla dolnego menu
bottom_frame = tk.Frame(log_errors_tab)
bottom_frame.grid(row=0, column=0, sticky="ew")
# Ramka dla licznika błędów
error_count_frame = tk.Frame(bottom_frame)
error_count_frame.pack(side=tk.LEFT, padx=10)
error_count_label = tk.Label(error_count_frame, text="", font=font_bold, anchor='e')
error_count_label.pack(pady=5)

# Ramka dla wyszukiwania
search_frame = tk.Frame(bottom_frame)
search_frame.pack(side=tk.LEFT, padx=10)
search_entry = tk.Entry(search_frame, textvariable=search_var, font=font_regular)
search_entry.pack(side=tk.LEFT, pady=5)
search_button = tk.Button(search_frame, text=current_language["Search"], command=search_logs, font=font_regular)
search_button.pack(side=tk.LEFT, padx=5)

# Ramka dla wyszukiwania po dacie i czasie
datetime_frame = tk.Frame(bottom_frame)
datetime_frame.pack(side=tk.LEFT, padx=10)
start_date_label = tk.Label(datetime_frame, text="Date (YYYY-MM-DD):")
start_date_label.pack(side=tk.LEFT)
start_date_entry = tk.Entry(datetime_frame, textvariable=start_date_var)
start_date_entry.pack(side=tk.LEFT, padx=5)
end_date_label = tk.Label(datetime_frame, text="Time (HH:MM):")
end_date_label.pack(side=tk.LEFT)
end_date_entry = tk.Entry(datetime_frame, textvariable=end_date_var)
end_date_entry.pack(side=tk.LEFT, padx=5)
search_datetime_button = tk.Button(datetime_frame, text=current_language["Search"], command=search_logs_by_datetime, font=font_regular)
search_datetime_button.pack(side=tk.LEFT, padx=5)

# Ramka dla wyboru słów kluczowych
keywords_frame = tk.Frame(bottom_frame)
keywords_frame.pack(side=tk.LEFT, padx=10)
level_dropdown = tk.Button(keywords_frame, text="Select Keywords", command=show_levels_popup)
level_dropdown.pack(side=tk.LEFT, padx=5)

text_frame = tk.Frame(log_errors_tab)
text_frame.grid(row=1, column=0, sticky="nsew")
log_errors_tab.grid_rowconfigure(1, weight=1)
log_errors_tab.grid_columnconfigure(0, weight=1)

text_area = tk.Text(text_frame, wrap=tk.WORD, font=font_regular)
text_area.pack(side=tk.LEFT, expand=1, fill=tk.BOTH)

scrollbar = Scrollbar(text_frame, command=text_area.yview)
text_area.config(yscrollcommand=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

text_area.tag_configure("keyword_highlight", foreground="red")
text_area.tag_configure("search_highlight", background="yellow")
text_area.tag_configure("criteria_highlight", foreground="green")
text_area.tag_configure("date_highlight", background="orange")
text_area.tag_configure("time_highlight", background="orange")
text_file_text_area.tag_configure("search_highlight", background="yellow")



root.geometry("600x400")
font_regular = ("Arial", 7)
creator_label = tk.Label(root, text="Created by Dominik Pacanowski", font=font_regular)
creator_label.pack(pady=10)
root.mainloop()