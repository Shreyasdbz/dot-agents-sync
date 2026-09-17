"""SQLite ownership of balances and delivery records."""

import sqlite3


class LedgerStore:
    """Persist tenant-local balances and deliveries in a caller-selected database."""

    def __init__(self, database):
        self.connection = sqlite3.connect(database, timeout=5)
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS balances (
                tenant TEXT NOT NULL,
                account TEXT NOT NULL,
                amount INTEGER NOT NULL CHECK (amount >= 0),
                PRIMARY KEY (tenant, account)
            );
            CREATE TABLE IF NOT EXISTS deliveries (
                tenant TEXT NOT NULL,
                event TEXT NOT NULL,
                account TEXT NOT NULL,
                amount INTEGER NOT NULL,
                PRIMARY KEY (tenant, event)
            );
            """
        )

    def apply_credit(self, tenant, event, account, amount):
        """Record a delivery and credit its account in one transaction."""
        with self.connection:
            self.connection.execute(
                "INSERT OR REPLACE INTO deliveries VALUES (?, ?, ?, ?)",
                (tenant, event, account, amount),
            )
            self.connection.execute(
                """
                INSERT INTO balances VALUES (?, ?, ?)
                ON CONFLICT (tenant, account)
                DO UPDATE SET amount = balances.amount + excluded.amount
                """,
                (tenant, account, amount),
            )
        return self.balance(tenant, account)

    def balance(self, tenant, account):
        """Return a persisted balance, or zero for an account with no credits."""
        row = self.connection.execute(
            "SELECT amount FROM balances WHERE tenant = ? AND account = ?", (tenant, account)
        ).fetchone()
        return row[0] if row else 0

    def close(self):
        """Release the database connection."""
        self.connection.close()
