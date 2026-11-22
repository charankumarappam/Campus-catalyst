"""
ui.py
Terminal UI utilities, ANSI color styling, fixed-width tabular formatting,
pagination breaks, and branded presentation for
Campus Catalyst: College Event Registration Manager (Project #8).
"""

from __future__ import annotations
import os
import sys
from typing import List, Dict, Any, Optional

# Enable Virtual Terminal sequences on Windows 10/11 consoles
if os.name == "nt":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        h_stdout = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(h_stdout, ctypes.byref(mode))
        mode.value |= 4  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        kernel32.SetConsoleMode(h_stdout, mode)
    except Exception:
        # Fallback to os.system invocation
        os.system("")


class Colors:
    """ANSI color codes for rich terminal styling."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # Regular Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright / Bold Colors
    B_RED = "\033[91m"
    B_GREEN = "\033[92m"
    B_YELLOW = "\033[93m"
    B_BLUE = "\033[94m"
    B_MAGENTA = "\033[95m"
    B_CYAN = "\033[96m"
    B_WHITE = "\033[97m"

    # Background Colors
    BG_BLUE = "\033[44m"
    BG_DARK = "\033[40m"


def colorize(text: str, color_code: str) -> str:
    """Wraps text in ANSI color sequence with automatic reset."""
    return f"{color_code}{text}{Colors.RESET}"


def print_banner() -> None:
    """Renders the branded Campus Catalyst ASCII welcome banner."""
    banner = f"""{Colors.B_CYAN}{Colors.BOLD}
  ╔══════════════════════════════════════════════════════════════════════════════════╗
  ║                🎓 CAMPUS CATALYST: COLLEGE EVENT REGISTRATION                    ║
  ║                   Project #8 | Domain: Education & Student Life                  ║
  ║               Offline-First • Defensive Validation • Real-Time KPIs              ║
  ╚══════════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}"""
    print(banner)


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """Prints a styled section header."""
    print(f"\n{Colors.B_BLUE}{Colors.BOLD}===[ {title.upper()} ]==={Colors.RESET}")
    if subtitle:
        print(f"{Colors.DIM} {subtitle}{Colors.RESET}")
    print()


def print_status(msg: str, status_type: str = "INFO") -> None:
    """Prints a badge-tagged status line."""
    badges = {
        "SUCCESS": f"{Colors.B_GREEN}[SUCCESS]{Colors.RESET}",
        "INFO": f"{Colors.B_CYAN}[INFO]{Colors.RESET}",
        "WARNING": f"{Colors.B_YELLOW}[WARNING]{Colors.RESET}",
        "CRITICAL": f"{Colors.B_RED}{Colors.BOLD}[CRITICAL]{Colors.RESET}",
        "ALERT": f"{Colors.B_RED}[ALERT]{Colors.RESET}",
    }
    badge = badges.get(status_type.upper(), f"[{status_type}]")
    print(f" {badge} {msg}")


def print_divider(char: str = "─", length: int = 84) -> None:
    """Prints a clean horizontal dividing line."""
    print(f"{Colors.DIM}{char * length}{Colors.RESET}")


def render_table(
    headers: List[str],
    rows: List[List[Any]],
    col_widths: Optional[List[int]] = None,
    page_size: int = 12
) -> None:
    """
    Renders clean, fixed-width tabular data with column separators
    and automated pagination breaks for large datasets.
    """
    if not rows:
        print(f"{Colors.YELLOW} [!] No records to display.{Colors.RESET}")
        return

    num_cols = len(headers)

    # Compute optimal column widths if not specified
    if not col_widths or len(col_widths) != num_cols:
        col_widths = []
        for i in range(num_cols):
            max_w = len(str(headers[i]))
            for r in rows:
                if i < len(r):
                    max_w = max(max_w, len(str(r[i])))
            col_widths.append(min(max_w + 2, 35))  # Cap column width at 35

    # Build borders
    top_border = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    sep_border = "+" + "+".join("=" * (w + 2) for w in col_widths) + "+"
    mid_border = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    total_rows = len(rows)
    total_pages = (total_rows + page_size - 1) // page_size

    current_idx = 0
    page_num = 1

    while current_idx < total_rows:
        page_rows = rows[current_idx : current_idx + page_size]

        print(f"\n{Colors.DIM}{top_border}{Colors.RESET}")

        # Render Header
        header_cells = []
        for i, h in enumerate(headers):
            w = col_widths[i]
            header_cells.append(f" {h[:w]:<{w}} ")
        print(f"{Colors.BOLD}|" + "|".join(header_cells) + f"|{Colors.RESET}")
        print(f"{Colors.B_CYAN}{sep_border}{Colors.RESET}")

        # Render Data Rows
        for row in page_rows:
            row_cells = []
            for i, val in enumerate(row):
                w = col_widths[i]
                val_str = str(val) if val is not None else ""
                # Status color coding
                if val_str in ("Confirmed", "Completed", "Attended"):
                    val_colored = f"{Colors.GREEN}{val_str[:w]:<{w}}{Colors.RESET}"
                elif val_str in ("Pending", "Pending Payment", "Waitlisted"):
                    val_colored = f"{Colors.YELLOW}{val_str[:w]:<{w}}{Colors.RESET}"
                elif val_str in ("Cancelled", "Absent", "CRITICAL"):
                    val_colored = f"{Colors.RED}{val_str[:w]:<{w}}{Colors.RESET}"
                else:
                    val_colored = f"{val_str[:w]:<{w}}"

                row_cells.append(f" {val_colored} ")
            print("|" + "|".join(row_cells) + "|")

        print(f"{Colors.DIM}{mid_border}{Colors.RESET}")

        current_idx += page_size

        if current_idx < total_rows:
            prompt_str = f" {Colors.B_CYAN}[Page {page_num}/{total_pages} - Showing {current_idx} of {total_rows} rows] Press Enter for next page, or 'q' to stop: {Colors.RESET}"
            try:
                user_choice = input(prompt_str).strip().lower()
                if user_choice == "q":
                    print(f" {Colors.DIM}Pagination stopped.{Colors.RESET}")
                    break
            except (KeyboardInterrupt, EOFError):
                print()
                break
            page_num += 1


def render_kpi_card(title: str, value: Any, subtitle: str = "", color: str = Colors.B_WHITE) -> None:
    """Renders a visual metric highlight box."""
    val_str = str(value)
    w = max(len(title), len(val_str), len(subtitle)) + 4
    box_top = f"┌{'─' * w}┐"
    box_bot = f"└{'─' * w}┘"

    print(f" {Colors.DIM}{box_top}{Colors.RESET}")
    print(f" │ {Colors.CYAN}{title:<{w-2}}{Colors.RESET} │")
    print(f" │ {Colors.BOLD}{color}{val_str:<{w-2}}{Colors.RESET} │")
    if subtitle:
        print(f" │ {Colors.DIM}{subtitle:<{w-2}}{Colors.RESET} │")
    print(f" {Colors.DIM}{box_bot}{Colors.RESET}")
