import tkinter as tk
from tkinter import Label
from tkcalendar import Calendar
import time

window = tk.Tk()
window.title("The House Hub")

# variables
width = 500
height = 500
x = 500
y = 200

# window size
window.geometry(f"{width}x{height}+{x}+{y}")

# grid config
window.grid_rowconfigure(0, weight=0)
window.grid_rowconfigure(1, weight=0)
window.grid_rowconfigure(2, weight=1)
window.grid_columnconfigure(0, weight=1)

# time label
clock_label = Label(window, font=('Segoe UI', 20), foreground='black')
clock_label.grid(row=0, column=0, columnspan=3, pady=10, sticky="ew")

# date label
date_label = Label(window, text="", font=('Segoe UI', 20))
date_label.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

# calendar
Cal = Calendar(
    window,
    selectmode="day",
    date_pattern="mm/dd/yyyy"
    )
Cal.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)

# time update function
def update_time():
    current_time = time.strftime('%I:%M:%S %p')
    clock_label.config(text=current_time)
    clock_label.after(1000, update_time)
update_time()

# date update function
def update_date(event=None):
    date = Cal.get_date()
    date_label.config(text="The date is " + date)
Cal.bind("<<CalendarSelected>>", update_date)
update_date()

# run it
window.mainloop()