import os
import json
import tkinter as tk
import pandas as pd
from tkinter import ttk, colorchooser
from datetime import datetime
import requests

MINUTE = 60 * 1000
SECOND = 1000

UPDATE_INTERVAL = 5 * MINUTE

def get_conf():
    global conf
    if os.path.exists('conf.json'):
        with open('conf.json', 'r', encoding='utf-8') as f:
            conf = json.load(f)
    else:
        exit(1)

get_conf()

def get_schedule_text():
    try:
        url = conf.get("google_sheet_url", "")
        df = pd.read_csv(url, encoding='utf-8')
        now = datetime.now()
        current_hour = now.hour
        current_weekday = now.strftime("%A")

        current_schedule = df.loc[df['time'] == f"{current_hour}:00", current_weekday].values[0]
        if pd.isna(current_schedule):
            current_schedule = "No schedule"

        today_df = df[[ 'time', current_weekday ]].copy()
        remaining_schedule = today_df[today_df['time'].apply(lambda t: int(t.split(':')[0])) > current_hour]
        remaining_schedule = remaining_schedule[remaining_schedule[current_weekday].notna()]
        remaining_schedule = remaining_schedule[remaining_schedule[current_weekday].str.lower() != "sleep"]

        remaining_text = ""
        for _, row in remaining_schedule.iterrows():
            remaining_text += f"{row['time']} - {row[current_weekday]}\n"

        full_text = f"{current_schedule}\n\n{remaining_text.strip()}"
        return full_text
    except Exception as e:
        return "Schedule: N/A"

