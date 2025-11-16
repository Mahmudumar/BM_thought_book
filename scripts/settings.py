from tkinter import Toplevel
import customtkinter as ctk
import tkinter as tk
import tkinter.messagebox as tkmsg
import os
import json

from scripts.constants import (
    APP_NAME, PASS_FILE, APP_ICON, SETTINGS_FILE,
    TNR_BMTB_SERVER
)


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"request_password": False}
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


class SettingsWindow(Toplevel):
    """Settings GUI window styled like NCH preferences with shared styles."""

    def __init__(self, parent, cipher):
        from .constants import COLORS
        self.parent = parent
        super().__init__(self.parent)

        self.configure(bg=COLORS['bg'])


        from scripts.feedback_collection import FeedbackAPI
        from scripts.auto_updater import AutoUpdater
        
        
        self.cipher = cipher
        self.wm_title(f"Thought Book - Settings")
        self.wm_iconbitmap(APP_ICON)

        from scripts.utils import center_window
        center_window(self, 450, 600,readjust=True)

        self.transient(self.parent)

        self.settings = load_settings()
        self.feedback_manager = FeedbackAPI(self)
        
        self.updater = AutoUpdater(self, False, True)

        # --- Theme palette ---
        self.colors = {
            "bg": "#2b2b2b",
            "fg": "#f0f0f0",
            "accent": "#3c3f41",
            "danger": "#a33",
            "danger_hover": "#c44"
        }

        # --- Shared styles ---
        self.styles = {
            "label": {"bg": self.colors["bg"], "fg": self.colors["fg"], "font": ("Segoe UI", 11)},
            "section": {"bg": self.colors["bg"],
                        "fg": self.colors["fg"],
                        "relief": "groove",
                        "font": ("Segoe UI", 11, "bold")},
            "button": {"bg": self.colors["accent"],
                       "fg": self.colors["fg"],
                       "activebackground": "#555",
                       "activeforeground": "#fff",
                       "relief": "flat", "bd": 1,
                       "font": ("Segoe UI", 11), "padx": 8, "pady": 4},
            "check": {"bg": self.colors["bg"],
                      "fg": self.colors["fg"],
                      "selectcolor": self.colors["bg"],
                      "activebackground": self.colors["bg"],
                      "activeforeground": self.colors["fg"],
                      "font": ("Segoe UI", 11)}
        }

        self.configure(bg=self.colors["bg"])

        # --- Section builder ---
        def make_section(title):
            frame = tk.LabelFrame(self, text=title, **self.styles["section"])
            frame.pack(fill="x", padx=15, pady=10, ipady=5)
            return frame

        # Password section
        pass_frame = make_section("Password")
        tk.Button(pass_frame, text="Change Password", command=self.change_password,
                  **self.styles["button"]).pack(anchor="w", padx=10, pady=5)

        #

        # Security section
        sec_frame = make_section("Security")
        self.startup_lock_var = tk.BooleanVar(
            value=self.settings.get("request_password", False))
        tk.Checkbutton(
            sec_frame, text="Request password at startup",
            variable=self.startup_lock_var, command=self.toggle_startup_lock,
            **self.styles["check"]
        ).pack(anchor="w", padx=10, pady=5)

        # Notes section
        notes_frame = make_section("Notes Management")
        tk.Button(notes_frame, text="Clear All Notes", command=self.confirm_clear_all,
                  bg=self.colors["danger"], fg="white",
                  activebackground=self.colors["danger_hover"], activeforeground="white",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=5)

        # Feedback section
        fb_frame = make_section("Feedback and Help")
        tk.Button(fb_frame, text="Give Feedback", command=self.feedback_collect,
                  **self.styles["button"]).pack(anchor="w", padx=10, pady=5)
        tk.Button(fb_frame, text="Report Bug", command=self.feedback_collect,
                  **self.styles["button"]).pack(anchor="w", padx=10, pady=5)

        

        update_bt = tk.Button(fb_frame,
                              text=f"Check for Updates",
                              command=self.check_updates,
                              **self.styles["button"])
        update_bt.pack(anchor="w", padx=10, pady=5)

        # Bottom buttons
        btn_frame = tk.Frame(self, bg=self.colors["bg"])
        btn_frame.pack(side="bottom", fill="x", pady=10)

        tk.Button(btn_frame, text="OK", width=10, command=lambda: self.on_close(True),
                  **self.styles["button"]).pack(side="right", padx=10)
        tk.Button(btn_frame, text="Cancel", width=10, command=lambda: self.on_close(False),
                  **self.styles["button"]).pack(side="right")

        self.after(2000, self.wake_server_up)
        # If the first one fails,
        self.after(1000, lambda: self.wm_iconbitmap(APP_ICON))

    # ----- window funcs -----
    def on_close(self, save=True):
        if save:
            save_settings(self.settings)
        self.destroy()

    def wake_server_up(self):
        from .utils import connected_to_server
        connected_to_server(TNR_BMTB_SERVER)

    def toggle_startup_lock(self):
        from scripts.utils import Askstring
        if self.startup_lock_var.get():
            new_pass = Askstring(self.parent).askstring(
                "Set Password",
                "Enter a new password:",
                show="*")

            if (not new_pass) or ("exit" in new_pass):
                tkmsg.showinfo("Info", "Password setup cancelled.")
                self.startup_lock_var.set(False)
                return

            recovery = Askstring(self.parent).askstring(
                "Recovery Code",
                "Enter a recovery code (save it safely):",
                show="*")

            if (not recovery) or ("exit" in recovery):
                tkmsg.showinfo("Info", "Recovery setup cancelled.")
                self.startup_lock_var.set(False)
                return

            with open(PASS_FILE, "w") as f:
                f.write(self.cipher.pass_hash(new_pass) + "\n")
                f.write(self.cipher.pass_hash(recovery))
            self.settings["request_password"] = True
        else:
            self.settings["request_password"] = False
            tkmsg.showinfo("Info", "Password request at startup disabled.")

    def feedback_collect(self, event=None):
        self.feedback_manager.start()


    def check_updates(self, event=None):
        self.updater.check_update_and_prompt()

    def confirm_clear_all(self):
        from scripts.utils import Askstring, clear_all_notes
        answer = Askstring(self.parent).askstring(
            "Confirm Clear All",
            "Type 'YES' to delete ALL notes permanently:"
        )
        if answer and answer.strip().upper() == "YES":
            clear_all_notes()
            self.parent.notes.clear()
            self.parent.refresh_list()
            self.parent.title_entry.delete(0, "end")
            self.parent.textbox.delete("1.0", "end")
            self.parent.current_index = None
            tkmsg.showinfo("Success", "All notes deleted successfully!")

    def verify_current_password(self):
        """If there's no password set or 
        There the "request at startup"
        button is not checked, then we should say
        No password set"""
        from scripts.utils import Askstring

        if (not os.path.exists(PASS_FILE)) or (
                not self.startup_lock_var.get()):
            tkmsg.showerror("Error", "No password set yet.")
            return False

        entered = Askstring(self.parent).askstring(
            "Verify Password", "Enter current password (or recovery code):", show="*")

        if entered is None:
            return False

        with open(PASS_FILE, "r") as f:
            stored_hash = f.readline().strip()

        if self.cipher.pass_hash(entered) == stored_hash:
            return True
        elif "Cancelled" in entered:
            return False
        else:
            tkmsg.showerror("Error", "Incorrect password.")
            return False

    def change_password(self):
        from scripts.utils import Askstring
        if not self.verify_current_password():
            return
        new_pass = Askstring(self.parent).askstring(
            "New Password", "Enter new password:", show="*")
        if not new_pass:
            tkmsg.showinfo("Info", "Password change cancelled.")
            return
        with open(PASS_FILE, "w") as f:
            f.write(self.cipher.pass_hash(new_pass))
        tkmsg.showinfo("Info", "Password changed successfully.")
