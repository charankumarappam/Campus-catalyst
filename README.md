# 🎓 Campus Catalyst: College Event Registration Manager
### **Project #8 | Domain: Education & Student Life | Production-Ready Python CLI & GUI**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Modular%20Clean%20Code-brightgreen.svg)]()
[![Persistence](https://img.shields.io/badge/Storage-Dual%20JSON%20%26%20CSV-orange.svg)]()
[![UI Modes](https://img.shields.io/badge/Interface-Interactive%20CLI%20%2B%20Tkinter%20GUI-purple.svg)]()
[![Status](https://img.shields.io/badge/Hackathon-100%25%20Tested%20%26%20Demo--Ready-success.svg)]()

---

## 1. Executive Summary & Problem Context

In university and campus environments, organizing technical hackathons, cultural fests, sports tourneys, and academic conferences is plagued by administrative friction:
- **Manual errors & bad entries:** Misspelled student emails, malformed roll numbers, or duplicate registrations for the same seat.
- **Capacity overbooking & deadline confusion:** Events quietly exceeding hall capacity or accepting registrations after deadlines have closed.
- **Fragmented reporting:** Event coordinators relying on disconnected spreadsheets without real-time insights, fee reconciliation, or visual trends.
- **Enterprise software bloat:** Existing enterprise solutions require intrusive server setups, cloud subscriptions, or high learning curves ill-suited for fast local workflows.

**Campus Catalyst: College Event Registration Manager** resolves this challenge with a lightweight, offline-first, production-grade Python application. Engineered with **strict defensive input validation**, **fault-tolerant local file persistence (JSON & CSV)**, **real-time threshold alerts**, **visual data plotting (Matplotlib & ASCII fallback)**, and an optional **Tkinter visual desktop interface**.

---

## 2. Codebase Architecture & Modular Layout

```
c:\Users\charankumar\Desktop\python project\
├── data/                               # Persistent Storage Directory
│   ├── events.json                     # Primary event store (JSON schema)
│   ├── events.csv                      # Synchronized event mirror (CSV)
│   ├── registrations.json              # Primary registration store (JSON schema)
│   ├── registrations.csv               # Synchronized registration mirror (CSV)
│   ├── sample_data.json                # Bundled hackathon preset (JSON)
│   ├── sample_data.csv                 # Bundled hackathon preset (CSV)
│   └── sample_legacy_import.csv        # Test dataset with intentional errors
├── exports/                            # Export Outputs & Audit Trail
│   ├── charts/                         # High-resolution Matplotlib graphs
│   │   ├── capacity_utilization.png    # Bar chart: Confirmed vs Max Capacity
│   │   ├── department_distribution.png # Donut chart: Department participation
│   │   └── registration_timeline.png   # Trend line: Daily sign-up trajectory
│   ├── attendees_<event_id>.csv        # Event-specific attendee rosters
│   ├── master_attendees.csv            # Master university attendee roster
│   ├── executive_summary.md            # Structured Markdown executive report
│   ├── audit_log.txt                   # Plain-text timestamped operational trail
│   └── import_errors.log               # Row-by-row bulk import error logger
├── models.py                           # Dataclasses & Enums (Event, Registration, Statuses)
├── validators.py                       # Defensive input loops, regex, bounds & row checks
├── storage.py                          # Dual JSON/CSV persistence & corrupted file auto-recovery
├── engine.py                           # Core business rules, capacity limits, search & aggregation
├── analytics.py                        # Matplotlib visualizations, ASCII fallbacks & multi-format reports
├── ui.py                               # ANSI color styling, fixed-width tables & pagination breaks
├── gui.py                              # Optional lightweight Tkinter graphical desktop view
├── seed_data.py                        # Realistic dataset generator (44 entries across 6 events)
├── main.py                             # CLI entry point, argument parser & main menu dispatch
├── test_suite.py                       # 17 automated unit & integration test cases
├── requirements.txt                    # Project dependency manifest
└── README.md                           # Documentation & Hackathon mentor walkthrough
```

---

## 3. Core Capabilities & Stretch Features

### 🛡️ Defensive Input Validation (`validators.py`)
- Continuous re-prompting loops: The program **never crashes** on blank entries, non-numeric values, or malformed strings.
- Regex-enforced checks:
  - **Emails:** RFC-compliant validation (`name@campus.edu`).
  - **Phone Numbers:** 10-digit mobile cleaning & validation (`9876543210`).
  - **Roll Numbers:** 4–15 character alphanumeric format (`22CS104`, `IT-2026-05`).
  - **Dates:** ISO `YYYY-MM-DD` calendar validation with past/future date logic.
- Graceful prompt cancellation: Users can enter `:q`, `cancel`, or trigger `Ctrl+C` / `EOF` to cleanly abort any prompt and return to the menu.

### 💾 Local Persistence & Auto-Recovery (`storage.py`)
- **Dual Synchronization:** State changes write synchronously to both structured `JSON` and `CSV` files.
- **Corrupted-File Auto-Recovery:** If `events.json` or `registrations.json` suffers corruption or truncation, the engine automatically creates a timestamped `.bak` backup, logs a warning, and seamlessly restores valid data from the synchronized CSV mirror.
- **Atomic File Writing:** Write-to-temp and atomic replace prevents file corruption during sudden system shutdowns.

### ⚙️ Core Business Rules & Intelligence (`engine.py`)
- **Duplicate Prevention:** Blocks multiple registrations with the same student roll number OR email for the same event.
- **Capacity Limits & Smart Waitlist:** When an event reaches maximum capacity, students are safely assigned to the `WAITLIST` rather than losing their registration intent.
- **Registration Deadlines:** Compares system clock against event deadlines, preventing late registrations while offering admin override capability.
- **Multi-Criteria Search:** Instant query filtering across names, roll numbers, departments, categories, and payment statuses.

### 🚨 Real-Time Threshold Warning Monitor (`engine.py` & `ui.py`)
Surfaces visual warning flags (`[CRITICAL]`, `[WARNING]`, `[ALERT]`):
1. **Critical Capacity:** Events reaching 100% capacity (e.g., `EVT-102` Robotics Challenge at 10/10 seats).
2. **Nearing Capacity:** Events at $\ge 85\%$ capacity (e.g., `EVT-101` Hackathon at 14/15 seats, 93.3%).
3. **Deadlines Expired / Imminent:** Highlights overdue events or deadlines closing within 48 hours.
4. **Financial Anomalies:** Flags pending unpaid registrations on past-deadline events.

### 📥 Bulk CSV Import with Row-by-Row Error Logger
- Ingests legacy or external attendee CSV files with flexible column headers (`name`, `student_name`, `roll`, `roll_no`, etc.).
- Evaluates domain rules row-by-row; skips malformed rows without crashing the batch.
- Outputs detailed row numbers and reasons to `exports/import_errors.log`.

### 📊 Visual Analytics & Multi-Format Exports (`analytics.py`)
- **Matplotlib High-Resolution PNGs:**
  - `capacity_utilization.png`: Bar chart color-coded by capacity risk (Red = Full, Orange = $\ge 85\%$, Teal = Normal).
  - `department_distribution.png`: Clean donut chart displaying departmental participation shares.
  - `registration_timeline.png`: Line trend chart visualizing registration velocity over time.
- **Terminal ASCII Fallback:** If Matplotlib is unavailable or running in a headless environment, visual bar charts render directly in the terminal console.
- **Multi-Format Exports:**
  - Standardized CSV attendee lists (`master_attendees.csv`, `attendees_<event_id>.csv`).
  - Structured Markdown Executive Summary (`exports/executive_summary.md`).
  - Persistent Audit Log (`exports/audit_log.txt`).

### 🖥️ Dual Interfaces: Interactive CLI + Modern Tkinter GUI (`gui.py`)
- **Branded CLI:** ANSI color-coded banners, fixed-width formatted tables, and interactive pagination breaks (10–12 rows per page).
- **Tkinter Desktop GUI:** Launch with `python main.py --gui` or Option 11 in the menu for visual table browsing, tabbed KPI cards, one-click exports, and file browser dialogs.

---

## 4. Installation & Setup Instructions

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14.
- Windows, macOS, or Linux.

### Quick Setup Steps

1. **Navigate to the Project Directory:**
   ```powershell
   cd "c:\Users\charankumar\Desktop\python project"
   ```

2. **Activate Existing Virtual Environment (or create a new one):**
   ```powershell
   # If using existing .venv in directory:
   .\.venv\Scripts\activate

   # Or create fresh:
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
   *(Only `matplotlib` is required; all other components utilize Python standard library).*

4. **Verify Installation via Automated Test Suite:**
   ```powershell
   python -m unittest test_suite.py -v
   ```
   *(All 17 tests verify models, validators, storage recovery, engine rules, and exports).*

---

## 5. Live Hackathon Demo Walkthrough (Mentor Script)

Follow this 5-minute step-by-step sequence for a live presentation:

### Step 1: Launch Application & Observe Branded Screen
```powershell
python main.py
```
- Showcase the branded ANSI ASCII welcome banner.
- Note the real-time active alert counter in the main menu: `[ 7] Threshold Warnings & Anomaly Detector (4 active!)`.

### Step 2: Demonstrate Defensive Input Validation (Option 2)
- Select `2` to Register a New Participant.
- Intentionally test bad inputs to demonstrate defensive loops:
  - Enter a blank name $\rightarrow$ App prompts: `[ERROR] Student Name cannot be blank.`
  - Enter an invalid roll number `CS` $\rightarrow$ App prompts: `[ERROR] Invalid roll number... Must be 4-15 alphanumeric chars.`
  - Enter an invalid email `john.doe` $\rightarrow$ App prompts: `[ERROR] Invalid email address... Expected name@campus.edu.`
  - Enter a 5-digit phone `12345` $\rightarrow$ App prompts: `[ERROR] Invalid phone number... Please enter a valid 10-digit number.`
- Now enter valid credentials:
  - Event: `EVT-101`
  - Name: `Rohan Gupta`
  - Roll: `22CS777`
  - Email: `rohan.g@campus.edu`
  - Phone: `9876543299`
  - Department: `Computer Science`
  - Year: `3`
- Confirm registration: System auto-generates ID `REG-2026-045`, timestamps the record, and syncs immediately to JSON & CSV.

### Step 3: Test Duplicate Registration Prevention
- Attempt to register `Rohan Gupta` again for `EVT-101` with roll number `22CS777`.
- **Outcome:** The engine immediately blocks the attempt with:
  `[CRITICAL] Student with roll number '22CS777' is already registered for event EVT-101.`

### Step 4: Review Threshold Warnings & Capacity Anomalies (Option 7)
- Select `7` in the menu.
- Observe highlighted alert categories:
  - `[CRITICAL] [CAPACITY_FULL] Event EVT-102 (National Collegiate Robotics Challenge) is at 100% capacity (10/10 seats full).`
  - `[WARNING] [CAPACITY_NEARING] Event EVT-101 (HackCampus 2026) nearing capacity at 93.3% (14/15 seats occupied).`
  - `[WARNING] [DEADLINE_IMMINENT] Event EVT-104 (Badminton Championship) registration closes tomorrow.`
  - `[CRITICAL] [DEADLINE_EXPIRED] Event EVT-105 (Cloud DevOps Workshop) registration deadline passed.`
  - `[WARNING] [UNPAID_EXPIRED_DEADLINE] Participant Deepak Nanda (23EC011) has unpaid fee of ₹150.00 past deadline.`

### Step 5: View Executive Summary & Analytics Dashboard (Option 5)
- Select `5` in the menu.
- View real-time aggregated metrics:
  - Total Events: `6`
  - Total Registrations: `44`
  - Seat Utilization: `48.9%`
  - Revenue Metrics: Projected, Collected, and Pending totals.
  - Formatted tables with column separators showing top trending events and departmental shares.

### Step 6: Generate Visual Charts (Option 6)
- Select `6` in the menu.
- The system generates 3 publication-ready PNG charts in `exports/charts/`.
- Answer `y` to view instant ASCII bar charts directly in the terminal console.

### Step 7: Test Bulk CSV Import with Error Logger (Option 9)
- Select `9` in the menu.
- Press Enter to accept the bundled test file: `data/sample_legacy_import.csv`.
- **Outcome:**
  - Evaluated: 9 rows.
  - Successfully Imported: 5 valid students.
  - Skipped: 4 erroneous rows (bad email, invalid phone, non-existent event, blank name).
  - Detailed error trail logged to `exports/import_errors.log`.

### Step 8: Prove Data Persistence Across Restarts
- Select `0` to cleanly exit the application.
- Observe: State saved cleanly to disk with session audit entry.
- Relaunch the application:
  ```powershell
  python main.py
  ```
- Select `1` (View All Events): Confirm all previously registered students, updated statuses, and imports are fully preserved.

### Step 9: Launch Optional Tkinter Desktop GUI (Option 11 or Flag)
- Run:
  ```powershell
  python main.py --gui
  ```
- Explore the interactive visual desktop view:
  - Tab 1: Live event capacity progress & attendee rosters.
  - Tab 2: Searchable participant table with instant filters by department and status.
  - Tab 3: KPI summary cards and one-click chart/report exporters.
  - Tab 4: Active threshold alerts and anomaly monitor.
  - Tab 5: Bulk CSV file picker and batch import log viewer.

---

## 6. Sample Datasets Included

The application ships with realistic data in `data/` and `seed_data.py`:

| Event ID | Event Title | Category | Capacity | Status / Highlight |
| :--- | :--- | :--- | :---: | :--- |
| **EVT-101** | HackCampus 2026: AI & Cloud Hackathon | Technical | 15 | **93.3% Full** (`[WARNING]` Capacity Threshold) |
| **EVT-102** | National Collegiate Robotics Challenge | Technical | 10 | **100% Full** (`[CRITICAL]` Sold Out + Waitlisted student) |
| **EVT-103** | Campus Symphony: Battle of the Bands | Cultural | 30 | Free Entry, 6 Confirmed, 1 Cancelled |
| **EVT-104** | Inter-Department Badminton Championship | Sports | 16 | **Deadline Tomorrow** (`[WARNING]` Imminent Deadline) |
| **EVT-105** | Cloud DevOps & Kubernetes Workshop | Workshop | 20 | **Deadline Expired** (`[ALERT]` Unpaid participant anomaly) |
| **EVT-106** | Venture Spark: Startup Pitch Deck Summit | Seminar | 40 | Free Entry, 5 Confirmed across MBA & Biotech |

---

## 7. Command-Line Arguments Reference

| Flag | Description | Example |
| :--- | :--- | :--- |
| *(None)* | Starts interactive full terminal CLI application | `python main.py` |
| `--gui` | Launches Tkinter desktop graphical interface | `python main.py --gui` |
| `--seed` | Resets and seeds 44 realistic records into database | `python main.py --seed` |
| `--charts` | Headless generation of all 3 Matplotlib PNG charts | `python main.py --charts` |
| `--export-summary` | Generates Markdown summary and Master attendee CSV | `python main.py --export-summary` |
| `-h`, `--help` | Displays command line usage and parameter documentation | `python main.py --help` |

---

## 8. Verification & Test Report

All 17 automated tests pass with 100% success rate:

```
Ran 17 tests in 0.392s
OK

[Passed Tests]
  ✔ test_bulk_csv_import_with_error_logging
  ✔ test_capacity_enforcement_and_waitlist
  ✔ test_date_validation
  ✔ test_duplicate_registration_prevention
  ✔ test_email_validation
  ✔ test_event_model_and_deadlines
  ✔ test_executive_summary_aggregation
  ✔ test_exports_csv_and_markdown
  ✔ test_phone_validation
  ✔ test_registration_cancellation
  ✔ test_registration_model
  ✔ test_roll_number_validation
  ✔ test_row_validator
  ✔ test_search_and_filtering
  ✔ test_storage_corruption_recovery
  ✔ test_storage_dual_sync
  ✔ test_threshold_warnings
```

---

*Designed and Developed for Campus Catalyst — Education & Student Life Domain.*
