"""
main.py
Main entry point, branded ASCII welcome banner, interactive menu dispatch loop,
CLI flags, and graceful exit handling for
Campus Catalyst: College Event Registration Manager (Project #8).
"""

from __future__ import annotations
import sys
import argparse
from pathlib import Path
from datetime import datetime

from models import EventCategory, PaymentStatus, AttendanceStatus, RegistrationStatus
from storage import StorageManager
from engine import RegistrationEngine
from analytics import ReportExporter, VisualPlotter, AuditLogger
from validators import (
    prompt_safe,
    validate_string,
    prompt_email,
    prompt_phone,
    prompt_roll_number,
    prompt_date,
    prompt_int,
    prompt_float,
    prompt_choice,
    prompt_year_of_study,
    UserCancelledException
)
from ui import (
    print_banner,
    print_header,
    print_status,
    print_divider,
    render_table,
    render_kpi_card,
    Colors
)
from seed_data import seed_database

# Optional GUI import
try:
    from gui import launch_gui, TKINTER_AVAILABLE
except ImportError:
    TKINTER_AVAILABLE = False
    launch_gui = None


class CollegeEventManagerCLI:
    """
    Console application driver coordinating user interactions, menu navigation,
    and workflow dispatching.
    """

    def __init__(self, base_dir: Path | str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent
        self.storage = StorageManager(self.base_dir)
        self.audit_logger = AuditLogger(self.storage.exports_dir / "audit_log.txt")
        self.engine = RegistrationEngine(self.storage, audit_logger=self.audit_logger.log)
        self.exporter = ReportExporter(self.storage.exports_dir)
        self.plotter = VisualPlotter(self.storage.charts_dir)

    def run(self) -> None:
        """Starts main interactive CLI loop."""
        print_banner()
        self.audit_logger.log("SYSTEM_START", "Campus Catalyst application initialized.")

        # If database is fresh and completely empty, offer to auto-seed
        if not self.engine.events:
            print_status("No existing event database found in storage.", "INFO")
            try:
                auto_seed = prompt_choice(
                    "Would you like to seed sample demo data (6 events, 44 participants)?",
                    ["y", "n"],
                    default="y"
                )
                if auto_seed == "y":
                    seed_database(self.base_dir, quiet=True)
                    self.engine.reload_data()
                    print_status(f"Successfully loaded {len(self.engine.events)} events and {len(self.engine.registrations)} participants.", "SUCCESS")
            except UserCancelledException:
                pass

        while True:
            try:
                self._display_main_menu()
                choice = prompt_safe(
                    f"\n{Colors.B_CYAN}{Colors.BOLD}Select an option (0-11){Colors.RESET}",
                    allow_cancel=False
                )

                if choice == "1":
                    self.view_all_events()
                elif choice == "2":
                    self.register_participant_flow()
                elif choice == "3":
                    self.search_registrations_flow()
                elif choice == "4":
                    self.update_registration_flow()
                elif choice == "5":
                    self.executive_summary_dashboard()
                elif choice == "6":
                    self.generate_visual_charts_flow()
                elif choice == "7":
                    self.view_threshold_warnings()
                elif choice == "8":
                    self.export_reports_flow()
                elif choice == "9":
                    self.bulk_csv_import_flow()
                elif choice == "10":
                    self.seed_demo_data_flow()
                elif choice == "11":
                    self.launch_gui_flow()
                elif choice in ("0", "exit", "quit", "q"):
                    self.graceful_exit()
                    break
                else:
                    print_status(f"Invalid option '{choice}'. Please enter a number between 0 and 11.", "ALERT")

            except UserCancelledException:
                print(f"\n{Colors.DIM}[Action cancelled. Returning to main menu.]{Colors.RESET}")
            except KeyboardInterrupt:
                print(f"\n\n{Colors.YELLOW}[Keyboard interrupt received. Press '0' or Enter at menu to exit cleanly.]{Colors.RESET}")
            except Exception as e:
                print_status(f"An unexpected error occurred: {e}", "CRITICAL")
                self.audit_logger.log("ERROR", str(e))

    def _display_main_menu(self) -> None:
        """Renders the formatted menu options."""
        print_header("Campus Catalyst — Main Menu", "Type option number and press Enter (or ':q' inside prompts to abort)")

        active_alerts = len(self.engine.get_threshold_warnings())
        alert_badge = f"{Colors.B_YELLOW}({active_alerts} active!){Colors.RESET}" if active_alerts > 0 else f"{Colors.GREEN}(all clear){Colors.RESET}"

        menu_items = [
            ("1", "View All Events & Capacity Status", ""),
            ("2", "Register New Participant (Defensive Flow)", ""),
            ("3", "Search & Filter Registrations", ""),
            ("4", "Update Registration / Payment / Attendance Status", ""),
            ("5", "Executive Summary & Performance Analytics", ""),
            ("6", "Generate Visual Charts (Matplotlib & ASCII)", ""),
            ("7", "Threshold Warnings & Anomaly Detector", alert_badge),
            ("8", "Export Attendee Lists & Reports (CSV / Markdown / Log)", ""),
            ("9", "Bulk Ingest Registrations from CSV (with Error Logger)", ""),
            ("10", "Seed Realistic Demo Data (Hackathon Preset)", ""),
            ("11", "Launch Visual GUI (Tkinter Window)", "(Optional Desktop View)"),
            ("0", "Exit Application", "")
        ]

        for num, text, extra in menu_items:
            num_colored = f"{Colors.B_CYAN}{num:>2}{Colors.RESET}"
            extra_colored = f" {extra}" if extra else ""
            print(f"  [{num_colored}] {text:<52}{extra_colored}")

    # ==========================================
    # MENU FLOWS
    # ==========================================

    def view_all_events(self) -> None:
        """Displays events with calculated capacity metrics."""
        print_header("College Events & Capacity Monitor")
        if not self.engine.events:
            print_status("No events found in system. Use Option 10 to seed demo data.", "INFO")
            return

        headers = ["ID", "Title", "Category", "Date", "Deadline", "Capacity", "Confirmed", "Waitlist", "Utilization", "Fee (₹)"]
        rows = []

        for e in self.engine.events:
            conf = self.engine.get_event_confirmed_count(e.event_id)
            wait = self.engine.get_event_waitlist_count(e.event_id)
            pct = (conf / e.max_capacity * 100) if e.max_capacity > 0 else 0.0

            rows.append([
                e.event_id,
                e.title,
                e.category,
                e.event_date,
                e.registration_deadline,
                e.max_capacity,
                conf,
                wait,
                f"{pct:.1f}%",
                f"{e.fee:.2f}"
            ])

        render_table(headers, rows, page_size=10)

        # Allow user to create an event directly
        print("\n Options: [C] Create New Event  |  [Enter] Return to Menu")
        try:
            sub = prompt_safe("Enter choice", default="").lower()
            if sub == "c":
                self._create_new_event_flow()
        except UserCancelledException:
            pass

    def _create_new_event_flow(self) -> None:
        """Guides user to create a new college event."""
        print_header("Create New College Event", "All fields validated with defensive boundary checks")

        title = validate_string("Enter Event Title", field_name="Event Title", min_len=3, max_len=80)

        categories = [c.value for c in EventCategory]
        print(f" Allowed Categories: {', '.join(categories)}")
        category = prompt_choice("Select Category", categories, default=EventCategory.TECHNICAL.value)

        event_date = prompt_date("Enter Event Date (YYYY-MM-DD)")
        reg_deadline = prompt_date("Enter Registration Deadline (YYYY-MM-DD)")
        max_cap = prompt_int("Enter Maximum Seat Capacity (1-5000)", field_name="Max Capacity", min_val=1, max_val=5000, default=50)
        venue = validate_string("Enter Event Venue / Room", field_name="Venue", min_len=2, max_len=100)
        fee = prompt_float("Enter Registration Fee (₹) [0 for Free]", field_name="Fee", min_val=0.0, max_val=50000.0, default=0.0)

        ok, msg, ev = self.engine.add_event(
            title=title,
            category=category,
            event_date=event_date,
            registration_deadline=reg_deadline,
            max_capacity=max_cap,
            venue=venue,
            fee=fee
        )

        if ok:
            print_status(msg, "SUCCESS")
        else:
            print_status(msg, "CRITICAL")

    def register_participant_flow(self) -> None:
        """Defensive step-by-step participant registration flow."""
        print_header("Register Participant for Event", "Defensive validation prevents duplicate roll/email and enforces capacities")

        if not self.engine.events:
            print_status("No events exist. Please create or seed an event first.", "WARNING")
            return

        # Show concise list of available events
        print(" Available Events:")
        for idx, e in enumerate(self.engine.events, 1):
            conf = self.engine.get_event_confirmed_count(e.event_id)
            print(f"  [{e.event_id}] {e.title} (Cap: {conf}/{e.max_capacity} | Deadline: {e.registration_deadline} | Fee: ₹{e.fee:.2f})")

        event_ids = [e.event_id for e in self.engine.events]
        target_eid = prompt_choice("\nEnter Event ID to register for", event_ids, default=event_ids[0]).upper()

        event = self.engine.get_event(target_eid)
        if event.is_deadline_passed():
            print_status(f"Notice: Registration deadline ({event.registration_deadline}) has passed for this event.", "WARNING")
            override = prompt_choice("Bypass deadline restriction as Administrator?", ["y", "n"], default="n")
            if override != "y":
                print_status("Registration aborted due to passed deadline.", "INFO")
                return

        student_name = validate_string("Enter Student Full Name", field_name="Student Name", min_len=2, max_len=60)
        roll_number = prompt_roll_number("Enter Student Roll Number (e.g., 22CS104)")
        email = prompt_email("Enter Campus Email Address (e.g., student@campus.edu)")
        phone = prompt_phone("Enter 10-Digit Mobile Number")

        departments = ["Computer Science", "Information Technology", "Electronics & Comm", "Electrical Engg", "Mechanical Engg", "Civil Engg", "Biotechnology", "Management Studies"]
        print(f" Common Departments: {', '.join(departments[:4])}...")
        department = validate_string("Enter Department / Branch", field_name="Department", min_len=2, max_len=40, default="Computer Science")
        year_of_study = prompt_year_of_study("Enter Year of Study (1-5)", default=3)

        notes = prompt_safe("Enter any optional notes / dietary / team details", default="")

        # Submit to business engine
        ok, msg, reg = self.engine.register_participant(
            event_id=target_eid,
            student_name=student_name,
            roll_number=roll_number,
            email=email,
            phone=phone,
            department=department,
            year_of_study=year_of_study,
            notes=notes,
            force_deadline_bypass=True
        )

        if ok:
            print_status(msg, "SUCCESS")
            print(f"  • Participant: {reg.student_name} ({reg.roll_number})")
            print(f"  • Event:       {event.title} [{event.event_id}]")
            print(f"  • Status:      {reg.registration_status} (Payment: {reg.payment_status})")
            print(f"  • Timestamp:   {reg.registration_timestamp}")
        else:
            print_status(msg, "CRITICAL")

    def search_registrations_flow(self) -> None:
        """Multi-criteria search & filter flow."""
        print_header("Search & Filter Registrations")
        print(" [Tip] Leave any filter blank to skip it.")

        kw = prompt_safe("Keyword Search (Name, Roll No, Email, Phone, Reg ID)", default="") or None
        target_eid = prompt_safe("Filter by Event ID (e.g. EVT-101)", default="") or None

        statuses = ["Confirmed", "Waitlisted", "Pending Payment", "Cancelled"]
        print(f" Filter by Status: {', '.join(statuses)}")
        rstat = prompt_safe("Enter Status filter", default="") or None

        matches = self.engine.search_registrations(
            keyword=kw,
            event_id=target_eid,
            reg_status=rstat
        )

        print(f"\n Found {len(matches)} matching registration(s):")
        if not matches:
            return

        headers = ["Reg ID", "Event", "Student Name", "Roll No", "Department", "Year", "Status", "Payment", "Phone"]
        rows = []
        for r, ev in matches:
            rows.append([
                r.registration_id,
                r.event_id,
                r.student_name,
                r.roll_number,
                r.department,
                r.year_of_study,
                r.registration_status,
                r.payment_status,
                r.phone
            ])

        render_table(headers, rows, page_size=12)

    def update_registration_flow(self) -> None:
        """Updates operational statuses or cancels registration."""
        print_header("Update Registration / Payment / Attendance")

        reg_id = prompt_safe("Enter Registration ID (e.g. REG-2026-001)").upper()
        reg = self.engine.get_registration(reg_id)
        if not reg:
            print_status(f"Registration '{reg_id}' not found.", "ALERT")
            return

        print(f"\n Found Record: {reg.student_name} ({reg.roll_number}) for Event {reg.event_id}")
        print(f"  Current Status:      {reg.registration_status}")
        print(f"  Current Payment:     {reg.payment_status}")
        print(f"  Current Attendance:  {reg.attendance_status}")
        print(f"  Notes:               {reg.notes or 'None'}")

        print("\n Modification Options:")
        print("  [1] Update Payment Status (Completed, Pending, Refunded, Exempt)")
        print("  [2] Update Attendance Status (Registered, Attended, Absent)")
        print("  [3] Cancel Registration Safely")
        print("  [4] Update Registration Status (Confirmed, Waitlisted)")
        print("  [0] Back to Menu")

        sub = prompt_safe("Select action (0-4)", default="0")
        if sub == "1":
            p_opts = [p.value for p in PaymentStatus]
            new_p = prompt_choice("Select new payment status", p_opts, default=reg.payment_status)
            ok, msg = self.engine.update_registration_status(reg_id, new_payment_status=new_p)
            print_status(msg, "SUCCESS" if ok else "ALERT")

        elif sub == "2":
            a_opts = [a.value for a in AttendanceStatus]
            new_a = prompt_choice("Select attendance status", a_opts, default=reg.attendance_status)
            ok, msg = self.engine.update_registration_status(reg_id, new_attendance_status=new_a)
            print_status(msg, "SUCCESS" if ok else "ALERT")

        elif sub == "3":
            confirm = prompt_choice(f"Are you sure you want to cancel registration {reg_id}?", ["y", "n"], default="n")
            if confirm == "y":
                reason = prompt_safe("Enter cancellation reason", default="Requested by participant")
                ok, msg = self.engine.cancel_registration(reg_id, reason=reason)
                print_status(msg, "SUCCESS" if ok else "ALERT")

        elif sub == "4":
            r_opts = [r.value for r in RegistrationStatus]
            new_r = prompt_choice("Select registration status", r_opts, default=reg.registration_status)
            ok, msg = self.engine.update_registration_status(reg_id, new_reg_status=new_r)
            print_status(msg, "SUCCESS" if ok else "ALERT")

    def executive_summary_dashboard(self) -> None:
        """Calculates and renders comprehensive KPI summary and department tables."""
        print_header("Executive Summary & Performance Analytics")

        summary = self.engine.compute_executive_summary()
        fin = summary.get("financials", {})

        print(f"{Colors.BOLD} Key Performance Indicators (KPIs):{Colors.RESET}")
        print_divider()
        col1 = f"Total Events:          {summary['total_events']}"
        col2 = f"Total Capacity:        {summary['total_capacity']}"
        col3 = f"Active Registrations:  {summary['active_registrations']}"
        col4 = f"Seat Utilization:      {summary['overall_capacity_utilization']:.1f}%"
        print(f"  {col1:<32} {col2:<32}")
        print(f"  {col3:<32} {col4:<32}")

        rev1 = f"Projected Revenue:     ₹{fin.get('total_projected', 0.0):,.2f}"
        rev2 = f"Collected Revenue:     ₹{fin.get('total_collected', 0.0):,.2f}"
        rev3 = f"Pending Revenue:       ₹{fin.get('total_pending', 0.0):,.2f}"
        print(f"  {rev1:<32} {rev2:<32}")
        print(f"  {rev3:<32}")
        print_divider()

        # Top Trending Events Table
        print(f"\n{Colors.BOLD} Top Trending Events by Attendance:{Colors.RESET}")
        top_headers = ["Event ID", "Title", "Category", "Confirmed", "Capacity", "Utilization %", "Waitlist"]
        top_rows = []
        for te in summary.get("top_events", [])[:5]:
            top_rows.append([
                te["event_id"],
                te["title"],
                te["category"],
                te["confirmed"],
                te["max_capacity"],
                f"{te['utilization_pct']:.1f}%",
                te["waitlisted"]
            ])
        render_table(top_headers, top_rows)

        # Department Participation Table
        print(f"\n{Colors.BOLD} Department Participation Breakdown:{Colors.RESET}")
        dept_counts = summary.get("department_counts", {})
        total_dept_regs = sum(dept_counts.values()) or 1
        d_headers = ["Department", "Registrations", "Share %"]
        d_rows = []
        for dept, cnt in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (cnt / total_dept_regs) * 100
            d_rows.append([dept, cnt, f"{pct:.1f}%"])
        render_table(d_headers, d_rows)

    def generate_visual_charts_flow(self) -> None:
        """Triggers Matplotlib chart generation with fallback to terminal ASCII bars."""
        print_header("Visual Data Plotting Engine", "High-resolution charts saved to exports/charts/ with fallback ASCII views")

        summary = self.engine.compute_executive_summary()
        results = self.plotter.generate_all_charts(summary, self.engine.registrations)

        if results.get("capacity_chart"):
            print_status(f"Saved Capacity Bar Chart:   {results['capacity_chart'].name}", "SUCCESS")
        if results.get("department_chart"):
            print_status(f"Saved Department Donut:     {results['department_chart'].name}", "SUCCESS")
        if results.get("timeline_chart"):
            print_status(f"Saved Timeline Trend:       {results['timeline_chart'].name}", "SUCCESS")

        print(f"\n Charts Directory: {self.storage.charts_dir.resolve()}")

        # Also display terminal ASCII charts
        view_ascii = prompt_choice("Display terminal ASCII chart view right now?", ["y", "n"], default="y")
        if view_ascii == "y":
            self.plotter.render_ascii_capacity_chart(summary)
            self.plotter.render_ascii_department_chart(summary)

    def view_threshold_warnings(self) -> None:
        """Evaluates and surfaces real-time threshold warnings and anomalies."""
        print_header("Threshold Warnings & Operational Alerts")

        warnings = self.engine.get_threshold_warnings()
        if not warnings:
            print_status("All systems operating within nominal limits. Zero active alerts.", "SUCCESS")
            return

        print_status(f"Identified {len(warnings)} active alerts requiring review:\n", "WARNING")

        for w in warnings:
            color = Colors.B_RED if w["level"] == "CRITICAL" else Colors.B_YELLOW
            icon = "[!]" if w["level"] == "CRITICAL" else "[?]"
            print(f" {color}{icon} [{w['level']}] [{w['code']}]{Colors.RESET} Event {w['event_id']} ({w['title']}):")
            print(f"     {w['message']}\n")

    def export_reports_flow(self) -> None:
        """Exports CSV attendee lists, Markdown summary, and Audit Log."""
        print_header("Export Attendee Lists & Executive Reports")

        print(" Select Export Format:")
        print("  [1] Master Attendee List CSV (All Registrations)")
        print("  [2] Specific Event Attendee List CSV")
        print("  [3] Executive Summary Report (Markdown .md)")
        print("  [4] Plain-Text Audit Log (.txt)")
        print("  [5] Export All Formats Simultaneously")
        print("  [0] Return to Menu")

        sub = prompt_safe("Choose option (0-5)", default="5")

        if sub == "1":
            p = self.exporter.export_attendee_list_csv(None, self.engine.registrations)
            print_status(f"Exported Master CSV: {p.resolve()}", "SUCCESS")

        elif sub == "2":
            if not self.engine.events:
                print_status("No events available.", "INFO")
                return
            event_ids = [e.event_id for e in self.engine.events]
            eid = prompt_choice("Select Event ID", event_ids, default=event_ids[0])
            event = self.engine.get_event(eid)
            regs = [r for r in self.engine.registrations if r.event_id == eid]
            p = self.exporter.export_attendee_list_csv(event, regs)
            print_status(f"Exported {eid} Attendee List: {p.resolve()}", "SUCCESS")

        elif sub == "3":
            summary = self.engine.compute_executive_summary()
            warnings = self.engine.get_threshold_warnings()
            p = self.exporter.export_markdown_summary(summary, warnings)
            print_status(f"Exported Executive Summary Markdown: {p.resolve()}", "SUCCESS")

        elif sub == "4":
            log_p = self.storage.exports_dir / "audit_log.txt"
            print_status(f"Audit Log Path: {log_p.resolve()} ({log_p.stat().st_size if log_p.exists() else 0} bytes)", "SUCCESS")

        elif sub == "5":
            # Master CSV
            p1 = self.exporter.export_attendee_list_csv(None, self.engine.registrations)
            # Markdown
            summary = self.engine.compute_executive_summary()
            warnings = self.engine.get_threshold_warnings()
            p2 = self.exporter.export_markdown_summary(summary, warnings)
            # Event CSVs
            for ev in self.engine.events:
                regs = [r for r in self.engine.registrations if r.event_id == ev.event_id]
                self.exporter.export_attendee_list_csv(ev, regs)

            print_status("Successfully exported Master CSV, Markdown Summary, and Event CSVs.", "SUCCESS")
            print(f" Directory: {self.storage.exports_dir.resolve()}")

    def bulk_csv_import_flow(self) -> None:
        """Imports legacy attendee CSV with row-by-row validation & error logger."""
        print_header("Bulk CSV Dataset Import", "Validates schema, checks duplicates, skips corrupt rows, and logs errors")

        default_file = self.storage.data_dir / "sample_legacy_import.csv"
        file_input = prompt_safe(f"Enter CSV file path to import", default=str(default_file))

        import_path = Path(file_input)
        if not import_path.exists():
            print_status(f"File '{import_path}' does not exist.", "ALERT")
            return

        print_status(f"Reading and validating records from {import_path.name}...", "INFO")
        res = self.engine.bulk_import_csv(import_path)

        if not res.get("success"):
            print_status(res["message"], "CRITICAL")
            return

        print_status(f"Batch Import Completed!", "SUCCESS")
        print(f"  • Total Rows Evaluated:  {res['total_rows']}")
        print(f"  • Successfully Imported: {res['imported_count']}")
        print(f"  • Skipped / Invalid:     {res['skipped_count']}")

        if res.get("errors"):
            print_status(f"Encountered {len(res['errors'])} formatting/data issues. Displaying error details:", "WARNING")
            for err in res["errors"]:
                print(f"  [Row {err['row']}] Reason(s): {', '.join(err['reasons'])}")
                print(f"    Raw: {err['data']}")

            if res.get("error_log_path"):
                print(f"\n Detailed error report written to: {res['error_log_path']}")

    def seed_demo_data_flow(self) -> None:
        """Seeds realistic sample records."""
        print_header("Seed Demo Dataset (Hackathon Ready)")
        print(" This operation resets the data stores with 6 realistic college events and 44 participant registrations.")
        confirm = prompt_choice("Are you sure you want to seed demo data?", ["y", "n"], default="y")
        if confirm == "y":
            seed_database(self.base_dir)
            self.engine.reload_data()
            print_status("Database seeded and reloaded successfully.", "SUCCESS")

    def launch_gui_flow(self) -> None:
        """Launches the optional desktop GUI."""
        print_header("Launch Visual GUI")
        if not TKINTER_AVAILABLE or launch_gui is None:
            print_status("Tkinter graphical package is not available in this Python environment.", "ALERT")
            return

        print_status("Opening Tkinter graphical window. Keep this terminal open...", "INFO")
        try:
            launch_gui(self.engine)
            print_status("GUI closed. Synchronizing updates to CLI session...", "SUCCESS")
            self.engine.reload_data()
        except Exception as e:
            print_status(f"Could not open GUI window: {e}", "CRITICAL")

    def graceful_exit(self) -> None:
        """Handles clean application exit."""
        print(f"\n{Colors.B_CYAN}Saving operational state and generating session exit audit...{Colors.RESET}")
        self.storage.save_events(self.engine.events)
        self.storage.save_registrations(self.engine.registrations)
        self.audit_logger.log("SYSTEM_SHUTDOWN", "Application terminated cleanly by user.")
        print(f"{Colors.GREEN}Data successfully saved to {self.storage.data_dir.resolve()}. Goodbye!{Colors.RESET}\n")


def parse_cli_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Campus Catalyst: College Event Registration Manager (Project #8)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--gui", action="store_true", help="Launch the lightweight Tkinter graphical desktop view directly")
    parser.add_argument("--seed", action="store_true", help="Seed the database with sample records and exit")
    parser.add_argument("--export-summary", action="store_true", help="Generate Markdown summary and CSV reports, then exit")
    parser.add_argument("--charts", action="store_true", help="Generate all Matplotlib charts and exit")
    return parser.parse_args()


def main():
    """Application entry point."""
    args = parse_cli_args()
    app = CollegeEventManagerCLI()

    if args.seed:
        seed_database()
        print("Database seeded successfully.")
        sys.exit(0)

    if args.gui:
        if TKINTER_AVAILABLE and launch_gui:
            launch_gui(app.engine)
            sys.exit(0)
        else:
            print("Tkinter is not available. Launching CLI mode instead.")

    if args.export_summary:
        summary = app.engine.compute_executive_summary()
        warnings = app.engine.get_threshold_warnings()
        app.exporter.export_markdown_summary(summary, warnings)
        app.exporter.export_attendee_list_csv(None, app.engine.registrations)
        print("Summary and attendee reports exported successfully.")
        sys.exit(0)

    if args.charts:
        summary = app.engine.compute_executive_summary()
        app.plotter.generate_all_charts(summary, app.engine.registrations)
        print("Charts generated successfully.")
        sys.exit(0)

    app.run()


if __name__ == "__main__":
    main()
