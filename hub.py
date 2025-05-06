import tkinter as tk
from tkinter import Label, Button, Text, messagebox, Toplevel, Frame, Scrollbar, Entry, LEFT, ttk
from tkcalendar import Calendar
from datetime import datetime, timedelta
import time
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pytz
from ip2geotools.databases.noncommercial import DbIpCity
import requests


# looks
FONT = "Arial"
BG_COLOR = "#f0f4f8"
ACCENT_COLOR = "#4a90e2"
TEXT_COLOR = "#333"
available_fonts = ['Arial', 'Cooper Black', 'Courier New', 'Segoe UI', 'Georgia']

# variables
current_main_user = None
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]
EVENTS_FILE = "calendar_events.json"
USERS_FILE = "users.json"
USER_TOKENS_DIR = "user_tokens"
os.makedirs(USER_TOKENS_DIR, exist_ok=True) 
user_services = {}
settings_v =  {"use_military_time": False}
after_id = None
shared_calendar_id = None
WEATHER_API_KEY = "3078c2d7706052bdbe3b68c6858c5242"
weather_label = None
current_location = None

# window
window = tk.Tk()
window.title("The House Hub")
window.configure(bg=BG_COLOR)
window.geometry("800x500")
font_var = tk.StringVar(value=FONT) 

# event storage
events = {}
if os.path.exists(EVENTS_FILE):
    with open(EVENTS_FILE, 'r') as ef:
        events = json.load(ef)


# frames
header_frame = Frame(window, bg=BG_COLOR)
header_frame.pack(pady=10, fill=tk.X)

main_frame = Frame(window, bg=BG_COLOR)
main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

left_frame = Frame(main_frame, bg=BG_COLOR)
left_frame.pack(side=tk.LEFT, expand=True, fill=tk.Y, padx=10, ipadx=150)

right_frame = Frame(main_frame, bg=BG_COLOR)
right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10)

# clock
clock_label = Label(header_frame, font=(FONT, 24, "bold"), fg=TEXT_COLOR, bg=BG_COLOR)
clock_label.pack(side=tk.LEFT, padx=20)

# date
date_label = Label(header_frame, font=(FONT, 24, "bold"), fg=TEXT_COLOR, bg=BG_COLOR)
date_label.pack(side=tk.RIGHT, padx=20)

# main user
main_user_label = Label(header_frame, font=(FONT, 10), fg=TEXT_COLOR, bg=BG_COLOR)
main_user_label.pack(side=tk.RIGHT, padx=20)

# calendar
Cal = Calendar(left_frame, selectmode="day", date_pattern="mm/dd/yyyy")
Cal.pack(expand=True, fill=tk.BOTH, pady=10)

# tabs
right_tabs = Frame(right_frame, bg=BG_COLOR)
right_tabs.pack(fill=tk.X)

event_tab_button = Button(right_tabs, text="Event Details", font=(FONT, 10), bg=ACCENT_COLOR, fg="black", command=lambda: show_tab("details"))
event_tab_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

upcoming_tab_button = Button(right_tabs, text="Upcoming Events", font=(FONT, 10), bg=ACCENT_COLOR, fg="black", command=lambda: show_tab("upcoming"))
upcoming_tab_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

text_frame = Frame(right_frame, bg=BG_COLOR)
text_frame.pack(expand=True, fill=tk.BOTH, pady=10)

scrollbar_event = Scrollbar(text_frame)
scrollbar_event.pack(side=tk.RIGHT, fill=tk.Y)

event_text = Text(text_frame, font=(FONT, 10), wrap=tk.WORD, yscrollcommand=scrollbar_event.set, bg="white", fg=TEXT_COLOR)
event_text.pack(expand=True, fill=tk.BOTH)
scrollbar_event.config(command=event_text.yview)

settings_users_frame = Frame(window, bg=BG_COLOR)
settings_users_frame.pack(fill=tk.X, pady=10)

# weather
weather_frame = Frame(header_frame, bg=BG_COLOR)
weather_frame.pack(side=tk.RIGHT, padx=20)

weather_label = Label(weather_frame, font=(FONT, 10), fg=TEXT_COLOR, bg=BG_COLOR)
weather_label.pack(side=tk.LEFT)

refresh_weather_btn = Button(weather_frame, text="⟳", font=(FONT, 8),command=lambda:update_weather, bg=ACCENT_COLOR, fg="black")
refresh_weather_btn.pack(side=tk.LEFT, padx=5)

