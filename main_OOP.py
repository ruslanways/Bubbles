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

# image for intro logo
LOGO_IMG = "img/logo.gif"

COLORS_BALL = "red", "orange", "yellow", "green", "blue", "LightSkyBlue1"

MUSIC = {
    "intro": "sound/intro.mp3",
    "stage1": "sound/stage1.mp3",
    "stage2": "sound/stage2.mp3",
    "stage3": "sound/stage3.mp3",
    "hit": "sound/hit.mp3",
    "fail": "sound/fail.mp3",
    "win": "sound/win.wav",
}


class MainWindow(Tk):
    def __init__(self):
        super().__init__()
        self.points = 0
        self.date_game = (datetime.date.today()).strftime("%b-%d-%Y")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        shift_x = int(screen_width / 2 - screen_width / 3)
        shift_y = int(screen_height / 2 - screen_height / 3)
        self.geometry(
            f"{(2*screen_width)//3}x{(2*screen_height)//3}+{shift_x}+{shift_y-30}"
        )
        self.resizable(False, False)
        self.title("BUBBLES")

    def create_canv(self, bg="LightSkyBlue1"):
        canv = MainCanvas(self, bg=bg)
        canv.pack(fill=BOTH, expand=1)
        return canv


class MainCanvas(Canvas):
    def __init__(self, master, **kwargs):
        Canvas.__init__(self, master=master, **kwargs)
        self.colors = COLORS_BALL
        self.image = None
        self.logo_img_y = 0
        self.speed = 1000

    def create_text_score(self, text):
        return self.create_text(
            self.winfo_width() - 10, 10, text=text, font="Arial 20", anchor=NE
        )

    def create_logo(self, img):
        self.image = PhotoImage(file=img)
        self.update_idletasks()
        self.logo_img_y = (
            int(0.0625 * self.master.winfo_height()) + self.image.height() // 2
        )
        return self.create_image(
            self.master.winfo_width() // 2, self.logo_img_y, image=self.image
        )

    def create_pause_banner(self, text="PAUSE"):
        return self.create_text(
            self.winfo_width() / 2,
            self.winfo_height() / 2,
            text="PAUSE",
            fill="red",
            font="Arial 60",
        )

    def nick_validator(self, *args):
        """
        validates player input nickname
        """
        self.user_name = self.ent_nick.get()
        pattern = re.compile(r"[\w]{1,10}$")
        if pattern.match(self.user_name):
            self.master.unbind("<Return>")
            self.delete(frm_login_canv)
            self.create_start_quit_frame()
        else:
            messagebox.showerror(
                "login failure",
                "Nickname must contain alphanumeric string max 10 symbols",
            )
            self.master.focus()
            self.ent_nick.focus()

    def create_login_frame(self):
        frm_login = Frame(self.master)
        frm_login.pack()
        Label(frm_login, text="Enter your nickname:").pack(side=LEFT)
        self.ent_nick = Entry(frm_login)
        self.ent_nick.pack(side=LEFT)
        self.ent_nick.focus()
        Button(frm_login, text="Login", command=self.nick_validator).pack(side=LEFT)
        frm_login.update_idletasks()
        return self.create_window(
            self.master.winfo_width() // 2,
            self.logo_img_y + self.image.height() // 2 + frm_login.winfo_height() / 2,
            window=frm_login,
        )

    def create_start_quit_frame(self, after_game=None):
        frm_start = Frame(self.master)
        frm_start.pack()
        btn_start = Button(frm_start, text="Start", command=start_game)
        btn_start.pack(side=LEFT)
        btn_quit = Button(frm_start, text="Qiut", command=self.master.destroy)
        btn_quit.pack(side=LEFT)
        frm_start.update_idletasks()
        self.master.bind("<Return>", start_game)
        if after_game:
            return self.create_window(
                self.master.winfo_width() // 2,
                self.master.winfo_height() // 2,
                window=frm_start,
            )
        else:
            return self.create_window(
                self.master.winfo_width() // 2,
                self.logo_img_y
                + self.image.height() // 2
                + frm_start.winfo_height() / 2,
                window=frm_start,
            )

    def create_balls(self):

        if self.master.points >= 30:
            self.speed = 650
            if music.music != music.music_3_level:
                music.music = music.music_3_level
                pygame.mixer.music.load(music.music)
                pygame.mixer.music.play(-1, 0.0)

        elif self.master.points >= 20:
            self.speed = 800
            if music.music != music.music_2_level:
                music.music = music.music_2_level
                pygame.mixer.music.load(music.music)
                pygame.mixer.music.play(-1, 0.0)
        else:
            pass

        if hasattr(self, "ball"):
            self.delete(self.ball)
        self.update_idletasks()
        self.radius_ball = r = randrange(
            int(0.015 * self.winfo_width()), int(0.09 * self.winfo_height())
        )
        self.x_ball = x = randrange(r + 5, self.winfo_width() - r - 5)
        self.y_ball = y = randrange(r + 5, self.winfo_height() - r - 5)
        self.radius_relative = self.radius_ball / (
            0.09 * self.winfo_height() - 0.015 * self.winfo_width()
        )
        self.ball_color = choice(self.colors)
        self.ball = self.create_oval(
            x - r, y - r, x + r, y + r, fill=self.ball_color, width=0.1
        )
        self.ball_loop = self.after(self.speed, self.create_balls)


