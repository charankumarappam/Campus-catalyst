"""
gui.py
Optional lightweight Tkinter graphical interface for visual menu navigation,
table browsing, capacity monitoring, and quick exports for
Campus Catalyst: College Event Registration Manager (Project #8).
"""

from __future__ import annotations
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

from engine import RegistrationEngine
from storage import StorageManager
from analytics import ReportExporter, VisualPlotter
from models import EventCategory, RegistrationStatus, PaymentStatus, AttendanceStatus


class CollegeEventManagerGUI:
    """
    Tkinter desktop view providing visual monitoring, interactive search,
    registration forms, threshold warning badges, and instant export buttons.
    """

    def __init__(self, root: tk.Tk, engine: RegistrationEngine):
        self.root = root
        self.engine = engine
        self.storage = engine.storage
        self.exporter = ReportExporter(self.storage.exports_dir)
        self.plotter = VisualPlotter(self.storage.charts_dir)

        self.root.title("Campus Catalyst - College Event Registration Manager")
        self.root.geometry("1150x720")
        self.root.minsize(900, 600)

        # Apply modern ttk theme styling
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self._configure_styles()
        self._build_header()
        self._build_tabs()
        self._build_statusbar()

        self.refresh_all_views()

    def _configure_styles(self) -> None:
        """Configures ttk styles for a modern, clean look."""
        self.style.configure(".", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#0f2b48")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 10), foreground="#555555")
        self.style.configure("CardTitle.TLabel", font=("Segoe UI", 10, "bold"), foreground="#1a365d")
        self.style.configure("CardValue.TLabel", font=("Segoe UI", 18, "bold"), foreground="#2b6cb0")
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.configure("Treeview", rowheight=26, font=("Segoe UI", 9))
        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"))

    def _build_header(self) -> None:
        """Creates branded title header."""
        header_frame = ttk.Frame(self.root, padding="15 10 15 10")
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(
            header_frame,
            text="🎓 Campus Catalyst: College Event Registration Manager",
            style="Header.TLabel"
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = ttk.Label(
            header_frame,
            text="Project #8 | Domain: Education & Student Life | Real-Time Sync & Analytics",
            style="SubHeader.TLabel"
        )
        subtitle_lbl.pack(anchor=tk.W)

    def _build_tabs(self) -> None:
        """Builds tabbed workspace."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        # Tab 1: Events Overview
        self.tab_events = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_events, text="📅 Events & Capacity")
        self._setup_events_tab()

        # Tab 2: Registrations Management
        self.tab_registrations = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_registrations, text="👥 Participant Registrations")
        self._setup_registrations_tab()

        # Tab 3: Executive Summary & KPIs
        self.tab_kpis = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_kpis, text="📊 Executive Summary")
        self._setup_kpi_tab()

        # Tab 4: Threshold Alerts & Anomalies
        self.tab_warnings = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_warnings, text="⚠️ Threshold Alerts")
        self._setup_warnings_tab()

        # Tab 5: Bulk CSV Import
        self.tab_import = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_import, text="📥 Bulk CSV Import")
        self._setup_import_tab()

    def _build_statusbar(self) -> None:
        """Builds bottom status and quick reload bar."""
        bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding="6 4")
        bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_var = tk.StringVar(value="System Ready. Dual JSON/CSV persistence active.")
        status_lbl = ttk.Label(bar, textvariable=self.status_var, font=("Segoe UI", 9))
        status_lbl.pack(side=tk.LEFT)

        reload_btn = ttk.Button(bar, text="🔄 Reload Data", command=self.refresh_all_views)
        reload_btn.pack(side=tk.RIGHT, padx=5)

    # ----------------------------------------------------
    # TAB 1: EVENTS OVERVIEW
    # ----------------------------------------------------
    def _setup_events_tab(self) -> None:
        btn_bar = ttk.Frame(self.tab_events)
        btn_bar.pack(fill=tk.X, pady=(0, 10))

        add_btn = ttk.Button(btn_bar, text="➕ Create New Event", command=self._dialog_create_event)
        add_btn.pack(side=tk.LEFT, padx=5)

        export_btn = ttk.Button(btn_bar, text="📄 Export Selected Event CSV", command=self._export_event_attendees)
        export_btn.pack(side=tk.LEFT, padx=5)

        # Treeview for Events
        cols = ("id", "title", "category", "capacity", "confirmed", "waitlist", "utilization", "fee", "deadline", "venue")
        self.events_tree = ttk.Treeview(self.tab_events, columns=cols, show="headings", selectmode="browse")

        headings = {
            "id": ("Event ID", 80),
            "title": ("Event Title", 220),
            "category": ("Category", 100),
            "capacity": ("Capacity", 75),
            "confirmed": ("Confirmed", 80),
            "waitlist": ("Waitlist", 70),
            "utilization": ("Utilization", 85),
            "fee": ("Fee (₹)", 75),
            "deadline": ("Deadline", 95),
            "venue": ("Venue", 180)
        }

        for c, (txt, w) in headings.items():
            self.events_tree.heading(c, text=txt)
            self.events_tree.column(c, width=w, anchor=tk.CENTER if c in ("id", "capacity", "confirmed", "waitlist", "utilization", "fee", "deadline") else tk.W)

        scroll = ttk.Scrollbar(self.tab_events, orient=tk.VERTICAL, command=self.events_tree.yview)
        self.events_tree.configure(yscrollcommand=scroll.set)

        self.events_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # ----------------------------------------------------
    # TAB 2: PARTICIPANT REGISTRATIONS
    # ----------------------------------------------------
    def _setup_registrations_tab(self) -> None:
        filter_bar = ttk.Frame(self.tab_registrations)
        filter_bar.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(filter_bar, text="Search:").pack(side=tk.LEFT, padx=(0, 4))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_bar, textvariable=self.search_var, width=22)
        search_entry.pack(side=tk.LEFT, padx=4)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_registrations())

        ttk.Label(filter_bar, text="Event:").pack(side=tk.LEFT, padx=(10, 4))
        self.event_filter_var = tk.StringVar(value="All")
        self.event_combo = ttk.Combobox(filter_bar, textvariable=self.event_filter_var, state="readonly", width=14)
        self.event_combo.pack(side=tk.LEFT, padx=4)
        self.event_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_registrations())

        ttk.Label(filter_bar, text="Status:").pack(side=tk.LEFT, padx=(10, 4))
        self.status_filter_var = tk.StringVar(value="All")
        self.status_combo = ttk.Combobox(
            filter_bar,
            textvariable=self.status_filter_var,
            values=["All", "Confirmed", "Waitlisted", "Pending Payment", "Cancelled"],
            state="readonly",
            width=14
        )
        self.status_combo.pack(side=tk.LEFT, padx=4)
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_registrations())

        clear_btn = ttk.Button(filter_bar, text="Reset", command=self._reset_filters)
        clear_btn.pack(side=tk.LEFT, padx=8)

        # Action buttons
        act_bar = ttk.Frame(self.tab_registrations)
        act_bar.pack(fill=tk.X, pady=(0, 8))

        reg_btn = ttk.Button(act_bar, text="➕ Register Participant", command=self._dialog_register_participant)
        reg_btn.pack(side=tk.LEFT, padx=4)

        upd_btn = ttk.Button(act_bar, text="✏️ Update Status", command=self._dialog_update_status)
        upd_btn.pack(side=tk.LEFT, padx=4)

        del_btn = ttk.Button(act_bar, text="❌ Cancel Registration", command=self._cancel_selected_registration)
        del_btn.pack(side=tk.LEFT, padx=4)

        exp_all_btn = ttk.Button(act_bar, text="📄 Export Master Attendees CSV", command=self._export_master_csv)
        exp_all_btn.pack(side=tk.RIGHT, padx=4)

        # Registrations Treeview
        r_cols = ("reg_id", "event_id", "student_name", "roll_no", "dept", "year", "email", "phone", "reg_status", "payment")
        self.reg_tree = ttk.Treeview(self.tab_registrations, columns=r_cols, show="headings", selectmode="browse")

        r_headings = {
            "reg_id": ("Reg ID", 110),
            "event_id": ("Event", 80),
            "student_name": ("Student Name", 160),
            "roll_no": ("Roll No", 95),
            "dept": ("Department", 140),
            "year": ("Year", 55),
            "email": ("Email", 170),
            "phone": ("Phone", 100),
            "reg_status": ("Status", 95),
            "payment": ("Payment", 85)
        }

        for c, (txt, w) in r_headings.items():
            self.reg_tree.heading(c, text=txt)
            self.reg_tree.column(c, width=w, anchor=tk.CENTER if c in ("reg_id", "event_id", "roll_no", "year", "reg_status", "payment") else tk.W)

        r_scroll = ttk.Scrollbar(self.tab_registrations, orient=tk.VERTICAL, command=self.reg_tree.yview)
        self.reg_tree.configure(yscrollcommand=r_scroll.set)

        self.reg_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        r_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # ----------------------------------------------------
    # TAB 3: EXECUTIVE SUMMARY & KPIS
    # ----------------------------------------------------
    def _setup_kpi_tab(self) -> None:
        cards_frame = ttk.Frame(self.tab_kpis)
        cards_frame.pack(fill=tk.X, pady=10)

        self.card_events_val = tk.StringVar(value="0")
        self.card_regs_val = tk.StringVar(value="0")
        self.card_util_val = tk.StringVar(value="0.0%")
        self.card_rev_val = tk.StringVar(value="₹0.00")

        self._create_card(cards_frame, "Total Events", self.card_events_val, 0)
        self._create_card(cards_frame, "Total Registrations", self.card_regs_val, 1)
        self._create_card(cards_frame, "Capacity Utilization", self.card_util_val, 2)
        self._create_card(cards_frame, "Collected Revenue", self.card_rev_val, 3)

        # Action Buttons for Analytics & Reports
        action_frame = ttk.LabelFrame(self.tab_kpis, text="Analytics & Exporters", padding=10)
        action_frame.pack(fill=tk.X, pady=10)

        chart_btn = ttk.Button(action_frame, text="📈 Generate Visual Charts (Matplotlib)", command=self._generate_charts_gui)
        chart_btn.pack(side=tk.LEFT, padx=8)

        md_btn = ttk.Button(action_frame, text="📝 Export Markdown Executive Report", command=self._export_markdown_gui)
        md_btn.pack(side=tk.LEFT, padx=8)

        audit_btn = ttk.Button(action_frame, text="🔍 Open Audit Trail Log", command=self._open_audit_log)
        audit_btn.pack(side=tk.LEFT, padx=8)

        open_folder_btn = ttk.Button(action_frame, text="📂 Open Exports Folder", command=self._open_exports_folder)
        open_folder_btn.pack(side=tk.RIGHT, padx=8)

        # Department share table
        detail_frame = ttk.Frame(self.tab_kpis)
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        dept_lbl = ttk.Label(detail_frame, text="Department Participation Breakdown:", font=("Segoe UI", 11, "bold"))
        dept_lbl.pack(anchor=tk.W, pady=(0, 5))

        d_cols = ("dept", "count", "pct")
        self.dept_tree = ttk.Treeview(detail_frame, columns=d_cols, show="headings", height=8)
        self.dept_tree.heading("dept", text="Department")
        self.dept_tree.heading("count", text="Participant Count")
        self.dept_tree.heading("pct", text="Share (%)")
        self.dept_tree.column("dept", width=250)
        self.dept_tree.column("count", width=120, anchor=tk.CENTER)
        self.dept_tree.column("pct", width=120, anchor=tk.CENTER)
        self.dept_tree.pack(fill=tk.BOTH, expand=True)

    def _create_card(self, parent: ttk.Frame, title: str, str_var: tk.StringVar, col: int) -> None:
        card = ttk.Frame(parent, relief=tk.RIDGE, padding=12)
        card.grid(row=0, column=col, padx=8, sticky="nsew")
        parent.columnconfigure(col, weight=1)

        t_lbl = ttk.Label(card, text=title, style="CardTitle.TLabel")
        t_lbl.pack(anchor=tk.W)

        v_lbl = ttk.Label(card, textvariable=str_var, style="CardValue.TLabel")
        v_lbl.pack(anchor=tk.W, pady=(4, 0))

    # ----------------------------------------------------
    # TAB 4: THRESHOLD WARNINGS
    # ----------------------------------------------------
    def _setup_warnings_tab(self) -> None:
        top_lbl = ttk.Label(
            self.tab_warnings,
            text="Active Threshold Alerts & Anomaly Monitor (Capacity Breaches, Overdue Deadlines, Unpaid Records):",
            font=("Segoe UI", 10, "bold")
        )
        top_lbl.pack(anchor=tk.W, pady=(0, 8))

        w_cols = ("level", "code", "event_id", "title", "message")
        self.warn_tree = ttk.Treeview(self.tab_warnings, columns=w_cols, show="headings", selectmode="browse")

        self.warn_tree.heading("level", text="Severity")
        self.warn_tree.heading("code", text="Alert Code")
        self.warn_tree.heading("event_id", text="Event ID")
        self.warn_tree.heading("title", text="Event Title")
        self.warn_tree.heading("message", text="Details")

        self.warn_tree.column("level", width=90, anchor=tk.CENTER)
        self.warn_tree.column("code", width=160)
        self.warn_tree.column("event_id", width=80, anchor=tk.CENTER)
        self.warn_tree.column("title", width=180)
        self.warn_tree.column("message", width=420)

        w_scroll = ttk.Scrollbar(self.tab_warnings, orient=tk.VERTICAL, command=self.warn_tree.yview)
        self.warn_tree.configure(yscrollcommand=w_scroll.set)

        self.warn_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        w_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # ----------------------------------------------------
    # TAB 5: BULK CSV IMPORT
    # ----------------------------------------------------
    def _setup_import_tab(self) -> None:
        info_frame = ttk.Frame(self.tab_import)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            info_frame,
            text="Ingest legacy or external attendee CSV files with row-by-row validation & automated error logging:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W)

        file_row = ttk.Frame(self.tab_import)
        file_row.pack(fill=tk.X, pady=8)

        self.import_path_var = tk.StringVar(value=str(self.storage.data_dir / "sample_legacy_import.csv"))
        ttk.Entry(file_row, textvariable=self.import_path_var, width=60).pack(side=tk.LEFT, padx=(0, 8))

        browse_btn = ttk.Button(file_row, text="Browse...", command=self._browse_import_file)
        browse_btn.pack(side=tk.LEFT, padx=4)

        run_btn = ttk.Button(file_row, text="🚀 Run Batch Import", command=self._execute_import)
        run_btn.pack(side=tk.LEFT, padx=4)

        # Import logs / results text area
        self.import_log_text = tk.Text(self.tab_import, height=18, font=("Consolas", 10), wrap=tk.WORD)
        self.import_log_text.pack(fill=tk.BOTH, expand=True, pady=10)

    # ----------------------------------------------------
    # DATA REFRESH LOGIC
    # ----------------------------------------------------
    def refresh_all_views(self) -> None:
        """Reloads engine data and updates all UI tabs."""
        self.engine.reload_data()

        # Update Events Tab
        self.events_tree.delete(*self.events_tree.get_children())
        event_ids = ["All"]
        for e in self.engine.events:
            event_ids.append(e.event_id)
            conf = self.engine.get_event_confirmed_count(e.event_id)
            wait = self.engine.get_event_waitlist_count(e.event_id)
            pct = (conf / e.max_capacity * 100) if e.max_capacity > 0 else 0.0
            self.events_tree.insert(
                "",
                tk.END,
                values=(
                    e.event_id,
                    e.title,
                    e.category,
                    e.max_capacity,
                    conf,
                    wait,
                    f"{pct:.1f}%",
                    f"{e.fee:.2f}",
                    e.registration_deadline,
                    e.venue
                )
            )

        self.event_combo["values"] = event_ids
        self.filter_registrations()

        # Update KPIs Tab
        summary = self.engine.compute_executive_summary()
        fin = summary.get("financials", {})
        self.card_events_val.set(str(summary.get("total_events", 0)))
        self.card_regs_val.set(f"{summary.get('active_registrations', 0)} / {summary.get('total_registrations', 0)}")
        self.card_util_val.set(f"{summary.get('overall_capacity_utilization', 0.0):.1f}%")
        self.card_rev_val.set(f"₹{fin.get('total_collected', 0.0):,.2f}")

        self.dept_tree.delete(*self.dept_tree.get_children())
        dept_counts = summary.get("department_counts", {})
        total_d = sum(dept_counts.values()) or 1
        for dept, cnt in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (cnt / total_d) * 100
            self.dept_tree.insert("", tk.END, values=(dept, cnt, f"{pct:.1f}%"))

        # Update Warnings Tab
        self.warn_tree.delete(*self.warn_tree.get_children())
        warnings = self.engine.get_threshold_warnings()
        for w in warnings:
            self.warn_tree.insert("", tk.END, values=(w["level"], w["code"], w["event_id"], w["title"], w["message"]))

        self.status_var.set(f"Synced {len(self.engine.events)} events, {len(self.engine.registrations)} registrations. Active alerts: {len(warnings)}")

    def filter_registrations(self) -> None:
        """Filters registrations treeview based on input widgets."""
        kw = self.search_var.get().strip() or None
        target_eid = self.event_filter_var.get()
        if target_eid == "All":
            target_eid = None
        target_status = self.status_filter_var.get()
        if target_status == "All":
            target_status = None

        matches = self.engine.search_registrations(keyword=kw, event_id=target_eid, reg_status=target_status)

        self.reg_tree.delete(*self.reg_tree.get_children())
        for r, ev in matches:
            self.reg_tree.insert(
                "",
                tk.END,
                values=(
                    r.registration_id,
                    r.event_id,
                    r.student_name,
                    r.roll_number,
                    r.department,
                    f"Yr {r.year_of_study}",
                    r.email,
                    r.phone,
                    r.registration_status,
                    r.payment_status
                )
            )

    def _reset_filters(self) -> None:
        self.search_var.set("")
        self.event_filter_var.set("All")
        self.status_filter_var.set("All")
        self.filter_registrations()

    # ----------------------------------------------------
    # DIALOGS & ACTIONS
    # ----------------------------------------------------
    def _dialog_create_event(self) -> None:
        top = tk.Toplevel(self.root)
        top.title("Create New College Event")
        top.geometry("450x420")
        top.transient(self.root)
        top.grab_set()

        fields = [
            ("Title:", tk.StringVar()),
            ("Category:", tk.StringVar(value="Technical")),
            ("Event Date (YYYY-MM-DD):", tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))),
            ("Deadline (YYYY-MM-DD):", tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))),
            ("Max Capacity:", tk.StringVar(value="30")),
            ("Venue:", tk.StringVar()),
            ("Entry Fee (₹):", tk.StringVar(value="0.0"))
        ]

        for idx, (label_txt, var) in enumerate(fields):
            ttk.Label(top, text=label_txt).grid(row=idx, column=0, padx=12, pady=6, sticky=tk.W)
            if label_txt.startswith("Category"):
                cb = ttk.Combobox(top, textvariable=var, values=[c.value for c in EventCategory], state="readonly", width=25)
                cb.grid(row=idx, column=1, padx=12, pady=6)
            else:
                ttk.Entry(top, textvariable=var, width=28).grid(row=idx, column=1, padx=12, pady=6)

        def save():
            title = fields[0][1].get().strip()
            cat = fields[1][1].get().strip()
            edate = fields[2][1].get().strip()
            dline = fields[3][1].get().strip()
            cap_str = fields[4][1].get().strip()
            venue = fields[5][1].get().strip()
            fee_str = fields[6][1].get().strip()

            if not title or not venue:
                messagebox.showerror("Error", "Title and Venue cannot be blank.", parent=top)
                return

            try:
                cap = int(cap_str)
                if cap <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Error", "Capacity must be a positive integer.", parent=top)
                return

            try:
                fee = float(fee_str)
                if fee < 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Error", "Fee must be a non-negative number.", parent=top)
                return

            ok, msg, ev = self.engine.add_event(title, cat, edate, dline, cap, venue, fee)
            if ok:
                messagebox.showinfo("Success", msg, parent=top)
                top.destroy()
                self.refresh_all_views()
            else:
                messagebox.showerror("Error", msg, parent=top)

        ttk.Button(top, text="Create Event", command=save, style="Action.TButton").grid(row=len(fields), column=1, pady=15, sticky=tk.E, padx=12)

    def _dialog_register_participant(self) -> None:
        if not self.engine.events:
            messagebox.showwarning("Warning", "Please create at least one event before registering participants.")
            return

        top = tk.Toplevel(self.root)
        top.title("Register Participant for Event")
        top.geometry("480x480")
        top.transient(self.root)
        top.grab_set()

        event_titles = [f"{e.event_id} - {e.title}" for e in self.engine.events]

        f_event = tk.StringVar(value=event_titles[0])
        f_name = tk.StringVar()
        f_roll = tk.StringVar()
        f_email = tk.StringVar()
        f_phone = tk.StringVar()
        f_dept = tk.StringVar(value="Computer Science")
        f_year = tk.StringVar(value="3")

        entries = [
            ("Target Event:", f_event),
            ("Student Full Name:", f_name),
            ("Roll Number:", f_roll),
            ("Campus Email:", f_email),
            ("10-Digit Phone:", f_phone),
            ("Department:", f_dept),
            ("Year of Study (1-5):", f_year)
        ]

        for idx, (label_txt, var) in enumerate(entries):
            ttk.Label(top, text=label_txt).grid(row=idx, column=0, padx=12, pady=6, sticky=tk.W)
            if label_txt.startswith("Target Event"):
                cb = ttk.Combobox(top, textvariable=var, values=event_titles, state="readonly", width=28)
                cb.grid(row=idx, column=1, padx=12, pady=6)
            elif label_txt.startswith("Department"):
                cb = ttk.Combobox(
                    top, textvariable=var,
                    values=["Computer Science", "Information Technology", "Electronics & Comm", "Electrical Engg", "Mechanical Engg", "Civil Engg", "Biotechnology", "Management Studies"],
                    state="readonly", width=28
                )
                cb.grid(row=idx, column=1, padx=12, pady=6)
            elif label_txt.startswith("Year"):
                cb = ttk.Combobox(top, textvariable=var, values=["1", "2", "3", "4", "5"], state="readonly", width=28)
                cb.grid(row=idx, column=1, padx=12, pady=6)
            else:
                ttk.Entry(top, textvariable=var, width=30).grid(row=idx, column=1, padx=12, pady=6)

        def submit():
            raw_event = f_event.get()
            target_eid = raw_event.split(" - ")[0].strip()
            name = f_name.get().strip()
            roll = f_roll.get().strip().upper()
            email = f_email.get().strip()
            phone = f_phone.get().strip()
            dept = f_dept.get().strip()

            try:
                year = int(f_year.get())
            except ValueError:
                year = 1

            if not name or not roll or not email or not phone:
                messagebox.showerror("Validation Error", "All fields are required.", parent=top)
                return

            ok, msg, reg = self.engine.register_participant(
                event_id=target_eid,
                student_name=name,
                roll_number=roll,
                email=email,
                phone=phone,
                department=dept,
                year_of_study=year
            )

            if ok:
                messagebox.showinfo("Registration Successful", msg, parent=top)
                top.destroy()
                self.refresh_all_views()
            else:
                messagebox.showerror("Registration Failed", msg, parent=top)

        ttk.Button(top, text="Register Participant", command=submit, style="Action.TButton").grid(row=len(entries), column=1, pady=15, sticky=tk.E, padx=12)

    def _dialog_update_status(self) -> None:
        sel = self.reg_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Please select a registration from the table to update.")
            return

        item = self.reg_tree.item(sel[0])
        reg_id = item["values"][0]
        reg = self.engine.get_registration(reg_id)
        if not reg:
            return

        top = tk.Toplevel(self.root)
        top.title(f"Update Status: {reg.registration_id}")
        top.geometry("380x260")
        top.transient(self.root)
        top.grab_set()

        r_var = tk.StringVar(value=reg.registration_status)
        p_var = tk.StringVar(value=reg.payment_status)
        a_var = tk.StringVar(value=reg.attendance_status)

        ttk.Label(top, text="Registration Status:").grid(row=0, column=0, padx=12, pady=8, sticky=tk.W)
        ttk.Combobox(top, textvariable=r_var, values=[s.value for s in RegistrationStatus], state="readonly").grid(row=0, column=1, padx=12, pady=8)

        ttk.Label(top, text="Payment Status:").grid(row=1, column=0, padx=12, pady=8, sticky=tk.W)
        ttk.Combobox(top, textvariable=p_var, values=[s.value for s in PaymentStatus], state="readonly").grid(row=1, column=1, padx=12, pady=8)

        ttk.Label(top, text="Attendance Status:").grid(row=2, column=0, padx=12, pady=8, sticky=tk.W)
        ttk.Combobox(top, textvariable=a_var, values=[s.value for s in AttendanceStatus], state="readonly").grid(row=2, column=1, padx=12, pady=8)

        def save():
            ok, msg = self.engine.update_registration_status(
                reg_id,
                new_reg_status=r_var.get(),
                new_payment_status=p_var.get(),
                new_attendance_status=a_var.get()
            )
            if ok:
                messagebox.showinfo("Success", msg, parent=top)
                top.destroy()
                self.refresh_all_views()
            else:
                messagebox.showerror("Error", msg, parent=top)

        ttk.Button(top, text="Save Status", command=save).grid(row=3, column=1, pady=15, sticky=tk.E, padx=12)

    def _cancel_selected_registration(self) -> None:
        sel = self.reg_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Please select a registration from the table to cancel.")
            return

        item = self.reg_tree.item(sel[0])
        reg_id = item["values"][0]
        student_name = item["values"][2]

        confirm = messagebox.askyesno(
            "Confirm Cancellation",
            f"Are you sure you want to cancel the registration for '{student_name}' [{reg_id}]?"
        )
        if confirm:
            ok, msg = self.engine.cancel_registration(reg_id)
            if ok:
                messagebox.showinfo("Success", msg)
                self.refresh_all_views()
            else:
                messagebox.showerror("Error", msg)

    def _export_event_attendees(self) -> None:
        sel = self.events_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Please select an event from the table first.")
            return

        item = self.events_tree.item(sel[0])
        event_id = item["values"][0]
        event = self.engine.get_event(event_id)
        if not event:
            return

        regs = [r for r in self.engine.registrations if r.event_id == event_id]
        out_path = self.exporter.export_attendee_list_csv(event, regs)
        messagebox.showinfo("Export Complete", f"Attendee list saved to:\n{out_path.resolve()}")

    def _export_master_csv(self) -> None:
        out_path = self.exporter.export_attendee_list_csv(None, self.engine.registrations)
        messagebox.showinfo("Export Complete", f"Master attendee CSV exported to:\n{out_path.resolve()}")

    def _generate_charts_gui(self) -> None:
        summary = self.engine.compute_executive_summary()
        results = self.plotter.generate_all_charts(summary, self.engine.registrations)
        if any(results.values()):
            messagebox.showinfo(
                "Charts Generated",
                f"High-resolution PNG charts have been saved to:\n{self.storage.charts_dir.resolve()}"
            )
        else:
            messagebox.showinfo("ASCII Charts", "Matplotlib not installed. ASCII charts were rendered to terminal.")

    def _export_markdown_gui(self) -> None:
        summary = self.engine.compute_executive_summary()
        warnings = self.engine.get_threshold_warnings()
        out_path = self.exporter.export_markdown_summary(summary, warnings)
        messagebox.showinfo("Export Complete", f"Structured Markdown report exported to:\n{out_path.resolve()}")

    def _open_audit_log(self) -> None:
        log_path = self.storage.exports_dir / "audit_log.txt"
        if not log_path.exists():
            messagebox.showinfo("Info", "Audit log is currently empty.")
            return
        self._open_file(log_path)

    def _open_exports_folder(self) -> None:
        self._open_file(self.storage.exports_dir)

    def _open_file(self, path: Path) -> None:
        try:
            if os.name == "nt":
                os.startfile(str(path))
            else:
                subprocess.run(["xdg-open", str(path)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open path: {e}")

    def _browse_import_file(self) -> None:
        filename = filedialog.askopenfilename(
            title="Select Attendee CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialdir=str(self.storage.data_dir)
        )
        if filename:
            self.import_path_var.set(filename)

    def _execute_import(self) -> None:
        fpath = self.import_path_var.get().strip()
        if not fpath:
            messagebox.showerror("Error", "Please specify a CSV file path.")
            return

        res = self.engine.bulk_import_csv(fpath)
        self.import_log_text.delete("1.0", tk.END)

        self.import_log_text.insert(tk.END, f"=== BATCH CSV IMPORT REPORT ===\n")
        self.import_log_text.insert(tk.END, f"File: {fpath}\n")
        self.import_log_text.insert(tk.END, f"Total Rows Processed: {res['total_rows']}\n")
        self.import_log_text.insert(tk.END, f"Successfully Imported: {res['imported_count']}\n")
        self.import_log_text.insert(tk.END, f"Skipped / Invalid Rows: {res['skipped_count']}\n\n")

        if res.get("errors"):
            self.import_log_text.insert(tk.END, f"--- ROW-BY-ROW ERROR LOG ({len(res['errors'])} errors) ---\n")
            for err in res["errors"]:
                self.import_log_text.insert(tk.END, f"[Row {err['row']}] {'; '.join(err['reasons'])}\n")
                self.import_log_text.insert(tk.END, f"  Data: {err['data']}\n\n")
            if res.get("error_log_path"):
                self.import_log_text.insert(tk.END, f"\nDetailed error log saved to:\n{res['error_log_path']}\n")

        self.refresh_all_views()
        messagebox.showinfo("Import Complete", res["message"])


def launch_gui(engine: RegistrationEngine = None) -> None:
    """Launches the Tkinter GUI interface."""
    if not TKINTER_AVAILABLE:
        print(" [ERROR] Tkinter is not available on this Python installation.")
        return

    root = tk.Tk()
    eng = engine or RegistrationEngine()
    app = CollegeEventManagerGUI(root, eng)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
