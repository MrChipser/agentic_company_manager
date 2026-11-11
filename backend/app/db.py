from __future__ import annotations

import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    direction TEXT NOT NULL,
    amount TEXT NOT NULL,
    vat_rate INTEGER NOT NULL,
    vat_amount TEXT NOT NULL,
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    partner_name TEXT NOT NULL,
    discount_days INTEGER,
    discount_rate TEXT,
    credit_rate TEXT,
    credit_limit TEXT
);
CREATE TABLE IF NOT EXISTS account_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    starting_balance TEXT NOT NULL,
    vat_balance TEXT NOT NULL,
    credit_limit TEXT NOT NULL,
    credit_rate TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str = "financial_manager.db") -> None:
        self.path = path
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.connection.execute(
            "INSERT OR IGNORE INTO account_state VALUES (1, ?, ?, ?, ?)",
            ("1000000.00", "0.00", "5000000.00", "12.00"),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def add_invoice(self, data: dict) -> int:
        cursor = self.connection.execute(
            """INSERT INTO invoices
            (direction, amount, vat_rate, vat_amount, issue_date, due_date,
             partner_name, discount_days, discount_rate, credit_rate, credit_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["direction"], str(data["amount"]), data["vat_rate"],
                str(data["vat_amount"]), data["issue_date"].isoformat(),
                data["due_date"].isoformat(), data["partner_name"],
                data.get("discount_days"), str(data["discount_rate"]) if data.get("discount_rate") is not None else None,
                str(data["credit_rate"]) if data.get("credit_rate") is not None else None,
                str(data["credit_limit"]) if data.get("credit_limit") is not None else None,
            ),
        )
        if data["direction"] == "OUTGOING":
            self.connection.execute(
                "UPDATE account_state SET vat_balance = CAST(vat_balance AS REAL) + ? WHERE id = 1",
                (str(data["vat_amount"]),),
            )
        else:
            self.connection.execute(
                "UPDATE account_state SET vat_balance = CAST(vat_balance AS REAL) - ? WHERE id = 1",
                (str(data["vat_amount"]),),
            )
        self.connection.commit()
        return int(cursor.lastrowid)

    def list_invoices(self) -> list[sqlite3.Row]:
        return list(self.connection.execute("SELECT * FROM invoices ORDER BY due_date, id"))

    def account_state(self) -> sqlite3.Row:
        row = self.connection.execute("SELECT * FROM account_state WHERE id = 1").fetchone()
        assert row is not None
        return row

    def reset(self) -> None:
        self.connection.execute("DELETE FROM invoices")
        self.connection.execute(
            "UPDATE account_state SET starting_balance='1000000.00', vat_balance='0.00', credit_limit='5000000.00', credit_rate='12.00' WHERE id=1"
        )
        self.connection.commit()