change_loc_btn = Button(weather_frame, text="✎", font=(FONT, 8), command=lambda:change_location, bg=ACCENT_COLOR, fg="black")
change_loc_btn.pack(side=tk.LEFT)

# tab container
tab_container = Frame(window)
tab_container.pack(padx=10, pady=10, fill="both", expand=True)
window.grid_rowconfigure(4, weight=1)
window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)

event_tab = Frame(tab_container)
upcoming_tab = Frame(tab_container)
for frame in (event_tab, upcoming_tab):
    frame.place(relwidth=1, relheight=1)

button_frame = Frame(left_frame, bg=BG_COLOR)
button_frame.pack(pady=10, fill=tk.X)

# functions

def show_tab(name):
    if name == "details":
        event_text.config(state=tk.NORMAL)
        event_text.delete("1.0", tk.END)
        if Cal.get_date() in events and events[Cal.get_date()]:
            for evt in events[Cal.get_date()]:
                if isinstance(evt, dict):
                    time_info = ""
                    if 'start_time' in evt and 'end_time' in evt:
                        start = datetime.strptime(evt['start_time'], "%H:%M").strftime("%I:%M %p")
                        end = datetime.strptime(evt['end_time'], "%H:%M").strftime("%I:%M %p")
                        time_info = f" ({start} - {end})"
                    event_text.insert(tk.END, f"- {evt['text']}{time_info}\n")
                    if evt.get('description'):
                        event_text.insert(tk.END, f"    {evt['description']}\n")
                else:
                    event_text.insert(tk.END, f"- {evt}\n")
        else:
            event_text.insert(tk.END, "No events for this date.")
        event_text.config(state=tk.DISABLED)
    else:
        event_text.config(state=tk.NORMAL)
        event_text.delete("1.0", tk.END)
        today = datetime.strptime(Cal.get_date(), "%m/%d/%Y")
        upcoming = {k: v for k, v in events.items() if datetime.strptime(k, "%m/%d/%Y") >= today}
        if upcoming:
            for date in sorted(upcoming.keys(), key=lambda d: datetime.strptime(d, "%m/%d/%Y")):
                event_text.insert(tk.END, f"{date}:\n")
                for evt in upcoming[date]:
                    if isinstance(evt, dict):
                        time_info = ""
                        if 'start_time' in evt and 'end_time' in evt:
                            start = datetime.strptime(evt['start_time'], "%H:%M").strftime("%I:%M %p")
                            end = datetime.strptime(evt['end_time'], "%H:%M").strftime("%I:%M %p")
                            time_info = f" ({start} - {end})"
                        event_text.insert(tk.END, f"  - {evt['text']}{time_info}\n")
                        if evt.get('description'):
                            event_text.insert(tk.END, f"    {evt['description']}\n")
                    else:
                        event_text.insert(tk.END, f"  - {evt}\n")
                event_text.insert(tk.END, "\n")
        else:
            event_text.insert(tk.END, "No upcoming events.")
        event_text.config(state=tk.DISABLED)

def update_time():
    global after_id
    if not clock_label.winfo_exists():
        return
    if settings_v["use_military_time"]:
        thetime = '%H:%M:%S'
    else:
        thetime = '%I:%M:%S %p'
    current_time = time.strftime(thetime)
    clock_label.config(text=current_time)
    after_id = clock_label.after(1000, update_time)

def on_closing():
    global after_id
    if after_id:
        clock_label.after_cancel(after_id)
    window.destroy()

def update_date(event=None):
    date = Cal.get_date()
    date_label.config(text=date)
    display_events_for_date(date)
    upcoming_tab_button.config(command=lambda: show_tab("upcoming"))

