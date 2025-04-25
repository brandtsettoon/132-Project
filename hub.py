import tkinter as tk
from tkinter import Label, Button, Text, messagebox, Toplevel, Frame, Scrollbar
from tkcalendar import Calendar
from datetime import datetime
import time
import json
import os

# variables and such
FONT = "Segoe UI"
window = tk.Tk()
window.title("The House Hub")
settings_v =  {
    "use_military_time": False
    }
# window size
width, height, x, y = 500, 600, 500, 200
window.geometry(f"{width}x{height}+{x}+{y}")

# event storage
EVENTS_FILE = "calendar_events.json"
events = {}
if os.path.exists(EVENTS_FILE):
    with open(EVENTS_FILE, 'r') as ef:
        events = json.load(ef)

# clock
clock_label = Label(window, font=(FONT, 20), foreground='black')
clock_label.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")

# date
date_label = Label(window, text="", font=(FONT, 20))
date_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

# calendar
Cal = Calendar(window, selectmode="day", date_pattern="mm/dd/yyyy")
Cal.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

# tabs (details/upcoming)
tab_button_frame = Frame(window)
tab_button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 0))

event_tab_button = Button(tab_button_frame, text="Event Details", command=lambda: show_tab("details"))
event_tab_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

upcoming_tab_button = Button(tab_button_frame, text="Upcoming Events", command=lambda: show_tab("upcoming"))
upcoming_tab_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

# tab container
tab_container = Frame(window)
tab_container.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
window.grid_rowconfigure(4, weight=1)
window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)

event_tab = Frame(tab_container)
upcoming_tab = Frame(tab_container)
for frame in (event_tab, upcoming_tab):
    frame.place(relwidth=1, relheight=1)

# event tab
scrollbar_event = Scrollbar(event_tab)
scrollbar_event.pack(side=tk.RIGHT, fill=tk.Y)

event_text = Text(event_tab, height=10, yscrollcommand=scrollbar_event.set, wrap=tk.WORD)
event_text.pack(expand=True, fill=tk.BOTH)
scrollbar_event.config(command=event_text.yview)

# upcoming tab
scrollbar_upcoming = Scrollbar(upcoming_tab)
scrollbar_upcoming.pack(side=tk.RIGHT, fill=tk.Y)

upcoming_text = Text(upcoming_tab, height=10, yscrollcommand=scrollbar_upcoming.set, wrap=tk.WORD)
upcoming_text.pack(expand=True, fill=tk.BOTH)
scrollbar_upcoming.config(command=upcoming_text.yview)

# right-side buttons
button_frame = Frame(window)
button_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

add_button = Button(button_frame, text="Add Event", command=lambda: add_event(Cal.get_date()))
add_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

delete_button = Button(button_frame, text="Delete Event", command=lambda: delete_event(Cal.get_date()))
delete_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

today_button = Button(button_frame, text="Go to Today", command=lambda: go_to_today())
today_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

settings_button = Button(button_frame, text="Settings", command=lambda: settings())
settings_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

# functions

def show_tab(name):
    if name == "details":
        event_tab.lift()
    else:
        upcoming_tab.lift()

def update_time():
    if settings_v["use_military_time"]:
        thetime = '%H:%M:%S'
    else:
        thetime = '%I:%M:%S %p'
    current_time = time.strftime(thetime)
    clock_label.config(text=current_time)
    clock_label.after(1000, update_time)

def update_date(event=None):
    date = Cal.get_date()
    date_label.config(text=date)
    display_events_for_date(date)
    display_upcoming_events()

def display_events_for_date(date):
    event_text.config(state=tk.NORMAL)
    event_text.delete("1.0", tk.END)
    if date in events and events[date]:
        for evt in events[date]:
            event_text.insert(tk.END, f"- {evt}\n")
    else:
        event_text.insert(tk.END, "No events for this date.")
    event_text.config(state=tk.DISABLED)

def display_upcoming_events():
    upcoming_text.config(state=tk.NORMAL)
    upcoming_text.delete("1.0", tk.END)
    today = datetime.strptime(Cal.get_date(), "%m/%d/%Y")
    upcoming = {k: v for k, v in events.items() if datetime.strptime(k, "%m/%d/%Y") >= today}
    if upcoming:
        for date in sorted(upcoming.keys(), key=lambda d: datetime.strptime(d, "%m/%d/%Y")):
            upcoming_text.insert(tk.END, f"{date}:\n")
            for evt in upcoming[date]:
                upcoming_text.insert(tk.END, f"  - {evt}\n")
            upcoming_text.insert(tk.END, "\n")
    else:
        upcoming_text.insert(tk.END, "No upcoming events.")
    upcoming_text.config(state=tk.DISABLED)

def add_event(date):
    def save_event():
        text = event_entry.get("1.0", tk.END).strip()
        if text:
            if date not in events:
                events[date] = []
            events[date].append(text)
            save_events_to_file()
            update_date()
            add_window.destroy()
        else:
            messagebox.showwarning("error", "Event cannot be empty.")

    add_window = Toplevel(window)
    add_window.title(f"Add event for {date}")
    Label(add_window, text=f"Add event for {date}:").pack(padx=10, pady=5)
    event_entry = Text(add_window, height=5, width=40)
    event_entry.pack(padx=10, pady=5)
    Button(add_window, text="Save", command=save_event).pack(pady=5)

def delete_event(date):
    if date not in events or not events[date]:
        messagebox.showinfo("Info", "No events to delete for this date.")
        return

    def confirm_delete():
        selected = event_listbox.curselection()
        if selected:
            index = selected[0]
            del events[date][index]
            if not events[date]:
                del events[date]
            save_events_to_file()
            update_date()
            delete_window.destroy()
        else:
            messagebox.showwarning("error", "please select an event to delete")

    delete_window = Toplevel(window)
    delete_window.title(f"Delete Event for {date}")
    Label(delete_window, text="Select event to delete:").pack(padx=10, pady=5)
    event_listbox = tk.Listbox(delete_window, width=50, height=5)
    event_listbox.pack(padx=10, pady=5)

    for evt in events[date]:
        event_listbox.insert(tk.END, evt)

    Button(delete_window, text="Delete Selected", command=confirm_delete).pack(pady=5)

def save_events_to_file():
    with open(EVENTS_FILE, 'w') as f:
        json.dump(events, f)

def go_to_today():
    today_str = datetime.now().strftime("%m/%d/%Y")
    Cal.selection_set(today_str)
    update_date()

def settings():
    settings_window = Toplevel(window)
    settings_window.title("Settings")
    settings_window.geometry("300x200")
    Label(settings_window, text="Settings", font=(FONT, 14)).pack(pady=20)
    time_change = tk.BooleanVar(value=settings_v["use_military_time"])
    def toggle_time_format():
        settings_v["use_military_time"] = time_change.get()
        update_time()

    time_checkbox = tk.Checkbutton(
        settings_window,
        text="Use Military Time (24-hour format)",
        variable=time_change,
        command=toggle_time_format
    )
    time_checkbox.pack(pady=10)


# initialization
update_time()
Cal.bind("<<CalendarSelected>>", update_date)
show_tab("details")
update_date()

# run it
window.mainloop()