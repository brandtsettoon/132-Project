import tkinter as tk
from tkinter import Label, Button, Text, messagebox, Toplevel, Frame, Scrollbar, simpledialog
from tkcalendar import Calendar
from datetime import datetime
import time
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


# variables and such
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]
EVENTS_FILE = "events.pkl"
USERS_FILE = "users.json"
USER_TOKENS_DIR = "user_tokens"
os.makedirs(USER_TOKENS_DIR, exist_ok=True) 
FONT = "Segoe UI"
user_services = {} 
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
            if isinstance(evt, dict):
                event_text.insert(tk.END, f"- {evt['text']}\n")
            else:
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
                if isinstance(evt, dict):
                    upcoming_text.insert(tk.END, f"  - {evt['text']}\n")
                else:
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
            events[date].append({"text": text})
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
            messagebox.showwarning("Error", "Please select an event to delete")
    delete_window = Toplevel(window)
    delete_window.title(f"Delete Event for {date}")
    Label(delete_window, text="Select event to delete:").pack(padx=10, pady=5)
    event_listbox = tk.Listbox(delete_window, width=50, height=5)
    event_listbox.pack(padx=10, pady=5)
    for evt in events[date]:
        if isinstance(evt, dict):
            event_listbox.insert(tk.END, evt['text'])
        else:
            event_listbox.insert(tk.END, evt)
    Button(delete_window, text="Delete Selected", command=confirm_delete).pack(pady=5)

def save_events_to_file():
    with open(EVENTS_FILE, 'w') as f:
        json.dump(events, f)

def go_to_today():
    today_str = datetime.now().strftime("%m/%d/%Y")
    Cal.selection_set(today_str)
    update_date()

def setup_shared_calendar():
    global shared_calendar_id
    shared_calendar = {'summary': 'Family/House Shared Calendar', 'timeZone': 'America/New_York'}
    try:
        service = get_calendar_service()
        created_calendar = service.calendars().insert(body=shared_calendar).execute()
        shared_calendar_id = created_calendar['id']
        messagebox.showinfo("Success", "Shared calendar created successfully")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create shared calendar: {e}")

def sync_to_shared_calendar():
    if not shared_calendar_id:
        messagebox.showwarning("Warning", "Please setup shared calendar first")
        return
    try:
        service = get_calendar_service()
        count = 0
        for date, evt_list in events.items():
            start_date = datetime.strptime(date, "%m/%d/%Y").replace(hour=9)
            for evt in evt_list:
                if evt.get('shared_id'):
                    continue
                end_time = start_date.replace(hour=10)
                event = {
                    'summary': evt['text'],
                    'start': {'dateTime': start_date.isoformat(), 'timeZone': 'America/New_York'},
                    'end': {'dateTime': end_time.isoformat(), 'timeZone': 'America/New_York'},
                }
                created_event = service.events().insert(calendarId=shared_calendar_id, body=event).execute()
                evt['shared_id'] = created_event['id']
                count += 1
        save_events_to_file()
        messagebox.showinfo("Success", f"Synced {count} events to shared calendar")
    except Exception as e:
        messagebox.showerror("Error", f"Shared calendar sync failed: {e}")

def settings():
    settings_window = Toplevel(window)
    settings_window.title("Settings")
    settings_window.geometry("400x300")
    Label(settings_window, text="Settings", font=(FONT, 14)).pack(pady=10)
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
    time_checkbox.pack(pady=5)
    sync_frame = Frame(settings_window)
    sync_frame.pack(pady=10, fill=tk.X)
    Label(sync_frame, text="Calendar Sync:").pack(anchor=tk.W)
    Button(sync_frame, text="Sync All to Google", command=sync_all_events).pack(fill=tk.X, pady=2)
    Button(sync_frame, text="Pull from Google", command=pull_and_merge_events).pack(fill=tk.X, pady=2)
    Button(sync_frame, text="Setup Shared Calendar", command=setup_shared_calendar).pack(fill=tk.X, pady=2)
    Button(sync_frame, text="Sync to Shared Calendar", command=sync_to_shared_calendar).pack(fill=tk.X, pady=2)

def manage_users():
    win = Toplevel(window)
    win.title("Manage Users")
    win.geometry("300x300")
    def login_new_user():
        email = simpledialog.askstring("Login", "Enter a name (email or identifier):")
        if email:
            token_file = os.path.join(USER_TOKENS_DIR, f"{email}_token.json")
            try:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
                service = build('calendar', 'v3', credentials=creds)
                user_services[email] = service
                refresh_user_list()
                messagebox.showinfo("Success", f"User {email} logged in.")
            except Exception as e:
                messagebox.showerror("Error", f"Login failed: {e}")
    def logout_user():
        selected = user_listbox.curselection()
        if not selected:
            return
        email = user_listbox.get(selected[0])
        if email in user_services:
            del user_services[email]
        token_file = os.path.join(USER_TOKENS_DIR, f"{email}_token.json")
        if os.path.exists(token_file):
            os.remove(token_file)
        refresh_user_list()
    def refresh_user_list():
        user_listbox.delete(0, tk.END)
        for user in user_services:
            user_listbox.insert(tk.END, user)
    user_listbox = tk.Listbox(win)
    user_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    Button(win, text="Login New User", command=login_new_user).pack(side=tk.LEFT, padx=10)
    Button(win, text="Logout Selected", command=logout_user).pack(side=tk.RIGHT, padx=10)
    refresh_user_list()

