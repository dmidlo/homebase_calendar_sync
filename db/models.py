import sqlite3
import config
import time

def execute_with_retry(query, params=(), retries=5):
    while retries:
        try:
            config.DB_CURSOR.execute(query, params)
            return
        except sqlite3.OperationalError as e:
            if 'locked' in str(e).lower():
                retries -= 1
                print(f"Database is locked, retrying... {retries}/5")
                time.sleep(1)
            else:
                raise
    raise sqlite3.OperationalError("Database is Locked. all retries failed.")

def connect_database():
    config.DB = sqlite3.connect("events.db")
    config.DB_CURSOR = config.DB.cursor()

def setup_database():
    config.DB = sqlite3.connect("events.db")
    config.DB_CURSOR = config.DB.cursor()
    config.DB_CURSOR.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            hash TEXT NOT NULL,
            from_homebase INTEGER NOT NULL CHECK (from_homebase IN (0, 1)),
            homebase_shift_id TEXT UNIQUE
        )
    '''
    )
    config.DB_CURSOR.execute('''
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            homebase_shift_id TEXT NOT NULL UNIQUE,
            hash TEXT NOT NULL
        )
    '''
    )
    config.DB.commit()