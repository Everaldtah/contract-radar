"""
Contract date extraction using regex patterns.
Handles common date formats found in legal documents.
"""
import re
from datetime import datetime, date
from typing import Dict, Optional


# Regex patterns for various date formats
DATE_PATTERNS = [
    # January 15, 2025 or Jan 15, 2025
    (r'\b(January|February|March|April|May|June|July|August|September|October|November|December|'
     r'Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s+(\d{4})\b', '%B %d %Y'),
    # 15th day of January, 2025
    (r'\b(\d{1,2})(?:st|nd|rd|th)?\s+day\s+of\s+'
     r'(January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*(\d{4})\b', None),
    # 2025-01-15 (ISO)
    (r'\b(\d{4})-(\d{2})-(\d{2})\b', 'iso'),
    # 01/15/2025 or 1/15/2025
    (r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', 'mdy'),
    # 15.01.2025
    (r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b', 'dmy'),
]

EXPIRY_KEYWORDS = [
    r'(?:expir(?:es?|ation|y)|terminat(?:es?|ion)|end(?:s|ing)?\s+date|expires?\s+on|effective\s+through|valid\s+(?:until|through|to)|term\s+end)',
]

START_KEYWORDS = [
    r'(?:effective\s+(?:date|as\s+of|from)|commenc(?:es?|ing)|start(?:s|ing)?\s+date|begins?\s+on)',
]

MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
}


def _parse_date_match(match, fmt: Optional[str]) -> Optional[date]:
    try:
        groups = match.groups()
        if fmt == 'iso':
            return datetime(int(groups[0]), int(groups[1]), int(groups[2])).date()
        elif fmt == 'mdy':
            return datetime(int(groups[2]), int(groups[0]), int(groups[1])).date()
        elif fmt == 'dmy':
            return datetime(int(groups[2]), int(groups[1]), int(groups[0])).date()
        elif fmt is None:
            # "15th day of January, 2025" pattern
            day = int(groups[0])
            month = MONTH_MAP[groups[1].lower()]
            year = int(groups[2])
            return datetime(year, month, day).date()
        else:
            # Month name formats
            month_str = groups[0].strip('.').lower()[:3]
            month = MONTH_MAP.get(month_str, 0)
            if not month:
                return None
            day = int(groups[1])
            year = int(groups[2])
            return datetime(year, month, day).date()
    except (ValueError, IndexError):
        return None


def _find_dates_near_keyword(text: str, keywords: list) -> list:
    """Find dates that appear within 100 characters of a keyword."""
    found = []
    text_lower = text.lower()

    for kw_pattern in keywords:
        for m in re.finditer(kw_pattern, text_lower, re.IGNORECASE):
            start, end = m.span()
            context = text[max(0, start - 10):end + 120]

            for pattern, fmt in DATE_PATTERNS:
                for dm in re.finditer(pattern, context, re.IGNORECASE):
                    parsed = _parse_date_match(dm, fmt)
                    if parsed and parsed.year >= 2000:
                        found.append(parsed)
    return found


def extract_dates_from_text(text: str) -> Dict[str, Optional[str]]:
    """
    Extract start and end dates from contract text.
    Returns dict with 'start_date', 'end_date', and 'all_dates' keys.
    """
    all_dates = []

    # First pass: find all dates in the document
    for pattern, fmt in DATE_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            parsed = _parse_date_match(m, fmt)
            if parsed and parsed.year >= 2000:
                all_dates.append(parsed)

    all_dates = sorted(set(all_dates))

    # Second pass: look for dates near expiry/start keywords
    expiry_dates = _find_dates_near_keyword(text, EXPIRY_KEYWORDS)
    start_dates = _find_dates_near_keyword(text, START_KEYWORDS)

    end_date = None
    start_date = None

    if expiry_dates:
        # Take the latest expiry date found near expiry keywords
        end_date = max(expiry_dates)
    elif all_dates:
        # Heuristic: latest date in document is likely the end date
        end_date = max(all_dates)

    if start_dates:
        start_date = min(start_dates)
    elif all_dates and len(all_dates) >= 2:
        start_date = min(all_dates)

    return {
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "all_dates_found": [d.isoformat() for d in all_dates],
    }