def display_events_for_date(date):
    event_text.config(state=tk.NORMAL)
    event_text.delete("1.0", tk.END)
    if date in events and events[date]:
        for evt in events[date]:
            if isinstance(evt, dict):
                display_text = evt['text']
                
                if 'created_by' in evt:
                    display_text += f" (by {evt['created_by']})"
                
                if 'assigned_to' in evt:
                    if evt['assigned_to'] == "All":
                        display_text += " → Everyone"
                    else:
                        display_text += f" → {evt['assigned_to']}"
                
                time_info = ""
                if 'start_time' in evt and 'end_time' in evt:
                    if settings_v["use_military_time"]:
                        time_fmt = "%H:%M"
                    else:
                        time_fmt = "%I:%M %p"
                    start = datetime.strptime(evt['start_time'], "%H:%M").strftime(time_fmt)
                    end = datetime.strptime(evt['end_time'], "%H:%M").strftime(time_fmt)
                    time_info = f" ({start} - {end})"
                
                event_text.insert(tk.END, f"- {display_text}{time_info}\n")
                if evt.get('description'):
                    event_text.insert(tk.END, f"    {evt['description']}\n")
            else:
                event_text.insert(tk.END, f"- {evt}\n")
    else:
        event_text.insert(tk.END, "No events for this date.")
    event_text.config(state=tk.DISABLED)

def update_main_user_display():
    if current_main_user:
        main_user_label.config(text=f"User: {current_main_user}")
    else:
        main_user_label.config(text="No user selected")

def change_main_user():
    if not user_services:
        messagebox.showwarning("No Users", "Please login users first")
        return
    
    win = Toplevel(window)
    win.title("Select Main User")
    win.geometry("300x200")
    
    Label(win, text="Select Main User:", font=(FONT, 12)).pack(pady=10)
    
    user_var = tk.StringVar(value=current_main_user if current_main_user else "")
    user_dropdown = ttk.Combobox(win, textvariable=user_var, values=list(user_services.keys()))
    user_dropdown.pack(pady=10)
    
    def confirm_selection():
        global current_main_user
        selected = user_var.get()
        if selected in user_services:
            current_main_user = selected
            update_main_user_display()
            win.destroy()
        else:
            messagebox.showwarning("Invalid", "Please select a valid user")
    
    Button(win, text="Confirm", command=confirm_selection, font=(FONT, 10), bg=ACCENT_COLOR, fg="black").pack(pady=10)

def add_event(date):
    def save_event():
        title = title_entry.get("1.0", tk.END).strip()
        description = desc_entry.get("1.0", tk.END).strip()
        start_time = start_time_var.get()
        end_time = end_time_var.get()
        assigned_to = assign_var.get() if assign_var.get() != "None" else None
        
        if title:
            if date not in events:
                events[date] = []
                
            event_obj = {"text": title}
            if description:
                event_obj["description"] = description
            if start_time and end_time:
                event_obj["start_time"] = start_time
                event_obj["end_time"] = end_time
            if assigned_to:
                event_obj["assigned_to"] = assigned_to
            else:
                event_obj["assigned_to"] = "All"
            if current_main_user:
                event_obj["created_by"] = current_main_user
                
            events[date].append(event_obj)
            save_events_to_file()
            update_date()
            
            sync_event_to_all_users(date, len(events[date])-1)
            
            add_window.destroy()
        else:
            messagebox.showwarning("Error", "Event title cannot be empty.")

    add_window = Toplevel(window)
    add_window.title(f"Add Event")
    add_window.geometry("400x450")

    Label(add_window, text=f"Add Event for {date}:", font=(FONT, 10, "bold")).pack(padx=10, pady=5)

    if len(user_services) > 1:
        assign_frame = Frame(add_window)
        assign_frame.pack(pady=5, fill=tk.X, padx=10)
        
        Label(assign_frame, text="Assign To:", font=(FONT, 10)).pack(side=tk.LEFT)
        
        assign_var = tk.StringVar(value="All")  
        assign_dropdown = ttk.Combobox(assign_frame, textvariable=assign_var, 
                                     values=["All"] + [u for u in user_services.keys() if u != current_main_user])
        assign_dropdown.pack(side=tk.LEFT, padx=10)
    else:
        assign_var = tk.StringVar(value="All") 
    
    Label(add_window, text="Title:", font=(FONT, 10)).pack(padx=10, anchor="w")
    title_entry = Text(add_window, height=2, width=40)
    title_entry.pack(padx=10, pady=5)

    Label(add_window, text="Description:", font=(FONT, 10)).pack(padx=10, anchor="w")
    desc_entry = Text(add_window, height=4, width=40)
    desc_entry.pack(padx=10, pady=5)

    time_frame = Frame(add_window)
    time_frame.pack(pady=10)
    
    Label(time_frame, text="Start Time:", font=(FONT, 10)).grid(row=0, column=0, padx=5)
    start_time_var = tk.StringVar(value="09:00")
    start_time_menu = ttk.Combobox(time_frame, textvariable=start_time_var, values=generate_time_slots())
    start_time_menu.grid(row=0, column=1, padx=5)
    
    Label(time_frame, text="End Time:", font=(FONT, 10)).grid(row=1, column=0, padx=5)
    end_time_var = tk.StringVar(value="10:00")
    end_time_menu = ttk.Combobox(time_frame, textvariable=end_time_var, values=generate_time_slots())
    end_time_menu.grid(row=1, column=1, padx=5)

    Button(add_window, text="Save", font=(FONT, 10), command=save_event, bg=ACCENT_COLOR, fg="black").pack(pady=5)

