# constants.py
from logging.handlers import RotatingFileHandler
import os
import json
import uuid
import logging
from pathlib import Path

COLORS = {
            "bg": "#2b2b2b",
            "fg": "#f0f0f0",
            "accent": "#3c3f41",
            "danger": "#a33",
            "danger_hover": "#c44"
        }

__all__ = [
    "NOTES_DB", "NOTES_FOLDER",
    "RECOVERY_FILE", "PASS_FILE",
    "DATA_FOLDER", "LOGS_FILE",
    "BMA_DOWNLOAD_LINK", "APP_NAME",
    "APP_VERSION", "APP_ICON", "APP_PHOTO"
]

# --- App Info ---
APP_NAME = "Thought Book"
APP_VERSION = "1.0.54"
APP_SHORT_NAME = "BMTB"


# --- Helper Functions ---
def resource_path(relative_path="") -> Path:
    """Return absolute path to resource (works for dev & PyInstaller)."""
    try:
        # will run when compiled into .exe by pyinstaller
        base_path= Path("_internal") / "data" / relative_path
        if not base_path.exists():
            raise TypeError
    except TypeError:
        # will run while you are testing
        base_path =  Path(__file__).resolve().parent.parent

    return base_path

# --- Main Folders ---
MAIN_FOLDER = Path(__file__).resolve().parent.parent


# --- Images & Icons ---
IMGS_FOLDER = resource_path() / "imgs"
APP_ICON = IMGS_FOLDER / "logo.ico"
APP_SPLASH = IMGS_FOLDER / "splash.png"
APP_PHOTO = IMGS_FOLDER / "logo.png"


# --- Data Storage (always under %APPDATA%/BM) ---
DATA_FOLDER = Path(os.getenv("APPDATA", "")) / "BM"
NOTES_FOLDER = DATA_FOLDER / APP_NAME
# Only create folders if they do not exist (avoid unnecessary disk operations)
if not NOTES_FOLDER.exists():
    NOTES_FOLDER.mkdir(parents=True)

HIDDEN_FOLDER = NOTES_FOLDER / f".{APP_SHORT_NAME.lower()}"
if not HIDDEN_FOLDER.exists():
    HIDDEN_FOLDER.mkdir(parents=True)


# --- Files ---
ID_FILE = HIDDEN_FOLDER / "config.json"
EMAIL_ID_FILE = HIDDEN_FOLDER / "email_config.json"

# For updates system
DEPLOY_INFO_PATH = HIDDEN_FOLDER / "deploy.info"
UPDATE_INFO_URL = "https://tech-naija-rise.github.io/BMTB/update.json"


NOTES_DB = NOTES_FOLDER / "BMTbnotes.db"
RECOVERY_FILE = NOTES_FOLDER / "recovery.key"
PASS_FILE = NOTES_FOLDER / "pass.pass"
FB_PATH = NOTES_FOLDER / "feedbacks.json"
SETTINGS_FILE = NOTES_FOLDER / "settings.json"
LOGS_FILE = NOTES_FOLDER / "app.log"


# --- Logging ---
# Use RotatingFileHandler to prevent slow startup from large log files
handler = RotatingFileHandler(LOGS_FILE, maxBytes=1_000_000, backupCount=3)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler]
)



def write_json_file(file, contents={}):
    """Must be in json"""
    try:
        
        with open(file, "w") as w:
            json.dump(contents, w)
        
    except Exception as e:
        logging.error(e)


def read_json_file(file):
    """Must be in json"""
    try:
       
        with open(file, "r") as r:
            contents = dict(json.load(r))
        
        return contents
    except Exception as e:
        logging.error(e)
        raise e


def read_txt_file(file):
    """Must be string"""
    with open(file, "r") as r:
        contents = r.read()
    return contents


def write_txt_file(file, contents=""):
    """Must be string"""
    with open(file, "r") as w:
        w.write(contents)
    return


# AutoUpdater
UPDATE_DOWNLOAD_FOLDER = os.path.join(
    os.path.expanduser("~"), f"{APP_SHORT_NAME}_updates")


# --- External Links ---
BMA_DOWNLOAD_LINK = "https://github.com/Mahmudumar/BMA/releases/latest"
BMTB_DOWNLOAD_LINK = "https://github.com/tech-naija-rise/BMTB/releases/latest"
BMTB_DOWNLOAD_LINK2 = "https://tech-naija-rise.github.io/BMTB_webpage/"

BMTB_FEEDBACK_SERVER = "https://feedback-server-tnr.onrender.com/feedback"
TNR_BMTB_SERVER = "https://feedback-server-tnr.onrender.com"


if __name__ == "__main__":
    
    pass