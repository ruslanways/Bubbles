from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from random import randrange, choice
import time
import datetime
import pygame
from pygame.mixer import pause
import re
import sqlite3

# nullify some parameters needs further for timer implementation
before_pause_time = 0
all_pause_time = 0

# nullify points
points = 0
colors = ["red", "orange", "yellow", "green", "blue", "LightSkyBlue1"]

# initialising a music
pause_music = False
intro_music = "sound/intro.mp3"
win_music = "sound/win.wav"
music_1_level = "sound/stage1.mp3"
music_2_level = "sound/stage2.mp3"
music_3_level = "sound/stage3.mp3"
music = intro_music

pygame.mixer.init()
pygame.mixer.music.load(music)
pygame.mixer.music.play(-1, 0.0)

hit_sound = pygame.mixer.Sound("sound/hit.mp3")
fail_hit_sound = pygame.mixer.Sound("sound/fail.mp3")


# create main window - root
root = Tk()

# centering the root window
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
shift_x_root = int(screen_width / 2 - screen_width / 3)
shift_y_root = int(screen_height / 2 - screen_height / 3)
root.geometry(
    f"{(2*screen_width)//3}x{(2*screen_height)//3}+{shift_x_root}+{shift_y_root-30}"
)
# making root window not resizable
root.resizable(False, False)
root.title("BUBBLES")

# create a canvas where we can draw a bubbles (balls), text, frames and so on
canv = Canvas(root, bg="LightSkyBlue1")
canv.pack(fill=BOTH, expand=1)

# adding picture - splash screen
img = PhotoImage(file="img/logo.gif")
root.update_idletasks()
root_width = logo_img_x = root.winfo_width() // 2
root_height = root.winfo_height() // 2
logo_img_y = int(0.0625 * root.winfo_height()) + img.height() // 2
logo = canv.create_image(logo_img_x, logo_img_y, image=img)

# nullify (initialise) text widgets, first ball, score-table that we'll use further
text_score = canv.create_text(-100, 0, text="")
pause_text_banner = canv.create_text(-100, 0, text="")
frm_score_table = Frame(root, bg="LightSkyBlue1")
ball = canv.create_oval(-100, 0, 0, 0)


def new_ball():
    """
    the function creates random sized balls in random location,
    changes levels - speed of balls appearance and music depends on player's points
    """
    global x, y, r, radius_ball, x_ball, y_ball, ball, color, points, level_top, level_middle, level_start, music, radius_relative

    canv.delete(ball)

    # x, y - coordinates of the circle center
    # r - radius
    # x_min = r + little_padding
    # y_min = r + little_padding
    # x_max = width - r - little_padding
    # y_max = height - r - little_padding

    canv.update_idletasks()
    radius_ball = r = randrange(
        int(0.015 * canv.winfo_width()), int(0.09 * canv.winfo_height())
    )
    x_ball = x = randrange(r + 5, canv.winfo_width() - r - 5)
    y_ball = y = randrange(r + 5, canv.winfo_height() - r - 5)
    radius_relative = radius_ball / (
        0.09 * canv.winfo_height() - 0.015 * canv.winfo_width()
    )
    color = choice(colors)
    ball = canv.create_oval(x - r, y - r, x + r, y + r, fill=color, width=0.1)

    if points >= 30:
        if music != music_3_level:
            music = music_3_level
            pygame.mixer.music.load(music)
            pygame.mixer.music.play(-1, 0.0)
        level_top = root.after(650, new_ball)

    elif points >= 20:
        if music != music_2_level:
            music = music_2_level
            pygame.mixer.music.load(music)
            pygame.mixer.music.play(-1, 0.0)
        level_middle = root.after(800, new_ball)

    else:
        level_start = root.after(1000, new_ball)


def click(event):
    """
    the function handles hiting the ball, counts the points and finishes the game with win or lose,
    invoke creation of database (if not exist), insert new data in it and shows score-table on the screen
    """
    global points, x_ball, text_score, timer, before_pause_time, all_pause_time, user_name, date_game, radius_ball, radius_relative

    if (event.x - x_ball) ** 2 + (event.y - y_ball) ** 2 <= radius_ball**2:
        hit_sound.play()
        if color == "LightSkyBlue1":
            points -= 5
        elif radius_relative <= 0.25:
            points += 7
        elif radius_relative <= 0.50:
            points += 5
        elif radius_relative <= 0.75:
            points += 2
        else:
            points += 1

        # видалення круга при кліку
        canv.delete(text_score)
        canv.delete(ball)
        canv.update_idletasks()
        text_score = canv.create_text(
            canv.winfo_width() - 10,
            10,
            text=f"{user_name}\nScore: " + str(points),
            font="Arial 20",
            anchor=NE,
        )

        if points >= 35:
            canv.delete(text_score)
            canv.delete(ball)
            root.after_cancel(level_top)
            pygame.mixer.music.load(win_music)
            pygame.mixer.music.play()
            finish_time = time.time()
            timer = finish_time - start_time + all_pause_time
            messagebox.showinfo(
                "winner",
                f"B R A V O !!!\n{user_name}\nYou win with score: {points}\nTime: {round(timer)} sec.",
            )
            date_game = (datetime.date.today()).strftime("%b-%d-%Y")
            data_base()
            points = 0
            all_pause_time = 0
            timer = 0
            pre_start(after_game=1)

    else:
        fail_hit_sound.play()
        canv.delete(text_score)
        canv.delete(ball)
        if points >= 30:
            root.after_cancel(level_top)
        elif points >= 20:
            root.after_cancel(level_middle)
        else:
            root.after_cancel(level_start)
        pygame.mixer.music.stop()
        finish_time = time.time()
        timer = finish_time - start_time + all_pause_time
        canv.update_idletasks()
        text_score = canv.create_text(
            canv.winfo_width() - 10,
            10,
            text=f"{user_name}\nScore: {points}\nTime: {round(timer)} sec",
            font="Arial 20",
            anchor=NE,
        )
        date_game = (datetime.date.today()).strftime("%b-%d-%Y")
        data_base()
        points = 0
        all_pause_time = 0
        timer = 0
        pre_start(after_game=1)


