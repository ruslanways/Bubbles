import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from random import randrange, choice
import time
import datetime
import pygame
import re
import sqlite3
import sys
import os


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# --- Constants ---
WIN_SCORE = 35
LEVEL_3_THRESHOLD = 30
LEVEL_2_THRESHOLD = 20
LEVEL_3_DELAY_MS = 650
LEVEL_2_DELAY_MS = 800
LEVEL_1_DELAY_MS = 1000
MIN_RADIUS_FACTOR = 0.015
MAX_RADIUS_FACTOR = 0.09
DB_MAX_ENTRIES = 100
COLORS = ["red", "orange", "yellow", "green", "blue", "LightSkyBlue1"]
BG_COLOR = "LightSkyBlue1"

# --- Game state ---
before_pause_time = 0
all_pause_time = 0
points = 0
pause_music = False

# --- Sound paths ---
intro_music = resource_path("sound/intro.mp3")
win_music = resource_path("sound/win.wav")
music_1_level = resource_path("sound/stage1.mp3")
music_2_level = resource_path("sound/stage2.mp3")
music_3_level = resource_path("sound/stage3.mp3")
music = intro_music

# --- Initialize audio ---
pygame.mixer.init()
pygame.mixer.music.load(music)
pygame.mixer.music.play(-1, 0.0)

hit_sound = pygame.mixer.Sound(resource_path("sound/hit.mp3"))
fail_hit_sound = pygame.mixer.Sound(resource_path("sound/fail.mp3"))

# --- Create main window ---
root = tk.Tk()

# Center the root window
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
shift_x_root = int(screen_width / 2 - screen_width / 3)
shift_y_root = int(screen_height / 2 - screen_height / 3)
root.geometry(
    f"{(2 * screen_width) // 3}x{(2 * screen_height) // 3}+{shift_x_root}+{shift_y_root - 30}"
)
root.resizable(False, False)
root.title("BUBBLES")

# --- Create canvas for drawing bubbles, text, frames ---
canv = tk.Canvas(root, bg=BG_COLOR)
canv.pack(fill=tk.BOTH, expand=1)

# --- Splash screen logo ---
img = tk.PhotoImage(file=resource_path("img/logo.gif"))
canv.update_idletasks()
root_width = logo_img_x = root.winfo_width() // 2
root_height = root.winfo_height() // 2
logo_img_y = int(0.0625 * root.winfo_height()) + img.height() // 2
logo = canv.create_image(logo_img_x, logo_img_y, image=img)

# --- Initialize placeholder widgets used later ---
text_score = canv.create_text(-100, 0, text="")
pause_text_banner = canv.create_text(-100, 0, text="")
frm_score_table = tk.Frame(root, bg=BG_COLOR)
ball = canv.create_oval(-100, 0, 0, 0)


def cancel_current_level():
    """Cancel the scheduled new_ball callback for the current level."""
    if points >= LEVEL_3_THRESHOLD:
        canv.after_cancel(level_top)
    elif points >= LEVEL_2_THRESHOLD:
        canv.after_cancel(level_middle)
    else:
        canv.after_cancel(level_start)


def new_ball():
    """Create a random-sized ball at a random location and schedule the next one."""
    global \
        radius_ball, \
        x_ball, \
        y_ball, \
        ball, \
        color, \
        points, \
        level_top, \
        level_middle, \
        level_start, \
        music, \
        radius_relative

    canv.delete(ball)

    canv.update_idletasks()
    r = randrange(
        int(MIN_RADIUS_FACTOR * canv.winfo_width()),
        int(MAX_RADIUS_FACTOR * canv.winfo_height()),
    )
    radius_ball = r
    x = randrange(r + 5, canv.winfo_width() - r - 5)
    y = randrange(r + 5, canv.winfo_height() - r - 5)
    x_ball = x
    y_ball = y
    radius_relative = radius_ball / (
        MAX_RADIUS_FACTOR * canv.winfo_height() - MIN_RADIUS_FACTOR * canv.winfo_width()
    )
    color = choice(COLORS)
    ball = canv.create_oval(x - r, y - r, x + r, y + r, fill=color, width=0.1)

    if points >= LEVEL_3_THRESHOLD:
        if music != music_3_level:
            music = music_3_level
            pygame.mixer.music.load(music)
            pygame.mixer.music.play(-1, 0.0)
        level_top = canv.after(LEVEL_3_DELAY_MS, new_ball)

    elif points >= LEVEL_2_THRESHOLD:
        if music != music_2_level:
            music = music_2_level
            pygame.mixer.music.load(music)
            pygame.mixer.music.play(-1, 0.0)
        level_middle = canv.after(LEVEL_2_DELAY_MS, new_ball)

    else:
        level_start = canv.after(LEVEL_1_DELAY_MS, new_ball)


