"""
SQLite database for managing video generation prompts.
Lives at: <project_root>/prompts.db
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

# Always store DB next to this file (project root)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts.db")


class PromptDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic         TEXT NOT NULL,
                    prompt        TEXT NOT NULL,
                    status        TEXT DEFAULT 'pending',
                    video_path    TEXT,
                    youtube_url   TEXT,
                    scheduled_date TEXT,
                    notes         TEXT,
                    created_at    TEXT DEFAULT (datetime('now')),
                    updated_at    TEXT DEFAULT (datetime('now'))
                )
            """)
            # Index for fast status queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON prompts(status)
            """)
            conn.commit()

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def add_prompt(self, topic: str, prompt: str) -> int:
        """Add a single prompt. Returns new row id."""
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO prompts (topic, prompt) VALUES (?, ?)",
                (topic, prompt)
            )
            conn.commit()
            return cur.lastrowid

    def add_prompts_bulk(self, items: List[Dict]) -> int:
        """
        Add many prompts at once.
        items = [{"topic": "...", "prompt": "..."}, ...]
        Returns number inserted.
        """
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO prompts (topic, prompt) VALUES (:topic, :prompt)",
                items
            )
            conn.commit()
            return len(items)

    def update_status(
        self,
        prompt_id: int,
        status: str,
        video_path: str = None,
        youtube_url: str = None,
        scheduled_date: str = None,
        notes: str = None,
    ):
        """Update the status and optional fields of a prompt."""
        fields = ["status = ?", "updated_at = ?"]
        values = [status, datetime.now().isoformat()]

        if video_path is not None:
            fields.append("video_path = ?")
            values.append(video_path)
        if youtube_url is not None:
            fields.append("youtube_url = ?")
            values.append(youtube_url)
        if scheduled_date is not None:
            fields.append("scheduled_date = ?")
            values.append(scheduled_date)
        if notes is not None:
            fields.append("notes = ?")
            values.append(notes)

        values.append(prompt_id)

        with self._connect() as conn:
            conn.execute(
                f"UPDATE prompts SET {', '.join(fields)} WHERE id = ?",
                values
            )
            conn.commit()

    def reset_status(self, prompt_id: int):
        """Reset a prompt back to pending."""
        self.update_status(prompt_id, "pending")

    def reset_all_failed(self):
        """Reset all failed prompts back to pending."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE prompts SET status='pending', updated_at=? WHERE status='failed'",
                (datetime.now().isoformat(),)
            )
            conn.commit()

    def delete_prompt(self, prompt_id: int):
        """Delete a prompt by ID."""
        with self._connect() as conn:
            conn.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
            conn.commit()

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def get_pending(self, statuses: List[str] = None) -> List[Dict]:
        """Get all pending (or given statuses) prompts, oldest first."""
        if statuses is None:
            statuses = ["pending"]
        placeholders = ",".join("?" * len(statuses))
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM prompts WHERE status IN ({placeholders}) ORDER BY id ASC",
                statuses
            ).fetchall()
        return [dict(r) for r in rows]

    def get_all(self) -> List[Dict]:
        """Get all prompts."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM prompts ORDER BY id ASC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_by_id(self, prompt_id: int) -> Optional[Dict]:
        """Get a single prompt by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM prompts WHERE id = ?", (prompt_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_stats(self) -> Dict:
        """Get counts by status."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) as count FROM prompts GROUP BY status"
            ).fetchall()
        return {r["status"]: r["count"] for r in rows}

    def search(self, keyword: str) -> List[Dict]:
        """Search prompts by topic or prompt text."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM prompts WHERE topic LIKE ? OR prompt LIKE ? ORDER BY id",
                (f"%{keyword}%", f"%{keyword}%")
            ).fetchall()
        return [dict(r) for r in rows]
