import os
import sqlite3


class DataService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _open_db(self) -> sqlite3.Connection:
        dir_name = os.path.dirname(self.db_path) or "."
        os.makedirs(dir_name, exist_ok=True)
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        conn = self._open_db()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS flights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flight_number TEXT UNIQUE NOT NULL,
                seat_start INTEGER NOT NULL,
                seat_end INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                flight_id INTEGER NOT NULL,
                seat_number INTEGER NOT NULL,
                meal_selection TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(flight_id) REFERENCES flights(id)
            )
            """
        )
        seed_flights = [
            ("AL100", 1, 30),
            ("AL200", 1, 24),
            ("AL300", 1, 36),
        ]
        for flight_number, seat_start, seat_end in seed_flights:
            conn.execute(
                "INSERT OR IGNORE INTO flights (flight_number, seat_start, seat_end) VALUES (?, ?, ?)",
                (flight_number, seat_start, seat_end),
            )
        conn.commit()
        conn.close()