def on_click(event):
    """Handle click on canvas: score hit/miss and end the game on miss or win."""
    global \
        points, \
        x_ball, \
        text_score, \
        timer, \
        before_pause_time, \
        all_pause_time, \
        user_name, \
        date_game, \
        radius_ball, \
        radius_relative

    if (event.x - x_ball) ** 2 + (event.y - y_ball) ** 2 <= radius_ball**2:
        hit_sound.play()
        if color == BG_COLOR:
            points -= 5
        elif radius_relative <= 0.25:
            points += 7
        elif radius_relative <= 0.50:
            points += 5
        elif radius_relative <= 0.75:
            points += 2
        else:
            points += 1

        # Remove the ball on successful hit
        canv.delete(text_score)
        canv.delete(ball)
        canv.update_idletasks()
        text_score = canv.create_text(
            canv.winfo_width() - 10,
            10,
            text=f"{user_name}\nScore: {points}",
            font="Arial 20",
            anchor=tk.NE,
        )

        if points >= WIN_SCORE:
            canv.delete(text_score)
            canv.delete(ball)
            canv.after_cancel(level_top)
            pygame.mixer.music.load(win_music)
            pygame.mixer.music.play()
            finish_time = time.time()
            timer = finish_time - start_time + all_pause_time
            messagebox.showinfo(
                "winner",
                f"B R A V O !!!\n{user_name}\nYou win with score: {points}\nTime: {round(timer)} sec.",
            )
            date_game = (datetime.date.today()).strftime("%b-%d-%Y")
            save_score()
            points = 0
            all_pause_time = 0
            timer = 0
            canv.unbind("<Button-1>")
            canv.unbind_all("<space>")
            pre_start(after_game=1)
    else:
        fail_hit_sound.play()
        canv.delete(text_score)
        canv.delete(ball)
        cancel_current_level()
        pygame.mixer.music.stop()
        finish_time = time.time()
        timer = finish_time - start_time + all_pause_time
        canv.update_idletasks()
        text_score = canv.create_text(
            canv.winfo_width() - 10,
            10,
            text=f"{user_name}\nScore: {points}\nTime: {round(timer)} sec",
            font="Arial 20",
            anchor=tk.NE,
        )
        date_game = (datetime.date.today()).strftime("%b-%d-%Y")
        save_score()
        points = 0
        all_pause_time = 0
        timer = 0
        canv.unbind("<Button-1>")
        canv.unbind_all("<space>")
        pre_start(after_game=1)


def pause_game(*args):
    """Pause the game: stop ball spawning, show pause banner, pause music."""
    global pause_text_banner, pause_music, before_pause_time

    pause_text_banner = canv.create_text(
        canv.winfo_width() / 2,
        canv.winfo_height() / 2,
        text="PAUSE",
        fill="red",
        font="Arial 60",
    )
    pygame.mixer.music.pause()
    pause_music = True

    canv.unbind("<Button-1>")

    before_pause_time = time.time()

    canv.delete(ball)
    cancel_current_level()

    canv.bind_all("<space>", start_game)


def start_game(*args):
    """Start or resume the game with appropriate music and event bindings."""
    global \
        ball, \
        text_score, \
        points, \
        start_time, \
        logo, \
        music, \
        pause_text_banner, \
        pause_music, \
        before_pause_time, \
        all_pause_time, \
        user_name, \
        frm_score_table

    root.unbind("<Return>")

    if pause_music:
        pygame.mixer.music.unpause()
        pause_music = False
        after_pause_time = time.time()
        all_pause_time += after_pause_time - before_pause_time
    else:
        pygame.mixer.music.stop()
        music = music_1_level
        pygame.mixer.music.load(music)
        pygame.mixer.music.play(-1, 0.0)
        start_time = time.time()

    frm_score_table.destroy()
    canv.delete(text_score)
    canv.delete(logo)
    canv.delete(pause_text_banner)
    canv.delete(cnv_frm_start)

    canv.update_idletasks()
    text_score = canv.create_text(
        canv.winfo_width() - 10,
        10,
        text=f"{user_name}\nScore: {points}",
        font="Arial 20",
        anchor=tk.NE,
    )

    new_ball()

    canv.bind("<Button-1>", on_click)
    canv.bind_all("<space>", pause_game)