def paused(*args):
    """
    game pause
    """
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
    if points >= 30:
        root.after_cancel(level_top)
    elif points >= 20:
        root.after_cancel(level_middle)
    else:
        root.after_cancel(level_start)

    canv.bind_all("<space>", start_game)


def start_game(*args):
    """
    starts the game with first level with apropriate music,
    hands over job to function new_ball(),
    runs an event handlers - left mouse button click, space key
    """
    global ball, text_score, points, start_time, logo, music, pause_text_banner, pause_music, before_pause_time, all_pause_time, user_name, frm_score_table

    root.unbind("<Return>")

    if pause_music == True:
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
        text=f"{user_name}\nScore: " + str(points),
        font="Arial 20",
        anchor=NE,
    )

    new_ball()

    canv.bind("<Button-1>", click)
    canv.bind_all("<space>", paused)


def pre_start(after_game=None):
    """
    create buttons Start & Quit
    """
    global btn_start, btn_quit, cnv_frm_start

    root.unbind("<Return>")
    canv.unbind("<Button-1>")
    canv.unbind_all("<space>")

    canv.delete(cnv_frm_login)

    frm_start = Frame(root)
    frm_start.pack()
    btn_start = Button(frm_start, text="Start", command=start_game)
    btn_start.pack(side=LEFT)
    root.bind("<Return>", start_game)
    btn_quit = Button(frm_start, text="Qiut", command=root.destroy)
    btn_quit.pack(side=LEFT)
    frm_start.update_idletasks()
    if after_game:
        cnv_frm_start = canv.create_window(root_width, root_height, window=frm_start)
    else:
        cnv_frm_start = canv.create_window(
            logo_img_x,
            logo_img_y + img.height() // 2 + frm_start.winfo_height() / 2,
            window=frm_start,
        )


def nick(*args):
    """
    validates player input nickname
    """
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
    """
    asking user to enter the nickname and hand over to function nick()
    """
    global nickname, ent_nick, b, c, id1, id2, id3, cnv_frm_login, logo_img_x, logo_img_y, img, root
    frm_login = Frame(root)
    frm_login.pack()
    Label(frm_login, text="Enter your nickname:").pack(side=LEFT)
    ent_nick = Entry(frm_login)
    ent_nick.pack(side=LEFT)
    ent_nick.focus()
    Button(frm_login, text="Login", command=nick).pack(side=LEFT)
    root.bind("<Return>", nick)
    frm_login.update_idletasks()
    cnv_frm_login = canv.create_window(
        logo_img_x,
        logo_img_y + img.height() // 2 + frm_login.winfo_height() / 2,
        window=frm_login,
    )


def data_base():
    """
    creates database with file database.db
    and shows score-table with best 10 results
    """
    global frm_score_table

    with sqlite3.connect("database.db") as db:

        cursor = db.cursor()
        query = """CREATE TABLE IF NOT EXISTS achivements(name TEXT, score INTEGER, time INTEGER, date TEXT)"""
        cursor.execute(query)
        db.commit()

        #  allow add 100 data entry only (not allow over-increasing size of db file)
        query = "SELECT COUNT(*) FROM achivements"
        cursor.execute(query)
        count = cursor.fetchone()[0]
        if count == 100:
            query = "DELETE FROM achivements WHERE ROWID in(SELECT ROWID FROM achivements ORDER BY score ASC, time DESC LIMIT 1)"
            cursor.execute(query)
            db.commit()

        query = f"INSERT INTO achivements (name, score, time, date) VALUES('{user_name}', {points}, {round(timer)}, '{date_game}')"
        cursor.execute(query)
        db.commit()

        query = "SELECT * FROM achivements ORDER BY score DESC, time ASC LIMIT 10"
        frm_score_table = Frame(root, bg="LightSkyBlue1")
        frm_score_table.place(x=10, y=10)
        ttk.Style().configure(
            "Treeview",
            background="LightSkyBlue1",
            fieldbackground="LightSkyBlue1",
            rowheight=int(0.0564 * root_height),
        )
        columns = ("rating", "name", "score", "time", "date")
        tree = ttk.Treeview(frm_score_table, columns=columns, show="headings")
        tree.heading("rating", text="rating")
        tree.heading("name", text="nickname")
        tree.heading("score", text="score")
        tree.heading("time", text="time")
        tree.heading("date", text="date")
        tree.column("rating", width=int(0.15 * root_width), anchor=CENTER)
        tree.column("name", width=int(0.24 * root_width))
        tree.column("score", width=int(0.13 * root_width), anchor=CENTER)
        tree.column("time", width=int(0.19 * root_width), anchor=CENTER)
        tree.column("date", width=int(0.22 * root_width), anchor=CENTER)
        players = cursor.execute(query)
        i = 1
        for player in players:
            tree.insert(
                "", END, values=(i, player[0], player[1], f"{player[2]} sec", player[3])
            )
            i += 1
        tree.pack(side=LEFT, fill=BOTH)


login()

mainloop()
