import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from random import randrange, choice
import time
import datetime
import re
import sqlite3
import os
from pathlib import Path
import sys
import pygame


# --- Constants ---
APP_NAME = "bubbles"


def runtime_base_dir():
    """Return the directory that contains packaged runtime assets."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def resource_path(*parts):
    """Build an absolute path to a bundled resource."""
    return str(runtime_base_dir().joinpath(*parts))


def database_path():
    """Return a writable database path for dev and bundled runs."""
    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        app_data_dir = base / APP_NAME
        app_data_dir.mkdir(parents=True, exist_ok=True)
        return app_data_dir / "database.db"

    return Path(__file__).resolve().parent / "database.db"


DB_FILE = database_path()
LOGO_IMG = resource_path("img", "logo.gif")
BG_COLOR = "LightSkyBlue1"
COLORS_BALL = "red", "orange", "yellow", "green", "blue", BG_COLOR

WIN_SCORE = 35
LEVEL_3_THRESHOLD = 30
LEVEL_2_THRESHOLD = 20
LEVEL_3_DELAY_MS = 650
LEVEL_2_DELAY_MS = 800
LEVEL_1_DELAY_MS = 1000
MIN_RADIUS_FACTOR = 0.015
MAX_RADIUS_FACTOR = 0.09
DB_MAX_ENTRIES = 100

MUSIC = {
    "intro": resource_path("sound", "intro.mp3"),
    "stage1": resource_path("sound", "stage1.mp3"),
    "stage2": resource_path("sound", "stage2.mp3"),
    "stage3": resource_path("sound", "stage3.mp3"),
    "hit": resource_path("sound", "hit.mp3"),
    "fail": resource_path("sound", "fail.mp3"),
    "win": resource_path("sound", "win.wav"),
}


class MainWindow(tk.Tk):
    """Main application window centered on screen."""

    def __init__(self):
        super().__init__()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        shift_x = int(screen_width / 2 - screen_width / 3)
        shift_y = int(screen_height / 2 - screen_height / 3)
        self.geometry(
            f"{(2 * screen_width) // 3}x{(2 * screen_height) // 3}+{shift_x}+{shift_y - 30}"
        )
        self.resizable(False, False)
        self.title("BUBBLES")

    def create_canv(self, background_color=BG_COLOR):
        """Create and return the main game canvas."""
        canv = MainCanvas(self, bg=background_color)
        canv.pack(fill=tk.BOTH, expand=1)
        return canv


class MainCanvas(tk.Canvas):
    """Game canvas that handles drawing balls, UI frames, and score text."""

    def __init__(self, master, **kwargs):
        tk.Canvas.__init__(self, master=master, **kwargs)
        self.colors = COLORS_BALL
        self.image = None
        self.logo_img_y = 0
        self.speed = LEVEL_1_DELAY_MS
        self.frm_login_id = None

    def create_text_score(self, text):
        """Draw the score text in the top-right corner."""
        return self.create_text(
            self.winfo_width() - 10, 10, text=text, font="Arial 20", anchor=tk.NE
        )

    def create_logo(self, img):
        """Load and display the splash screen logo image."""
        self.image = tk.PhotoImage(file=img)
        self.update_idletasks()
        self.logo_img_y = (
            int(0.0625 * self.master.winfo_height()) + self.image.height() // 2
        )
        return self.create_image(
            self.master.winfo_width() // 2, self.logo_img_y, image=self.image
        )

    def create_pause_banner(self, text="PAUSE"):
        """Display a large PAUSE text in the center of the canvas."""
        return self.create_text(
            self.winfo_width() / 2,
            self.winfo_height() / 2,
            text=text,
            fill="red",
            font="Arial 60",
        )

    def validate_nickname(self, on_success):
        """Validate the player nickname and proceed to pre-start screen."""
        self.user_name = self.ent_nick.get()
        pattern = re.compile(r"[\w]{1,10}$")
        if pattern.match(self.user_name):
            self.master.unbind("<Return>")
            self.delete(self.frm_login_id)
            on_success()
        else:
            messagebox.showerror(
                "login failure",
                "Nickname must contain alphanumeric string max 10 symbols",
            )
            self.master.focus()
            self.ent_nick.focus()

    def create_login_frame(self, on_validate):
        """Show the nickname entry form.

        on_validate is called (with no args) when the user submits a valid nickname.
        """
        def do_validate(*_args):
            self.validate_nickname(on_validate)

        frm_login = tk.Frame(self.master)
        frm_login.pack()
        tk.Label(frm_login, text="Enter your nickname:").pack(side=tk.LEFT)
        self.ent_nick = tk.Entry(frm_login)
        self.ent_nick.pack(side=tk.LEFT)
        self.ent_nick.focus()
        tk.Button(frm_login, text="Login", command=do_validate).pack(side=tk.LEFT)
        frm_login.update_idletasks()
        self.frm_login_id = self.create_window(
            self.master.winfo_width() // 2,
            self.logo_img_y + self.image.height() // 2 + frm_login.winfo_height() / 2,
            window=frm_login,
        )
        self.master.bind("<Return>", do_validate)

    def create_start_quit_frame(self, start_callback, after_game=None):
        """Show the Start and Quit buttons."""
        frm_start = tk.Frame(self.master)
        frm_start.pack()
        btn_start = tk.Button(frm_start, text="Start", command=start_callback)
        btn_start.pack(side=tk.LEFT)
        btn_quit = tk.Button(frm_start, text="Quit", command=self.master.destroy)
        btn_quit.pack(side=tk.LEFT)
        frm_start.update_idletasks()
        self.master.bind("<Return>", start_callback)
        if after_game:
            return self.create_window(
                self.master.winfo_width() // 2,
                self.master.winfo_height() // 2,
                window=frm_start,
            )
        return self.create_window(
            self.master.winfo_width() // 2,
            self.logo_img_y + self.image.height() // 2 + frm_start.winfo_height() / 2,
            window=frm_start,
        )

    def create_ball(self, game):
        """Create a random-sized ball at a random location and schedule the next one.

        Accepts a Game instance so it can read the current points and music each tick.
        """
        if game.points >= LEVEL_3_THRESHOLD:
            self.speed = LEVEL_3_DELAY_MS
            if game.music.music != game.music.music_3_level:
                game.music.music = game.music.music_3_level
                pygame.mixer.music.load(game.music.music)
                pygame.mixer.music.play(-1, 0.0)

        elif game.points >= LEVEL_2_THRESHOLD:
            self.speed = LEVEL_2_DELAY_MS
            if game.music.music != game.music.music_2_level:
                game.music.music = game.music.music_2_level
                pygame.mixer.music.load(game.music.music)
                pygame.mixer.music.play(-1, 0.0)

        if hasattr(self, "ball"):
            self.delete(self.ball)
        self.update_idletasks()
        self.radius_ball = r = randrange(
            int(MIN_RADIUS_FACTOR * self.winfo_width()), int(MAX_RADIUS_FACTOR * self.winfo_height())
        )
        self.x_ball = x = randrange(r + 5, self.winfo_width() - r - 5)
        self.y_ball = y = randrange(r + 5, self.winfo_height() - r - 5)
        self.radius_relative = self.radius_ball / (
            MAX_RADIUS_FACTOR * self.winfo_height() - MIN_RADIUS_FACTOR * self.winfo_width()
        )
        self.ball_color = choice(self.colors)
        self.ball = self.create_oval(
            x - r, y - r, x + r, y + r, fill=self.ball_color, width=0.1
        )
        self.ball_loop = self.after(self.speed, lambda: self.create_ball(game))


class DataBase:
    """Handles SQLite database creation, score insertion, and leaderboard queries."""

    def __init__(self):
        with sqlite3.connect(DB_FILE) as db:
            cursor = db.cursor()
            query = """CREATE TABLE IF NOT EXISTS achivements(
                name TEXT, score INTEGER, time INTEGER, date TEXT)"""
            cursor.execute(query)
            db.commit()

            # Keep database size limited to DB_MAX_ENTRIES rows
            query = "SELECT COUNT(*) FROM achivements"
            cursor.execute(query)
            count = cursor.fetchone()[0]
            if count == DB_MAX_ENTRIES:
                query = """DELETE FROM achivements WHERE ROWID in(
                    SELECT ROWID FROM achivements ORDER BY score ASC,
                    time DESC LIMIT 1)"""
                cursor.execute(query)
                db.commit()

    def add_data(self, name, score, time_spent, date):
        """Insert a game result into the database."""
        with sqlite3.connect(DB_FILE) as db:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO achivements (name, score, time, date) VALUES(?, ?, ?, ?)",
                (name, score, round(time_spent), date),
            )
            db.commit()

    def get_top_scores(self, limit=10):
        """Return the top scores as a list of (name, score, time, date) tuples."""
        with sqlite3.connect(DB_FILE) as db:
            cursor = db.cursor()
            cursor.execute(
                "SELECT * FROM achivements ORDER BY score DESC, time ASC LIMIT ?",
                (limit,),
            )
            return cursor.fetchall()


class Music:
    """Manages background music, sound effects, and pause state."""

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
    """Tracks game timing: start, finish, pause durations."""

    def __init__(self):
        self.timer = 0
        self.start_time = 0
        self.finish_time = 0
        self.before_pause_time = 0
        self.all_pause_time = 0
        self.after_pause_time = 0


class Game:
    """Orchestrates gameplay: holds state and wires together all components."""

    def __init__(self, root, canv, music, timer, db):
        self.root = root
        self.canv = canv
        self.music = music
        self.timer = timer
        self.db = db
        self.points = 0
        self.date_game = datetime.date.today().strftime("%b-%d-%Y")
        self.frm_score_table = None

    # --- public entry point ---------------------------------------------------

    def show_login(self):
        """Display the login screen (logo + nickname form)."""
        self.canv.create_login_frame(on_validate=self._on_login_success)

    # --- callbacks ------------------------------------------------------------

    def _on_login_success(self):
        """Called after a valid nickname is entered."""
        self.canv.create_start_quit_frame(start_callback=self._start_game)

    def _start_game(self, *_args):
        """Start or resume the game with appropriate music and event bindings."""
        if self.music.pause_music:
            pygame.mixer.music.unpause()
            self.music.pause_music = False
            self.timer.after_pause_time = time.time()
            self.timer.all_pause_time += (
                self.timer.after_pause_time - self.timer.before_pause_time
            )
        else:
            self.music.music = self.music.music_1_level
            pygame.mixer.music.load(self.music.music)
            pygame.mixer.music.play(-1, 0.0)
            self.timer.start_time = time.time()

        self.canv.delete("all")
        if self.frm_score_table:
            self.frm_score_table.destroy()
            self.frm_score_table = None
        self.root.unbind("<Return>")
        self.canv.create_text_score(
            text=f"{self.canv.user_name}\nScore: {self.points}"
        )
        self.canv.bind("<Button-1>", self._on_click)
        self.canv.bind_all("<space>", self._pause_game)
        self.canv.create_ball(self)

    def _pause_game(self, _event):
        """Pause the game: stop ball spawning, show pause banner, pause music."""
        pygame.mixer.music.pause()
        self.music.pause_music = True
        self.timer.before_pause_time = time.time()
        self.canv.create_pause_banner()
        self.canv.unbind("<Button-1>")
        self.canv.after_cancel(self.canv.ball_loop)
        self.canv.delete(self.canv.ball)
        self.canv.bind_all("<space>", self._start_game)

    def _on_click(self, event):
        """Handle click on canvas: score hit/miss and end the game on miss or win."""
        if (event.x - self.canv.x_ball) ** 2 + (
            event.y - self.canv.y_ball
        ) ** 2 <= self.canv.radius_ball ** 2:
            self.music.hit_sound.play()
            if self.canv.ball_color == BG_COLOR:
                self.points -= 5
            elif self.canv.radius_relative <= 0.25:
                self.points += 7
            elif self.canv.radius_relative <= 0.50:
                self.points += 5
            elif self.canv.radius_relative <= 0.75:
                self.points += 2
            else:
                self.points += 1

            self.canv.delete("all")
            self.canv.update_idletasks()
            self.canv.create_text_score(
                text=f"{self.canv.user_name}\nScore: {self.points}"
            )

            if self.points >= WIN_SCORE:
                pygame.mixer.music.load(self.music.win_music)
                pygame.mixer.music.play()
                self.timer.finish_time = time.time()
                self.timer.timer = (
                    self.timer.finish_time
                    - self.timer.start_time
                    - self.timer.all_pause_time
                )
                messagebox.showinfo(
                    "winner",
                    f"""B R A V O !!!
                {self.canv.user_name}
                You win with score: {self.points}
                Time: {round(self.timer.timer)} sec.""",
                )
                self._end_game()
        else:
            self.music.fail_hit_sound.play()
            pygame.mixer.music.stop()
            self.timer.finish_time = time.time()
            self.timer.timer = (
                self.timer.finish_time
                - self.timer.start_time
                - self.timer.all_pause_time
            )
            self._end_game()

    # --- helpers --------------------------------------------------------------

    def _end_game(self):
        """Shared cleanup for both win and miss game-over paths."""
        self.canv.after_cancel(self.canv.ball_loop)
        self.canv.delete("all")
        self.canv.update_idletasks()
        self.canv.create_text_score(
            text=f"{self.canv.user_name}\nScore: {self.points}\nTime: {round(self.timer.timer)} sec."
        )
        self.canv.unbind("<Button-1>")
        self.canv.unbind_all("<space>")
        self.root.focus()

        self.db.add_data(
            self.canv.user_name,
            self.points,
            self.timer.timer,
            self.date_game,
        )
        self._show_score_table()

        self.points = 0
        self.timer.all_pause_time = 0
        self.timer.timer = 0
        self.canv.speed = LEVEL_1_DELAY_MS
        self.canv.create_start_quit_frame(
            start_callback=self._start_game, after_game=True
        )

    def _show_score_table(self):
        """Build and display the top-10 leaderboard Treeview."""
        rows = self.db.get_top_scores()
        self.frm_score_table = tk.Frame(self.root, bg=BG_COLOR)
        self.frm_score_table.place(x=10, y=10)
        ttk.Style().configure(
            "Treeview",
            background=BG_COLOR,
            fieldbackground=BG_COLOR,
            rowheight=int(0.0564 * self.root.winfo_height() // 2),
        )
        columns = ("rating", "name", "score", "time", "date")
        tree = ttk.Treeview(self.frm_score_table, columns=columns, show="headings")
        tree.heading("rating", text="rating")
        tree.heading("name", text="nickname")
        tree.heading("score", text="score")
        tree.heading("time", text="time")
        tree.heading("date", text="date")
        tree.column(
            "rating", width=int(0.15 * self.root.winfo_width() // 2), anchor=tk.CENTER
        )
        tree.column("name", width=int(0.24 * self.root.winfo_width() // 2))
        tree.column(
            "score", width=int(0.13 * self.root.winfo_width() // 2), anchor=tk.CENTER
        )
        tree.column(
            "time", width=int(0.19 * self.root.winfo_width() // 2), anchor=tk.CENTER
        )
        tree.column(
            "date", width=int(0.22 * self.root.winfo_width() // 2), anchor=tk.CENTER
        )
        for i, player in enumerate(rows, start=1):
            tree.insert(
                "",
                tk.END,
                values=(i, player[0], player[1], f"{player[2]} sec", player[3]),
            )
        tree.pack(side=tk.LEFT, fill=tk.BOTH)


# --- Bootstrap ----------------------------------------------------------------

def main():
    root = MainWindow()

    try:
        music = Music()
    except (pygame.error, FileNotFoundError) as exc:
        messagebox.showerror("Missing audio files", f"Cannot load audio:\n{exc}")
        root.destroy()
        return

    timer = Timer()
    db = DataBase()
    canv = root.create_canv()

    try:
        canv.create_logo(LOGO_IMG)
    except tk.TclError as exc:
        messagebox.showerror("Missing image file", f"Cannot load logo:\n{exc}")
        root.destroy()
        return

    game = Game(root, canv, music, timer, db)
    game.show_login()

    root.mainloop()


if __name__ == "__main__":
    main()