def sync_event_to_all_users(date, event_index):
    if date not in events or event_index >= len(events[date]):
        return
    
    event_data = events[date][event_index]
    assigned_to = event_data.get('assigned_to', 'All')
    
    for user, service in user_services.items():
        try:
            if assigned_to != "All" and assigned_to != user:
                continue
                
            if event_data.get(f"{user}_id"):
                continue 
                
            date_obj = datetime.strptime(date, "%m/%d/%Y")
            start_time = event_data.get('start_time', '09:00')
            end_time = event_data.get('end_time', '10:00')
            
            local_tz = pytz.timezone('America/New_York')
            start_naive = datetime.combine(
                date_obj.date(),
                datetime.strptime(start_time, "%H:%M").time()
            )
            end_naive = datetime.combine(
                date_obj.date(),
                datetime.strptime(end_time, "%H:%M").time()
            )
            
            start_local = local_tz.localize(start_naive)
            end_local = local_tz.localize(end_naive)
            
            start_utc = start_local.astimezone(pytz.UTC)
            end_utc = end_local.astimezone(pytz.UTC)
            
            event_body = {
                'summary': event_data["text"],
                'start': {
                    'dateTime': start_utc.isoformat(),
                    'timeZone': 'America/New_York'
                },
                'end': {
                    'dateTime': end_utc.isoformat(),
                    'timeZone': 'America/New_York'
                },
            }
            if 'description' in event_data:
                event_body['description'] = event_data['description']
            
            created_event = service.events().insert(
                calendarId='primary',
                body=event_body
            ).execute()
            event_data[f"{user}_id"] = created_event["id"]
            
        except Exception as e:
            print(f"Failed to sync event to {user}'s calendar: {e}")
    
    save_events_to_file()


def generate_time_slots():
    return [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 30]]

def delete_event(date):
    if date not in events or not events[date]:
        messagebox.showinfo("Info", "No events to delete for this date.")
        return
        
    def confirm_delete():
        selected = event_listbox.curselection()
        if selected:
            index = selected[0]
            event_to_delete = events[date][index]
            
            delete_event_from_all_users(event_to_delete)
            
            del events[date][index]
            if not events[date]:
                del events[date]
                
            save_events_to_file()
            update_date()
            delete_window.destroy()
        else:
            messagebox.showwarning("Error", "Please select an event to delete.")
            
    delete_window = Toplevel(window)
    delete_window.title(f"Delete Event")
    Label(delete_window, text="Select Event to Delete:", font=(FONT, 10)).pack(padx=10, pady=5)
    event_listbox = tk.Listbox(delete_window, width=50, height=5)
    event_listbox.pack(padx=10, pady=5)
    for evt in events[date]:
        if isinstance(evt, dict):
            display_text = evt['text']
            if 'start_time' in evt and 'end_time' in evt:
                display_text += f" ({evt['start_time']}-{evt['end_time']})"
            event_listbox.insert(tk.END, display_text)
        else:
            event_listbox.insert(tk.END, evt)
    Button(delete_window, text="Delete Selected", command=confirm_delete, font=(FONT, 10), bg=ACCENT_COLOR, fg="black").pack(pady=5)
def save_events_to_file():
    with open(EVENTS_FILE, 'w') as f:
        json.dump(events, f)

def delete_event_from_all_users(event_data):
    for user, service in user_services.items():
        try:
            event_id = event_data.get(f"{user}_id")
            if event_id:
                service.events().delete(calendarId='primary', eventId=event_id).execute()
        except Exception as e:
            print(f"Failed to delete event from {user}'s calendar: {e}")

