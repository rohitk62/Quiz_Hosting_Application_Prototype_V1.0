import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import pandas as pd
import os
import sys
import subprocess
import json


class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Competition Interface")
        self.root.geometry("1400x1000")

        # Load config
        with open("config.json", "r") as f:
            self.config = json.load(f)

        self.teams = self.config["teams"]
        self.rounds_config = self.config["rounds"]

        # Excel questions
        self.data = pd.read_excel("quiz_questions.xlsx")
        self.current_round = None
        self.round_questions = None
        self.current_question = None

        self.time_left = 60

        self.rounds = [r["name"] for r in self.rounds_config]

        self.scores = {
            team: {round_conf["name"]: [] for round_conf in self.rounds_config}
            for team in self.teams
        }

        self.opened_questions = {}

        self.selected_team = None
        self.selected_points = 0
        self.team_buttons = {}
        self.points_buttons = {}

        self.create_welcome_page()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_background(self, image_path):
        img = Image.open(image_path)
        img = img.resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight()), Image.LANCZOS)
        bg = ImageTk.PhotoImage(img)
        label = tk.Label(self.root, image=bg)
        label.image = bg
        label.place(x=0, y=0, relwidth=1, relheight=1)

    def create_welcome_page(self):
        self.clear_screen()
        self.create_background("bg_welcome.jpg")

        container = tk.Frame(self.root, bg="#ffffff")
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            container,
            text="Welcome to the Quiz Competition!",
            font=("Helvetica", 28),
            bg="#ffffff"
        ).pack(pady=40)

        if os.path.exists("progress.json"):
            tk.Button(
                container,
                text="Load Previous Progress",
                font=("Helvetica", 18),
                command=self.load_progress
            ).pack(pady=20)

        tk.Button(
            container,
            text="Start Fresh",
            font=("Helvetica", 18),
            command=self.start_fresh
        ).pack(pady=20)

    def start_fresh(self):
        self.opened_questions = {}
        self.scores = {
            team: {round_conf["name"]: [] for round_conf in self.rounds_config}
            for team in self.teams
        }
        self.show_rounds()

    def load_progress(self):
        try:
            with open("progress.json", "r") as f:
                progress = json.load(f)
            self.opened_questions = {
                k: set(v) for k, v in progress.get("opened_questions", {}).items()
            }
            self.scores = progress.get("scores", self.scores)
            print("[INFO] Progress loaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load progress: {e}")
            messagebox.showerror("Error", "Failed to load progress.")
        self.show_rounds()

    def show_rounds(self):
        self.clear_screen()
        self.create_background("bg_rounds.jpg")

        container = tk.Frame(self.root, bg="#ffffff")
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(container, text="Select a Round", font=("Helvetica", 22), bg="#ffffff").pack(pady=20)

        for r in self.rounds:
            round_frame = tk.Frame(container, bg="#ffffff")
            round_frame.pack(pady=8)

            tk.Button(
                round_frame,
                text=r,
                font=("Helvetica", 16),
                command=lambda r=r: self.load_round(r),
                width=40
            ).pack(side="left", padx=10)

            status_frame = tk.Frame(round_frame, bg="#ffffff")
            status_frame.pack(side="left", padx=10)
            self.draw_round_status(r, status_frame)

        tk.Button(
            container,
            text="Check Scores",
            font=("Helvetica", 14),
            command=self.show_scores
        ).pack(pady=10)

        tk.Button(
            container,
            text="Quit",
            font=("Helvetica", 14),
            command=self.on_close
        ).pack(pady=30)

    def draw_round_status(self, round_name, container):
        opened = self.opened_questions.get(round_name, set())
        round_conf = next(r for r in self.rounds_config if r["name"] == round_name)
        total_questions = round_conf["questions"]
        for num in range(1, total_questions + 1):
            color = "green" if num in opened else "yellow"
            lbl = tk.Label(
                container,
                text=str(num),
                bg=color,
                width=3,
                height=1,
                relief="solid",
                font=("Helvetica", 8, "bold")
            )
            lbl.pack(side="left", padx=1)

    def load_round(self, round_name):
        self.current_round = round_name
        self.round_questions = self.data[self.data["Round"] == round_name]

        if round_name not in self.opened_questions:
            self.opened_questions[round_name] = set()

        self.clear_screen()
        self.create_background("bg_question_select.jpg")

        container = tk.Frame(self.root, bg="#ffffff")
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(container, text=f"Round: {round_name}", font=("Helvetica", 22), bg="#ffffff").pack(pady=20)

        self.status_frame = tk.Frame(container, bg="#ffffff")
        self.status_frame.pack(pady=20)
        self.draw_question_buttons()

        tk.Button(
            container,
            text="Enter Question Number",
            font=("Helvetica", 14),
            command=self.ask_question_number
        ).pack(pady=10)

        tk.Button(
            container,
            text="Back to Rounds",
            font=("Helvetica", 12),
            command=self.show_rounds
        ).pack(pady=10)

    def draw_question_buttons(self):
        for widget in self.status_frame.winfo_children():
            widget.destroy()

        round_conf = next(r for r in self.rounds_config if r["name"] == self.current_round)
        total_questions = round_conf["questions"]

        for num in range(1, total_questions + 1):
            color = "green" if num in self.opened_questions[self.current_round] else "yellow"
            btn = tk.Button(
                self.status_frame,
                text=str(num),
                bg=color,
                width=4,
                height=2,
                font=("Helvetica", 12),
                command=lambda n=num: self.show_question_by_number(n)
            )
            btn.grid(row=(num - 1) // 7, column=(num - 1) % 7, padx=5, pady=5)

    def ask_question_number(self):
        num = simpledialog.askinteger("Question Number", "Enter question number:")
        self.show_question_by_number(num)

    def show_question_by_number(self, num):
        found = self.round_questions[self.round_questions["Number"] == num]
        if not found.empty:
            self.opened_questions[self.current_round].add(num)
            self.show_question(found.iloc[0])
        else:
            messagebox.showerror("Error", "Invalid question number!")

    def show_question(self, q):
        self.clear_screen()
        self.create_background("bg_question.jpg")
        self.current_question = q
        self.selected_team = None
        self.selected_points = 0
        self.team_buttons = {}
        self.points_buttons = {}

        media = str(q.get("MediaFile", "") or "").strip()
        media_opened = False

        if media:
            media_path = os.path.join("media", media)
            if os.path.exists(media_path):
                self.open_in_default_player(media_path)
                media_opened = True

        container = tk.Frame(self.root, bg="#ffffff")
        container.place(relx=0.5, rely=0.5, anchor="center")

        if media_opened:
            tk.Label(
                container,
                text="Media Opened",
                font=("Helvetica", 20),
                bg="#ffffff"
            ).pack(pady=20)
        else:
            tk.Label(
                container,
                text="No Media attached",
                font=("Helvetica", 20),
                bg="#ffffff"
            ).pack(pady=20)

        tk.Button(
            container,
            text="Go To Question",
            font=("Helvetica", 20, "bold"),
            command=self.show_question_with_button
        ).pack(pady=20)

    def show_question_with_button(self):
        self.clear_screen()
        self.create_background("bg_question.jpg")

        self.container = tk.Frame(self.root, bg="#ffffff")
        self.container.place(relx=0.5, rely=0.5, anchor="center")

        self.question_label = tk.Label(
            self.container,
            text=self.current_question["Question"],
            wraplength=1500,
            font=("Helvetica", 40, "bold"),
            bg="#ffffff"
        )
        self.question_label.pack(pady=40)

        round_conf = next(r for r in self.rounds_config if r["name"] == self.current_round)
        self.time_left = round_conf["time_per_question"]

        self.timer_label = tk.Label(
            self.container, text=f"Time Left: {self.time_left}", font=("Helvetica", 48), bg="#ffffff"
        )
        self.timer_label.pack()

        tk.Button(
            self.container,
            text="Start Timer",
            font=("Helvetica", 20, "bold"),
            command=self.start_countdown
        ).pack(pady=20)

    def open_in_default_player(self, filepath):
        try:
            if sys.platform.startswith('win'):
                os.startfile(filepath)
            elif sys.platform.startswith('darwin'):
                subprocess.Popen(['open', filepath])
            else:
                subprocess.Popen(['xdg-open', filepath])
        except Exception as e:
            print(f"[ERROR] Could not open file: {e}")

    def start_countdown(self):
        self.countdown()

    def countdown(self):
        if self.time_left > 0:
            self.timer_label.config(text=f"Time Left:\n{self.time_left}", fg="green")
            self.time_left -= 1
            self.root.after(1000, self.countdown)
        else:
            self.play_buzzer()
            self.timer_label.config(text="TIME UP!", fg="red")
            self.show_answer_prompt()

    def play_buzzer(self):
        buzzer_file = "buzzer.mp3"
        if os.path.exists(buzzer_file):
            self.open_in_default_player(buzzer_file)
        else:
            print(f"[WARN] Buzzer file '{buzzer_file}' not found!")

    def show_answer_prompt(self):
        tk.Button(
            self.container,
            text="Show Answer",
            font=("Helvetica", 16),
            command=self.show_answer
        ).pack(pady=20)

    def show_answer(self):
        ans = self.current_question["Answer"]

        self.answer_label = tk.Label(
            self.container,
            text=f"Answer: {ans}",
            wraplength=1500,
            font=("Helvetica", 22, "bold"),
            fg="green",
            bg="#ffffff"
        )
        self.answer_label.pack(pady=30)

        self.show_assign_score_panel(self.container)

        btn_frame = tk.Frame(self.container, bg="#ffffff")
        btn_frame.pack(pady=20)
        tk.Button(
            btn_frame,
            text="Back to Round",
            font=("Helvetica", 14),
            command=lambda: self.load_round(self.current_round)
        ).pack(side="left", padx=5)
        tk.Button(
            btn_frame,
            text="Back to Rounds",
            font=("Helvetica", 12),
            command=self.show_rounds
        ).pack(side="left", padx=5)
        tk.Button(
            btn_frame,
            text="Quit",
            font=("Helvetica", 12),
            command=self.on_close
        ).pack(side="left", padx=5)

    def show_assign_score_panel(self, parent):
        panel = tk.Frame(parent, bg="#ffffff")
        panel.pack(pady=20)

        tk.Label(panel, text="Assign Score", font=("Helvetica", 36), bg="#ffffff").pack()

        team_frame = tk.Frame(panel, bg="#ffffff")
        team_frame.pack(pady=5)
        self.team_buttons = {}
        for team in self.teams:
            btn = tk.Button(
                team_frame,
                text=team,
                width=10,
                command=lambda t=team: self.select_team(t)
            )
            btn.pack(side="left", padx=2)
            self.team_buttons[team] = btn

        score_frame = tk.Frame(panel, bg="#ffffff")
        score_frame.pack(pady=5)
        btn_direct = tk.Button(
            score_frame, text="Direct (5)", command=lambda: self.select_points(5)
        )
        btn_direct.pack(side="left", padx=5)
        self.points_buttons[5] = btn_direct

        btn_bonus = tk.Button(
            score_frame, text="Bonus (2)", command=lambda: self.select_points(2)
        )
        btn_bonus.pack(side="left", padx=5)
        self.points_buttons[2] = btn_bonus

        tk.Button(
            panel, text="Assign Score", command=self.assign_score
        ).pack(pady=10)

    def select_team(self, team):
        self.selected_team = team
        for t, btn in self.team_buttons.items():
            btn.config(bg="blue" if t == team else "SystemButtonFace")

    def select_points(self, points):
        self.selected_points = points
        for p, btn in self.points_buttons.items():
            btn.config(bg="blue" if p == points else "SystemButtonFace")

    def assign_score(self):
        if not self.selected_team or self.selected_points == 0:
            messagebox.showerror("Error", "Select a team and points first!")
            return

        self.scores[self.selected_team][self.current_round].append(self.selected_points)

        messagebox.showinfo(
            "Score Assigned",
            f"Assigned {self.selected_points} to Team {self.selected_team} for {self.current_round}."
        )

        self.selected_team = None
        self.selected_points = 0
        for btn in self.team_buttons.values():
            btn.config(bg="SystemButtonFace")
        for btn in self.points_buttons.values():
            btn.config(bg="SystemButtonFace")

    def show_scores(self):
        win = tk.Toplevel(self.root)
        win.title("Score Table")
        win.geometry("2000x400")

        columns = ["Team", "Total"] + self.rounds

        for col, name in enumerate(columns):
            tk.Label(
                win,
                text=name,
                font=("Helvetica", 12, "bold"),
                borderwidth=1,
                relief="solid",
                width=20
            ).grid(row=0, column=col)

        for row_idx, (team, rounds) in enumerate(self.scores.items()):
            total = sum(sum(r) for r in rounds.values())
            tk.Label(win, text=team, borderwidth=1, relief="solid", width=25).grid(row=row_idx+1, column=0)
            tk.Label(win, text=str(total), borderwidth=1, relief="solid", width=25).grid(row=row_idx+1, column=1)
            for i, round_name in enumerate(self.rounds):
                score = rounds[round_name]
                disp = "+".join(map(str, score)) if score else ""
                tk.Label(win, text=disp, borderwidth=1, relief="solid", width=20).grid(row=row_idx+1, column=i+2)

        tk.Button(
            win,
            text="Show Rank",
            font=("Helvetica", 12),
            command=self.show_rank
        ).grid(row=row_idx+2, column=0, columnspan=5, pady=10)

    def show_rank(self):
        win = tk.Toplevel(self.root)
        win.title("Team Rankings")
        win.geometry("1000x600")

        team_totals = []
        for team, rounds in self.scores.items():
            total = sum(sum(r) for r in rounds.values())
            team_totals.append((team, total))

        team_totals.sort(key=lambda x: (-x[1], x[0]))

        tk.Label(win, text="Rank", font=("Helvetica", 30, "bold"), width=4).grid(row=0, column=0)
        tk.Label(win, text="Team", font=("Helvetica", 30, "bold"), width=4).grid(row=0, column=1)
        tk.Label(win, text="Total", font=("Helvetica", 30, "bold"), width=4).grid(row=0, column=2)

        for idx, (team, total) in enumerate(team_totals):
            bg = "gold" if idx == 0 else "silver" if idx == 1 else "orange" if idx == 2 else "grey"
            tk.Label(win, text=str(idx + 1), font=("Helvetica", 20, "bold"), bg=bg, width=20).grid(row=idx + 1, column=0)
            tk.Label(win, text=team, font=("Helvetica", 20, "bold"), bg=bg, width=20).grid(row=idx + 1, column=1)
            tk.Label(win, text=str(total), font=("Helvetica", 20, "bold"), bg=bg, width=20).grid(row=idx + 1, column=2)

    def save_progress(self):
        progress = {
            "opened_questions": {
                k: list(v) for k, v in self.opened_questions.items()
            },
            "scores": self.scores
        }
        try:
            with open("progress.json", "w") as f:
                json.dump(progress, f, indent=4)
            print("[INFO] Progress saved to progress.json")
        except Exception as e:
            print(f"[ERROR] Failed to save progress: {e}")

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def on_close(self):
        self.save_progress()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()
