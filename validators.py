"""
validators.py
Centralized defensive input validation routines and boundary checks for
Campus Catalyst: College Event Registration Manager (Project #8).
"""

from __future__ import annotations
import re
from datetime import datetime, date
from typing import Optional, List, Tuple, Any


class UserCancelledException(Exception):
    """Raised when the user enters 'q', 'cancel', or issues Ctrl+C / EOF to abort a prompt."""
    pass


# Regular expressions for strict validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^[6-9]\d{9}$")  # Standard Indian 10-digit mobile number format
PHONE_GENERAL_REGEX = re.compile(r"^\d{10}$")  # General 10-digit numeric
ROLL_NO_REGEX = re.compile(r"^[A-Za-z0-9\-_]{4,15}$")  # Alphanumeric roll number (e.g. 21CS042, CS-2026-01)


def prompt_safe(prompt_text: str, default: Optional[str] = None, allow_cancel: bool = True) -> str:
    """
    Safely prompts user for input, catching KeyboardInterrupt and EOFError.
    If allow_cancel is True, typing ':q' or 'cancel' raises UserCancelledException.
    """
    default_str = f" [{default}]" if default is not None else ""
    full_prompt = f"{prompt_text}{default_str}: "

    try:
        user_input = input(full_prompt).strip()
    except (KeyboardInterrupt, EOFError):
        print("\n[Operation cancelled by user]")
        raise UserCancelledException("Prompt aborted via terminal interrupt.")

    if not user_input and default is not None:
        return str(default).strip()

    if allow_cancel and user_input.lower() in (":q", "cancel", "abort"):
        raise UserCancelledException("Prompt aborted by user command.")

    return user_input


def validate_string(
    prompt: str,
    field_name: str = "Input",
    min_len: int = 1,
    max_len: int = 120,
    allow_empty: bool = False,
    default: Optional[str] = None
) -> str:
    """Loops defensively until user provides a non-empty, length-valid string."""
    while True:
        try:
            val = prompt_safe(prompt, default=default)
        except UserCancelledException:
            raise

        if not val:
            if allow_empty:
                return ""
            print(f" [ERROR] {field_name} cannot be blank. Please try again.")
            continue

        if len(val) < min_len:
            print(f" [ERROR] {field_name} must be at least {min_len} character(s) long.")
            continue

        if len(val) > max_len:
            print(f" [ERROR] {field_name} cannot exceed {max_len} characters (currently {len(val)}).")
            continue

        return val


def is_valid_email(email_str: str) -> bool:
    """Validates email format using regex."""
    if not email_str:
        return False
    return bool(EMAIL_REGEX.match(email_str.strip()))


def prompt_email(prompt: str = "Enter Student Email", default: Optional[str] = None) -> str:
    """Prompts and defensively validates standard email syntax."""
    while True:
        raw = prompt_safe(prompt, default=default)
        if not raw and default:
            raw = default
        if is_valid_email(raw):
            return raw.lower()
        print(f" [ERROR] Invalid email address '{raw}'. Expected format: name@campus.edu or user@domain.com")


def clean_phone(phone_str: str) -> str:
    """Strips non-digit characters (+91, spaces, dashes) and returns 10-digit number."""
    digits = re.sub(r"\D", "", phone_str)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits


def is_valid_phone(phone_str: str) -> bool:
    """Checks if phone string represents a valid 10-digit mobile number."""
    digits = clean_phone(phone_str)
    return len(digits) == 10 and digits.isdigit()


def prompt_phone(prompt: str = "Enter 10-digit Phone Number", default: Optional[str] = None) -> str:
    """Prompts and validates 10-digit mobile number."""
    while True:
        raw = prompt_safe(prompt, default=default)
        cleaned = clean_phone(raw)
        if is_valid_phone(cleaned):
            return cleaned
        print(f" [ERROR] Invalid phone number '{raw}'. Please enter a valid 10-digit phone number.")


def is_valid_roll_number(roll_str: str) -> bool:
    """Validates student roll number format."""
    if not roll_str:
        return False
    return bool(ROLL_NO_REGEX.match(roll_str.strip()))


def prompt_roll_number(prompt: str = "Enter Student Roll Number (e.g., 22CS104)", default: Optional[str] = None) -> str:
    """Prompts and validates student roll number."""
    while True:
        raw = prompt_safe(prompt, default=default)
        raw_upper = raw.strip().upper()
        if is_valid_roll_number(raw_upper):
            return raw_upper
        print(f" [ERROR] Invalid roll number '{raw}'. Must be 4-15 alphanumeric characters (e.g., 22CS104, IT-2026-05).")


def is_valid_date(date_str: str) -> Tuple[bool, Optional[date], str]:
    """Validates ISO YYYY-MM-DD date."""
    if not date_str:
        return False, None, "Date cannot be empty."
    try:
        parsed = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        return True, parsed, ""
    except ValueError:
        return False, None, "Format must be YYYY-MM-DD (e.g., 2026-12-15)."


