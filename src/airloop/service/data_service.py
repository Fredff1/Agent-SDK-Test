import os
import random
import sqlite3
import string


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
                confirmation_number TEXT,
                seat_number INTEGER NOT NULL,
                meal_selection TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(flight_id) REFERENCES flights(id)
            )
            """
        )
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(orders)").fetchall()]
        if "confirmation_number" not in columns:
            conn.execute("ALTER TABLE orders ADD COLUMN confirmation_number TEXT")
        if "meal_selection" not in columns:
            conn.execute("ALTER TABLE orders ADD COLUMN meal_selection TEXT")
        if "status" not in columns:
            conn.execute("ALTER TABLE orders ADD COLUMN status TEXT")
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

    def _generate_confirmation_number(self, conn: sqlite3.Connection) -> str:
        while True:
            value = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            cur = conn.execute(
                "SELECT 1 FROM orders WHERE confirmation_number = ?",
                (value,),
            )
            if not cur.fetchone():
                return value

    def get_flight_by_number(self, flight_number: str) -> dict | None:
        conn = self._open_db()
        cur = conn.execute(
            "SELECT id, flight_number, seat_start, seat_end FROM flights WHERE flight_number = ?",
            (flight_number,),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row["id"],
            "flight_number": row["flight_number"],
            "seat_start": row["seat_start"],
            "seat_end": row["seat_end"],
        }

    def get_order(self, order_id: int, user_id: int) -> dict | None:
        conn = self._open_db()
        cur = conn.execute(
            """
            SELECT orders.id, orders.confirmation_number, orders.seat_number, orders.meal_selection, orders.status,
                   flights.id AS flight_id, flights.flight_number, flights.seat_start, flights.seat_end
            FROM orders
            JOIN flights ON orders.flight_id = flights.id
            WHERE orders.id = ? AND orders.user_id = ?
            """,
            (order_id, user_id),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row["id"],
            "confirmation_number": row["confirmation_number"],
            "seat_number": row["seat_number"],
            "meal_selection": row["meal_selection"],
            "status": row["status"],
            "flight_id": row["flight_id"],
            "flight_number": row["flight_number"],
            "seat_start": row["seat_start"],
            "seat_end": row["seat_end"],
        }

    def list_orders(self, user_id: int) -> list[dict]:
        conn = self._open_db()
        rows = conn.execute(
            """
            SELECT orders.id, orders.confirmation_number, orders.seat_number, orders.meal_selection, orders.status,
                   flights.flight_number
            FROM orders
            JOIN flights ON orders.flight_id = flights.id
            WHERE orders.user_id = ?
            ORDER BY orders.id DESC
            """,
            (user_id,),
        ).fetchall()
        conn.close()
        return [
            {
                "id": row["id"],
                "confirmation_number": row["confirmation_number"],
                "seat_number": row["seat_number"],
                "meal_selection": row["meal_selection"],
                "status": row["status"],
                "flight_number": row["flight_number"],
            }
            for row in rows
        ]

    def create_order(self, user_id: int) -> dict:
        conn = self._open_db()
        flight_row = conn.execute(
            "SELECT id, flight_number, seat_start, seat_end FROM flights ORDER BY id LIMIT 1"
        ).fetchone()
        if not flight_row:
            conn.close()
            raise ValueError("No flights available")
        confirmation = self._generate_confirmation_number(conn)
        seat_number = random.randint(flight_row["seat_start"], flight_row["seat_end"])
        conn.execute(
            "INSERT INTO orders (user_id, flight_id, confirmation_number, seat_number, status) VALUES (?, ?, ?, ?, ?)",
            (user_id, flight_row["id"], confirmation, seat_number, "active"),
        )
        order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()
        return {
            "id": order_id,
            "confirmation_number": confirmation,
            "seat_number": seat_number,
            "flight_number": flight_row["flight_number"],
            "meal_selection": None,
            "status": "active",
        }

    def update_order(
        self,
        order_id: int,
        user_id: int,
        seat_number: int | None = None,
        meal_selection: str | None = None,
    ) -> dict:
        existing = self.get_order(order_id, user_id)
        if not existing:
            raise ValueError("Order not found")
        if existing.get("status") == "canceled":
            raise ValueError("Order is canceled")
        conn = self._open_db()
        seat_value = seat_number if seat_number is not None else existing["seat_number"]
        meal_value = meal_selection if meal_selection is not None else existing["meal_selection"]
        conn.execute(
            "UPDATE orders SET seat_number = ?, meal_selection = ? WHERE id = ? AND user_id = ?",
            (seat_value, meal_value, order_id, user_id),
        )
        conn.commit()
        conn.close()
        return {
            "id": order_id,
            "seat_number": seat_value,
            "meal_selection": meal_value,
        }

    def cancel_order(self, user_id: int, order_id: int) -> None:
        conn = self._open_db()
        conn.execute(
            "UPDATE orders SET status = 'canceled' WHERE user_id = ? AND id = ?",
            (user_id, order_id),
        )
        conn.commit()
        conn.close()
