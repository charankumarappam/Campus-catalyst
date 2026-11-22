"""
app_streamlit.py
Interactive, production-ready Streamlit Web Application for
Campus Catalyst: College Event Registration Manager (Project #8).
Domain: Education & Student Life | Modern UI for Hackathon Expo & LetzProject Assessment.
"""

from __future__ import annotations
import os
import io
from pathlib import Path
from datetime import datetime, date

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from models import Event, Registration, EventCategory, PaymentStatus, AttendanceStatus, RegistrationStatus
from storage import StorageManager
from engine import RegistrationEngine
from analytics import ReportExporter, VisualPlotter, AuditLogger
from validators import is_valid_email, is_valid_phone, is_valid_roll_number, clean_phone


# Page configuration
st.set_page_config(
    page_title="Campus Catalyst | Event Manager",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge-critical {
        background-color: #FEE2E2;
        color: #DC2626;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-warning {
        background-color: #FEF3C7;
        color: #D97706;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-success {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Core Engine & Session State
@st.cache_resource
def get_system_components():
    base_dir = Path(__file__).resolve().parent
    storage = StorageManager(base_dir)
    audit_logger = AuditLogger(storage.exports_dir / "audit_log.txt")
    engine = RegistrationEngine(storage, audit_logger=audit_logger.log)
    exporter = ReportExporter(storage.exports_dir)
    plotter = VisualPlotter(storage.charts_dir)
    return storage, engine, exporter, plotter, audit_logger

storage, engine, exporter, plotter, audit_logger = get_system_components()


# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/color/96/graduation-cap.png", width=64)
st.sidebar.markdown("## **Campus Catalyst**")
st.sidebar.caption("Project #8: College Event Manager")

active_warnings = engine.get_threshold_warnings()
warning_badge = f" ⚠️ ({len(active_warnings)})" if active_warnings else " ✅"

nav_choice = st.sidebar.radio(
    "Navigation Menu",
    [
        "📊 Dashboard & Live Analytics",
        "📅 Events & Capacity Monitor",
        "📝 Participant Registration Wizard",
        "👥 Attendees Directory & Status",
        f"⚠️ Threshold Alerts{warning_badge}",
        "📥 Bulk CSV Data Import",
        "📤 Reports & Data Export Center"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Offline-First • Dual JSON/CSV & SQLite Storage • Python 3.10+")


# ==============================================================================
# 1. DASHBOARD & LIVE ANALYTICS
# ==============================================================================
if nav_choice == "📊 Dashboard & Live Analytics":
    st.markdown('<p class="main-header">🎓 Campus Catalyst: Executive Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Real-time attendance metrics, capacity utilization gauges, and institutional breakdown.</p>', unsafe_allow_html=True)

    summary = engine.compute_executive_summary()
    fin = summary.get("financials", {})

    # Top KPI Metrics Cards
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.metric("Total Events", summary["total_events"], delta=None)
    with kpi2:
        st.metric("Total Registrations", summary["total_registrations"], delta=f"{summary['active_registrations']} Active")
    with kpi3:
        st.metric("Capacity Utilization", f"{summary['overall_capacity_utilization']:.1f}%", delta=f"{summary['total_confirmed_seats']}/{summary['total_capacity']} Seats")
    with kpi4:
        st.metric("Revenue Collected", f"₹{fin.get('total_collected', 0.0):,.2f}", delta=f"₹{fin.get('total_pending', 0.0):,.2f} Pending")
    with kpi5:
        st.metric("Active Alerts", len(active_warnings), delta=None, delta_color="inverse")

    st.divider()

    # Visual Charts
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Seat Capacity vs. Confirmed Registrations")
        breakdown = summary.get("event_breakdown", [])
        if breakdown:
            df_cap = pd.DataFrame(breakdown)
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=df_cap["title"],
                y=df_cap["max_capacity"],
                name="Max Capacity",
                marker_color="#CBD5E1"
            ))
            fig_bar.add_trace(go.Bar(
                x=df_cap["title"],
                y=df_cap["confirmed"],
                name="Confirmed Attendees",
                marker_color=df_cap["utilization_pct"].apply(
                    lambda p: "#EF4444" if p >= 100 else ("#F59E0B" if p >= 85 else "#10B981")
                )
            ))
            fig_bar.update_layout(
                barmode="group",
                xaxis_tickangle=-25,
                margin=dict(l=20, r=20, t=30, b=80),
                height=380
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No event data to plot.")

    with col_chart2:
        st.subheader("Department Participation Distribution")
        dept_counts = summary.get("department_counts", {})
        if dept_counts:
            df_dept = pd.DataFrame(list(dept_counts.items()), columns=["Department", "Registrations"])
            fig_pie = px.pie(
                df_dept,
                names="Department",
                values="Registrations",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=380)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No registrations recorded yet.")

    # Second row charts
    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        st.subheader("Registration Velocity Trend Over Time")
        dates_count = {}
        for r in engine.registrations:
            if r.registration_timestamp:
                d = r.registration_timestamp.split(" ")[0]
                dates_count[d] = dates_count.get(d, 0) + 1
        if dates_count:
            df_trend = pd.DataFrame(sorted(dates_count.items()), columns=["Date", "Registrations"])
            fig_line = px.line(df_trend, x="Date", y="Registrations", markers=True, line_shape="spline")
            fig_line.update_traces(line_color="#2563EB", line_width=3)
            fig_line.update_layout(margin=dict(l=20, r=20, t=30, b=40), height=320)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No timeline trend data.")

    with col_chart4:
        st.subheader("Payment & Status Distribution")
        status_counts = summary.get("status_counts", {})
        if status_counts:
            df_status = pd.DataFrame(list(status_counts.items()), columns=["Status", "Count"])
            fig_donut = px.bar(
                df_status,
                x="Status",
                y="Count",
                color="Status",
                color_discrete_map={
                    "Confirmed": "#10B981",
                    "Waitlisted": "#F59E0B",
                    "Pending Payment": "#6366F1",
                    "Cancelled": "#EF4444"
                }
            )
            fig_donut.update_layout(margin=dict(l=20, r=20, t=30, b=40), height=320)
            st.plotly_chart(fig_donut, use_container_width=True)


# ==============================================================================
# 2. EVENTS & CAPACITY MONITOR
# ==============================================================================
elif nav_choice == "📅 Events & Capacity Monitor":
    st.markdown('<p class="main-header">📅 College Events Management & Capacity Monitor</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Create new college events, configure capacity limits and deadlines, and view real-time rosters.</p>', unsafe_allow_html=True)

    with st.expander("➕ Create New College Event", expanded=False):
        with st.form("create_event_form"):
            c1, c2 = st.columns(2)
            with c1:
                ev_title = st.text_input("Event Title *", placeholder="e.g. National Hackathon 2026")
                ev_cat = st.selectbox("Category *", [c.value for c in EventCategory])
                ev_venue = st.text_input("Venue / Hall *", placeholder="e.g. Ramanujan Auditorium")
            with c2:
                ev_date = st.date_input("Event Date *", min_value=date.today())
                ev_deadline = st.date_input("Registration Deadline *", min_value=date.today())
                c_cap, c_fee = st.columns(2)
                with c_cap:
                    ev_cap = st.number_input("Max Capacity *", min_value=1, max_value=5000, value=30)
                with c_fee:
                    ev_fee = st.number_input("Entry Fee (₹)", min_value=0.0, value=0.0, step=50.0)

            submitted = st.form_submit_button("Create Event", use_container_width=True)
            if submitted:
                if not ev_title.strip() or not ev_venue.strip():
                    st.error("Please fill in both Title and Venue.")
                elif ev_deadline > ev_date:
                    st.error("Registration deadline cannot be after the event date.")
                else:
                    ok, msg, new_ev = engine.add_event(
                        title=ev_title,
                        category=ev_cat,
                        event_date=ev_date.strftime("%Y-%m-%d"),
                        registration_deadline=ev_deadline.strftime("%Y-%m-%d"),
                        max_capacity=int(ev_cap),
                        venue=ev_venue,
                        fee=float(ev_fee)
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    st.subheader("Current Active Events")
    for ev in engine.events:
        confirmed = engine.get_event_confirmed_count(ev.event_id)
        waitlisted = engine.get_event_waitlist_count(ev.event_id)
        pct = (confirmed / ev.max_capacity) if ev.max_capacity > 0 else 0.0

        with st.container():
            col_info, col_prog, col_btn = st.columns([3, 2, 1.5])
            with col_info:
                st.markdown(f"### **{ev.title}** `{ev.event_id}`")
                st.caption(f"📍 {ev.venue} | 🏷️ {ev.category} | 📅 Date: {ev.event_date} | ⏳ Deadline: {ev.registration_deadline}")
            with col_prog:
                st.write(f"**Capacity: {confirmed} / {ev.max_capacity} Seats ({pct*100:.1f}%)**")
                prog_val = min(pct, 1.0)
                st.progress(prog_val)
                if waitlisted > 0:
                    st.caption(f"⚠️ {waitlisted} student(s) currently on WAITLIST")
            with col_btn:
                ev_regs = [r for r in engine.registrations if r.event_id == ev.event_id]
                csv_data = pd.DataFrame([r.to_dict() for r in ev_regs]).to_csv(index=False).encode('utf-8') if ev_regs else b""
                st.download_button(
                    label=f"📥 Attendee List ({len(ev_regs)})",
                    data=csv_data,
                    file_name=f"attendees_{ev.event_id}.csv",
                    mime="text/csv",
                    disabled=len(ev_regs) == 0,
                    key=f"dl_{ev.event_id}"
                )
            st.divider()


# ==============================================================================
# 3. PARTICIPANT REGISTRATION WIZARD
# ==============================================================================
elif nav_choice == "📝 Participant Registration Wizard":
    st.markdown('<p class="main-header">📝 Guided Participant Registration Wizard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Strict defensive validation, duplicate detection, and automated seat allocation.</p>', unsafe_allow_html=True)

    if not engine.events:
        st.warning("No events found. Please create an event first.")
    else:
        event_options = {f"{e.event_id} - {e.title}": e for e in engine.events}
        selected_label = st.selectbox("Select College Event *", list(event_options.keys()))
        selected_event = event_options[selected_label]

        # Live Event Status Box
        confirmed = engine.get_event_confirmed_count(selected_event.event_id)
        is_full = confirmed >= selected_event.max_capacity
        is_closed = selected_event.is_deadline_passed()

        status_box = st.container()
        with status_box:
            m1, m2, m3 = st.columns(3)
            with m1:
                st.write(f"**Available Seats:** {max(0, selected_event.max_capacity - confirmed)} / {selected_event.max_capacity}")
            with m2:
                st.write(f"**Registration Fee:** ₹{selected_event.fee:.2f}")
            with m3:
                if is_full:
                    st.markdown('<span class="badge-warning">Event Full (Waitlist Mode Active)</span>', unsafe_allow_html=True)
                elif is_closed:
                    st.markdown('<span class="badge-critical">Deadline Passed</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="badge-success">Registrations Open</span>', unsafe_allow_html=True)

        st.write("")
        with st.form("registration_form"):
            r1, r2 = st.columns(2)
            with r1:
                s_name = st.text_input("Student Full Name *", placeholder="e.g. Aarav Sharma")
                s_roll = st.text_input("Student Roll Number *", placeholder="e.g. 22CS104").strip().upper()
                s_dept = st.selectbox("Department *", [
                    "Computer Science", "Information Technology", "Electronics & Comm",
                    "Electrical Engg", "Mechanical Engg", "Civil Engg", "Biotechnology", "Management Studies"
                ])
                s_year = st.selectbox("Year of Study *", [1, 2, 3, 4, 5], index=2)

            with r2:
                s_email = st.text_input("Student Email *", placeholder="e.g. student@campus.edu").strip().lower()
                s_phone = st.text_input("10-Digit Mobile Number *", placeholder="e.g. 9876543210").strip()
                s_payment = st.selectbox("Payment Status", [
                    PaymentStatus.COMPLETED.value, PaymentStatus.PENDING.value, PaymentStatus.EXEMPT.value
                ])
                s_notes = st.text_input("Notes (Optional)", placeholder="Team name, dietary constraints, etc.")

            submit_reg = st.form_submit_button("Submit Registration", use_container_width=True)

            if submit_reg:
                # Client-Side Defensive Validation
                errors = []
                if not s_name or len(s_name.strip()) < 2:
                    errors.append("Student Name must be at least 2 characters long.")
                if not is_valid_roll_number(s_roll):
                    errors.append(f"Invalid Roll Number '{s_roll}'. Expected 4-15 alphanumeric characters (e.g., 22CS104).")
                if not is_valid_email(s_email):
                    errors.append(f"Invalid Email Address '{s_email}'. Expected standard format (e.g., name@campus.edu).")
                if not is_valid_phone(s_phone):
                    errors.append(f"Invalid Phone '{s_phone}'. Expected a valid 10-digit mobile number.")

                if errors:
                    for err in errors:
                        st.error(f"❌ {err}")
                else:
                    ok, msg, reg = engine.register_participant(
                        event_id=selected_event.event_id,
                        student_name=s_name,
                        roll_number=s_roll,
                        email=s_email,
                        phone=clean_phone(s_phone),
                        department=s_dept,
                        year_of_study=s_year,
                        payment_status=s_payment,
                        notes=s_notes,
                        force_deadline_bypass=True
                    )
                    if ok:
                        st.success(f"🎉 {msg}")
                        st.balloons()
                        st.info(f"**Receipt:** Student **{reg.student_name}** | Reg ID: `{reg.registration_id}` | Status: **{reg.registration_status}**")
                    else:
                        st.error(f"❌ {msg}")


# ==============================================================================
# 4. ATTENDEES DIRECTORY & STATUS
# ==============================================================================
elif nav_choice == "👥 Attendees Directory & Status":
    st.markdown('<p class="main-header">👥 Registered Attendees Directory & Status Control</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Search, filter, update payment and attendance statuses, or safely cancel registrations.</p>', unsafe_allow_html=True)

    # Search & Filter Controls
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        search_kw = st.text_input("🔍 Search Keyword", placeholder="Name, Roll No, Email...")
    with f2:
        filter_ev = st.selectbox("Event", ["All"] + [e.event_id for e in engine.events])
    with f3:
        filter_dept = st.selectbox("Department", ["All", "Computer Science", "Information Technology", "Electronics & Comm", "Electrical Engg", "Mechanical Engg", "Civil Engg", "Biotechnology", "Management Studies"])
    with f4:
        filter_status = st.selectbox("Status", ["All", "Confirmed", "Waitlisted", "Pending Payment", "Cancelled"])

    # Query Engine
    matches = engine.search_registrations(
        keyword=search_kw or None,
        event_id=filter_ev if filter_ev != "All" else None,
        department=filter_dept if filter_dept != "All" else None,
        reg_status=filter_status if filter_status != "All" else None
    )

    st.write(f"Showing **{len(matches)}** matching attendee records:")
    if matches:
        data_rows = []
        for r, ev in matches:
            data_rows.append({
                "Reg ID": r.registration_id,
                "Event": r.event_id,
                "Student Name": r.student_name,
                "Roll Number": r.roll_number,
                "Department": r.department,
                "Year": r.year_of_study,
                "Email": r.email,
                "Phone": r.phone,
                "Status": r.registration_status,
                "Payment": r.payment_status,
                "Attendance": r.attendance_status
            })
        df_display = pd.DataFrame(data_rows)
        st.dataframe(df_display, use_container_width=True, height=350)

        # Quick Status Update Action Bar
        st.subheader("⚡ Quick Status Update & Cancellation")
        with st.form("status_update_form"):
            u1, u2, u3, u4 = st.columns(4)
            with u1:
                target_reg_id = st.selectbox("Select Registration ID", [d["Reg ID"] for d in data_rows])
            with u2:
                new_reg_s = st.selectbox("Registration Status", ["(No Change)", "Confirmed", "Waitlisted", "Pending Payment"])
            with u3:
                new_pay_s = st.selectbox("Payment Status", ["(No Change)", "Completed", "Pending", "Exempt", "Refunded"])
            with u4:
                new_att_s = st.selectbox("Attendance Status", ["(No Change)", "Registered", "Attended", "Absent"])

            u_sub, u_cancel = st.columns([1, 1])
            with u_sub:
                update_btn = st.form_submit_button("Update Statuses", use_container_width=True)
            with u_cancel:
                cancel_btn = st.form_submit_button("Cancel Registration ❌", use_container_width=True)

            if update_btn:
                ok, msg = engine.update_registration_status(
                    target_reg_id,
                    new_reg_status=new_reg_s if new_reg_s != "(No Change)" else None,
                    new_payment_status=new_pay_s if new_pay_s != "(No Change)" else None,
                    new_attendance_status=new_att_s if new_att_s != "(No Change)" else None
                )
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

            if cancel_btn:
                ok, msg = engine.cancel_registration(target_reg_id, reason="Cancelled via Streamlit Portal")
                if ok:
                    st.warning(msg)
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.info("No records matched your search criteria.")


# ==============================================================================
# 5. THRESHOLD WARNINGS & ANOMALIES
# ==============================================================================
elif nav_choice.startswith("⚠️ Threshold Alerts"):
    st.markdown('<p class="main-header">⚠️ Real-Time Threshold Alerts & Anomaly Monitor</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Automated detection of sold-out events, imminent deadlines, overdue registrations, and financial anomalies.</p>', unsafe_allow_html=True)

    warnings = engine.get_threshold_warnings()
    if not warnings:
        st.success("✅ All events and participants are operating within nominal thresholds. Zero active alerts!")
    else:
        crit_count = sum(1 for w in warnings if w["level"] == "CRITICAL")
        warn_count = sum(1 for w in warnings if w["level"] == "WARNING")

        c_box1, c_box2 = st.columns(2)
        with c_box1:
            st.metric("Critical Alerts (Action Required)", crit_count)
        with c_box2:
            st.metric("Warning Flags (Thresholds Nearing)", warn_count)

        st.write("")
        for w in warnings:
            if w["level"] == "CRITICAL":
                st.error(f"🔴 **[{w['code']}]** Event `{w['event_id']}` ({w['title']}): {w['message']}")
            else:
                st.warning(f"⚠️ **[{w['code']}]** Event `{w['event_id']}` ({w['title']}): {w['message']}")


# ==============================================================================
# 6. BULK CSV DATA IMPORT
# ==============================================================================
elif nav_choice == "📥 Bulk CSV Data Import":
    st.markdown('<p class="main-header">📥 Bulk CSV Dataset Ingestion Engine</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Upload legacy registration sheets with schema verification, duplicate rejection, and automated error logging.</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload Attendees CSV File", type=["csv"])

    if uploaded_file is not None:
        temp_import_path = storage.data_dir / f"uploaded_{uploaded_file.name}"
        with open(temp_import_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.subheader("Preview Uploaded File")
        try:
            df_preview = pd.read_csv(temp_import_path)
            st.dataframe(df_preview.head(8), use_container_width=True)

            if st.button("🚀 Execute Batch Import", type="primary"):
                with st.spinner("Processing records..."):
                    res = engine.bulk_import_csv(temp_import_path)

                st.success(res["message"])
                r1, r2, r3 = st.columns(3)
                r1.metric("Total Rows Evaluated", res["total_rows"])
                r2.metric("Successfully Imported", res["imported_count"])
                r3.metric("Skipped / Invalid", res["skipped_count"])

                if res.get("errors"):
                    st.subheader(f"⚠️ Row-by-Row Error Log ({len(res['errors'])} Issues Found)")
                    err_rows = []
                    for e in res["errors"]:
                        err_rows.append({
                            "Row #": e["row"],
                            "Student Name": e["data"].get("student_name", "N/A"),
                            "Roll No": e["data"].get("roll_number", "N/A"),
                            "Reasons": ", ".join(e["reasons"])
                        })
                    st.table(pd.DataFrame(err_rows))
        except Exception as ex:
            st.error(f"Error parsing uploaded file: {ex}")
    else:
        st.info("💡 You can test the batch import engine using the bundled test file: `data/sample_legacy_import.csv`")
        if st.button("Run Test Import on `sample_legacy_import.csv`"):
            test_csv = storage.data_dir / "sample_legacy_import.csv"
            res = engine.bulk_import_csv(test_csv)
            st.success(res["message"])
            st.write(f"Evaluated {res['total_rows']} rows: {res['imported_count']} imported, {res['skipped_count']} rejected.")


# ==============================================================================
# 7. REPORTS & DATA EXPORT CENTER
# ==============================================================================
elif nav_choice == "📤 Reports & Data Export Center":
    st.markdown('<p class="main-header">📤 Executive Reports & Multi-Format Exporter</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Generate and download official CSV attendee rosters, Markdown summaries, and system audit trails.</p>', unsafe_allow_html=True)

    summary = engine.compute_executive_summary()
    warnings = engine.get_threshold_warnings()

    col_exp1, col_exp2, col_exp3 = st.columns(3)

    with col_exp1:
        st.subheader("Master Attendee CSV")
        st.caption("Standardized roster containing all student registrations across every event.")
        master_path = exporter.export_attendee_list_csv(None, engine.registrations)
        with open(master_path, "rb") as mf:
            st.download_button("📥 Download Master CSV", mf, file_name="master_attendees.csv", mime="text/csv", use_container_width=True)

    with col_exp2:
        st.subheader("Markdown Executive Summary")
        st.caption("Official executive report with KPI tables, capacity rankings, and alerts.")
        md_path = exporter.export_markdown_summary(summary, warnings)
        with open(md_path, "rb") as mdf:
            st.download_button("📝 Download Summary (.md)", mdf, file_name="executive_summary.md", mime="text/markdown", use_container_width=True)

    with col_exp3:
        st.subheader("System Audit Log")
        st.caption("Cryptographic/timestamped operational trail recording session actions.")
        log_path = storage.exports_dir / "audit_log.txt"
        if log_path.exists():
            with open(log_path, "rb") as lf:
                st.download_button("📜 Download Audit Log (.txt)", lf, file_name="audit_log.txt", mime="text/plain", use_container_width=True)
        else:
            st.info("Audit log is currently empty.")

    st.divider()
    st.subheader("Executive Report Preview")
    if md_path.exists():
        with open(md_path, "r", encoding="utf-8") as f:
            st.markdown(f.read())
