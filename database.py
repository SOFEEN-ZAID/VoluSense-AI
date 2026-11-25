
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "volusense.db"


def initialize_database():

    with sqlite3.connect(DB_NAME) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                object_name TEXT,
                estimated_volume REAL,
                actual_volume REAL,
                error REAL,
                date TEXT
            )
        """)


def save_measurement(name, estimated, actual):

    if actual <= 0:
        raise ValueError("Actual volume must be positive.")

    error = abs(estimated - actual) / actual * 100

    with sqlite3.connect(DB_NAME) as conn:

        conn.execute("""
            INSERT INTO measurements
            (object_name, estimated_volume,
             actual_volume, error, date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            float(estimated),
            float(actual),
            float(error),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))


def get_measurements():

    with sqlite3.connect(DB_NAME) as conn:

        return pd.read_sql_query(
            "SELECT * FROM measurements ORDER BY id DESC",
            conn
        )


initialize_database()
