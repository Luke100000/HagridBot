import sqlite3
from pathlib import Path

from app.config import get_data_path

DB_PATH = Path(get_data_path("storage.sqlite3"))


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_storage() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS user_xp
            (
                guild           INTEGER NOT NULL,
                user            INTEGER NOT NULL,
                xp              INTEGER NOT NULL DEFAULT 0,
                minute_bucket   REAL    NOT NULL DEFAULT 0,
                hour_bucket     REAL    NOT NULL DEFAULT 0,
                last_message_at REAL    NOT NULL DEFAULT 0,
                PRIMARY KEY (guild, user)
            );

            CREATE TABLE IF NOT EXISTS rank_settings
            (
                guild INTEGER NOT NULL,
                role  INTEGER NOT NULL,
                xp    INTEGER NOT NULL,
                PRIMARY KEY (guild, role)
            );

            CREATE TABLE IF NOT EXISTS rank_channel
            (
                guild       INTEGER PRIMARY KEY,
                rankChannel INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS stats
            (
                guild      TEXT    NOT NULL,
                group_name TEXT    NOT NULL,
                count      INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild, group_name)
            );
            """
        )


def fetch_one(query: str, params: tuple = ()) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute(query, params).fetchone()


def fetch_all(query: str, params: tuple = ()) -> list[sqlite3.Row]:
    with _connect() as conn:
        return list(conn.execute(query, params).fetchall())


def execute(query: str, params: tuple = ()) -> None:
    with _connect() as conn:
        conn.execute(query, params)


def executemany(query: str, params: list[tuple]) -> None:
    with _connect() as conn:
        conn.executemany(query, params)
