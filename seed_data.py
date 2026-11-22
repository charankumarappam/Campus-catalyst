"""
seed_data.py
Generates realistic, high-fidelity sample datasets (40+ records across 6 diverse events)
with boundary values, capacity triggers, deadline alerts, and legacy test files for
Campus Catalyst: College Event Registration Manager (Project #8).
"""

from __future__ import annotations
import csv
import json
from pathlib import Path
from datetime import datetime, timedelta

from models import Event, Registration, EventCategory, PaymentStatus, AttendanceStatus, RegistrationStatus
from storage import StorageManager


def get_sample_events() -> list[Event]:
    """Generates 6 diverse college events with distinct dates and capacity profiles."""
    today = datetime.now().date()

    return [
        Event(
            event_id="EVT-101",
            title="HackCampus 2026: AI & Cloud Hackathon",
            category=EventCategory.TECHNICAL.value,
            event_date=(today + timedelta(days=14)).strftime("%Y-%m-%d"),
            registration_deadline=(today + timedelta(days=8)).strftime("%Y-%m-%d"),
            max_capacity=15,  # 14 confirmed will reach 93.3% capacity -> triggers WARNING
            venue="Turing Main Auditorium & Innovation Hub",
            fee=250.00,
            created_at=(today - timedelta(days=10)).strftime("%Y-%m-%d 09:00:00")
        ),
        Event(
            event_id="EVT-102",
            title="National Collegiate Robotics Challenge",
            category=EventCategory.TECHNICAL.value,
            event_date=(today + timedelta(days=20)).strftime("%Y-%m-%d"),
            registration_deadline=(today + timedelta(days=12)).strftime("%Y-%m-%d"),
            max_capacity=10,  # 10 confirmed will reach 100% capacity -> triggers CRITICAL
            venue="Advanced Robotics & Mechatronics Arena",
            fee=500.00,
            created_at=(today - timedelta(days=12)).strftime("%Y-%m-%d 10:30:00")
        ),
        Event(
            event_id="EVT-103",
            title="Campus Symphony: Battle of the Bands",
            category=EventCategory.CULTURAL.value,
            event_date=(today + timedelta(days=25)).strftime("%Y-%m-%d"),
            registration_deadline=(today + timedelta(days=18)).strftime("%Y-%m-%d"),
            max_capacity=30,
            venue="University Open Air Amphitheatre",
            fee=0.00,  # Free entry
            created_at=(today - timedelta(days=8)).strftime("%Y-%m-%d 11:15:00")
        ),
        Event(
            event_id="EVT-104",
            title="Inter-Department Badminton Championship",
            category=EventCategory.SPORTS.value,
            event_date=(today + timedelta(days=5)).strftime("%Y-%m-%d"),
            registration_deadline=(today + timedelta(days=1)).strftime("%Y-%m-%d"),  # Deadline tomorrow -> triggers IMMINENT DEADLINE
            max_capacity=16,
            venue="Campus Indoor Sports Complex Court 1-3",
            fee=100.00,
            created_at=(today - timedelta(days=6)).strftime("%Y-%m-%d 14:00:00")
        ),
        Event(
            event_id="EVT-105",
            title="Cloud DevOps & Kubernetes Hands-On Workshop",
            category=EventCategory.WORKSHOP.value,
            event_date=(today - timedelta(days=2)).strftime("%Y-%m-%d"),
            registration_deadline=(today - timedelta(days=5)).strftime("%Y-%m-%d"),  # Deadline passed -> triggers EXPIRED DEADLINE & ANOMALIES
            max_capacity=20,
            venue="Systems Lab 304, Computing Block",
            fee=150.00,
            created_at=(today - timedelta(days=20)).strftime("%Y-%m-%d 08:45:00")
        ),
        Event(
            event_id="EVT-106",
            title="Venture Spark: Startup Pitch Deck Summit",
            category=EventCategory.SEMINAR.value,
            event_date=(today + timedelta(days=30)).strftime("%Y-%m-%d"),
            registration_deadline=(today + timedelta(days=22)).strftime("%Y-%m-%d"),
            max_capacity=40,
            venue="Management Studies Executive Hall",
            fee=0.00,
            created_at=(today - timedelta(days=5)).strftime("%Y-%m-%d 16:20:00")
        )
    ]