class DataBase:
    def __init__(self):
        self.frm_score_table = None
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

    def add_data(self):
        with sqlite3.connect("database.db") as db:
            cursor = db.cursor()
            query = f"INSERT INTO achivements (name, score, time, date) VALUES('{canv.user_name}', {root.points}, {round(timer.timer)}, '{root.date_game}')"
            cursor.execute(query)
            db.commit()

    def show_tabe_score(self):
        with sqlite3.connect("database.db") as db:
            cursor = db.cursor()
            query = "SELECT * FROM achivements ORDER BY score DESC, time ASC LIMIT 10"
            self.frm_score_table = Frame(root, bg="LightSkyBlue1")
            self.frm_score_table.place(x=10, y=10)
            ttk.Style().configure(
                "Treeview",
                background="LightSkyBlue1",
                fieldbackground="LightSkyBlue1",
                rowheight=int(0.0564 * root.winfo_height() // 2),
            )
            columns = ("rating", "name", "score", "time", "date")
            tree = ttk.Treeview(self.frm_score_table, columns=columns, show="headings")
            tree.heading("rating", text="rating")
            tree.heading("name", text="nickname")
            tree.heading("score", text="score")
            tree.heading("time", text="time")
            tree.heading("date", text="date")
            tree.column(
                "rating", width=int(0.15 * root.winfo_width() // 2), anchor=CENTER
            )
            tree.column("name", width=int(0.24 * root.winfo_width() // 2))
            tree.column(
                "score", width=int(0.13 * root.winfo_width() // 2), anchor=CENTER
            )
            tree.column(
                "time", width=int(0.19 * root.winfo_width() // 2), anchor=CENTER
            )
            tree.column(
                "date", width=int(0.22 * root.winfo_width() // 2), anchor=CENTER
            )
            players = cursor.execute(query)
            i = 1
            for player in players:
                tree.insert(
                    "",
                    END,
                    values=(i, player[0], player[1], f"{player[2]} sec", player[3]),
                )
                i += 1
            tree.pack(side=LEFT, fill=BOTH)


class Music:
    def __init__(self):
        self.pause_music = False
        self.intro_music = MUSIC["intro"]
        self.win_music = MUSIC["win"]
        self.music_1_level = MUSIC["stage1"]
        self.music_2_level = MUSIC["stage2"]
        self.music_3_level = MUSIC["stage3"]
        self.music = self.intro_music
        pygame.mixer.init()
        pygame.mixer.music.load(self.music)
        pygame.mixer.music.play(-1, 0.0)
        self.hit_sound = pygame.mixer.Sound(MUSIC["hit"])
        self.fail_hit_sound = pygame.mixer.Sound(MUSIC["fail"])


class Timer:
    def __init__(self):
        self.timer = 0
        self.start_time = 0
        self.finish_time = 0
        self.before_pause_time = 0
        self.all_pause_time = 0
        self.after_pause_time = 0


def click(coord):
    # handle hitting the ball, update points if hit
    if (coord.x - canv.x_ball) ** 2 + (
        coord.y - canv.y_ball
    ) ** 2 <= canv.radius_ball**2:
        music.hit_sound.play()
        if canv.ball_color == "LightSkyBlue1":
            root.points -= 5
        elif canv.radius_relative <= 0.25:
            root.points += 7
        elif canv.radius_relative <= 0.50:
            root.points += 5
        elif canv.radius_relative <= 0.75:
            root.points += 2
        else:
            root.points += 1
        canv.delete("all")
        canv.update_idletasks()
        canv.create_text_score(text=f"{canv.user_name}\nScore: " + str(root.points))

        # handle finish the game with WIN
        if root.points >= 35:
            canv.delete("all")
            canv.after_cancel(canv.ball_loop)
            pygame.mixer.music.load(music.win_music)
            pygame.mixer.music.play()
            timer.finish_time = time.time()
            timer.timer = timer.finish_time - timer.start_time + timer.all_pause_time
            messagebox.showinfo(
                "winner",
                f"B R A V O !!!\n{canv.user_name}\nYou win with score: {root.points}\nTime: {round(timer.timer)} sec.",
            )
            # date_game = (datetime.date.today()).strftime("%b-%d-%Y")
            # data_base()

            canv.unbind("<Button-1>")
            canv.unbind_all("<space>")
            root.focus()
            db.add_data()
            db.show_tabe_score()
            root.points = 0
            timer.all_pause_time = 0
            timer.timer = 0
            canv.create_start_quit_frame(after_game=True)
    else:
        music.fail_hit_sound.play()
        pygame.mixer.music.stop()
        canv.after_cancel(canv.ball_loop)
        canv.delete("all")
        canv.update_idletasks()
        timer.finish_time = time.time()
        timer.timer = timer.finish_time - timer.start_time + timer.all_pause_time
        canv.create_text_score(
            text=f"{canv.user_name}\nScore: {root.points}\nTime: {round(timer.timer)} sec."
        )
        # date_game = (datetime.date.today()).strftime("%b-%d-%Y")
        # data_base()
        canv.unbind("<Button-1>")
        canv.unbind_all("<space>")
        root.focus()
        db.add_data()
        db.show_tabe_score()
        root.points = 0
        timer.all_pause_time = 0
        timer.timer = 0
        canv.create_start_quit_frame(after_game=True)


def pause(space):
    pygame.mixer.music.pause()
    music.pause_music = True
    timer.before_pause_time = time.time()
    canv.create_pause_banner()
    canv.unbind("<Button-1>")
    canv.after_cancel(canv.ball_loop)
    canv.delete(canv.ball)
    canv.bind_all("<space>", start_game)


def start_game(*args):
    # *args because it gets the event object when pressing <Return> from binding event
    print("starting the game...")
    # pygame.mixer.music.stop()
    if music.pause_music == True:
        pygame.mixer.music.unpause()
        music.pause_music = False
        timer.after_pause_time = time.time()
        timer.all_pause_time += timer.after_pause_time - timer.before_pause_time
    else:
        music.music = music.music_1_level
        pygame.mixer.music.load(music.music)
        pygame.mixer.music.play(-1, 0.0)
        timer.start_time = time.time()
    canv.delete("all")
    if db.frm_score_table:
        db.frm_score_table.destroy()
    root.unbind("<Return>")
    canv.create_text_score(text=f"{canv.user_name}\nScore: " + str(root.points))
    canv.bind("<Button-1>", click)
    canv.bind_all("<space>", pause)
    canv.create_balls()


root = MainWindow()
music = Music()
timer = Timer()
db = DataBase()
canv = root.create_canv()
logo_canv = canv.create_logo(LOGO_IMG)
frm_login_canv = canv.create_login_frame()
root.bind("<Return>", canv.nick_validator)

mainloop()