def sync_event(date):
    if date not in events or not events[date]:
        messagebox.showinfo("Info", "No event to sync for this date.")
        return
    event_data = events[date][0] 
    try:
        service = get_calendar_service()
        start_time = datetime.strptime(date, "%m/%d/%Y").replace(hour=9, minute=0)
        end_time = start_time.replace(hour=10)
        timezone = 'America/New_York'
        event = {
            'summary': event_data['text'],
            'start': {'dateTime': start_time.isoformat(), 'timeZone': timezone},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': timezone},
        }
        service.events().insert(calendarId='primary', body=event).execute()
        messagebox.showinfo("Success", f"Event synced to Google Calendar.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to sync event: {e}")

def get_calendar_service():
    try:
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        messagebox.showerror("Google Connection Error", f"Failed to connect to Google: {str(e)}")
        raise

def sync_all_events():
    try:
        service = get_calendar_service()
        count = 0
        for date, evt_list in events.items():
            start_date = datetime.strptime(date, "%m/%d/%Y").replace(hour=9)
            for i, evt in enumerate(evt_list):
                if evt.get("id"):
                    continue
                end_time = start_date.replace(hour=10)
                event_body = {
                    'summary': evt["text"],
                    'start': {'dateTime': start_date.isoformat(), 'timeZone': 'America/New_York'},
                    'end': {'dateTime': end_time.isoformat(), 'timeZone': 'America/New_York'},
                }
                created_event = service.events().insert(calendarId='primary', body=event_body).execute()
                events[date][i]["id"] = created_event["id"]
                count += 1
        save_events_to_file()
        messagebox.showinfo("Success", f"{count} event(s) synced to Google Calendar.")
    except Exception as e:
        messagebox.showerror("Error", f"Sync failed: {e}")

def pull_and_merge_events():
    added = 0
    try:
        for user, service in user_services.items():
            now = datetime.utcnow().isoformat() + 'Z'
            result = service.events().list(
                calendarId='primary', timeMin=now,
                maxResults=100, singleEvents=True,
                orderBy='startTime').execute()
            for gevent in result.get('items', []):
                summary = gevent.get('summary')
                g_id = gevent.get('id')
                start = gevent['start'].get('dateTime', gevent['start'].get('date'))
                date_obj = datetime.fromisoformat(start)
                date_str = date_obj.strftime("%m/%d/%Y")
                if date_str not in events:
                    events[date_str] = []
                already = any(e.get("id") == g_id for e in events[date_str])
                if not already:
                    events[date_str].append({
                        "text": f"[{user}] {summary}",
                        "id": g_id
                    })
                    added += 1
        save_events_to_file()
        update_date()
        messagebox.showinfo("Success", f"Pulled and merged {added} events from all users.")
    except Exception as e:
        messagebox.showerror("Error", f"Multi-user pull failed: {e}")

def get_service_for_user(token_file):
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

scrollbar_event = Scrollbar(event_tab)
scrollbar_event.pack(side=tk.RIGHT, fill=tk.Y)
event_text = Text(event_tab, height=10, yscrollcommand=scrollbar_event.set, wrap=tk.WORD)
event_text.pack(expand=True, fill=tk.BOTH)
scrollbar_event.config(command=event_text.yview)

scrollbar_upcoming = Scrollbar(upcoming_tab)
scrollbar_upcoming.pack(side=tk.RIGHT, fill=tk.Y)
upcoming_text = Text(upcoming_tab, height=10, yscrollcommand=scrollbar_upcoming.set, wrap=tk.WORD)
upcoming_text.pack(expand=True, fill=tk.BOTH)
scrollbar_upcoming.config(command=upcoming_text.yview)

button_frame = Frame(window)
button_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

add_button = Button(button_frame, text="Add Event", command=lambda: add_event(Cal.get_date()))
add_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

delete_button = Button(button_frame, text="Delete Event", command=lambda: delete_event(Cal.get_date()))
delete_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

today_button = Button(button_frame, text="Go to Today", command=lambda: go_to_today())
today_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

settings_button = Button(button_frame, text="Settings", command=settings)
settings_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

manage_users_button = Button(button_frame, text="Manage Users", command=manage_users)
manage_users_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

if not os.path.exists('credentials.json'):
    messagebox.showerror("Missing Credentials", "Google Calendar integration requires credentials.json file")
else:
    try:
        get_calendar_service()
    except Exception as e:
        messagebox.showerror("Google Auth Error", f"Failed to connect: {str(e)}")

# initialization
if not os.path.exists('credentials.json'):
    messagebox.showerror("Missing Credentials", 
        "Google Calendar integration requires credentials.json file")
else:
    try:
        get_calendar_service()
    except Exception as e:
        messagebox.showerror("Google Auth Error", f"Failed to connect: {str(e)}")

update_time()
Cal.bind("<<CalendarSelected>>", update_date)
show_tab("details")
update_date()
window.mainloop()
# run it
window.mainloop()