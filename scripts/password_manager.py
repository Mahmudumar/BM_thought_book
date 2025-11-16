import hashlib
import string
import tkinter.messagebox as tkmsg


class PasswordManager:
    def __init__(self, parent):
        """You must have initialized 
        `SimpleCipher()` before using this class"""
        from scripts.constants import (PASS_FILE,)
        self.parent = parent

        # Security
        self.cipher = SimpleCipher()
        self.encrypt = self.cipher.encrypt
        self.decrypt = self.cipher.decrypt

        self.password_file = PASS_FILE

    def forgot_password(self):
        """Handle password recovery via recovery code input."""
        from .utils import (verify_recovery_key,
                            Askstring)
        code = Askstring(self.parent).askstring(
            "Recovery",
            "Enter recovery code:"
            "\n\nWrite this recovery code down in a safe place."
            "\nLosing it means you cannot reset your password.",
            show="*", width=400, height=200, )

        if code is None:
            return False

        if code.lower() == "exit":
            exit()

        if verify_recovery_key(code):
            new_pass = Askstring(self.parent).askstring(
                "New Password", "Enter new password:", show="*")
            if new_pass:
                with open(self.password_file, 'w') as f:
                    f.write(self.cipher.pass_hash(new_pass))
                tkmsg.showinfo("Success", "Password reset successfully!")
                return True
        else:
            tkmsg.showerror("Error", "Invalid recovery code.")
            return False

    def ask_password(self):
        """Prompt user for password and validate or trigger recovery."""
        from .utils import (
            Askstring,
            set_recovery_key)
        try:
            with open(self.password_file, 'r') as f:
                stored_hash = f.readline().strip()

            entered = Askstring(self.parent).askstring(
                "Password",
                "Enter password (or leave blank to reset):",
                show="*", width=400, height=200)
            if entered is None:
                return "Cancelled"
            if entered.lower() == "exit":
                return "exit"
            if entered == "":
                return self.forgot_password()

            if self.cipher.pass_hash(entered) == stored_hash:
                return True
            else:
                tkmsg.showerror("Error", "Incorrect password.")
                return False

        except FileNotFoundError:
            # First-time setup
            new_pass = Askstring(self.parent).askstring(
                "Password",
                "Create password:",
                show="*", width=400,height=200)
            if new_pass is None:
                return "Cancelled"

            with open(self.password_file, 'w') as f:
                f.write(self.cipher.pass_hash(new_pass))

            recovery = Askstring(self.parent).askstring(
                "Recovery Code",
                "Set a recovery code (write it down somewhere safe):",
                show="*", width=400,height=200)
            if recovery:
                set_recovery_key(recovery)

            tkmsg.showinfo("Info", "Password and recovery code set.")
            return True


class SimpleCipher:
    """
    TODO: find a way to encrypt even the key itself
    so that a person cannot use a program to hack and decode
    the notes
    """

    def __init__(self, key=3):
        self.alphabet = string.ascii_lowercase
        self.key = key

    def encrypt(self, text: str):
        encoded = ""
        for ch in text:
            c = ord(ch) + self.key % 26
            encoded += chr(c)
        return encoded

    def decrypt(self, text):
        decoded = ""
        for ch in text:
            c = ord(ch) - self.key % 26
            decoded += chr(c)
        return decoded

    def pass_hash(self, text: str) -> str:
        """
        Generate a secure SHA-256 hash of the password.
        Returns the hex digest string (64 characters).
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
