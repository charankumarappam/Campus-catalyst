"""
models.py
Foundational data structures and domain enumerations for
Campus Catalyst: College Event Registration Manager (Project #8).
"""

from __future__ import annotations
from dataclasses import dataclass, asdict, field
from datetime import datetime, date
from enum import Enum
from typing import Dict, Any, Optional


class EventCategory(str, Enum):
    TECHNICAL = "Technical"
    CULTURAL = "Cultural"
    SPORTS = "Sports"
    WORKSHOP = "Workshop"
    SEMINAR = "Seminar"
    OTHER = "Other"

    @classmethod
    def from_str(cls, value: str) -> EventCategory:
        for item in cls:
            if item.value.lower() == value.strip().lower():
                return item
        return cls.OTHER


class PaymentStatus(str, Enum):
    COMPLETED = "Completed"
    PENDING = "Pending"
    EXEMPT = "Exempt"
    REFUNDED = "Refunded"

    @classmethod
    def from_str(cls, value: str) -> PaymentStatus:
        for item in cls:
            if item.value.lower() == value.strip().lower():
                return item
        return cls.PENDING


class AttendanceStatus(str, Enum):
    REGISTERED = "Registered"
    ATTENDED = "Attended"
    ABSENT = "Absent"
    CANCELLED = "Cancelled"

    @classmethod
    def from_str(cls, value: str) -> AttendanceStatus:
        for item in cls:
            if item.value.lower() == value.strip().lower():
                return item
        return cls.REGISTERED


class RegistrationStatus(str, Enum):
    CONFIRMED = "Confirmed"
    WAITLISTED = "Waitlisted"
    PENDING_PAYMENT = "Pending Payment"
    CANCELLED = "Cancelled"

    @classmethod
    def from_str(cls, value: str) -> RegistrationStatus:
        for item in cls:
            if item.value.lower() == value.strip().lower():
                return item
        return cls.CONFIRMED


@dataclass
class Event:
    event_id: str
    title: str
    category: str
    event_date: str  # YYYY-MM-DD
    registration_deadline: str  # YYYY-MM-DD
    max_capacity: int
    venue: str
    fee: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def get_deadline_date(self) -> Optional[date]:
        try:
            return datetime.strptime(self.registration_deadline, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def get_event_date(self) -> Optional[date]:
        try:
            return datetime.strptime(self.event_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def is_registration_open(self, reference_date: Optional[date] = None) -> bool:
        d = self.get_deadline_date()
        if not d:
            return True
        ref = reference_date or date.today()
        return ref <= d

    def days_until_deadline(self, reference_date: Optional[date] = None) -> int:
        d = self.get_deadline_date()
        if not d:
            return 999
        ref = reference_date or date.today()
        return (d - ref).days

    def is_deadline_passed(self, reference_date: Optional[date] = None) -> bool:
        return self.days_until_deadline(reference_date) < 0

    def is_deadline_imminent(self, days: int = 2, reference_date: Optional[date] = None) -> bool:
        diff = self.days_until_deadline(reference_date)
        return 0 <= diff <= days

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Event:
        return cls(
            event_id=str(data.get("event_id", "")).strip().upper(),
            title=str(data.get("title", "")).strip(),
            category=str(data.get("category", EventCategory.OTHER.value)).strip(),
            event_date=str(data.get("event_date", "")).strip(),
            registration_deadline=str(data.get("registration_deadline", "")).strip(),
            max_capacity=int(data.get("max_capacity", 0)),
            venue=str(data.get("venue", "")).strip(),
            fee=float(data.get("fee", 0.0)),
            created_at=str(data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        )


@dataclass
class Registration:
    registration_id: str
    event_id: str
    student_name: str
    roll_number: str
    email: str
    phone: str
    department: str
    year_of_study: int
    registration_timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    payment_status: str = PaymentStatus.COMPLETED.value
    attendance_status: str = AttendanceStatus.REGISTERED.value
    registration_status: str = RegistrationStatus.CONFIRMED.value
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Registration:
        return cls(
            registration_id=str(data.get("registration_id", "")).strip().upper(),
            event_id=str(data.get("event_id", "")).strip().upper(),
            student_name=str(data.get("student_name", "")).strip(),
            roll_number=str(data.get("roll_number", "")).strip().upper(),
            email=str(data.get("email", "")).strip().lower(),
            phone=str(data.get("phone", "")).strip(),
            department=str(data.get("department", "")).strip(),
            year_of_study=int(data.get("year_of_study", 1)),
            registration_timestamp=str(data.get("registration_timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
            payment_status=str(data.get("payment_status", PaymentStatus.COMPLETED.value)).strip(),
            attendance_status=str(data.get("attendance_status", AttendanceStatus.REGISTERED.value)).strip(),
            registration_status=str(data.get("registration_status", RegistrationStatus.CONFIRMED.value)).strip(),
            notes=str(data.get("notes", "")).strip()
        )