def go_to_today():
    today_str = datetime.now().strftime("%m/%d/%Y")
    Cal.selection_set(today_str)
    update_date()

def get_location_from_ip():
    try:
        response = DbIpCity.get(requests.get('https://api.ipify.org').text, api_key='free')
        return f"{response.city}, {response.region}, {response.country}"
    except Exception as e:
        print(f"Couldn't get location from IP: {e}")
        return None

def get_weather_data(location):
    try:
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={WEATHER_API_KEY}"
        geo_response = requests.get(geo_url).json()
        
        if not geo_response:
            return None
            
        lat = geo_response[0]['lat']
        lon = geo_response[0]['lon']
        
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=imperial"
        weather_data = requests.get(weather_url).json()
        
        return {
            'temp': weather_data['main']['temp'],
            'description': weather_data['weather'][0]['description'],
            'icon': weather_data['weather'][0]['icon']
        }
    except Exception as e:
        print(f"Weather API error: {e}")
        return None

def update_weather():
    global current_location
    
    if not current_location:
        current_location = get_location_from_ip()
        
        if not current_location:
            current_location = custom_askstring("Location", "Enter your location (City, State/Country):")
            if not current_location:
                return
    
    weather = get_weather_data(current_location)
    if weather:
        weather_label.config(
            text=f"{current_location}: {weather['temp']}°F, {weather['description'].title()}",
            font=(font_var.get(), 10)
        )
    else:
        weather_label.config(text="Couldn't get weather data")

def change_location():
    global current_location
    new_loc = custom_askstring("Change Location", "Enter new location (City, State/Country):")
    if new_loc:
        current_location = new_loc
        update_weather()

headers = {
    'User-Agent': 'House Hub App (jdd064@email.latech.edu)' 
}

def get_coordinates(location):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&addressdetails=1&limit=1"
        response = requests.get(url, headers=headers).json()
        return (response[0]['lat'], response[0]['lon']) if response else None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None

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
            for evt in evt_list:
                if evt.get('shared_id'):
                    continue
                
                date_obj = datetime.strptime(date, "%m/%d/%Y")
                start_time = evt.get('start_time', '09:00')
                end_time = evt.get('end_time', '10:00')
                
                start_datetime = datetime.combine(
                    date_obj.date(),
                    datetime.strptime(start_time, "%H:%M").time()
                )
                end_datetime = datetime.combine(
                    date_obj.date(),
                    datetime.strptime(end_time, "%H:%M").time()
                )
                
                event = {
                    'summary': evt['text'],
                    'start': {'dateTime': start_datetime.isoformat(), 'timeZone': 'America/New_York'},
                    'end': {'dateTime': end_datetime.isoformat(), 'timeZone': 'America/New_York'},
                }
                if 'description' in evt:
                    event['description'] = evt['description']
                
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
    settings_window.geometry("400x400")
    Label(settings_window, text="Settings", fg=TEXT_COLOR, font=(FONT, 18, "bold")).pack(pady=10)
    time_change = tk.BooleanVar(value=settings_v["use_military_time"])
    def toggle_time_format():
        settings_v["use_military_time"] = time_change.get()
        update_time()
    time_checkbox = tk.Checkbutton(
        settings_window,
        text="Military Time",
        variable=time_change,
        command=toggle_time_format
    )
    time_checkbox.pack(pady=5)
    sync_frame = Frame(settings_window)
    sync_frame.pack(pady=10, fill=tk.X)
    Label(sync_frame, text="Calendar Sync:", font=(FONT, 10)).pack(anchor=tk.W, padx=5)
    Button(sync_frame, text="Sync all to Google", command=sync_all_events, font=(FONT, 10), bg=ACCENT_COLOR, fg="black").pack(fill=tk.X, padx=5, pady=2)
    Button(sync_frame, text="Pull from Google", command=pull_and_merge_events, font=(FONT, 10), bg=ACCENT_COLOR, fg="black").pack(fill=tk.X, padx=5, pady=2)
    Button(sync_frame, text="Setup Shared Calendar", command=setup_shared_calendar, font=(FONT, 10), bg=ACCENT_COLOR, fg="black").pack(fill=tk.X, padx=5, pady=2)
    Button(sync_frame, text="Sync to Shared Calendar", command=sync_to_shared_calendar, font=(FONT, 10), bg=ACCENT_COLOR, fg="black").pack(fill=tk.X, padx=5, pady=2)
    font_frame = Frame(settings_window)
    font_frame.pack(pady=10, fill=tk.X)
    Label(font_frame, text="Select Font:", font=(FONT, 10)).pack(anchor=tk.W, padx=5)


    font_menu = tk.OptionMenu(
        font_frame,
        font_var,
        *available_fonts,
        command=lambda _: update_font()
    )
    font_menu.config(
        font=(FONT, 10),
        bg=ACCENT_COLOR,
        fg="black",
        activebackground=ACCENT_COLOR,
        activeforeground="black"
    )
    font_menu.pack(fill=tk.X, padx=5)