def prompt_date(
    prompt: str = "Enter Date (YYYY-MM-DD)",
    min_date: Optional[date] = None,
    default: Optional[str] = None
) -> str:
    """Prompts and validates an ISO calendar date with optional lower bound check."""
    while True:
        raw = prompt_safe(prompt, default=default)
        valid, parsed_date, err = is_valid_date(raw)
        if not valid:
            print(f" [ERROR] {err}")
            continue

        if min_date and parsed_date and parsed_date < min_date:
            print(f" [ERROR] Date cannot be prior to {min_date.strftime('%Y-%m-%d')}.")
            continue

        return raw.strip()


def prompt_int(
    prompt: str,
    field_name: str = "Integer Value",
    min_val: Optional[int] = None,
    max_val: Optional[int] = None,
    default: Optional[int] = None
) -> int:
    """Prompts and defensive validates an integer within boundary limits."""
    while True:
        raw = prompt_safe(prompt, default=str(default) if default is not None else None)
        try:
            val = int(raw)
        except ValueError:
            print(f" [ERROR] {field_name} must be a valid whole number.")
            continue

        if min_val is not None and val < min_val:
            print(f" [ERROR] {field_name} cannot be less than {min_val}.")
            continue
        if max_val is not None and val > max_val:
            print(f" [ERROR] {field_name} cannot exceed {max_val}.")
            continue

        return val


def prompt_float(
    prompt: str,
    field_name: str = "Numeric Value",
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    default: Optional[float] = None
) -> float:
    """Prompts and defensive validates a floating-point number within bounds."""
    while True:
        raw = prompt_safe(prompt, default=f"{default:.2f}" if default is not None else None)
        try:
            val = float(raw)
        except ValueError:
            print(f" [ERROR] {field_name} must be a valid decimal number.")
            continue

        if min_val is not None and val < min_val:
            print(f" [ERROR] {field_name} cannot be less than {min_val}.")
            continue
        if max_val is not None and val > max_val:
            print(f" [ERROR] {field_name} cannot exceed {max_val}.")
            continue

        return val


def prompt_choice(
    prompt: str,
    options: List[str],
    case_sensitive: bool = False,
    default: Optional[str] = None
) -> str:
    """Prompts user to select from a predefined list of allowed choices."""
    opts_display = "/".join(options)
    full_prompt = f"{prompt} ({opts_display})"

    # Normalized lookup map
    lookup = {opt if case_sensitive else opt.lower(): opt for opt in options}

    while True:
        raw = prompt_safe(full_prompt, default=default)
        key = raw if case_sensitive else raw.lower()
        if key in lookup:
            return lookup[key]

        print(f" [ERROR] Invalid selection '{raw}'. Allowed options: {', '.join(options)}")


def prompt_menu_option(prompt: str, min_opt: int, max_opt: int) -> int:
    """Prompts for a numeric menu option within [min_opt, max_opt]."""
    return prompt_int(prompt, field_name="Menu Option", min_val=min_opt, max_val=max_opt)


def prompt_year_of_study(prompt: str = "Enter Year of Study (1-5)", default: int = 1) -> int:
    """Prompts and validates academic year of study (1 to 5)."""
    return prompt_int(prompt, field_name="Year of Study", min_val=1, max_val=5, default=default)


# Row Validator for CSV bulk imports
def validate_registration_row(row: dict) -> Tuple[bool, List[str]]:
    """
    Validates a single participant registration record from CSV/dict.
    Returns (is_valid, list_of_error_reasons).
    """
    errors: List[str] = []

    event_id = str(row.get("event_id", "")).strip()
    if not event_id:
        errors.append("Missing event_id")

    name = str(row.get("student_name", "")).strip()
    if not name or len(name) < 2:
        errors.append("Invalid or missing student_name (minimum 2 chars)")

    roll = str(row.get("roll_number", "")).strip()
    if not is_valid_roll_number(roll):
        errors.append(f"Invalid roll_number '{roll}' (expected 4-15 alphanumeric chars)")

    email = str(row.get("email", "")).strip()
    if not is_valid_email(email):
        errors.append(f"Invalid email '{email}'")

    phone = str(row.get("phone", "")).strip()
    if not is_valid_phone(phone):
        errors.append(f"Invalid phone '{phone}' (expected 10 digits)")

    dept = str(row.get("department", "")).strip()
    if not dept:
        errors.append("Missing department")

    try:
        year = int(row.get("year_of_study", 1))
        if year < 1 or year > 5:
            errors.append(f"Year of study '{year}' out of range (1-5)")
    except (ValueError, TypeError):
        errors.append("Year of study must be an integer between 1 and 5")

    return (len(errors) == 0, errors)
