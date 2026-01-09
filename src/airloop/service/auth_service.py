import os
import sqlite3
from typing import Optional


class AuthService:
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
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                account_number TEXT
            )
            """
        )
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "account_number" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN account_number TEXT")
        seed_users = [
            ("Amy", "123456", "ACCT-1001"),
            ("bob", "123456", "ACCT-1002"),
            ("Alex", "123456", "ACCT-1003"),
        ]
        for username, password, account_number in seed_users:
            conn.execute(
                "INSERT OR IGNORE INTO users (username, password, account_number) VALUES (?, ?, ?)",
                (username, password, account_number),
            )
        conn.commit()
        conn.close()

    def login(self, username: str, password: str) -> Optional[dict]:
        conn = self._open_db()
        cur = conn.execute(
            "SELECT id, username, account_number FROM users WHERE username = ? AND password = ?",
            (username, password),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row["id"],
            "username": row["username"],
            "account_number": row["account_number"],
        }

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        conn = self._open_db()
        cur = conn.execute(
            "SELECT id, username, account_number FROM users WHERE id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row["id"],
            "username": row["username"],
            "account_number": row["account_number"],
        }

    def list_users(self) -> list[dict]:
        conn = self._open_db()
        rows = conn.execute("SELECT id, username, account_number FROM users").fetchall()
        conn.close()
        return [
            {"id": row["id"], "username": row["username"], "account_number": row["account_number"]}
            for row in rows
        ]