def manage_users():
    win = Toplevel(window)
    win.title("Manage Users")
    win.geometry("300x300")
    def login_new_user():
        email = custom_askstring("Login", "Enter Name:")
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
    Button(win, text="Login New User", command=login_new_user, font=(FONT, 10), bg=ACCENT_COLOR, fg="black").pack(side=tk.LEFT, padx=20, pady=20)
    Button(win, text="Logout Selected", command=logout_user, font=(FONT, 10), bg=ACCENT_COLOR, fg="black").pack(side=tk.RIGHT, padx=20, pady=20)
    refresh_user_list()

def sync_event(date):
    if date not in events or not events[date]:
        messagebox.showinfo("Info", "No event to sync for this date.")
        return
    event_data = events[date][0] 
    try:
        service = get_calendar_service()
        
        date_obj = datetime.strptime(date, "%m/%d/%Y")
        start_time = event_data.get('start_time', '09:00')
        end_time = event_data.get('end_time', '10:00')
        
        start_datetime = datetime.combine(
            date_obj.date(),
            datetime.strptime(start_time, "%H:%M").time()
        )
        end_datetime = datetime.combine(
            date_obj.date(),
            datetime.strptime(end_time, "%H:%M").time()
        )
        
        event = {
            'summary': event_data['text'],
            'start': {'dateTime': start_datetime.isoformat(), 'timeZone': 'America/New_York'},
            'end': {'dateTime': end_datetime.isoformat(), 'timeZone': 'America/New_York'},
        }
        if 'description' in event_data:
            event['description'] = event_data['description']
            
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
        count = 0
        for user, service in user_services.items():
            for date, evt_list in events.items():
                for i, evt in enumerate(evt_list):
                    if evt.get(f"{user}_id"):
                        continue
                        
                    date_obj = datetime.strptime(date, "%m/%d/%Y")
                    start_time = evt.get('start_time', '09:00')
                    end_time = evt.get('end_time', '10:00')
                    
                    start_datetime = datetime.combine(
                        date_obj.date(),
                        datetime.strptime(start_time, "%H:%M").time()
                    )
                    end_datetime = datetime.combine(
                        date_obj.date(),
                        datetime.strptime(end_time, "%H:%M").time()
                    )
                    
                    event_body = {
                        'summary': evt["text"],
                        'start': {'dateTime': start_datetime.isoformat(), 'timeZone': 'America/New_York'},
                        'end': {'dateTime': end_datetime.isoformat(), 'timeZone': 'America/New_York'},
                    }
                    if 'description' in evt:
                        event_body['description'] = evt['description']
                    
                    created_event = service.events().insert(calendarId='primary', body=event_body).execute()
                    evt[f"{user}_id"] = created_event["id"]
                    count += 1
                    
        save_events_to_file()
        messagebox.showinfo("Success", f"{count} event(s) synced to all user calendars.")
    except Exception as e:
        messagebox.showerror("Error", f"Sync failed: {e}")

