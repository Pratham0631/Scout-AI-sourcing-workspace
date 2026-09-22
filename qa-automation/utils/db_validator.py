import json
import sqlite3
from typing import Any, Dict, List, Optional
from utils.config import Config
from utils.logger import logger

class DatabaseValidator:
    """
    Database validation utility for QA Automation.
    Simulates / validates relational database persistence of candidates and search states.
    Can operate on an embedded SQLite database seeded from profiles.json or an external DB.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self._seed_candidates()

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                current_title TEXT NOT NULL,
                years_experience INTEGER NOT NULL,
                location TEXT NOT NULL,
                current_company TEXT NOT NULL,
                current_company_type TEXT NOT NULL,
                skills TEXT NOT NULL,
                education TEXT,
                summary TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS past_companies (
                candidate_id TEXT,
                company TEXT,
                company_type TEXT,
                title TEXT,
                years INTEGER,
                FOREIGN KEY (candidate_id) REFERENCES candidates(id)
            )
        """)
        self.conn.commit()

    def _seed_candidates(self):
        if not Config.PROFILES_JSON_PATH.exists():
            logger.warning(f"Profiles JSON not found at {Config.PROFILES_JSON_PATH}")
            return

        with open(Config.PROFILES_JSON_PATH, "r", encoding="utf-8") as f:
            profiles = json.load(f)

        cursor = self.conn.cursor()
        for p in profiles:
            cursor.execute("""
                INSERT OR REPLACE INTO candidates
                (id, name, current_title, years_experience, location, current_company, current_company_type, skills, education, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["id"],
                p["name"],
                p["current_title"],
                p["years_experience"],
                p["location"],
                p["current_company"],
                p["current_company_type"],
                ", ".join(p.get("skills", [])),
                p.get("education", ""),
                p.get("summary", "")
            ))

            for past in p.get("past_companies", []):
                cursor.execute("""
                    INSERT INTO past_companies (candidate_id, company, company_type, title, years)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    p["id"],
                    past.get("company"),
                    past.get("company_type"),
                    past.get("title"),
                    past.get("years", 0)
                ))
        self.conn.commit()
        logger.info(f"Database seeded with {len(profiles)} candidates.")

    def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def count_candidates(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM candidates")
        return cursor.fetchone()[0]

    def query_matching_candidates(
        self,
        min_years: Optional[int] = None,
        max_years: Optional[int] = None,
        location: Optional[str] = None,
        required_skill: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM candidates WHERE 1=1"
        params = []

        if min_years is not None:
            query += " AND years_experience >= ?"
            params.append(min_years)
        if max_years is not None:
            query += " AND years_experience <= ?"
            params.append(max_years)
        if location:
            query += " AND LOWER(location) = LOWER(?)"
            params.append(location.strip())
        if required_skill:
            query += " AND LOWER(skills) LIKE LOWER(?)"
            params.append(f"%{required_skill.strip()}%")

        cursor = self.conn.cursor()
        cursor.execute(query, tuple(params))
        return [dict(r) for r in cursor.fetchall()]

    def close(self):
        self.conn.close()