class DigitalClock(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Digital Clock")
        self.geometry("600x300")
        self.configure(bg="#111")

        self.show_seconds = True
        self.is_24hour = True
        self.font_name = "Segoe UI"
        self.time_font_size = 200
        self.date_font_size = 50
        self.fullscreen = False
        self.menu_visible = True

        self.weather_label = tk.Label(self, font=(self.font_name, 16, "bold"),
                                      fg="#ffffff", bg="#111", anchor="w", justify="left")
        self.weather_label.place(x=10, y=10)
        self.weather_label.config(text="Weather: N/A")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Modern.TButton",
            font=(self.font_name, 12, "bold"),
            padding=10,
            foreground="#fff",
            background="#333",
            borderwidth=0,
            focusthickness=3,
            focuscolor="none"
        )
        style.map(
            "Modern.TButton",
            background=[("active", "#555"), ("pressed", "#777")]
        )

        self.time_label = tk.Label(self, font=(self.font_name, self.time_font_size, "bold"),
                                   fg="#ffffff", bg="#111")
        self.time_label.pack(expand=True)

        self.date_label = tk.Label(self, font=(self.font_name, self.date_font_size),
                                   fg="#ffffff", bg="#111")
        self.date_label.pack(anchor="center", pady=(0, 10))

        self.schedule_label = tk.Label(self, font=(self.font_name, 14, "bold"),
                                    fg="#ffffff", bg="#111", anchor="e", justify="right")
        self.schedule_label.place(relx=.99, y=10, anchor="ne")
        self.schedule_label.config(text=get_schedule_text())


        self.ctrl = tk.Frame(self, bg="#111")
        self.ctrl.pack(side="bottom", fill="x", pady=10)

        self.btn_toggle_hour = ttk.Button(self.ctrl, text="12 Hr", style="Modern.TButton",
                                          command=self.toggle_hour_format)
        self.btn_toggle_hour.pack(side="left", padx=6)

        self.btn_toggle_sec = ttk.Button(self.ctrl, text="Hide Seconds", style="Modern.TButton",
                                         command=self.toggle_seconds)
        self.btn_toggle_sec.pack(side="left", padx=6)

        self.btn_smaller = ttk.Button(self.ctrl, text="Font -", style="Modern.TButton",
                                      command=self.decrease_font)
        self.btn_smaller.pack(side="left", padx=6)

        self.btn_bigger = ttk.Button(self.ctrl, text="Font +", style="Modern.TButton",
                                     command=self.increase_font)
        self.btn_bigger.pack(side="left", padx=6)

        self.btn_font_color = ttk.Button(self.ctrl, text="Font Color", style="Modern.TButton",
                                         command=self.change_font_color)
        self.btn_font_color.pack(side="left", padx=6)

        self.btn_bg_color = ttk.Button(self.ctrl, text="Backround Color", style="Modern.TButton",
                                       command=self.change_bg_color)
        self.btn_bg_color.pack(side="left", padx=6)

        self.btn_fullscreen = ttk.Button(self.ctrl, text="Full Screen", style="Modern.TButton",
                                         command=self.toggle_fullscreen)
        self.btn_fullscreen.pack(side="left", padx=6)

        self.btn_quit = ttk.Button(self.ctrl, text="Exit", style="Modern.TButton",
                                   command=self.destroy)
        self.btn_quit.pack(side="right", padx=6)

        self.bind("<Control-h>", self.toggle_menu)
        self.bind("<Control-f>", self.toggle_fullscreen)
        self.bind("<Control-s>", self.toggle_seconds)
        self.bind("<Control-z>", self.decrease_font)
        self.bind("<Control-x>", self.increase_font)
        self.bind("<Control-w>", self.update_weather)
        self.bind("<Control-c>", self.update_schedule)
        self.bind("<Escape>", lambda e: self.exit_fullscreen())  # ESC로 전체화면 해제

        self.update_clock()
        self.update_weather()
        self.update_schedule()
        self.toggle_fullscreen()
        self.toggle_menu()

    def format_time(self, now: datetime) -> str:
        if self.is_24hour:
            return now.strftime("%H:%M:%S" if self.show_seconds else "%H:%M")
        else:
            return now.strftime("%I:%M:%S %p" if self.show_seconds else "%I:%M %p")

    def update_clock(self):
        now = datetime.now()
        self.time_label.config(text=self.format_time(now))
        self.date_label.config(text=now.strftime("%A, %Y-%m-%d"))

        self.btn_toggle_hour.config(text="24 Hr" if not self.is_24hour else "12 Hr")
        self.btn_toggle_sec.config(text="Hide Seconds" if self.show_seconds else "Show Seconds")
        self.btn_fullscreen.config(text="Window Screen" if self.fullscreen else "Full Screen")

        self.after(200 if self.show_seconds else 800, self.update_clock)
    
    def update_schedule(self, event=None):
        self.schedule_label.config(text=get_schedule_text())

        self.after(UPDATE_INTERVAL, self.update_schedule)

    def update_weather(self, event=None):
        precip_code_dict = {
            "0": "No Rain",
            "1": "Rain",
            "2": "Rain/Snow",
            "3": "Snow",
            "4": "Snow/Rain"
        }

        sky_code_dict = {
            "DB01": "Clear",
            "DB02": "Partly Cloudy",
            "DB03": "Mostly Cloudy",
            "DB04": "Overcast"
        }
        try:
            url = f'https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php?stn=108&help=1&authKey={conf.get("auth_key", "")}'
            response = requests.get(url, verify=False)
            current_temp = response.text.split("\n")[54].split()[11]

            url = f'https://apihub.kma.go.kr/api/typ01/url/fct_afs_dl.php?reg=11B10101&disp=0&help=1&authKey={conf.get("auth_key", "")}'
            response = requests.get(url, verify=False)
            sky_code = sky_code_dict[response.text.split("\n")[23].split()[14]]
            precip_code = precip_code_dict[response.text.split("\n")[23].split()[15]]
            self.weather_label.config(text=f"🌡 {current_temp}°C \n☁ {sky_code} \n☔ {precip_code}")
        except Exception as e:
            self.weather_label.config(text="Weather: N/A")
        
        self.after(UPDATE_INTERVAL, self.update_weather)



    def toggle_hour_format(self):
        self.is_24hour = not self.is_24hour

    def toggle_seconds(self, event=None):
        self.show_seconds = not self.show_seconds

    def increase_font(self, event=None):
        self.time_font_size += 6
        self.time_label.config(font=(self.font_name, self.time_font_size, "bold"))

    def decrease_font(self, event=None):
        if self.time_font_size > 24:
            self.time_font_size -= 6
            self.time_label.config(font=(self.font_name, self.time_font_size, "bold"))

    def change_font_color(self):
        color = colorchooser.askcolor(title="Choose Font Color")
        if color[1]:
            self.time_label.config(fg=color[1])
            self.date_label.config(fg=color[1])
            self.weather_label.config(fg=color[1])

    def change_bg_color(self):
        color = colorchooser.askcolor(title="Choose Background color")
        if color[1]:
            self.config(bg=color[1])
            self.time_label.config(bg=color[1])
            self.date_label.config(bg=color[1])
            self.weather_label.config(bg=color[1])
            self.ctrl.config(bg=color[1])

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.attributes("-fullscreen", self.fullscreen)

    def exit_fullscreen(self):
        if self.fullscreen:
            self.fullscreen = False
            self.attributes("-fullscreen", False)

    def toggle_menu(self, event=None):
        if self.menu_visible:
            self.ctrl.pack_forget()
            self.menu_visible = False
        else:
            self.ctrl.pack(side="bottom", fill="x", pady=10)
            self.menu_visible = True


if __name__ == "__main__":
    app = DigitalClock()
    app.mainloop()