def pull_and_merge_events():
    added = 0
    try:
        for user, service in user_services.items():
            now = datetime.utcnow().isoformat() + 'Z'
            result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            for gevent in result.get('items', []):
                summary = gevent.get('summary')
                if not summary:
                    continue
                    
                g_id = gevent.get('id')
                start = gevent['start'].get('dateTime', gevent['start'].get('date'))
                end = gevent['end'].get('dateTime', gevent['end'].get('date'))
                
                try:
                    local_tz = pytz.timezone('America/New_York')
                    
                    if 'T' in start:
                        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        start_local = start_dt.astimezone(local_tz)
                        date_str = start_local.strftime("%m/%d/%Y")
                        start_time = start_local.strftime("%H:%M")
                    else:
                        start_dt = datetime.fromisoformat(start)
                        date_str = start_dt.strftime("%m/%d/%Y")
                        start_time = "00:00"
                    
                    if 'T' in end:
                        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                        end_local = end_dt.astimezone(local_tz)
                        end_time = end_local.strftime("%H:%M")
                    else:
                        end_dt = datetime.fromisoformat(end)
                        end_time = "23:59"
                    
                    if date_str not in events:
                        events[date_str] = []
                        
                    already_exists = any(
                        e.get(f"{user}_id") == g_id or 
                        (isinstance(e, dict) and e.get('text') == f"[{user}] {summary}")
                        for e in events[date_str]
                    )
                    
                    if not already_exists:
                        new_event = {
                            "text": f"[{user}] {summary}",
                            f"{user}_id": g_id,
                            "start_time": start_time,
                            "end_time": end_time,
                            "assigned_to": user
                        }
                        if gevent.get('description'):
                            new_event['description'] = gevent['description']
                            
                        events[date_str].append(new_event)
                        added += 1
                        
                except ValueError as e:
                    print(f"Error parsing event: {e}")
                    continue
                    
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

def custom_askstring(prompt_title, prompt_text):
    def on_submit():
        user_input = entry.get()
        result[0] = user_input
        dialog.destroy()

    def on_cancel():
        result[0] = None
        dialog.destroy()

    result = [None]
    dialog = Toplevel(window)
    dialog.title(prompt_title)
    dialog.geometry("300x150")

    label = Label(dialog, text=prompt_text)
    label.pack(pady=10)

    entry = Entry(dialog)
    entry.pack(pady=5)

    button_frame = Frame(dialog)
    button_frame.pack(pady=10)

    submit_button = Button(button_frame, text="Submit", command=on_submit, font=(FONT, 10), bg=ACCENT_COLOR, fg="black")
    submit_button.pack(side=LEFT, padx=10)

    cancel_button = Button(button_frame, text="Cancel", command=on_cancel, font=(FONT, 10), bg=ACCENT_COLOR, fg="black")
    cancel_button.pack(side=LEFT, padx=10)

    dialog.transient(window)
    dialog.grab_set()
    window.wait_window(dialog)

    return result[0]

def update_font():
    new_font = font_var.get()

    clock_label.config(font=(new_font, 24, "bold"))
    date_label.config(font=(new_font, 24, "bold"))
    event_tab_button.config(font=(new_font, 10))
    upcoming_tab_button.config(font=(new_font, 10))
    event_text.config(font=(new_font, 10))
    if weather_label:
        weather_label.config(font=(new_font, 10))
    for btn in buttons:
        btn.config(font=(new_font, 10))

button_list = [
    ("Add Event", lambda: add_event(Cal.get_date())),
    ("Delete Event", lambda: delete_event(Cal.get_date())),
    ("Go to Today", lambda: go_to_today()),
    ("Change User", change_main_user),
    ("Settings", settings),
    ("Manage Users", manage_users),
    ("Update Weather", update_weather)
]

buttons = []

for i, (text, cmd) in enumerate(button_list):
    btn = Button(button_frame, text=text, font=(FONT, 10), bg=ACCENT_COLOR, command=cmd)
    btn.grid(row=0, column=i, sticky="nsew", padx=5)
    buttons.append(btn)

for i in range(len(button_list)):
    button_frame.columnconfigure(i, weight=1)

# initialization

if not os.path.exists('credentials.json'):
    messagebox.showerror("Missing Credentials", 
        "Google Calendar integration requires credentials.json file")
else:
    try:
        for token_file in os.listdir(USER_TOKENS_DIR):
            if token_file.endswith('_token.json'):
                email = token_file.replace('_token.json', '')
                try:
                    creds = Credentials.from_authorized_user_file(os.path.join(USER_TOKENS_DIR, token_file), SCOPES)
                    if creds and creds.valid:
                        service = build('calendar', 'v3', credentials=creds)
                        user_services[email] = service
                except Exception as e:
                    print(f"Failed to load token for {email}: {e}")
    except Exception as e:
        messagebox.showerror("Initialization Error", f"Failed to initialize: {str(e)}")



update_time()
window.protocol("WM_DELETE_WINDOW", on_closing)
Cal.bind("<<CalendarSelected>>", update_date)
show_tab("details")
update_date()

# run it
window.mainloop()