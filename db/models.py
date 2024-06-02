import sqlite3
import config

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
    config.DB.commit()
    config.DB.close()