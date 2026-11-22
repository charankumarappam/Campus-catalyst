"""
analytics.py
Visualization engine (Matplotlib high-res charts with ASCII fallbacks) and
multi-format report exporter (CSV attendee lists, Markdown executive summary, Audit Log) for
Campus Catalyst: College Event Registration Manager (Project #8).
"""

from __future__ import annotations
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from models import Event, Registration, RegistrationStatus, PaymentStatus

# Defensive import for matplotlib
MATPLOTLIB_AVAILABLE = False
try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive headless backend for clean file rendering
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class AuditLogger:
    """Manages the plain-text audit trail."""

    def __init__(self, log_path: Path | str):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, action: str, details: str, actor: str = "Admin") -> None:
        """Appends a timestamped audit entry."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{ts}] [{actor}] [{action.upper()}] {details}\n"
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            print(f" [WARNING] Failed to write to audit log: {e}")


class ReportExporter:
    """Handles multi-format reporting: CSV attendee lists and Markdown executive summaries."""

    def __init__(self, exports_dir: Path | str):
        self.exports_dir = Path(exports_dir)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def export_attendee_list_csv(
        self,
        event: Optional[Event],
        registrations: List[Registration],
        custom_filename: Optional[str] = None
    ) -> Path:
        """
        Exports attendee list for a specific event or all events to CSV.
        """
        if custom_filename:
            filename = custom_filename
        elif event:
            filename = f"attendees_{event.event_id}.csv"
        else:
            filename = "master_attendees.csv"

        out_path = self.exports_dir / filename
        fieldnames = [
            "Registration ID", "Event ID", "Event Title", "Student Name",
            "Roll Number", "Email", "Phone", "Department", "Year",
            "Registration Status", "Payment Status", "Attendance Status",
            "Timestamp", "Notes"
        ]

        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(fieldnames)
            for r in registrations:
                writer.writerow([
                    r.registration_id,
                    r.event_id,
                    event.title if event else r.event_id,
                    r.student_name,
                    r.roll_number,
                    r.email,
                    r.phone,
                    r.department,
                    f"Year {r.year_of_study}",
                    r.registration_status,
                    r.payment_status,
                    r.attendance_status,
                    r.registration_timestamp,
                    r.notes
                ])

        return out_path

    def export_markdown_summary(self, summary: Dict[str, Any], warnings: List[Dict[str, str]]) -> Path:
        """
        Generates a comprehensive executive summary in structured Markdown.
        """
        out_path = self.exports_dir / "executive_summary.md"
        gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        fin = summary.get("financials", {})
        total_events = summary.get("total_events", 0)
        total_regs = summary.get("total_registrations", 0)
        active_regs = summary.get("active_registrations", 0)
        util_rate = summary.get("overall_capacity_utilization", 0.0)

        lines = [
            "# Campus Catalyst: College Event Registration Executive Summary",
            f"*Generated on: {gen_time}*",
            "",
            "## 1. High-Level Performance Indicators (KPIs)",
            "",
            "| Metric | Value |",
            "| :--- | :--- |",
            f"| **Total Managed Events** | {total_events} |",
            f"| **Total Registrations** | {total_regs} |",
            f"| **Active / Confirmed Registrations** | {active_regs} |",
            f"| **Waitlisted Registrations** | {summary.get('waitlisted_registrations', 0)} |",
            f"| **Cancelled Registrations** | {summary.get('cancelled_registrations', 0)} |",
            f"| **Total Seat Capacity Across Events** | {summary.get('total_capacity', 0)} |",
            f"| **Overall Seat Utilization Rate** | {util_rate:.1f}% |",
            f"| **Average Registrations per Event** | {summary.get('avg_registrations_per_event', 0.0):.1f} |",
            f"| **Total Projected Revenue** | ₹{fin.get('total_projected', 0.0):,.2f} |",
            f"| **Revenue Collected** | ₹{fin.get('total_collected', 0.0):,.2f} |",
            f"| **Pending Revenue** | ₹{fin.get('total_pending', 0.0):,.2f} |",
            "",
            "## 2. Event-by-Event Capacity Breakdown",
            "",
            "| Event ID | Event Title | Category | Capacity | Confirmed | Waitlist | Utilization | Fee (₹) | Deadline |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        for eb in summary.get("event_breakdown", []):
            lines.append(
                f"| `{eb['event_id']}` | **{eb['title']}** | {eb['category']} | "
                f"{eb['max_capacity']} | {eb['confirmed']} | {eb['waitlisted']} | "
                f"{eb['utilization_pct']:.1f}% | ₹{eb['fee']:.2f} | {eb['deadline']} |"
            )

        lines.extend([
            "",
            "## 3. Department Participation Breakdown",
            "",
            "| Department | Registrations | Share % |",
            "| :--- | :--- | :--- |"
        ])

        dept_counts = summary.get("department_counts", {})
        total_dept_regs = sum(dept_counts.values()) if dept_counts else 1
        for dept, count in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total_dept_regs) * 100
            lines.append(f"| {dept} | {count} | {pct:.1f}% |")

        lines.extend([
            "",
            "## 4. Operational Threshold & Anomaly Alerts",
            ""
        ])

        if not warnings:
            lines.append("*All events and registrations are currently operating within nominal parameters.*")
        else:
            lines.append(f"Found **{len(warnings)}** active alerts requiring attention:")
            lines.append("")
            lines.append("| Severity | Code | Target Event | Message |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for w in warnings:
                icon = "🔴" if w['level'] == "CRITICAL" else "⚠️"
                lines.append(f"| {icon} `{w['level']}` | `{w['code']}` | **{w['event_id']}** ({w['title']}) | {w['message']} |")

        lines.append("")
        lines.append("---")
        lines.append("*Campus Catalyst System — Education & Student Life Domain*")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        return out_path


class VisualPlotter:
    """Generates high-resolution Matplotlib graphs and ASCII terminal charts."""

    def __init__(self, charts_dir: Path | str):
        self.charts_dir = Path(charts_dir)
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_charts(self, summary: Dict[str, Any], registrations: List[Registration]) -> Dict[str, Optional[Path]]:
        """
        Creates all three required charts:
        1. Capacity vs Registrations Bar Chart
        2. Department / Category Distribution Donut Chart
        3. Registrations Timeline Trend
        """
        results: Dict[str, Optional[Path]] = {
            "capacity_chart": None,
            "department_chart": None,
            "timeline_chart": None
        }

        if not MATPLOTLIB_AVAILABLE:
            print(" [NOTICE] Matplotlib is not installed. Rendering ASCII fallback charts in console.")
            self.render_ascii_capacity_chart(summary)
            self.render_ascii_department_chart(summary)
            return results

        try:
            results["capacity_chart"] = self._plot_capacity_bar(summary)
            results["department_chart"] = self._plot_department_donut(summary)
            results["timeline_chart"] = self._plot_timeline_trend(registrations)
        except Exception as e:
            print(f" [WARNING] Error generating Matplotlib charts: {e}. Falling back to ASCII rendering.")
            self.render_ascii_capacity_chart(summary)
            self.render_ascii_department_chart(summary)

        return results

    def _plot_capacity_bar(self, summary: Dict[str, Any]) -> Path:
        """Bar chart: Registrations vs Max Capacity with threshold color coding."""
        breakdown = summary.get("event_breakdown", [])
        if not breakdown:
            return None

        event_names = [f"{b['event_id']}\n{b['title'][:14]}" for b in breakdown]
        confirmed = [b["confirmed"] for b in breakdown]
        capacities = [b["max_capacity"] for b in breakdown]
        pcts = [b["utilization_pct"] for b in breakdown]

        # Colors based on capacity utilization
        colors = []
        for p in pcts:
            if p >= 100.0:
                colors.append("#dc3545")  # Danger Red
            elif p >= 85.0:
                colors.append("#fd7e14")  # Warning Orange
            elif p >= 50.0:
                colors.append("#20c997")  # Teal / Normal
            else:
                colors.append("#0d6efd")  # Blue

        x = range(len(breakdown))
        width = 0.38

        plt.figure(figsize=(10, 5.5), dpi=150)
        plt.bar([i - width / 2 for i in x], capacities, width=width, label="Max Capacity", color="#adb5bd", alpha=0.7)
        bars = plt.bar([i + width / 2 for i in x], confirmed, width=width, label="Confirmed Attendees", color=colors)

        # Value annotations
        for bar, p in zip(bars, pcts):
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.5, f"{int(yval)}\n({p:.0f}%)", ha="center", va="bottom", fontsize=8, fontweight="bold")

        plt.title("College Events: Registrations vs Max Capacity Utilization", fontsize=13, fontweight="bold", pad=15)
        plt.xlabel("Events", fontsize=11, fontweight="bold")
        plt.ylabel("Seat Count", fontsize=11, fontweight="bold")
        plt.xticks(x, event_names, fontsize=9)
        plt.grid(axis="y", linestyle="--", alpha=0.5)
        plt.legend(frameon=True, loc="upper right")
        plt.tight_layout()

        out_path = self.charts_dir / "capacity_utilization.png"
        plt.savefig(out_path)
        plt.close()
        return out_path

    def _plot_department_donut(self, summary: Dict[str, Any]) -> Path:
        """Donut chart of department participation breakdown."""
        dept_counts = summary.get("department_counts", {})
        if not dept_counts:
            return None

        labels = list(dept_counts.keys())
        sizes = list(dept_counts.values())
        palette = ["#4361ee", "#3a0ca3", "#7209b7", "#f72585", "#4cc9f0", "#06d6a0", "#ffd166"]

        plt.figure(figsize=(8, 6), dpi=150)
        wedges, texts, autotexts = plt.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=palette[:len(sizes)],
            pctdistance=0.78,
            wedgeprops=dict(width=0.45, edgecolor="w", linewidth=2)
        )

        for at in autotexts:
            at.set_fontsize(9)
            at.set_fontweight("bold")

        plt.title("Student Participation Distribution by Department", fontsize=13, fontweight="bold", pad=15)
        plt.tight_layout()

        out_path = self.charts_dir / "department_distribution.png"
        plt.savefig(out_path)
        plt.close()
        return out_path

    def _plot_timeline_trend(self, registrations: List[Registration]) -> Optional[Path]:
        """Line/Bar trend chart of registrations over time."""
        if not registrations:
            return None

        dates_count: Dict[str, int] = {}
        for r in registrations:
            if r.registration_timestamp:
                d_str = r.registration_timestamp.split(" ")[0]
                dates_count[d_str] = dates_count.get(d_str, 0) + 1

        if not dates_count:
            return None

        sorted_dates = sorted(dates_count.keys())
        counts = [dates_count[d] for d in sorted_dates]

        plt.figure(figsize=(9, 5), dpi=150)
        plt.plot(sorted_dates, counts, marker="o", linewidth=2.5, color="#4361ee", label="Daily Sign-ups")
        plt.fill_between(sorted_dates, counts, color="#4361ee", alpha=0.15)

        for d, c in zip(sorted_dates, counts):
            plt.text(d, c + 0.2, str(c), ha="center", va="bottom", fontsize=8, fontweight="bold")

        plt.title("Participant Registration Trend Over Time", fontsize=13, fontweight="bold", pad=15)
        plt.xlabel("Registration Date", fontsize=11, fontweight="bold")
        plt.ylabel("Number of Registrations", fontsize=11, fontweight="bold")
        plt.xticks(rotation=45, ha="right", fontsize=8)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend(frameon=True)
        plt.tight_layout()

        out_path = self.charts_dir / "registration_timeline.png"
        plt.savefig(out_path)
        plt.close()
        return out_path

    # ==========================================
    # ASCII TERMINAL FALLBACK CHARTS
    # ==========================================

    def render_ascii_capacity_chart(self, summary: Dict[str, Any], bar_width: int = 30) -> None:
        """Renders clean ASCII horizontal bar chart in console."""
        print("\n" + "=" * 65)
        print(" [CHART] EVENT CAPACITY UTILIZATION (ASCII VIEW)")
        print("=" * 65)

        breakdown = summary.get("event_breakdown", [])
        if not breakdown:
            print(" No event data available.")
            return

        for b in breakdown:
            pct = b["utilization_pct"]
            filled_len = int((pct / 100) * bar_width)
            filled_len = min(filled_len, bar_width)
            bar = "#" * filled_len + "-" * (bar_width - filled_len)

            tag = "[CRIT]" if pct >= 100 else ("[WARN]" if pct >= 85 else "[OK]  ")
            print(f" {tag} {b['event_id']:<7} |{bar}| {b['confirmed']:>3}/{b['max_capacity']:<3} ({pct:>5.1f}%) {b['title'][:20]}")
        print("=" * 65)

    def render_ascii_department_chart(self, summary: Dict[str, Any], bar_width: int = 25) -> None:
        """Renders ASCII distribution by department."""
        print("\n" + "=" * 65)
        print(" [CHART] DEPARTMENT PARTICIPATION SHARE (ASCII VIEW)")
        print("=" * 65)

        dept_counts = summary.get("department_counts", {})
        if not dept_counts:
            print(" No registration data available.")
            return

        total = sum(dept_counts.values()) or 1
        for dept, count in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total) * 100
            filled_len = int((pct / 100) * bar_width)
            bar = "=" * filled_len + "." * (bar_width - filled_len)
            print(f" {dept:<22} |{bar}| {count:>3} ({pct:>5.1f}%)")
        print("=" * 65)
