"""
storage.py
Local persistence engine with multi-tiered synchronization:
1. SQLite relational database (ACID transactions, indexed schemas, foreign keys).
2. Dual JSON & CSV synchronization mirrors.
3. Automated corrupted-file recovery and atomic writing.
Engineered for Campus Catalyst: College Event Registration Manager (Project #8).
"""

from __future__ import annotations
import csv
import json
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from models import Event, Registration


class StorageManager:
    """
    Manages robust local data persistence with dual JSON/CSV mirrors and SQLite.
    Provides ACID safety, schema checks, and automatic corrupted-file recovery.
    """

    REQUIRED_EVENT_FIELDS = {"event_id", "title", "category", "event_date", "registration_deadline", "max_capacity", "venue"}
    REQUIRED_REG_FIELDS = {"registration_id", "event_id", "student_name", "roll_number", "email", "phone", "department", "year_of_study"}

    def __init__(self, base_dir: Path | str = None):
        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parent
        else:
            self.base_dir = Path(base_dir)

        self.data_dir = self.base_dir / "data"
        self.exports_dir = self.base_dir / "exports"
        self.charts_dir = self.exports_dir / "charts"

        self._ensure_directories()

        self.sqlite_db_path = self.data_dir / "campus_events.db"
        self.events_json_path = self.data_dir / "events.json"
        self.events_csv_path = self.data_dir / "events.csv"
        self.registrations_json_path = self.data_dir / "registrations.json"
        self.registrations_csv_path = self.data_dir / "registrations.csv"

        self._init_sqlite_schema()

    def _ensure_directories(self) -> None:
        """Ensures storage and export folders exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    def _get_sqlite_connection(self) -> sqlite3.Connection:
        """Returns SQLite connection with WAL mode enabled for high concurrency."""
        conn = sqlite3.connect(str(self.sqlite_db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _init_sqlite_schema(self) -> None:
        """Initializes relational tables and performance indexes in SQLite."""
        conn = None
        try:
            conn = self._get_sqlite_connection()
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        event_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        category TEXT NOT NULL,
                        event_date TEXT NOT NULL,
                        registration_deadline TEXT NOT NULL,
                        max_capacity INTEGER NOT NULL,
                        venue TEXT NOT NULL,
                        fee REAL DEFAULT 0.0,
                        created_at TEXT NOT NULL
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS registrations (
                        registration_id TEXT PRIMARY KEY,
                        event_id TEXT NOT NULL,
                        student_name TEXT NOT NULL,
                        roll_number TEXT NOT NULL,
                        email TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        department TEXT NOT NULL,
                        year_of_study INTEGER NOT NULL,
                        registration_timestamp TEXT NOT NULL,
                        payment_status TEXT NOT NULL,
                        attendance_status TEXT NOT NULL,
                        registration_status TEXT NOT NULL,
                        notes TEXT,
                        FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_reg_event ON registrations (event_id);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_reg_roll ON registrations (roll_number);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_reg_email ON registrations (email);")
        except Exception as e:
            print(f" [WARNING] Could not initialize SQLite schema: {e}")
        finally:
            if conn:
                conn.close()

    def _backup_corrupted_file(self, file_path: Path) -> Path:
        """Creates a timestamped backup of a malformed or corrupted file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_name(f"{file_path.stem}_corrupted_{timestamp}{file_path.suffix}.bak")
        try:
            shutil.copy2(file_path, backup_path)
            print(f" [RECOVERY] Corrupted file backed up to: {backup_path.name}")
        except Exception as e:
            print(f" [WARNING] Could not create backup of corrupted file {file_path}: {e}")
        return backup_path

    # ==========================================
    # EVENT PERSISTENCE
    # ==========================================

    def load_events(self) -> List[Event]:
        """
        Loads events with multi-tier fallback:
        1. JSON file (with schema validation & auto-recovery)
        2. SQLite DB
        3. CSV mirror
        """
        events: List[Event] = []

        if self.events_json_path.exists():
            try:
                with open(self.events_json_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and self._validate_event_schema(item):
                                    try:
                                        events.append(Event.from_dict(item))
                                    except Exception:
                                        continue
                            if events:
                                return events
            except (json.JSONDecodeError, ValueError) as e:
                print(f" [ALERT] Corrupted events.json detected ({e}). Initiating recovery...")
                self._backup_corrupted_file(self.events_json_path)

        # Fallback to SQLite
        events = self._load_events_from_sqlite()
        if events:
            self._save_events_to_json(events)
            self._save_events_to_csv(events)
            return events

        # Fallback to CSV
        if self.events_csv_path.exists():
            events = self._load_events_from_csv()
            if events:
                self.save_events(events)
                return events

        return []

    def _load_events_from_sqlite(self) -> List[Event]:
        """Loads events from SQLite database."""
        events = []
        conn = None
        try:
            conn = self._get_sqlite_connection()
            cursor = conn.execute("SELECT * FROM events ORDER BY event_id ASC;")
            for row in cursor.fetchall():
                events.append(Event.from_dict(dict(row)))
        except Exception:
            pass
        finally:
            if conn:
                conn.close()
        return events

    def _load_events_from_csv(self) -> List[Event]:
        """Loads events from CSV fallback file."""
        if not self.events_csv_path.exists():
            return []
        events: List[Event] = []
        try:
            with open(self.events_csv_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if self._validate_event_schema(row):
                        try:
                            events.append(Event.from_dict(row))
                        except Exception:
                            continue
        except Exception:
            pass
        return events

    def save_events(self, events: List[Event]) -> bool:
        """
        Synchronously persists events across SQLite, JSON, and CSV.
        """
        self._ensure_directories()
        data = [e.to_dict() for e in events]

        # 1. Sync SQLite
        conn = None
        try:
            conn = self._get_sqlite_connection()
            with conn:
                conn.execute("DELETE FROM events;")
                for e in events:
                    conn.execute("""
                        INSERT INTO events (event_id, title, category, event_date, registration_deadline, max_capacity, venue, fee, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (e.event_id, e.title, e.category, e.event_date, e.registration_deadline, e.max_capacity, e.venue, e.fee, e.created_at))
        except Exception as sqle:
            print(f" [WARNING] SQLite event sync: {sqle}")
        finally:
            if conn:
                conn.close()

        # 2. Sync JSON & CSV
        self._save_events_to_json(events)
        self._save_events_to_csv(events)
        return True

    def _save_events_to_json(self, events: List[Event]) -> bool:
        tmp_json = self.events_json_path.with_suffix(".tmp")
        try:
            data = [e.to_dict() for e in events]
            with open(tmp_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            tmp_json.replace(self.events_json_path)
            return True
        except Exception:
            if tmp_json.exists():
                tmp_json.unlink(missing_ok=True)
            return False

    def _save_events_to_csv(self, events: List[Event]) -> bool:
        tmp_csv = self.events_csv_path.with_suffix(".tmp")
        try:
            fieldnames = ["event_id", "title", "category", "event_date", "registration_deadline", "max_capacity", "venue", "fee", "created_at"]
            with open(tmp_csv, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for e in events:
                    writer.writerow(e.to_dict())
            tmp_csv.replace(self.events_csv_path)
            return True
        except Exception:
            if tmp_csv.exists():
                tmp_csv.unlink(missing_ok=True)
            return False

    def _validate_event_schema(self, item: Dict[str, Any]) -> bool:
        return self.REQUIRED_EVENT_FIELDS.issubset(item.keys())

    # ==========================================
    # REGISTRATION PERSISTENCE
    # ==========================================

    def load_registrations(self) -> List[Registration]:
        """
        Loads registrations with multi-tier fallback (JSON -> SQLite -> CSV).
        """
        regs: List[Registration] = []

        if self.registrations_json_path.exists():
            try:
                with open(self.registrations_json_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and self._validate_registration_schema(item):
                                    try:
                                        regs.append(Registration.from_dict(item))
                                    except Exception:
                                        continue
                            if regs:
                                return regs
            except (json.JSONDecodeError, ValueError) as e:
                print(f" [ALERT] Corrupted registrations.json detected ({e}). Initiating recovery...")
                self._backup_corrupted_file(self.registrations_json_path)

        # Fallback to SQLite
        regs = self._load_registrations_from_sqlite()
        if regs:
            self._save_registrations_to_json(regs)
            self._save_registrations_to_csv(regs)
            return regs

        # Fallback to CSV
        if self.registrations_csv_path.exists():
            regs = self._load_registrations_from_csv()
            if regs:
                self.save_registrations(regs)
                return regs

        return []

    def _load_registrations_from_sqlite(self) -> List[Registration]:
        """Loads registrations from SQLite."""
        regs = []
        conn = None
        try:
            conn = self._get_sqlite_connection()
            cursor = conn.execute("SELECT * FROM registrations ORDER BY registration_id ASC;")
            for row in cursor.fetchall():
                regs.append(Registration.from_dict(dict(row)))
        except Exception:
            pass
        finally:
            if conn:
                conn.close()
        return regs

    def _load_registrations_from_csv(self) -> List[Registration]:
        if not self.registrations_csv_path.exists():
            return []
        regs: List[Registration] = []
        try:
            with open(self.registrations_csv_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if self._validate_registration_schema(row):
                        try:
                            regs.append(Registration.from_dict(row))
                        except Exception:
                            continue
        except Exception:
            pass
        return regs

    def save_registrations(self, registrations: List[Registration]) -> bool:
        """Synchronously persists registrations across SQLite, JSON, and CSV."""
        self._ensure_directories()

        # 1. Sync SQLite
        conn = None
        try:
            conn = self._get_sqlite_connection()
            with conn:
                conn.execute("DELETE FROM registrations;")
                for r in registrations:
                    conn.execute("""
                        INSERT INTO registrations (
                            registration_id, event_id, student_name, roll_number, email, phone,
                            department, year_of_study, registration_timestamp, payment_status,
                            attendance_status, registration_status, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        r.registration_id, r.event_id, r.student_name, r.roll_number, r.email, r.phone,
                        r.department, r.year_of_study, r.registration_timestamp, r.payment_status,
                        r.attendance_status, r.registration_status, r.notes
                    ))
        except Exception as sqle:
            print(f" [WARNING] SQLite registration sync: {sqle}")
        finally:
            if conn:
                conn.close()

        # 2. Sync JSON & CSV
        self._save_registrations_to_json(registrations)
        self._save_registrations_to_csv(registrations)
        return True

    def _save_registrations_to_json(self, regs: List[Registration]) -> bool:
        tmp_json = self.registrations_json_path.with_suffix(".tmp")
        try:
            data = [r.to_dict() for r in regs]
            with open(tmp_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            tmp_json.replace(self.registrations_json_path)
            return True
        except Exception:
            if tmp_json.exists():
                tmp_json.unlink(missing_ok=True)
            return False

    def _save_registrations_to_csv(self, regs: List[Registration]) -> bool:
        tmp_csv = self.registrations_csv_path.with_suffix(".tmp")
        try:
            fieldnames = [
                "registration_id", "event_id", "student_name", "roll_number",
                "email", "phone", "department", "year_of_study",
                "registration_timestamp", "payment_status", "attendance_status",
                "registration_status", "notes"
            ]
            with open(tmp_csv, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in regs:
                    writer.writerow(r.to_dict())
            tmp_csv.replace(self.registrations_csv_path)
            return True
        except Exception:
            if tmp_csv.exists():
                tmp_csv.unlink(missing_ok=True)
            return False

    def _validate_registration_schema(self, item: Dict[str, Any]) -> bool:
        return self.REQUIRED_REG_FIELDS.issubset(item.keys())
