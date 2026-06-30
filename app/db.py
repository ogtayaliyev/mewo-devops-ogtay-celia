import os
import sqlite3
import time
from pathlib import Path

from app.games import sort_leaderboard

DB_PATH = Path(os.getenv("DB_PATH", "/data/leaderboard.db"))


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player TEXT NOT NULL,
                game TEXT NOT NULL,
                score INTEGER NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS last_submit (
                player TEXT NOT NULL,
                game TEXT NOT NULL,
                submitted_at REAL NOT NULL,
                PRIMARY KEY (player, game)
            )
            """
        )
        conn.commit()


def add_score(player: str, game: str, score: int) -> int:
    """Enregistre un score et retourne le rang obtenu (1 = meilleur)."""
    now = time.time()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO scores (player, game, score, created_at) VALUES (?, ?, ?, ?)",
            (player, game, score, now),
        )
        conn.execute(
            """
            INSERT INTO last_submit (player, game, submitted_at)
            VALUES (?, ?, ?)
            ON CONFLICT(player, game) DO UPDATE SET submitted_at = excluded.submitted_at
            """,
            (player, game, now),
        )
        rank = conn.execute(
            """
            SELECT COUNT(*) + 1 FROM scores
            WHERE game = ? AND score > ?
            """,
            (game, score),
        ).fetchone()[0]
        conn.commit()
        return rank


def get_last_submit(player: str, game: str) -> float | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT submitted_at FROM last_submit WHERE player = ? AND game = ?",
            (player, game),
        ).fetchone()
        return row["submitted_at"] if row else None


def get_leaderboard(game: str, limit: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT player, score FROM scores
            WHERE game = ?
            ORDER BY score DESC, created_at ASC
            LIMIT ?
            """,
            (game, limit),
        ).fetchall()
    return [{"player": r["player"], "score": r["score"]} for r in rows]


def get_player_best_scores(player: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT game, MAX(score) AS score
            FROM scores
            WHERE player = ?
            GROUP BY game
            ORDER BY score DESC
            """,
            (player,),
        ).fetchall()
    return sort_leaderboard([{"game": r["game"], "score": r["score"]} for r in rows])
