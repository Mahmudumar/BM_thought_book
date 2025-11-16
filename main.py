
import logging
import customtkinter as ctk
import tkinter.messagebox as tkmsg
import sys
from scripts.utils import (center_window)


class Book(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        # Variables
        self.current_index = None
        self.current_note = ""
        self.autosave_after_id = None
        self.notes = []

        # Ensure window shows first
        self.start_ui()

        # This is how we will do every startup block
        self.after(50, lambda: self.init_settings())

    # --- Managers and settings ---

    def init_db(self):
        try:
            from scripts.utils import (create_table)
            create_table()
        except Exception as e:
            logging.error(f"Error while creating table: {e}")
        self.load_notes()

    def init_settings(self):
        from scripts.settings import (load_settings)
        settings = load_settings()
        self.locked = settings.get("request_password", False)

        if self.locked:
            while self.locked:
                from scripts.password_manager import (PasswordManager)
                password_manager = PasswordManager(self)
                result = password_manager.ask_password()
                if result is True:
                    self.locked = False
                    self.unlock_app()
                elif result in ("Cancelled", "exit"):
                    sys.exit()
        else:
            self.unlock_app()

        self.focused = ctk.BooleanVar(value=False)

    def start_ui(self):
        """Draw everything before loading anything.
        Let not the UI depend on anything at all"""
        from scripts.constants import (APP_ICON,
                                       APP_NAME,
                                       APP_VERSION)
        self.wm_title(f"{APP_NAME} {APP_VERSION}")
        self.wm_iconbitmap(APP_ICON)

        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)

        self.focused = ctk.BooleanVar(self)

        if not self.focused.get():
            self.sidebar.pack(side="left", fill="y")

        button_frame = ctk.CTkFrame(self.sidebar)
        button_frame.pack(pady=5, fill="x")

        self.add_button = ctk.CTkButton(
            button_frame, text="Add Note",
            fg_color="#555555", width=80)
        self.add_button.pack(side="left", pady=5, padx=2)

        self.delete_button = ctk.CTkButton(button_frame, text="Delete Note", fg_color="#555555",
                                           hover_color="darkred", text_color="white",
                                           width=80)
        self.delete_button.pack(side="right", pady=5)

        self.scrollable_list = ctk.CTkScrollableFrame(self.sidebar, width=200)
        self.scrollable_list.pack(fill="both", expand=True)

        pair = ctk.CTkFrame(self.sidebar)
        pair.pack(fill="x")
        self.settings_btn = ctk.CTkButton(pair, fg_color="#555555",
                                          text="Settings",
                                          width=80,
                                          )
        self.settings_btn.pack(side="left", pady=5)

        self.focus_btn = ctk.CTkButton(
            pair, fg_color="#555555",
            width=80,
            text="Focus",
        )
        self.focus_btn.pack(side="right")

        self.note_buttons = []

        # Editor
        self.right_side = ctk.CTkFrame(self, height=300)
        self.right_side.pack(side="right", fill="both",
                             expand=True, padx=10)

        self.editor_frame = ctk.CTkFrame(self.right_side)
        self.editor_frame.pack(side="top", pady=10,
                               expand=True, fill="both")

        self.title_entry = ctk.CTkEntry(
            self.editor_frame, placeholder_text="Title")
        self.title_entry.pack(fill="x", pady=5)

        self.textbox = ctk.CTkTextbox(
            self.editor_frame, undo=True, wrap=ctk.WORD)
        self.textbox.pack(fill="both", expand=True, pady=5)

        self.extra_bt_frame = ctk.CTkFrame(self.right_side)
        self.unfocus_btn = ctk.CTkButton(
            self.extra_bt_frame, text="Unfocus",
            width=80,
            fg_color="#555555")

        self.wm_protocol("WM_DELETE_WINDOW", self.on_close)

        self.after(100, lambda: center_window(self, 900, 500))
        # self.wm_state('zoomed')

    def unlock_app(self):
        """Initialize all the things that should be initialized"""
        # TODO: add a status loading
        self.after(100, self.init_managers)
        self.after(150, self.init_db)
        self.after(200, self._assign_bt_commands)
        self.after(250, self.load_notes)
        self.after(300, self.refresh_list)

    def init_managers(self):
        from scripts.password_manager import (PasswordManager)
        
        from scripts.auto_updater import AutoUpdater
        from scripts.constants import (APP_VERSION)
        from scripts.password_manager import SimpleCipher

        # Security
        self.cipher = SimpleCipher()
        self.encrypt = self.cipher.encrypt
        self.decrypt = self.cipher.decrypt

        # Settings + Password
        self.password = None
        # self.password_file = PASS_FILE
        self.password_manager = PasswordManager(self)
 
        # App Update Management
        self.updater = AutoUpdater(self, False, False)
        logging.info(f"Current App Version: {APP_VERSION}")

        # Check after startup delay
        self.after(4000, self.updater.check_update_background)

    def _assign_bt_commands(self):
        """Because the window needs to appear
          as soon as possible"""
        from scripts.settings import SettingsWindow

        self.settings_btn.configure(
            command=lambda: SettingsWindow(self, self.cipher))
        self.add_button.configure(command=self.add_note)
        self.delete_button.configure(command=self.delete_note)
        self.focus_btn.configure(command=self.focus_write)
        self.unfocus_btn.configure(command=self.focus_write)

        self.title_entry.bind(
            "<KeyRelease>", lambda e: self.schedule_autosave())
        self.textbox.bind("<KeyRelease>", lambda e: self.schedule_autosave())
        self.title_entry.bind("<Return>", lambda e: self.textbox.focus_set())
        self.textbox.bind("<Return>", self.handle_bullets)

    def schedule_autosave(self):
        """Schedule an autosave after a short delay to reduce excessive writes."""
        if self.autosave_after_id:
            self.after_cancel(self.autosave_after_id)
        self.autosave_after_id = self.after(500, self.save_current_note)

    def on_close(self):
        """Handle app close event, process POAs and destroy window."""
        try:
            pass
            # Pause on BMA integration for now.
            # poas = self.get_poas(current_content)
            # self.bma.make_activities(poas)
        except Exception as e:
            logging.error(f"Error during app close: {e}")
        finally:
            logging.info("App closed successfully.")
            self.destroy()
            self.quit()

    def focus_write(self):
        # This is also a valuable feature given the UI
        """Toggle focus mode: hides/shows sidebar and extra buttons."""
        is_focused = not self.focused.get()
        self.focused.set(is_focused)

        if is_focused:
            self.unfocus_btn.pack_forget()
            self.extra_bt_frame.pack_forget()
            self.sidebar.pack(side="left", fill="y")
        else:
            self.extra_bt_frame.pack(fill="x", pady=5, side="bottom")
            self.unfocus_btn.pack(side="left")
            self.sidebar.pack_forget()

    def get_note_count(self):
        """Return current number of notes"""
        return len(self.notes)

    # --------------------------

    # --- Note-based methods ---

    def load_notes(self):
        """Load all notes from the database. Used in startup."""
        from scripts.utils import (get_notes)
        self.notes = get_notes()
        if not self.notes:
            self.add_note()
        else:
            self.load_note(0)

    def add_note(self, event=None):
        from scripts.constants import (APP_NAME)
        """Create a new note, save current"""
    
        if self.current_index is not None:
            self.save_current_note(index_to_save=self.current_index)

        self.current_index = None
        self.title_entry.delete(0, "end")
        self.textbox.delete("1.0", "end")
        self.title_entry.insert(0, "Untitled")
        self.title_entry.focus_set()

        self.save_current_note()

        self.title_entry.select_range(0, "end")
        self.title_entry.focus()

    def save_current_note(self, index_to_save=None):
        from scripts.utils import (save_note)
        """Save the current note or a specified note index to the database."""
        idx, content = self.get_current_note(index_to_save)
        content_encrypted = self.encrypt(content)
        title = self.title_entry.get()

        if idx is not None:
            note_id = self.notes[idx].get("id")
            if note_id:
                save_note(title, content_encrypted, note_id)
                self.notes[idx] = {"id": note_id,
                                   "title": title, "content": content_encrypted}
            else:
                new_id = save_note(title, content_encrypted)
                self.notes[idx] = {"id": new_id,
                                   "title": title, "content": content_encrypted}
        else:
            new_id = save_note(title, content_encrypted)
            self.notes.append({"id": new_id, "title": title,
                              "content": content_encrypted})
            self.current_index = len(self.notes) - 1

        self.after(50, self.refresh_list)

    def get_current_note(self, index_to_save=None):
        """Return the current note index and content (unencrypted)."""
        idx = index_to_save if index_to_save is not None else self.current_index
        content = self.textbox.get("1.0", "end-1c").strip()
        return idx, content

    def refresh_list(self):
        """Refresh the sidebar list of notes and update buttons."""
        for btn in self.note_buttons:
            btn.destroy()

        self.note_buttons.clear()

        for idx, note in enumerate(self.notes):
            display_title = self._truncate_text(
                note.get("title", "Untitled"), 20)
            btn = ctk.CTkButton(
                self.scrollable_list, fg_color="#333333", text=display_title, width=180,
                command=lambda i=idx: self.load_note(i))
            btn.pack(pady=2)
            self.note_buttons.append(btn)

    def load_note(self, index):
        """Load note by index, saving current note first."""
        if self.current_index is not None:
            self.save_current_note(index_to_save=self.current_index)

        self.current_index = index
        note = self.notes[index]

        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, note.get("title", ""))
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", self.decrypt(note.get("content", "")))

        for i, btn in enumerate(self.note_buttons):
            btn.configure(fg_color="#555555" if i == index else "#333333")

    def delete_note(self):
        """Delete the current note after confirmation."""
        from scripts.utils import (delete_note)
        if self.current_index is None:
            return

        if tkmsg.askyesno("Confirm Delete",
                          "Are you sure you want to delete this note?"):
            note_id = self.notes[self.current_index].get("id")
            if note_id:
                delete_note(note_id)
                del self.notes[self.current_index]

            self.title_entry.delete(0, "end")
            self.textbox.delete("1.0", "end")
            self.current_index = None

            self.after(50, self.refresh_list)

    # --------------------

    # --- Text-based methods ---

    def _truncate_text(self, text, max_length=20):
        """Truncate a string to fit within max_length (chr) for display in buttons."""
        return text if len(text) <= max_length else text[:max_length - 3] + "..."

    def handle_bullets(self, event=None):
        """Handle multiline bullet input when Enter key is pressed."""
        index = self.textbox.index("insert linestart")
        line_text = self.textbox.get(index, f"{index} lineend")
        if line_text.strip().startswith("-"):
            if line_text.strip() == "-":
                # Empty bullet line, exit bullet mode
                self.textbox.delete(index, f"{index} lineend")
                self.textbox.insert("insert", "\n")
                return "break"
            else:
                self.textbox.insert("insert", "\n- ")
                return "break"

        return None

    # TODO: .md support
    # --------------------


def main():
    Book().mainloop()


if __name__ == "__main__":
    main()
