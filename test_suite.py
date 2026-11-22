"""
test_suite.py
Comprehensive automated test suite for
Campus Catalyst: College Event Registration Manager (Project #8).
Verifies models, input validators, storage corruption recovery, engine rules,
threshold alerts, bulk import error logging, and analytics exporters.
"""

from __future__ import annotations
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, date, timedelta

from models import Event, Registration, EventCategory, PaymentStatus, AttendanceStatus, RegistrationStatus
from validators import (
    is_valid_email,
    is_valid_phone,
    clean_phone,
    is_valid_roll_number,
    is_valid_date,
    validate_registration_row
)
from storage import StorageManager
from engine import RegistrationEngine
from analytics import ReportExporter, VisualPlotter, AuditLogger
from seed_data import seed_database, get_sample_events, get_sample_registrations, create_sample_legacy_csv


class TestCollegeEventManager(unittest.TestCase):

    def setUp(self):
        # Create an isolated temporary test directory
        self.test_dir = Path(tempfile.mkdtemp(prefix="campus_test_"))
        self.storage = StorageManager(self.test_dir)
        self.audit_log_path = self.storage.exports_dir / "test_audit.log"
        self.audit_logger = AuditLogger(self.audit_log_path)
        self.engine = RegistrationEngine(self.storage, audit_logger=self.audit_logger.log)

    def tearDown(self):
        # Clean up temporary files
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ==========================================
    # 1. MODELS TEST
    # ==========================================
    def test_event_model_and_deadlines(self):
        today = date.today()
        future_date = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        past_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")

        event = Event(
            event_id="EVT-900",
            title="AI Workshop",
            category=EventCategory.WORKSHOP.value,
            event_date=future_date,
            registration_deadline=future_date,
            max_capacity=50,
            venue="Lab 101",
            fee=150.0
        )

        self.assertEqual(event.event_id, "EVT-900")
        self.assertTrue(event.is_registration_open())
        self.assertFalse(event.is_deadline_passed())
        self.assertEqual(event.days_until_deadline(), 10)

        # Test dictionary serialization and deserialization
        d = event.to_dict()
        event_recreated = Event.from_dict(d)
        self.assertEqual(event.title, event_recreated.title)
        self.assertEqual(event.fee, event_recreated.fee)

        # Test past deadline
        past_event = Event(
            event_id="EVT-901",
            title="Old Event",
            category=EventCategory.SEMINAR.value,
            event_date=past_date,
            registration_deadline=past_date,
            max_capacity=20,
            venue="Hall A",
            fee=0.0
        )
        self.assertTrue(past_event.is_deadline_passed())
        self.assertTrue(past_event.days_until_deadline() < 0)

    def test_registration_model(self):
        reg = Registration(
            registration_id="REG-2026-999",
            event_id="EVT-900",
            student_name="Test Student",
            roll_number="22CS999",
            email="test.student@campus.edu",
            phone="9876543210",
            department="Computer Science",
            year_of_study=3
        )
        self.assertEqual(reg.registration_id, "REG-2026-999")
        d = reg.to_dict()
        reg_copy = Registration.from_dict(d)
        self.assertEqual(reg.roll_number, reg_copy.roll_number)
        self.assertEqual(reg.email, reg_copy.email)

    # ==========================================
    # 2. VALIDATORS TEST
    # ==========================================
    def test_email_validation(self):
        self.assertTrue(is_valid_email("student@campus.edu"))
        self.assertTrue(is_valid_email("first.last@domain.co.in"))
        self.assertFalse(is_valid_email("invalid-email"))
        self.assertFalse(is_valid_email("missing-domain@"))
        self.assertFalse(is_valid_email("@nodomain.com"))
        self.assertFalse(is_valid_email(""))

    def test_phone_validation(self):
        self.assertTrue(is_valid_phone("9876543210"))
        self.assertTrue(is_valid_phone("+91-9876543210"))
        self.assertTrue(is_valid_phone("98765 43210"))
        self.assertEqual(clean_phone("+91-9876543210"), "9876543210")
        self.assertFalse(is_valid_phone("12345"))  # too short
        self.assertFalse(is_valid_phone("987654321000"))  # too long
        self.assertFalse(is_valid_phone("abcdefghij"))

    def test_roll_number_validation(self):
        self.assertTrue(is_valid_roll_number("22CS104"))
        self.assertTrue(is_valid_roll_number("IT-2026-05"))
        self.assertFalse(is_valid_roll_number("CS"))  # too short (<4)
        self.assertFalse(is_valid_roll_number("CS202612345678901"))  # too long (>15)
        self.assertFalse(is_valid_roll_number(""))

    def test_date_validation(self):
        valid, d_obj, err = is_valid_date("2026-12-15")
        self.assertTrue(valid)
        self.assertEqual(d_obj.year, 2026)

        invalid, _, err = is_valid_date("15-12-2026")
        self.assertFalse(invalid)
        invalid_feb, _, err = is_valid_date("2026-02-31")
        self.assertFalse(invalid_feb)

    def test_row_validator(self):
        good_row = {
            "event_id": "EVT-101",
            "student_name": "Valid Student",
            "roll_number": "22CS101",
            "email": "valid@campus.edu",
            "phone": "9876543210",
            "department": "Computer Science",
            "year_of_study": 3
        }
        ok, errors = validate_registration_row(good_row)
        self.assertTrue(ok)
        self.assertEqual(len(errors), 0)

        bad_row = {
            "event_id": "",
            "student_name": "X",  # too short
            "roll_number": "12",  # too short
            "email": "not-an-email",
            "phone": "999",
            "department": "",
            "year_of_study": 7   # out of bounds
        }
        ok_bad, errors_bad = validate_registration_row(bad_row)
        self.assertFalse(ok_bad)
        self.assertGreaterEqual(len(errors_bad), 6)

    # ==========================================
    # 3. STORAGE PERSISTENCE & CORRUPTION RECOVERY
    # ==========================================
    def test_storage_dual_sync(self):
        events = get_sample_events()
        self.storage.save_events(events)

        self.assertTrue(self.storage.events_json_path.exists())
        self.assertTrue(self.storage.events_csv_path.exists())

        loaded = self.storage.load_events()
        self.assertEqual(len(loaded), len(events))
        self.assertEqual(loaded[0].event_id, events[0].event_id)

    def test_storage_corruption_recovery(self):
        events = get_sample_events()
        self.storage.save_events(events)

        # Intentionally corrupt the JSON file
        with open(self.storage.events_json_path, "w", encoding="utf-8") as f:
            f.write("<<<CORRUPT_JSON_DATA_MALFORMED>>>")

        # Loading should detect corruption, back up corrupt file, and recover from CSV mirror
        recovered_events = self.storage.load_events()
        self.assertEqual(len(recovered_events), len(events))

        # Verify backup was created
        backups = list(self.storage.data_dir.glob("*corrupted*.bak"))
        self.assertGreaterEqual(len(backups), 1)

    # ==========================================
    # 4. BUSINESS LOGIC ENGINE TESTS
    # ==========================================
    def test_duplicate_registration_prevention(self):
        today = date.today()
        deadline = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        self.engine.add_event(
            title="Web Summit",
            category="Technical",
            event_date=deadline,
            registration_deadline=deadline,
            max_capacity=50,
            venue="Auditorium",
            fee=0.0
        )
        eid = self.engine.events[0].event_id

        # Register first student
        ok1, msg1, reg1 = self.engine.register_participant(
            event_id=eid,
            student_name="Alice Smith",
            roll_number="22CS101",
            email="alice@campus.edu",
            phone="9876543210",
            department="Computer Science",
            year_of_study=3
        )
        self.assertTrue(ok1)

        # Attempt to register with same roll number
        ok2, msg2, reg2 = self.engine.register_participant(
            event_id=eid,
            student_name="Alice Smith",
            roll_number="22CS101",
            email="alice.different@campus.edu",
            phone="9876543211",
            department="Computer Science",
            year_of_study=3
        )
        self.assertFalse(ok2)
        self.assertIn("already registered", msg2)

        # Attempt to register with same email
        ok3, msg3, reg3 = self.engine.register_participant(
            event_id=eid,
            student_name="Bob Smith",
            roll_number="22CS102",
            email="alice@campus.edu",
            phone="9876543212",
            department="Computer Science",
            year_of_study=3
        )
        self.assertFalse(ok3)
        self.assertIn("already registered", msg3)

    def test_capacity_enforcement_and_waitlist(self):
        today = date.today()
        deadline = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        # Create event with capacity 2
        self.engine.add_event(
            title="Exclusive Masterclass",
            category="Workshop",
            event_date=deadline,
            registration_deadline=deadline,
            max_capacity=2,
            venue="Seminar Room 1",
            fee=0.0
        )
        eid = self.engine.events[0].event_id

        # Participant 1
        ok1, _, r1 = self.engine.register_participant(eid, "P1", "22CS001", "p1@campus.edu", "9876543201", "CSE", 1)
        self.assertTrue(ok1)
        self.assertEqual(r1.registration_status, RegistrationStatus.CONFIRMED.value)

        # Participant 2 (Reaches 100%)
        ok2, _, r2 = self.engine.register_participant(eid, "P2", "22CS002", "p2@campus.edu", "9876543202", "CSE", 1)
        self.assertTrue(ok2)
        self.assertEqual(r2.registration_status, RegistrationStatus.CONFIRMED.value)

        # Participant 3 (Should be waitlisted)
        ok3, msg3, r3 = self.engine.register_participant(eid, "P3", "22CS003", "p3@campus.edu", "9876543203", "CSE", 1, allow_waitlist=True)
        self.assertTrue(ok3)
        self.assertEqual(r3.registration_status, RegistrationStatus.WAITLISTED.value)
        self.assertIn("WAITLIST", msg3)

    def test_registration_cancellation(self):
        today = date.today()
        deadline = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        self.engine.add_event("Fest", "Cultural", deadline, deadline, 10, "Ground", 0.0)
        eid = self.engine.events[0].event_id

        ok, _, reg = self.engine.register_participant(eid, "Cancel Me", "22CS999", "cancel@campus.edu", "9876543299", "CSE", 2)
        self.assertTrue(ok)

        # Cancel
        c_ok, c_msg = self.engine.cancel_registration(reg.registration_id, reason="Medical emergency")
        self.assertTrue(c_ok)

        cancelled_reg = self.engine.get_registration(reg.registration_id)
        self.assertEqual(cancelled_reg.registration_status, RegistrationStatus.CANCELLED.value)
        self.assertEqual(cancelled_reg.attendance_status, AttendanceStatus.CANCELLED.value)

    def test_search_and_filtering(self):
        seed_database(self.test_dir, quiet=True)
        self.engine.reload_data()

        # Search by keyword
        res1 = self.engine.search_registrations(keyword="Aarav")
        self.assertGreaterEqual(len(res1), 1)
        self.assertEqual(res1[0][0].student_name, "Aarav Sharma")

        # Search by event ID
        res2 = self.engine.search_registrations(event_id="EVT-101")
        self.assertEqual(len(res2), 14)

        # Search by status
        res3 = self.engine.search_registrations(reg_status="Waitlisted")
        self.assertGreaterEqual(len(res3), 1)

    def test_threshold_warnings(self):
        seed_database(self.test_dir, quiet=True)
        self.engine.reload_data()

        warnings = self.engine.get_threshold_warnings()
        self.assertGreater(len(warnings), 0)

        codes = [w["code"] for w in warnings]
        self.assertIn("CAPACITY_FULL", codes)  # EVT-102 is 10/10 full
        self.assertIn("CAPACITY_NEARING", codes)  # EVT-101 is 14/15 full (93.3%)
        self.assertIn("DEADLINE_EXPIRED", codes)  # EVT-105 deadline in past
        self.assertIn("UNPAID_EXPIRED_DEADLINE", codes)  # Deepak Nanda unpaid for EVT-105

    def test_executive_summary_aggregation(self):
        seed_database(self.test_dir, quiet=True)
        self.engine.reload_data()

        summary = self.engine.compute_executive_summary()
        self.assertEqual(summary["total_events"], 6)
        self.assertEqual(summary["total_registrations"], 44)
        self.assertGreater(summary["overall_capacity_utilization"], 0.0)
        self.assertIn("department_counts", summary)
        self.assertIn("Computer Science", summary["department_counts"])
        self.assertGreater(summary["financials"]["total_collected"], 0.0)

    def test_bulk_csv_import_with_error_logging(self):
        seed_database(self.test_dir, quiet=True)
        self.engine.reload_data()

        legacy_csv = self.storage.data_dir / "sample_legacy_import.csv"
        self.assertTrue(legacy_csv.exists())

        res = self.engine.bulk_import_csv(legacy_csv)
        self.assertTrue(res["success"])
        self.assertEqual(res["total_rows"], 9)  # 9 non-empty data rows
        # In sample_legacy_import.csv:
        # Row 3 has bad email, Row 5 has bad event EVT-999, Row 7 has 5-digit phone, Row 9 has blank name
        # 5 valid rows should be imported, 4 skipped with errors logged
        self.assertEqual(res["imported_count"], 5)
        self.assertEqual(res["skipped_count"], 4)

        # Check that error log was written
        error_log = Path(res["error_log_path"])
        self.assertTrue(error_log.exists())
        content = error_log.read_text(encoding="utf-8")
        self.assertIn("BULK IMPORT ERROR LOG", content)
        self.assertIn("Row 3", content)
        self.assertIn("Row 5", content)
        self.assertIn("Row 7", content)
        self.assertIn("Row 9", content)

    # ==========================================
    # 5. ANALYTICS & EXPORTS TEST
    # ==========================================
    def test_exports_csv_and_markdown(self):
        seed_database(self.test_dir, quiet=True)
        self.engine.reload_data()

        exporter = ReportExporter(self.storage.exports_dir)
        summary = self.engine.compute_executive_summary()
        warnings = self.engine.get_threshold_warnings()

        # Test Markdown Export
        md_path = exporter.export_markdown_summary(summary, warnings)
        self.assertTrue(md_path.exists())
        md_text = md_path.read_text(encoding="utf-8")
        self.assertIn("# Campus Catalyst: College Event Registration Executive Summary", md_text)
        self.assertIn("Seat Utilization Rate", md_text)

        # Test Master CSV Export
        csv_path = exporter.export_attendee_list_csv(None, self.engine.registrations)
        self.assertTrue(csv_path.exists())
        csv_text = csv_path.read_text(encoding="utf-8")
        self.assertIn("Registration ID", csv_text)
        self.assertIn("Aarav Sharma", csv_text)


if __name__ == "__main__":
    unittest.main()