def get_sample_registrations() -> list[Registration]:
    """
    Generates 44 realistic participant registrations across 6 departments,
    covering normal cases, capacity thresholds, waitlist, cancellations, and overdue payments.
    """
    regs = [
        # --- EVT-101: Hackathon (14 registrations, Cap: 15 -> 93.3% utilization [WARNING]) ---
        Registration("REG-2026-001", "EVT-101", "Aarav Sharma", "21CS101", "aarav.sharma@campus.edu", "9876543210", "Computer Science", 4, "2026-11-15 10:12:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Team Leader - NeuralByte"),
        Registration("REG-2026-002", "EVT-101", "Diya Patel", "21CS104", "diya.patel@campus.edu", "9876543211", "Computer Science", 4, "2026-11-15 10:15:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Frontend Dev"),
        Registration("REG-2026-003", "EVT-101", "Rohan Verma", "22IT045", "rohan.verma@campus.edu", "9876543212", "Information Technology", 3, "2026-11-15 11:00:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Cloud Architect"),
        Registration("REG-2026-004", "EVT-101", "Sneha Iyer", "22EC018", "sneha.iyer@campus.edu", "9876543213", "Electronics & Comm", 3, "2026-11-15 11:30:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Edge Computing"),
        Registration("REG-2026-005", "EVT-101", "Vikram Singh", "23CS202", "vikram.singh@campus.edu", "9876543214", "Computer Science", 2, "2026-11-16 09:20:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "ML Pipeline"),
        Registration("REG-2026-006", "EVT-101", "Ananya Reddy", "23AI012", "ananya.reddy@campus.edu", "9876543215", "Artificial Intelligence", 2, "2026-11-16 10:05:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "NLP Researcher"),
        Registration("REG-2026-007", "EVT-101", "Karthik Nair", "21ME089", "karthik.nair@campus.edu", "9876543216", "Mechanical Engg", 4, "2026-11-16 14:15:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Hardware Prototyping"),
        Registration("REG-2026-008", "EVT-101", "Pooja Desai", "22EE034", "pooja.desai@campus.edu", "9876543217", "Electrical Engg", 3, "2026-11-17 12:40:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "IoT Sensors"),
        Registration("REG-2026-009", "EVT-101", "Aditya Joshi", "24CS005", "aditya.joshi@campus.edu", "9876543218", "Computer Science", 1, "2026-11-17 16:30:00", PaymentStatus.PENDING.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Student discount coupon applied"),
        Registration("REG-2026-010", "EVT-101", "Meera Kulkarni", "22BT014", "meera.k@campus.edu", "9876543219", "Biotechnology", 3, "2026-11-18 10:20:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Bioinformatics project"),
        Registration("REG-2026-011", "EVT-101", "Tanmay Sen", "21CS115", "tanmay.sen@campus.edu", "9876543220", "Computer Science", 4, "2026-11-18 13:00:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "DevSecOps"),
        Registration("REG-2026-012", "EVT-101", "Neha Bansal", "23EC088", "neha.bansal@campus.edu", "9876543221", "Electronics & Comm", 2, "2026-11-18 15:45:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Embedded systems"),
        Registration("REG-2026-013", "EVT-101", "Rahul Gupta", "22CE033", "rahul.gupta@campus.edu", "9876543222", "Civil Engg", 3, "2026-11-19 11:10:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Smart City GIS"),
        Registration("REG-2026-014", "EVT-101", "Ishita Bose", "24AI022", "ishita.bose@campus.edu", "9876543223", "Artificial Intelligence", 1, "2026-11-19 14:50:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Computer Vision"),

        # --- EVT-102: Robotics Championship (10 registrations, Cap: 10 -> 100% full [CRITICAL] + 1 Waitlisted) ---
        Registration("REG-2026-015", "EVT-102", "Arjun Kapoor", "21ME001", "arjun.k@campus.edu", "9876543224", "Mechanical Engg", 4, "2026-11-12 09:30:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Bot Driver"),
        Registration("REG-2026-016", "EVT-102", "Siddharth Rao", "21ME012", "siddharth.r@campus.edu", "9876543225", "Mechanical Engg", 4, "2026-11-12 10:15:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Kinematics design"),
        Registration("REG-2026-017", "EVT-102", "Kavya Nambiar", "22EC055", "kavya.n@campus.edu", "9876543226", "Electronics & Comm", 3, "2026-11-12 11:00:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Circuit board fabrication"),
        Registration("REG-2026-018", "EVT-102", "Rishi Mukherjee", "22EE021", "rishi.m@campus.edu", "9876543227", "Electrical Engg", 3, "2026-11-13 14:00:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Battery management"),
        Registration("REG-2026-019", "EVT-102", "Gaurav Mehta", "23CS078", "gaurav.m@campus.edu", "9876543228", "Computer Science", 2, "2026-11-13 15:30:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "ROS2 Control"),
        Registration("REG-2026-020", "EVT-102", "Priyanka Soni", "23ME044", "priyanka.s@campus.edu", "9876543229", "Mechanical Engg", 2, "2026-11-14 09:10:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Pneumatics"),
        Registration("REG-2026-021", "EVT-102", "Nikhil Chawla", "21EC090", "nikhil.c@campus.edu", "9876543230", "Electronics & Comm", 4, "2026-11-14 11:45:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "RF Telemetry"),
        Registration("REG-2026-022", "EVT-102", "Sanya Taneja", "22CS130", "sanya.t@campus.edu", "9876543231", "Computer Science", 3, "2026-11-14 16:20:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Autonomous Navigation"),
        Registration("REG-2026-023", "EVT-102", "Harsh Vardhan", "24ME010", "harsh.v@campus.edu", "9876543232", "Mechanical Engg", 1, "2026-11-15 08:30:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Chassis assembly"),
        Registration("REG-2026-024", "EVT-102", "Shreya Das", "23EE019", "shreya.d@campus.edu", "9876543233", "Electrical Engg", 2, "2026-11-15 13:40:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Motor drivers (10th seat)"),
        Registration("REG-2026-025", "EVT-102", "Ayush Saxena", "24CS089", "ayush.s@campus.edu", "9876543234", "Computer Science", 1, "2026-11-15 17:00:00", PaymentStatus.PENDING.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.WAITLISTED.value, "Waitlist #1 - Full capacity reached"),

        # --- EVT-103: Battle of the Bands (Cultural - Free entry, 6 registrations) ---
        Registration("REG-2026-026", "EVT-103", "Kabir Khanna", "22BT002", "kabir.k@campus.edu", "9876543235", "Biotechnology", 3, "2026-11-16 12:00:00", PaymentStatus.EXEMPT.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Lead Vocalist - The Resonance"),
        Registration("REG-2026-027", "EVT-103", "Rhea Sengupta", "23CS111", "rhea.s@campus.edu", "9876543236", "Computer Science", 2, "2026-11-16 12:30:00", PaymentStatus.EXEMPT.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Bass Guitarist"),
        Registration("REG-2026-028", "EVT-103", "Devendra Chauhan", "21ME077", "dev.c@campus.edu", "9876543237", "Mechanical Engg", 4, "2026-11-17 14:15:00", PaymentStatus.EXEMPT.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Drummer"),
        Registration("REG-2026-029", "EVT-103", "Simran Gill", "24MBA01", "simran.g@campus.edu", "9876543238", "Management Studies", 1, "2026-11-17 15:45:00", PaymentStatus.EXEMPT.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Keyboard & Synthesizer"),
        Registration("REG-2026-030", "EVT-103", "Varun Chopra", "22EC066", "varun.c@campus.edu", "9876543239", "Electronics & Comm", 3, "2026-11-18 09:20:00", PaymentStatus.EXEMPT.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Lead Electric Guitar"),
        Registration("REG-2026-031", "EVT-103", "Akash Pillai", "21CE015", "akash.p@campus.edu", "9876543240", "Civil Engg", 4, "2026-11-18 10:10:00", PaymentStatus.EXEMPT.value, AttendanceStatus.CANCELLED.value, RegistrationStatus.CANCELLED.value, "Cancelled: Conflict with end-sem lab exam"),

        # --- EVT-104: Badminton Tournament (Sports, Deadline tomorrow, 5 registrations) ---
        Registration("REG-2026-032", "EVT-104", "Manish Pandey", "22ME050", "manish.p@campus.edu", "9876543241", "Mechanical Engg", 3, "2026-11-18 11:30:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Men's Singles"),
        Registration("REG-2026-033", "EVT-104", "Tanvi Bhat", "23CS019", "tanvi.b@campus.edu", "9876543242", "Computer Science", 2, "2026-11-18 14:20:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Women's Singles"),
        Registration("REG-2026-034", "EVT-104", "Yashwant Rao", "21EE088", "yashwant.r@campus.edu", "9876543243", "Electrical Engg", 4, "2026-11-19 16:00:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Men's Doubles Team A"),
        Registration("REG-2026-035", "EVT-104", "Zoya Farooqui", "24BT011", "zoya.f@campus.edu", "9876543244", "Biotechnology", 1, "2026-11-20 09:40:00", PaymentStatus.COMPLETED.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Mixed Doubles"),
        Registration("REG-2026-036", "EVT-104", "Pranav Anand", "22CS082", "pranav.a@campus.edu", "9876543245", "Computer Science", 3, "2026-11-20 15:10:00", PaymentStatus.PENDING.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Payment via UPI pending verification"),

        # --- EVT-105: Cloud DevOps Workshop (Past deadline, contains 1 overdue unpaid anomaly) ---
        Registration("REG-2026-037", "EVT-105", "Bhavna Trivedi", "21IT023", "bhavna.t@campus.edu", "9876543246", "Information Technology", 4, "2026-11-10 10:00:00", PaymentStatus.COMPLETED.value, AttendanceStatus.ATTENDED.value, RegistrationStatus.CONFIRMED.value, "Completed lab exercises"),
        Registration("REG-2026-038", "EVT-105", "Chetan Bhagat", "22CS144", "chetan.b@campus.edu", "9876543247", "Computer Science", 3, "2026-11-11 11:30:00", PaymentStatus.COMPLETED.value, AttendanceStatus.ATTENDED.value, RegistrationStatus.CONFIRMED.value, "Docker container certified"),
        Registration("REG-2026-039", "EVT-105", "Deepak Nanda", "23EC011", "deepak.n@campus.edu", "9876543248", "Electronics & Comm", 2, "2026-11-12 14:00:00", PaymentStatus.PENDING.value, AttendanceStatus.ABSENT.value, RegistrationStatus.CONFIRMED.value, "ANOMALY: Past deadline with pending payment"),

        # --- EVT-106: Venture Spark Startup Summit (Seminar, Free, 5 registrations) ---
        Registration("REG-2026-040", "EVT-106", "Esha Malhotra", "23MBA12", "esha.m@campus.edu", "9876543249", "Management Studies", 2, "2026-11-19 10:15:00", PaymentStatus.EXEMPT.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Pitching EdTech venture"),
        Registration("REG-2026-041", "EVT-106", "Farhan Akhtar", "22CS190", "farhan.a@campus.edu", "9876543250", "Computer Science", 3, "2026-11-19 11:30:00", PaymentStatus.EXEMPT.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "AI SaaS pitch"),
        Registration("REG-2026-042", "EVT-106", "Gita Radhakrishnan", "21EE040", "gita.r@campus.edu", "9876543251", "Electrical Engg", 4, "2026-11-20 13:20:00", PaymentStatus.EXEMPT.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "CleanTech battery storage"),
        Registration("REG-2026-043", "EVT-106", "Himanshu Tiwari", "24MBA20", "himanshu.t@campus.edu", "9876543252", "Management Studies", 1, "2026-11-20 14:45:00", PaymentStatus.EXEMPT.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "FinTech micro-loans"),
        Registration("REG-2026-044", "EVT-106", "Ira Trivedi", "22BT029", "ira.t@campus.edu", "9876543253", "Biotechnology", 3, "2026-11-21 16:00:00", PaymentStatus.EXEMPT.value, AttendanceStatus.REGISTERED.value, RegistrationStatus.CONFIRMED.value, "Bio-fertilizer AgriTech")
    ]
    return regs


def create_sample_legacy_csv(output_path: Path) -> Path:
    """
    Creates a sample legacy CSV file containing 10 records, with 4 intentional errors
    to test and demonstrate the Bulk CSV Import row-by-row error logger:
    - Row 3: Invalid email ('tarun.at.campus.com' - missing @)
    - Row 5: Non-existent event ID ('EVT-999')
    - Row 7: Invalid phone number ('12345' - only 5 digits)
    - Row 9: Blank student name
    """
    rows = [
        ["event_id", "student_name", "roll_number", "email", "phone", "department", "year_of_study", "payment_status", "notes"],
        ["EVT-103", "Kunal Goswami", "22CS210", "kunal.g@campus.edu", "9876543260", "Computer Science", "3", "Completed", "Valid entry"],
        ["EVT-106", "Tarun Roy", "23EE099", "tarun.at.campus.com", "9876543261", "Electrical Engg", "2", "Completed", "ERROR: Invalid email format"],
        ["EVT-104", "Pallavi Joshi", "24EC050", "pallavi.j@campus.edu", "9876543262", "Electronics & Comm", "1", "Completed", "Valid entry"],
        ["EVT-999", "Madhav Dixit", "21ME102", "madhav.d@campus.edu", "9876543263", "Mechanical Engg", "4", "Completed", "ERROR: Event EVT-999 does not exist"],
        ["EVT-106", "Suresh Menon", "22CE044", "suresh.m@campus.edu", "9876543264", "Civil Engg", "3", "Completed", "Valid entry"],
        ["EVT-103", "Anita Deshmukh", "23BT015", "anita.d@campus.edu", "12345", "Biotechnology", "2", "Completed", "ERROR: Phone number is only 5 digits"],
        ["EVT-104", "Vipin Rawat", "21CS301", "vipin.r@campus.edu", "9876543265", "Computer Science", "4", "Completed", "Valid entry"],
        ["EVT-106", "", "22IT077", "nameless@campus.edu", "9876543266", "Information Technology", "3", "Completed", "ERROR: Missing student name"],
        ["EVT-103", "Lata Mangesh", "24CS014", "lata.m@campus.edu", "9876543267", "Computer Science", "1", "Completed", "Valid entry"]
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    return output_path


def seed_database(base_dir: Path | str = None, quiet: bool = False) -> None:
    """
    Writes sample events and participant registrations into storage files.
    Also creates sample backup datasets (sample_data.json / sample_data.csv)
    and the legacy test CSV file for import error logging demonstration.
    """
    storage = StorageManager(base_dir)
    events = get_sample_events()
    regs = get_sample_registrations()

    # Save to primary operational stores
    storage.save_events(events)
    storage.save_registrations(regs)

    # Save mirror sample copies in data/
    sample_json_path = storage.data_dir / "sample_data.json"
    sample_csv_path = storage.data_dir / "sample_data.csv"
    legacy_csv_path = storage.data_dir / "sample_legacy_import.csv"

    combined_data = {
        "metadata": {
            "title": "Campus Catalyst Sample Dataset",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "events_count": len(events),
            "registrations_count": len(regs)
        },
        "events": [e.to_dict() for e in events],
        "registrations": [r.to_dict() for r in regs]
    }

    with open(sample_json_path, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=2)

    # Save sample master registrations CSV
    with open(sample_csv_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "registration_id", "event_id", "student_name", "roll_number",
            "email", "phone", "department", "year_of_study",
            "registration_timestamp", "payment_status", "attendance_status",
            "registration_status", "notes"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in regs:
            writer.writerow(r.to_dict())

    create_sample_legacy_csv(legacy_csv_path)

    if not quiet:
        print(f" [SUCCESS] Seeded {len(events)} events and {len(regs)} registrations.")
        print(f"  • Primary Storage:  {storage.data_dir.resolve()}")
        print(f"  • Sample JSON:      {sample_json_path.name}")
        print(f"  • Sample CSV:       {sample_csv_path.name}")
        print(f"  • Legacy Test CSV:  {legacy_csv_path.name} (with 4 intentional error rows)")


if __name__ == "__main__":
    seed_database()
