import os
from pathlib import Path
from dotenv import load_dotenv

ARGS = None

DOTENV_BASE_DIR = Path.cwd()
load_dotenv(Path(DOTENV_BASE_DIR, ".env"))

HOMEBASE_USERNAME = os.environ["CC_HOMEBASE_USERNAME"]
HOMEBASE_PASSWORD = os.environ["CC_HOMEBASE_PASSWORD"]
EMPLOYEE_FIRSTNAME = os.environ["CC_HOMEBASE_EMPLOYEE_FIRSTNAME"]
EMPLOYEE_LASTNAME = os.environ["CC_HOMEBASE_EMPLOYEE_LASTNAME"]
START_DATE = os.environ["CC_HOMEBASE_START_DATE"]
END_DATE = os.environ["CC_HOMEBASE_END_DATE"]
LOOKAHEAD = os.environ["CC_HOMEBASE_LOOKAHEAD"]
LOOKAHEAD = LOOKAHEAD.lower() in ["true", "1", "t", "y", "yes"]
LOOKAHEAD_DAYS = os.environ["CC_HOMEBASE_DAYS_LOOKAHEAD"]
LOOKAHEAD_DAYS = int(LOOKAHEAD_DAYS)

META = None
META_SETTINGS_PATH = ".homebase_calendar_sync"
META_DATA_PATH = ".homebase_calendar_sync_meta"
GOOGLE = None
API_SCOPES: list[str] = ["https://www.googleapis.com/auth/calendar"]

DB_NAME = "events.db"
DB = None
DB_CURSOR = None
