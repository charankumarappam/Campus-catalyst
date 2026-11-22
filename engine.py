"""
engine.py
Core business logic, computation algorithms, threshold warning checks,
search/filtering engine, and executive aggregation for
Campus Catalyst: College Event Registration Manager (Project #8).
"""

from __future__ import annotations
import csv
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from models import Event, Registration, RegistrationStatus, PaymentStatus, AttendanceStatus, EventCategory
from storage import StorageManager
from validators import validate_registration_row, clean_phone


class RegistrationEngine:
    """
    Central business engine governing all operational workflows, business rules,
    validation checks, and analytics aggregations.
    """

    def __init__(self, storage: StorageManager = None, audit_logger=None):
        self.storage = storage or StorageManager()
        self.audit_logger = audit_logger
        self.events: List[Event] = []
        self.registrations: List[Registration] = []
        self.reload_data()

    def reload_data(self) -> None:
        """Reloads in-memory data structures from persistent storage."""
        self.events = self.storage.load_events()
        self.registrations = self.storage.load_registrations()

    def log_audit(self, action: str, details: str) -> None:
        """Records action in persistent audit log."""
        if self.audit_logger:
            self.audit_logger(action, details)

    # ==========================================
    # EVENT MANAGEMENT
    # ==========================================

    def generate_next_event_id(self) -> str:
        """Generates sequential ID like EVT-101, EVT-102."""
        max_num = 100
        for e in self.events:
            if e.event_id.startswith("EVT-"):
                try:
                    num = int(e.event_id.split("-")[1])
                    if num > max_num:
                        max_num = num
                except (IndexError, ValueError):
                    pass
        return f"EVT-{max_num + 1}"

    def get_event(self, event_id: str) -> Optional[Event]:
        """Finds event by ID (case-insensitive)."""
        eid = event_id.strip().upper()
        for e in self.events:
            if e.event_id == eid:
                return e
        return None

    def add_event(
        self,
        title: str,
        category: str,
        event_date: str,
        registration_deadline: str,
        max_capacity: int,
        venue: str,
        fee: float = 0.0,
        custom_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Event]]:
        """
        Creates and persists a new event after verifying rules.
        """
        event_id = custom_id.strip().upper() if custom_id else self.generate_next_event_id()

        if self.get_event(event_id):
            return False, f"Event with ID '{event_id}' already exists.", None

        new_event = Event(
            event_id=event_id,
            title=title.strip(),
            category=category.strip(),
            event_date=event_date.strip(),
            registration_deadline=registration_deadline.strip(),
            max_capacity=max_capacity,
            venue=venue.strip(),
            fee=fee
        )

        self.events.append(new_event)
        self.storage.save_events(self.events)
        self.log_audit("CREATE_EVENT", f"Created event {event_id}: {title} (Cap: {max_capacity}, Fee: {fee})")
        return True, f"Event '{title}' [{event_id}] created successfully.", new_event

    def get_event_registration_count(self, event_id: str, include_cancelled: bool = False) -> int:
        """Counts registrations for an event (excluding cancelled by default)."""
        eid = event_id.strip().upper()
        count = 0
        for r in self.registrations:
            if r.event_id == eid:
                if not include_cancelled and r.registration_status == RegistrationStatus.CANCELLED.value:
                    continue
                count += 1
        return count

    def get_event_confirmed_count(self, event_id: str) -> int:
        """Counts only Confirmed registrations."""
        eid = event_id.strip().upper()
        return sum(1 for r in self.registrations if r.event_id == eid and r.registration_status == RegistrationStatus.CONFIRMED.value)

    def get_event_waitlist_count(self, event_id: str) -> int:
        """Counts Waitlisted registrations."""
        eid = event_id.strip().upper()
        return sum(1 for r in self.registrations if r.event_id == eid and r.registration_status == RegistrationStatus.WAITLISTED.value)

    # ==========================================
    # REGISTRATION MANAGEMENT
    # ==========================================

    def generate_next_registration_id(self) -> str:
        """Generates sequential ID like REG-2026-001."""
        year = datetime.now().year
        prefix = f"REG-{year}-"
        max_seq = 0
        for r in self.registrations:
            if r.registration_id.startswith(prefix):
                try:
                    seq = int(r.registration_id.split("-")[2])
                    if seq > max_seq:
                        max_seq = seq
                except (IndexError, ValueError):
                    pass
        return f"{prefix}{max_seq + 1:03d}"

    def get_registration(self, reg_id: str) -> Optional[Registration]:
        """Finds registration by ID."""
        rid = reg_id.strip().upper()
        for r in self.registrations:
            if r.registration_id == rid:
                return r
        return None

    def check_duplicate_registration(self, event_id: str, roll_number: str, email: str) -> Tuple[bool, str]:
        """
        Verifies if roll number or email is already registered for this event.
        Ignores previously cancelled registrations.
        """
        eid = event_id.strip().upper()
        roll = roll_number.strip().upper()
        em = email.strip().lower()

        for r in self.registrations:
            if r.event_id == eid and r.registration_status != RegistrationStatus.CANCELLED.value:
                if r.roll_number == roll:
                    return True, f"Student with roll number '{roll}' is already registered for event {eid} (Reg ID: {r.registration_id})."
                if r.email.lower() == em:
                    return True, f"Email '{em}' is already registered for event {eid} (Reg ID: {r.registration_id})."

        return False, ""

    def register_participant(
        self,
        event_id: str,
        student_name: str,
        roll_number: str,
        email: str,
        phone: str,
        department: str,
        year_of_study: int,
        payment_status: Optional[str] = None,
        notes: str = "",
        allow_waitlist: bool = True,
        force_deadline_bypass: bool = False
    ) -> Tuple[bool, str, Optional[Registration]]:
        """
        Enforces business rules before registering participant:
        1. Event exists.
        2. Deadline check (unless bypassed by admin).
        3. Duplicate check (roll number & email).
        4. Capacity check (places into Waitlist if full and allowed, or rejects).
        """
        event = self.get_event(event_id)
        if not event:
            return False, f"Event with ID '{event_id}' does not exist.", None

        # Deadline enforcement
        if event.is_deadline_passed() and not force_deadline_bypass:
            return False, f"Registration closed for '{event.title}'. Deadline was {event.registration_deadline}.", None

        # Duplicate check
        is_dup, dup_msg = self.check_duplicate_registration(event_id, roll_number, email)
        if is_dup:
            return False, dup_msg, None

        # Capacity enforcement
        confirmed_count = self.get_event_confirmed_count(event_id)
        reg_status = RegistrationStatus.CONFIRMED.value
        msg_suffix = "Registration confirmed."

        if confirmed_count >= event.max_capacity:
            if allow_waitlist:
                reg_status = RegistrationStatus.WAITLISTED.value
                msg_suffix = f"Event is at full capacity ({event.max_capacity}). Added to WAITLIST."
            else:
                return False, f"Event '{event.title}' is sold out ({event.max_capacity}/{event.max_capacity} capacity).", None

        # Fee & Payment defaults
        if payment_status is None:
            payment_status = PaymentStatus.EXEMPT.value if event.fee == 0.0 else PaymentStatus.PENDING.value

        cleaned_phone_num = clean_phone(phone)
        reg_id = self.generate_next_registration_id()

        new_reg = Registration(
            registration_id=reg_id,
            event_id=event.event_id,
            student_name=student_name.strip(),
            roll_number=roll_number.strip().upper(),
            email=email.strip().lower(),
            phone=cleaned_phone_num,
            department=department.strip(),
            year_of_study=year_of_study,
            registration_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            payment_status=payment_status,
            attendance_status=AttendanceStatus.REGISTERED.value,
            registration_status=reg_status,
            notes=notes.strip()
        )

        self.registrations.append(new_reg)
        self.storage.save_registrations(self.registrations)
        self.log_audit(
            "REGISTER_STUDENT",
            f"Registered {student_name} ({roll_number}) for {event.event_id} - ID: {reg_id} ({reg_status})"
        )

        return True, f"Success! {msg_suffix} [Reg ID: {reg_id}]", new_reg

    def update_registration_status(
        self,
        registration_id: str,
        new_reg_status: Optional[str] = None,
        new_payment_status: Optional[str] = None,
        new_attendance_status: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Updates operational statuses for an existing registration."""
        reg = self.get_registration(registration_id)
        if not reg:
            return False, f"Registration with ID '{registration_id}' not found."

        changes = []
        if new_reg_status and new_reg_status != reg.registration_status:
            changes.append(f"RegStatus: {reg.registration_status} -> {new_reg_status}")
            reg.registration_status = new_reg_status

        if new_payment_status and new_payment_status != reg.payment_status:
            changes.append(f"Payment: {reg.payment_status} -> {new_payment_status}")
            reg.payment_status = new_payment_status

        if new_attendance_status and new_attendance_status != reg.attendance_status:
            changes.append(f"Attendance: {reg.attendance_status} -> {new_attendance_status}")
            reg.attendance_status = new_attendance_status

        if notes is not None:
            reg.notes = notes.strip()
            changes.append("Notes updated")

        if not changes:
            return True, "No status modifications requested."

        self.storage.save_registrations(self.registrations)
        self.log_audit("UPDATE_STATUS", f"Updated {registration_id}: {'; '.join(changes)}")
        return True, f"Updated {registration_id} successfully: {', '.join(changes)}"

    def cancel_registration(self, registration_id: str, reason: str = "User requested cancellation") -> Tuple[bool, str]:
        """Safely marks a registration as CANCELLED."""
        reg = self.get_registration(registration_id)
        if not reg:
            return False, f"Registration with ID '{registration_id}' not found."

        if reg.registration_status == RegistrationStatus.CANCELLED.value:
            return False, f"Registration '{registration_id}' is already cancelled."

        reg.registration_status = RegistrationStatus.CANCELLED.value
        reg.attendance_status = AttendanceStatus.CANCELLED.value
        reg.notes = f"{reg.notes} | CANCELLED: {reason}".strip(" |")

        self.storage.save_registrations(self.registrations)
        self.log_audit("CANCEL_REGISTRATION", f"Cancelled {registration_id} (Reason: {reason})")
        return True, f"Registration '{registration_id}' has been cancelled."

    # ==========================================
    # SEARCH & QUERY
    # ==========================================

    def search_registrations(
        self,
        keyword: Optional[str] = None,
        event_id: Optional[str] = None,
        category: Optional[str] = None,
        department: Optional[str] = None,
        reg_status: Optional[str] = None,
        payment_status: Optional[str] = None,
        attendance_status: Optional[str] = None
    ) -> List[Tuple[Registration, Optional[Event]]]:
        """
        Multi-criteria search & filtering across registrations and associated events.
        """
        results: List[Tuple[Registration, Optional[Event]]] = []
        kw = keyword.strip().lower() if keyword else None
        target_eid = event_id.strip().upper() if event_id else None
        target_cat = category.strip().lower() if category else None
        target_dept = department.strip().lower() if department else None
        target_rstat = reg_status.strip().lower() if reg_status else None
        target_pstat = payment_status.strip().lower() if payment_status else None
        target_astat = attendance_status.strip().lower() if attendance_status else None

        # Build quick event lookup map
        event_map = {e.event_id: e for e in self.events}

        for r in self.registrations:
            ev = event_map.get(r.event_id)

            if target_eid and r.event_id != target_eid:
                continue

            if target_cat:
                if not ev or ev.category.lower() != target_cat:
                    continue

            if target_dept and r.department.lower() != target_dept:
                continue

            if target_rstat and r.registration_status.lower() != target_rstat:
                continue

            if target_pstat and r.payment_status.lower() != target_pstat:
                continue

            if target_astat and r.attendance_status.lower() != target_astat:
                continue

            if kw:
                text_corpus = f"{r.registration_id} {r.student_name} {r.roll_number} {r.email} {r.phone} {r.department} {r.notes}".lower()
                if ev:
                    text_corpus += f" {ev.title} {ev.venue} {ev.category}".lower()
                if kw not in text_corpus:
                    continue

            results.append((r, ev))

        return results

    # ==========================================
    # THRESHOLD WARNING ENGINE
    # ==========================================

    def get_threshold_warnings(self, reference_date: Optional[date] = None) -> List[Dict[str, str]]:
        """
        Evaluates system thresholds and detects anomalies:
        - Critical: Events at 100% capacity
        - Warning: Events nearing capacity (>= 85%)
        - Critical: Overdue registration deadlines
        - Warning: Approaching deadlines (within 48 hours)
        - Warning/Anomaly: Pending payment past deadline
        """
        warnings: List[Dict[str, str]] = []
        ref = reference_date or date.today()

        for event in self.events:
            confirmed = self.get_event_confirmed_count(event.event_id)
            cap = event.max_capacity
            pct = (confirmed / cap * 100) if cap > 0 else 0

            # Capacity checks
            if confirmed >= cap:
                warnings.append({
                    "level": "CRITICAL",
                    "code": "CAPACITY_FULL",
                    "event_id": event.event_id,
                    "title": event.title,
                    "message": f"Event '{event.title}' is at 100% capacity ({confirmed}/{cap} seats full)."
                })
            elif pct >= 85.0:
                warnings.append({
                    "level": "WARNING",
                    "code": "CAPACITY_NEARING",
                    "event_id": event.event_id,
                    "title": event.title,
                    "message": f"Event '{event.title}' nearing capacity at {pct:.1f}% ({confirmed}/{cap} seats occupied)."
                })

            # Deadline checks
            days_left = event.days_until_deadline(ref)
            if days_left < 0:
                warnings.append({
                    "level": "CRITICAL",
                    "code": "DEADLINE_EXPIRED",
                    "event_id": event.event_id,
                    "title": event.title,
                    "message": f"Registration deadline passed on {event.registration_deadline} ({abs(days_left)} day(s) ago)."
                })
            elif days_left <= 2:
                time_str = "today" if days_left == 0 else ("tomorrow" if days_left == 1 else f"in {days_left} days")
                warnings.append({
                    "level": "WARNING",
                    "code": "DEADLINE_IMMINENT",
                    "event_id": event.event_id,
                    "title": event.title,
                    "message": f"Registration deadline closes {time_str} ({event.registration_deadline})."
                })

        # Anomaly checks across participant registrations
        for r in self.registrations:
            ev = self.get_event(r.event_id)
            if not ev:
                warnings.append({
                    "level": "CRITICAL",
                    "code": "ORPHANED_REGISTRATION",
                    "event_id": r.event_id,
                    "title": "Unknown Event",
                    "message": f"Registration {r.registration_id} refers to non-existent event '{r.event_id}'."
                })
                continue

            # Pending payment past deadline
            if (
                ev.is_deadline_passed(ref)
                and r.payment_status == PaymentStatus.PENDING.value
                and r.registration_status != RegistrationStatus.CANCELLED.value
                and ev.fee > 0
            ):
                warnings.append({
                    "level": "WARNING",
                    "code": "UNPAID_EXPIRED_DEADLINE",
                    "event_id": ev.event_id,
                    "title": ev.title,
                    "message": f"Participant {r.student_name} ({r.roll_number}) has unpaid fee of ₹{ev.fee:.2f} past deadline."
                })

        return warnings

    # ==========================================
    # EXECUTIVE SUMMARY AGGREGATION
    # ==========================================

    def compute_executive_summary(self) -> Dict[str, Any]:
        """
        Computes high-level KPIs, capacity statistics, department metrics,
        revenue analysis, and trend rankings.
        """
        total_events = len(self.events)
        total_registrations = len(self.registrations)

        status_counts: Dict[str, int] = {}
        for r in self.registrations:
            status_counts[r.registration_status] = status_counts.get(r.registration_status, 0) + 1

        active_count = sum(1 for r in self.registrations if r.registration_status != RegistrationStatus.CANCELLED.value)
        cancelled_count = status_counts.get(RegistrationStatus.CANCELLED.value, 0)
        waitlisted_count = status_counts.get(RegistrationStatus.WAITLISTED.value, 0)

        # Capacity metrics
        total_capacity = sum(e.max_capacity for e in self.events)
        total_confirmed = sum(self.get_event_confirmed_count(e.event_id) for e in self.events)
        utilization_rate = (total_confirmed / total_capacity * 100) if total_capacity > 0 else 0.0
        avg_regs_per_event = (active_count / total_events) if total_events > 0 else 0.0

        # Financial metrics
        total_projected_revenue = 0.0
        total_collected_revenue = 0.0
        total_pending_revenue = 0.0

        event_map = {e.event_id: e for e in self.events}
        for r in self.registrations:
            if r.registration_status == RegistrationStatus.CANCELLED.value:
                continue
            ev = event_map.get(r.event_id)
            if not ev:
                continue
            fee = ev.fee
            total_projected_revenue += fee
            if r.payment_status == PaymentStatus.COMPLETED.value:
                total_collected_revenue += fee
            elif r.payment_status == PaymentStatus.PENDING.value:
                total_pending_revenue += fee

        # Department distribution
        dept_counts: Dict[str, int] = {}
        for r in self.registrations:
            if r.registration_status != RegistrationStatus.CANCELLED.value:
                dept_counts[r.department] = dept_counts.get(r.department, 0) + 1

        # Year of study distribution
        year_counts: Dict[int, int] = {}
        for r in self.registrations:
            if r.registration_status != RegistrationStatus.CANCELLED.value:
                year_counts[r.year_of_study] = year_counts.get(r.year_of_study, 0) + 1

        # Category distribution
        cat_counts: Dict[str, int] = {}
        for e in self.events:
            cnt = self.get_event_registration_count(e.event_id)
            cat_counts[e.category] = cat_counts.get(e.category, 0) + cnt

        # Event breakdown list
        event_breakdown = []
        for e in self.events:
            conf = self.get_event_confirmed_count(e.event_id)
            wait = self.get_event_waitlist_count(e.event_id)
            total_reg = self.get_event_registration_count(e.event_id, include_cancelled=True)
            u_pct = (conf / e.max_capacity * 100) if e.max_capacity > 0 else 0.0
            event_breakdown.append({
                "event_id": e.event_id,
                "title": e.title,
                "category": e.category,
                "max_capacity": e.max_capacity,
                "confirmed": conf,
                "waitlisted": wait,
                "total_registrations": total_reg,
                "utilization_pct": u_pct,
                "venue": e.venue,
                "fee": e.fee,
                "deadline": e.registration_deadline
            })

        # Sort top trending events by confirmed registrations descending
        top_events = sorted(event_breakdown, key=lambda x: x["confirmed"], reverse=True)

        return {
            "total_events": total_events,
            "total_registrations": total_registrations,
            "active_registrations": active_count,
            "cancelled_registrations": cancelled_count,
            "waitlisted_registrations": waitlisted_count,
            "total_capacity": total_capacity,
            "total_confirmed_seats": total_confirmed,
            "overall_capacity_utilization": utilization_rate,
            "avg_registrations_per_event": avg_regs_per_event,
            "financials": {
                "total_projected": total_projected_revenue,
                "total_collected": total_collected_revenue,
                "total_pending": total_pending_revenue
            },
            "status_counts": status_counts,
            "department_counts": dept_counts,
            "year_counts": year_counts,
            "category_counts": cat_counts,
            "event_breakdown": event_breakdown,
            "top_events": top_events
        }

    # ==========================================
    # BULK CSV IMPORT WITH ERROR LOGGING
    # ==========================================

    def bulk_import_csv(self, file_path: Path | str) -> Dict[str, Any]:
        """
        Ingests a CSV dataset of participant registrations with schema/format validation,
        skips invalid rows without crashing, and generates exports/import_errors.log.
        """
        p = Path(file_path)
        if not p.exists():
            return {
                "success": False,
                "message": f"File '{p}' does not exist.",
                "total_rows": 0,
                "imported_count": 0,
                "skipped_count": 0,
                "errors": []
            }

        imported_count = 0
        skipped_count = 0
        error_records: List[Dict[str, Any]] = []

        # Standard header aliases mapping
        header_map = {
            "event_id": "event_id",
            "event": "event_id",
            "eventid": "event_id",
            "student_name": "student_name",
            "name": "student_name",
            "roll_number": "roll_number",
            "roll": "roll_number",
            "roll_no": "roll_number",
            "email": "email",
            "student_email": "email",
            "phone": "phone",
            "phone_number": "phone",
            "mobile": "phone",
            "department": "department",
            "dept": "department",
            "year_of_study": "year_of_study",
            "year": "year_of_study",
            "payment_status": "payment_status",
            "payment": "payment_status",
            "notes": "notes"
        }

        try:
            with open(p, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                try:
                    headers = next(reader)
                except StopIteration:
                    return {
                        "success": False,
                        "message": "CSV file is empty.",
                        "total_rows": 0,
                        "imported_count": 0,
                        "skipped_count": 0,
                        "errors": []
                    }

                # Normalize headers
                clean_headers = [header_map.get(h.strip().lower().replace(" ", "_"), h.strip().lower()) for h in headers]

                total_rows = 0
                for row_idx, row in enumerate(reader, start=2):
                    if not row or all(not cell.strip() for cell in row):
                        continue
                    total_rows += 1

                    row_dict = {}
                    for col_idx, col_name in enumerate(clean_headers):
                        if col_idx < len(row):
                            row_dict[col_name] = row[col_idx].strip()
                        else:
                            row_dict[col_name] = ""

                    # Validate row structure
                    is_valid, validation_errors = validate_registration_row(row_dict)

                    if not is_valid:
                        skipped_count += 1
                        error_records.append({
                            "row": row_idx,
                            "data": row_dict,
                            "reasons": validation_errors
                        })
                        continue

                    # Business rule validation: event existence
                    event_id = row_dict["event_id"].upper()
                    event = self.get_event(event_id)
                    if not event:
                        skipped_count += 1
                        error_records.append({
                            "row": row_idx,
                            "data": row_dict,
                            "reasons": [f"Referenced Event ID '{event_id}' does not exist in system"]
                        })
                        continue

                    # Duplicate check
                    is_dup, dup_msg = self.check_duplicate_registration(
                        event_id, row_dict["roll_number"], row_dict["email"]
                    )
                    if is_dup:
                        skipped_count += 1
                        error_records.append({
                            "row": row_idx,
                            "data": row_dict,
                            "reasons": [dup_msg]
                        })
                        continue

                    # Perform registration
                    pay_status = row_dict.get("payment_status") or (PaymentStatus.EXEMPT.value if event.fee == 0 else PaymentStatus.PENDING.value)
                    year_val = int(row_dict.get("year_of_study", 1))

                    ok, reg_msg, reg_obj = self.register_participant(
                        event_id=event_id,
                        student_name=row_dict["student_name"],
                        roll_number=row_dict["roll_number"],
                        email=row_dict["email"],
                        phone=row_dict["phone"],
                        department=row_dict["department"],
                        year_of_study=year_val,
                        payment_status=pay_status,
                        notes=row_dict.get("notes", "Imported via bulk CSV"),
                        allow_waitlist=True,
                        force_deadline_bypass=True  # Batch historic imports can bypass deadlines
                    )

                    if ok:
                        imported_count += 1
                    else:
                        skipped_count += 1
                        error_records.append({
                            "row": row_idx,
                            "data": row_dict,
                            "reasons": [reg_msg]
                        })

        except Exception as e:
            return {
                "success": False,
                "message": f"CSV reading error: {e}",
                "total_rows": 0,
                "imported_count": 0,
                "skipped_count": 0,
                "errors": []
            }

        # Write error log if any errors occurred
        error_log_path = self.storage.exports_dir / "import_errors.log"
        if error_records:
            try:
                with open(error_log_path, "w", encoding="utf-8") as elf:
                    elf.write(f"=== BULK IMPORT ERROR LOG ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===\n")
                    elf.write(f"Source File: {p.resolve()}\n")
                    elf.write(f"Total Rows: {total_rows} | Successfully Imported: {imported_count} | Skipped: {skipped_count}\n\n")
                    for err in error_records:
                        elf.write(f"[Row {err['row']}] Reasons: {', '.join(err['reasons'])}\n")
                        elf.write(f"  Raw Data: {err['data']}\n\n")
            except Exception as le:
                print(f" [WARNING] Could not write error log: {le}")

        self.log_audit("BULK_IMPORT", f"Imported {imported_count} records from {p.name} (Skipped: {skipped_count})")

        return {
            "success": True,
            "message": f"Import completed: {imported_count} imported, {skipped_count} skipped.",
            "total_rows": total_rows,
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "error_log_path": str(error_log_path) if error_records else None,
            "errors": error_records
        }
