import datetime
import numpy as np
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
import simpleaudio as sa
import threading
import time
import tkinter as tk
from tkinter import simpledialog
import ttkbootstrap as ttk

timer_progress_percentage = 0


def update_layout():
    if clock_24h_var.get() == 1:
        top_progress.place_configure(rely=0, relheight=0.5)
        top_progress_24h.place_configure(relheight=0.5, relwidth=1, rely=0.5)
        top_progress_24h["value"] = (
            (datetime.datetime.now().hour * 60 + datetime.datetime.now().minute)
            / 1440
            * 100
        )
    else:
        top_progress.place_configure(rely=0, relheight=1)
        top_progress_24h.place_forget()
    # Update the top_progress with the current timer progress after adjusting the layout
    top_progress["value"] = timer_progress_percentage


def update_24h_progress():
    now = datetime.datetime.now()
    seconds_since_midnight = (
        now - now.replace(hour=0, minute=0, second=0, microsecond=0)
    ).total_seconds()
    daily_progress = (seconds_since_midnight / 86400) * 100
    if clock_24h_var.get() == 1:
        top_progress_24h["value"] = daily_progress
    root.after(1000, update_24h_progress)


def play_beep(frequency=440, duration=1000, volume=0.5):
    sample_rate = 44100
    t = np.linspace(0, duration / 1000, int(sample_rate * (duration / 1000)), False)
    wave = np.sin(frequency * t * 2 * np.pi)
    audio = wave * (2**15 - 1) * volume
    audio = audio.astype(np.int16)
    play_obj = sa.play_buffer(audio, 1, 2, sample_rate)
    play_obj.wait_done()


def toggle_top_progress():
    if toggle_top_progress_var.get() == 1:
        top_root.deiconify()
        if clock_24h_var.get() == 0:
            top_progress.place_configure(rely=0, relheight=1)
        else:
            top_progress.place_configure(rely=0.5, relheight=0.5)
            top_progress_24h.place_configure(relheight=0.5)
    else:
        top_root.withdraw()


def beep():
    global time_left, paused
    time_left = interval.get() * 60
    update_interval_label()
    while running:
        while time_left > 0 and running:
            if not paused:
                time.sleep(1)
                time_left -= 1
                update_progress(time_left)
            else:
                time.sleep(0.1)
        if not running:
            reset_progress()
            break
        if not paused:
            play_beep(frequency=volume.get(), duration=1000)
        if repeat_var.get() == 0:
            break
        if repeat_var.get() == 1:
            time_left = interval.get() * 60
            update_progress(time_left)


def set_interval():
    new_interval = simpledialog.askinteger(
        "Input", "Enter interval in minutes:", parent=root, minvalue=1, maxvalue=1440
    )
    if new_interval:
        interval.set(new_interval)
        update_interval_label()
        reset_progress()


def update_interval_label():
    current_interval_label.config(text=f"Current Interval: {interval.get()} min")


def update_progress(time_left):
    global timer_progress_percentage
    timer_progress_percentage = 100 - (time_left / (interval.get() * 60) * 100)
    progress["value"] = timer_progress_percentage
    top_progress[
        "value"
    ] = timer_progress_percentage  # Use the global variable to set the value
    if toggle_top_progress_var.get() == 1:
        if clock_24h_var.get() == 1:
            top_progress.place_configure(rely=0, relheight=0.5)
        else:
            top_progress.place_configure(rely=0, relheight=1)
    root.update_idletasks()


def reset_progress():
    progress["value"] = 0
    if toggle_top_progress_var.get() == 1:
        top_progress["value"] = 0
    root.update_idletasks()


def start_beeping():
    global running, paused
    if running:
        return
    running = True
    paused = False
    threading.Thread(target=beep, daemon=True).start()


def stop_beeping():
    global running, paused, time_left
    if running:
        running = False
        paused = False
        time_left = 0
        update_progress(time_left)
        reset_progress()


def pause_beeping():
    global paused
    paused = not paused


def create_image():
    # Create an image for the tray icon
    image = Image.new("RGBA", (64, 64), (255, 255, 255, 0))
    dc = ImageDraw.Draw(image)

    center = (32, 32)
    radius = 30

    dc.ellipse(
        [
            center[0] - radius,
            center[1] - radius,
            center[0] + radius,
            center[1] + radius,
        ],
        outline="black",
        fill="white",
    )

    hour_hand_length = 20
    hour_angle = (10 / 12) * 360  # 10 hours, in degrees
    hour_end = (
        center[0] + hour_hand_length * np.sin(np.radians(hour_angle)),
        center[1] - hour_hand_length * np.cos(np.radians(hour_angle)),
    )
    dc.line([center, hour_end], fill="black", width=4)

    # Minute hand
    minute_hand_length = 25
    minute_angle = (10 / 60) * 360  # 10 minutes, in degrees
    minute_end = (
        center[0] + minute_hand_length * np.sin(np.radians(minute_angle)),
        center[1] - minute_hand_length * np.cos(np.radians(minute_angle)),
    )
    dc.line([center, minute_end], fill="black", width=2)

    return image