def pre_start(after_game=None):
    """Show the Start and Quit buttons."""
    global btn_start, btn_quit, cnv_frm_start

    root.unbind("<Return>")

    canv.delete(cnv_frm_login)

    frm_start = tk.Frame(root)
    frm_start.pack()
    btn_start = tk.Button(frm_start, text="Start", command=start_game)
    btn_start.pack(side=tk.LEFT)
    root.bind("<Return>", start_game)
    btn_quit = tk.Button(frm_start, text="Quit", command=root.destroy)
    btn_quit.pack(side=tk.LEFT)
    frm_start.update_idletasks()
    if after_game:
        cnv_frm_start = canv.create_window(root_width, root_height, window=frm_start)
    else:
        cnv_frm_start = canv.create_window(
            logo_img_x,
            logo_img_y + img.height() // 2 + frm_start.winfo_height() / 2,
            window=frm_start,
        )


def validate_nickname(*args):
    """Validate the player nickname and proceed to pre-start screen."""
    global user_name
    user_name = ent_nick.get()
    pattern = re.compile(r"[\w]{1,10}$")
    if not pattern.match(user_name):
        messagebox.showerror(
            "login failure", "Nickname must contain alphanumeric string max 10 symbols"
        )
        canv.delete(cnv_frm_login)
        login()
    else:
        pre_start()


def login():
    """Show the nickname entry form."""
    global ent_nick, cnv_frm_login
    frm_login = tk.Frame(root)
    frm_login.pack()
    tk.Label(frm_login, text="Enter your nickname:").pack(side=tk.LEFT)
    ent_nick = tk.Entry(frm_login)
    ent_nick.pack(side=tk.LEFT)
    ent_nick.focus()
    tk.Button(frm_login, text="Login", command=validate_nickname).pack(side=tk.LEFT)
    root.bind("<Return>", validate_nickname)
    frm_login.update_idletasks()
    cnv_frm_login = canv.create_window(
        logo_img_x,
        logo_img_y + img.height() // 2 + frm_login.winfo_height() / 2,
        window=frm_login,
    )


def save_score():
    """Save the score to the database and display the top 10 leaderboard."""
    global frm_score_table

    with sqlite3.connect(resource_path("database.db")) as db:
        cursor = db.cursor()
        query = """CREATE TABLE IF NOT EXISTS achivements(name TEXT, score INTEGER, time INTEGER, date TEXT)"""
        cursor.execute(query)
        db.commit()

        # Keep database size limited to DB_MAX_ENTRIES rows
        query = "SELECT COUNT(*) FROM achivements"
        cursor.execute(query)
        count = cursor.fetchone()[0]
        if count == DB_MAX_ENTRIES:
            query = "DELETE FROM achivements WHERE ROWID in(SELECT ROWID FROM achivements ORDER BY score ASC, time DESC LIMIT 1)"
            cursor.execute(query)
            db.commit()

        cursor.execute(
            "INSERT INTO achivements (name, score, time, date) VALUES(?, ?, ?, ?)",
            (user_name, points, round(timer), date_game),
        )
        db.commit()

        query = "SELECT * FROM achivements ORDER BY score DESC, time ASC LIMIT 10"
        frm_score_table = tk.Frame(root, bg=BG_COLOR)
        frm_score_table.place(x=10, y=10)
        ttk.Style().configure(
            "Treeview",
            background=BG_COLOR,
            fieldbackground=BG_COLOR,
            rowheight=int(0.0564 * root_height),
        )
        columns = ("rating", "name", "score", "time", "date")
        tree = ttk.Treeview(frm_score_table, columns=columns, show="headings")
        tree.heading("rating", text="rating")
        tree.heading("name", text="nickname")
        tree.heading("score", text="score")
        tree.heading("time", text="time")
        tree.heading("date", text="date")
        tree.column("rating", width=int(0.15 * root_width), anchor=tk.CENTER)
        tree.column("name", width=int(0.24 * root_width))
        tree.column("score", width=int(0.13 * root_width), anchor=tk.CENTER)
        tree.column("time", width=int(0.19 * root_width), anchor=tk.CENTER)
        tree.column("date", width=int(0.22 * root_width), anchor=tk.CENTER)
        players = cursor.execute(query)
        i = 1
        for player in players:
            tree.insert(
                "",
                tk.END,
                values=(i, player[0], player[1], f"{player[2]} sec", player[3]),
            )
            i += 1
        tree.pack(side=tk.LEFT, fill=tk.BOTH)


login()

root.mainloop()
