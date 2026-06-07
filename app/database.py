from __future__ import annotations
import sqlite3
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from app.config import DB_PATH, DEFAULT_SETTINGS


@dataclass
class TestResult:
    id: Optional[int]
    timestamp: str
    mode: str
    duration: int
    wpm: float
    raw_wpm: float
    accuracy: float
    consistency: float
    char_count: int
    error_count: int
    test_text: str
    wpm_snapshots: list = None
    error_map: dict = None


class Database:
    def __init__(self):
        self._conn = sqlite3.connect(str(DB_PATH))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        self._seed_defaults()

    def _create_tables(self):
        cur = self._conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                mode TEXT NOT NULL,
                duration INTEGER NOT NULL DEFAULT 0,
                wpm REAL NOT NULL,
                raw_wpm REAL NOT NULL,
                accuracy REAL NOT NULL,
                consistency REAL NOT NULL,
                char_count INTEGER NOT NULL DEFAULT 0,
                error_count INTEGER NOT NULL DEFAULT 0,
                test_text TEXT NOT NULL DEFAULT '',
                wpm_snapshots TEXT NOT NULL DEFAULT '[]',
                error_map TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS lesson_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                wpm REAL NOT NULL,
                accuracy REAL NOT NULL,
                stars INTEGER NOT NULL DEFAULT 0,
                completed INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                badge_id TEXT NOT NULL UNIQUE,
                earned_at TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def _seed_defaults(self):
        cur = self._conn.cursor()
        for key, value in DEFAULT_SETTINGS.items():
            cur.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        self._conn.commit()

    # ── Test results ──────────────────────────────────────────────────────────

    def save_test_result(self, result: TestResult) -> int:
        cur = self._conn.cursor()
        cur.execute("""
            INSERT INTO test_results
                (timestamp, mode, duration, wpm, raw_wpm, accuracy, consistency,
                 char_count, error_count, test_text, wpm_snapshots, error_map)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.timestamp or datetime.now().isoformat(),
            result.mode, result.duration, result.wpm, result.raw_wpm,
            result.accuracy, result.consistency, result.char_count,
            result.error_count, result.test_text,
            json.dumps(result.wpm_snapshots or []),
            json.dumps(result.error_map or {}),
        ))
        self._conn.commit()
        return cur.lastrowid

    def get_test_history(self, mode: Optional[str] = None, limit: int = 500) -> list[TestResult]:
        cur = self._conn.cursor()
        if mode:
            cur.execute(
                "SELECT * FROM test_results WHERE mode = ? ORDER BY timestamp DESC LIMIT ?",
                (mode, limit)
            )
        else:
            cur.execute(
                "SELECT * FROM test_results ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
        return [self._row_to_result(r) for r in cur.fetchall()]

    def get_personal_bests(self) -> dict:
        cur = self._conn.cursor()
        cur.execute("""
            SELECT mode, MAX(wpm) as best_wpm, accuracy, consistency, timestamp
            FROM test_results
            GROUP BY mode
        """)
        return {row["mode"]: dict(row) for row in cur.fetchall()}

    def get_personal_best_for_mode(self, mode: str) -> Optional[TestResult]:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM test_results WHERE mode = ? ORDER BY wpm DESC LIMIT 1",
            (mode,)
        )
        row = cur.fetchone()
        return self._row_to_result(row) if row else None

    def _row_to_result(self, row) -> TestResult:
        return TestResult(
            id=row["id"],
            timestamp=row["timestamp"],
            mode=row["mode"],
            duration=row["duration"],
            wpm=row["wpm"],
            raw_wpm=row["raw_wpm"],
            accuracy=row["accuracy"],
            consistency=row["consistency"],
            char_count=row["char_count"],
            error_count=row["error_count"],
            test_text=row["test_text"],
            wpm_snapshots=json.loads(row["wpm_snapshots"]),
            error_map=json.loads(row["error_map"]),
        )

    # ── Lesson progress ───────────────────────────────────────────────────────

    def save_lesson_progress(self, lesson_id: str, wpm: float, accuracy: float,
                             stars: int, completed: bool):
        cur = self._conn.cursor()
        cur.execute("""
            INSERT INTO lesson_progress (lesson_id, timestamp, wpm, accuracy, stars, completed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (lesson_id, datetime.now().isoformat(), wpm, accuracy, stars, int(completed)))
        self._conn.commit()

    def get_lesson_progress(self, lesson_id: Optional[str] = None) -> dict:
        cur = self._conn.cursor()
        if lesson_id:
            cur.execute("""
                SELECT lesson_id, MAX(stars) as best_stars, MAX(wpm) as best_wpm,
                       MAX(accuracy) as best_accuracy, MAX(completed) as completed
                FROM lesson_progress WHERE lesson_id = ?
                GROUP BY lesson_id
            """, (lesson_id,))
        else:
            cur.execute("""
                SELECT lesson_id, MAX(stars) as best_stars, MAX(wpm) as best_wpm,
                       MAX(accuracy) as best_accuracy, MAX(completed) as completed
                FROM lesson_progress
                GROUP BY lesson_id
            """)
        return {row["lesson_id"]: dict(row) for row in cur.fetchall()}

    def get_completed_lesson_count(self) -> int:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT COUNT(DISTINCT lesson_id) FROM lesson_progress WHERE completed = 1"
        )
        return cur.fetchone()[0]

    # ── Settings ──────────────────────────────────────────────────────────────

    def get_setting(self, key: str) -> Optional[str]:
        cur = self._conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row["value"] if row else DEFAULT_SETTINGS.get(key)

    def set_setting(self, key: str, value: str):
        cur = self._conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        self._conn.commit()

    def get_all_settings(self) -> dict:
        cur = self._conn.cursor()
        cur.execute("SELECT key, value FROM settings")
        return {row["key"]: row["value"] for row in cur.fetchall()}

    # ── Badges ────────────────────────────────────────────────────────────────

    def save_badge(self, badge_id: str):
        cur = self._conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO badges (badge_id, earned_at) VALUES (?, ?)",
            (badge_id, datetime.now().isoformat())
        )
        self._conn.commit()

    def get_badges(self) -> list[dict]:
        cur = self._conn.cursor()
        cur.execute("SELECT badge_id, earned_at FROM badges ORDER BY earned_at")
        return [dict(row) for row in cur.fetchall()]

    def has_badge(self, badge_id: str) -> bool:
        cur = self._conn.cursor()
        cur.execute("SELECT 1 FROM badges WHERE badge_id = ?", (badge_id,))
        return cur.fetchone() is not None

    # ── Housekeeping ──────────────────────────────────────────────────────────

    def clear_test_history(self):
        self._conn.execute("DELETE FROM test_results")
        self._conn.commit()

    def clear_lesson_progress(self):
        self._conn.execute("DELETE FROM lesson_progress")
        self._conn.commit()

    def get_db_size(self) -> int:
        return DB_PATH.stat().st_size if DB_PATH.exists() else 0

    def close(self):
        self._conn.close()