def show_window(icon):
    icon.stop()
    root.after(0, root.deiconify)


def exit_program(icon):
    icon.stop()
    root.destroy()


def toggle_24h_clock():
    update_layout()
    update_24h_progress()
    # Directly update the top_progress with the current timer progress percentage
    top_progress["value"] = timer_progress_percentage
    # Continue to use root.after to ensure any delayed updates are handled properly
    root.after(100, lambda: top_progress.configure(value=timer_progress_percentage))


def show_tray_icon():
    global icon
    icon = pystray.Icon(
        "VizTime",
        create_image(),
        "VizTime",
        menu=(item("Show", show_window, default=True), item("Exit", exit_program)),
    )
    icon.run()


def toggle_window(icon, item):
    show_window(icon)


def on_close():
    if minimize_to_tray_var.get() == 1:
        minimize_to_tray()
    else:
        root.destroy()


def minimize_to_tray():
    if minimize_to_tray_var.get() == 1:
        root.withdraw()
        show_tray_icon()
    else:
        root.deiconify()


root = ttk.Window(themename="minty")
root.title("VizTime")
root.resizable(True, True)

clock_24h_var = tk.IntVar(value=0)

toggle_top_progress_var = tk.IntVar(value=1)
repeat_var = tk.IntVar(value=1)
minimize_to_tray_var = tk.IntVar(value=0)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

window_height = 280
window_width = 270

interval = tk.IntVar(value=15)
volume = tk.IntVar(value=1000)
running = False
paused = False

current_interval_label = tk.Label(root, text="Current Interval: 15 min")
current_interval_label.pack(pady=10)

set_interval_button = ttk.Button(
    root, text="Set Interval", command=set_interval, style="info.TButton"
)
set_interval_button.pack(pady=(5, 15))

toggle_top_progress_checkbox = ttk.Checkbutton(
    root,
    text="Top Progress Bar",
    variable=toggle_top_progress_var,
    command=toggle_top_progress,
    style="info.TCheckbutton",
)
toggle_top_progress_checkbox.pack(pady=5, padx=25, anchor="w")

clock_24h_checkbox = ttk.Checkbutton(
    root,
    text="24-Hour Clock",
    variable=clock_24h_var,
    style="info.TCheckbutton",
    command=toggle_24h_clock,
)
clock_24h_checkbox.pack(pady=5, padx=25, anchor="w")

repeat_checkbox = ttk.Checkbutton(
    root, text="Repeat After Interval", variable=repeat_var, style="info.TCheckbutton"
)
repeat_checkbox.pack(pady=5, padx=25, anchor="w")

minimize_to_tray_checkbox = ttk.Checkbutton(
    root,
    text="Minimize to Tray",
    variable=minimize_to_tray_var,
    style="info.TCheckbutton",
)
minimize_to_tray_checkbox.pack(pady=5, padx=25, anchor="w")

progress = ttk.Progressbar(root, length=200, mode="determinate")
progress.pack(pady=(10, 5))

start_button = ttk.Button(
    root, text="Start", command=start_beeping, style="primary.TButton"
)
start_button.pack(side="left", padx=5, pady=10)

pause_button = ttk.Button(
    root, text="Pause/Resume", command=pause_beeping, style="warning.TButton"
)
pause_button.pack(side="left", padx=5, pady=10)

stop_button = ttk.Button(
    root, text="Reset", command=stop_beeping, style="secondary.TButton"
)
stop_button.pack(side="right", padx=5, pady=10)

top_root = tk.Toplevel(root)
top_root.overrideredirect(True)
top_root.attributes("-topmost", True)
screen_width = top_root.winfo_screenwidth()
top_root.geometry(f"{screen_width}x14+0+0")

top_progress = ttk.Progressbar(top_root, length=screen_width, mode="determinate")
top_progress.pack(fill=tk.BOTH, expand=True)
top_progress.place(relx=0, rely=0.5, relwidth=1, relheight=1)

top_progress_24h = ttk.Progressbar(
    top_root,
    length=screen_width,
    mode="determinate",
    style="dark.Horizontal.TProgressbar",
)
top_progress_24h.pack(fill=tk.BOTH, expand=True)
top_progress_24h.place(relx=0, rely=0, relwidth=1, relheight=0.5)

x_cordinate = int((screen_width / 2) - (window_width / 2))
y_cordinate = int((screen_height / 2) - (window_height / 2))

root.after(1000, update_24h_progress)  # Start updating the 24-hour progress

root.geometry(
    "{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate)
)

root.protocol("WM_DELETE_WINDOW", on_close)
update_layout()
root.mainloop()
