from datetime import datetime, timedelta
import re
import unicodedata


# ===========================================================
# Helper
# ===========================================================
def strip_accents(s: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )


# ===========================================================
# 1) PARSE HOUR/MINUTE FROM SINGLE CANDIDATE
# ===========================================================
def parse_hour_minute(text: str):
    clean = text.lower()

    # 1) 11:30pm / 11:30 pm / 11:30
    m = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', clean)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        ampm = m.group(3)

        if ampm == "pm" and hour != 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0

        return hour, minute

    # 2) 11h30
    m = re.search(r'(\d{1,2})h(\d{1,2})', clean)
    if m:
        return int(m.group(1)), int(m.group(2))

    # 3) 11 giờ 30
    m = re.search(r'(\d{1,2})\s*giờ\s*(\d{1,2})', clean)
    if m:
        return int(m.group(1)), int(m.group(2))

    # 4) 11h
    m = re.search(r'(\d{1,2})h(?!\d)', clean)
    if m:
        return int(m.group(1)), 0

    # 5) 11 giờ
    m = re.search(r'(\d{1,2})\s*giờ(?!\s*\d)', clean)
    if m:
        return int(m.group(1)), 0

    return None, None


# ===========================================================
# 2) PERIOD
# ===========================================================
def parse_period(text: str):
    t = text.lower()
    if "sáng" in t:
        return "morning"
    if "trưa" in t:
        return "noon"
    if "chiều" in t:
        return "afternoon"
    if "tối" in t or "đêm" in t:
        return "evening"
    return None


# ===========================================================
# 3) RELATIVE DATE
# ===========================================================
def parse_relative_date(text: str, now: datetime):
    t = text.lower()

    if "mai" in t:
        return now.date() + timedelta(days=1)
    if "mốt" in t:
        return now.date() + timedelta(days=2)
    if "ngày kia" in t:
        return now.date() + timedelta(days=2)
    if "hôm nay" in t or t.strip() == "nay":
        return now.date()
    if "hôm sau" in t:
        return now.date() + timedelta(days=1)

    return None


# ===========================================================
# 4) ABSOLUTE DATE
# ===========================================================
def parse_absolute_date(text: str, now: datetime):
    t = text.lower()

    # dd/mm/yyyy
    m = re.search(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b', t)
    if m:
        d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        return datetime(y, mth, d).date()

    # dd/mm
    m = re.search(r'\b(\d{1,2})[/-](\d{1,2})\b', t)
    if m:
        d, mth = int(m.group(1)), int(m.group(2))
        return datetime(now.year, mth, d).date()

    # ngày dd tháng mm (năm optional)
    m = re.search(
        r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})(?:\s+năm\s+(\d{2,4}))?',
        t
    )
    if m:
        d, mth = int(m.group(1)), int(m.group(2))
        y = int(m.group(3)) if m.group(3) else now.year
        if y < 100:
            y += 2000
        return datetime(y, mth, d).date()

    return None


# ===========================================================
# 5) WEEKDAY + TUẦN
# ===========================================================
VN_WEEKDAY = {
    "thứ hai": 0, "thứ 2": 0,
    "thứ ba": 1, "thứ 3": 1,
    "thứ tư": 2, "thứ 4": 2,
    "thứ năm": 3, "thứ 5": 3,
    "thứ sáu": 4, "thứ 6": 4,
    "thứ bảy": 5, "thứ 7": 5,
    "chủ nhật": 6
}


def parse_weekday(text: str, now: datetime):
    raw = text.lower()
    norm = strip_accents(raw)

    weekday_idx = None
    for label, idx in VN_WEEKDAY.items():
        if strip_accents(label) in norm:
            weekday_idx = idx
            break

    if weekday_idx is None:
        return None

    next_week = "tuần sau" in raw or "tuần tới" in raw
    this_week = "tuần này" in raw

    if next_week:
        base = now.date() - timedelta(days=now.weekday()) + timedelta(days=7)
        return base + timedelta(days=weekday_idx)

    if this_week:
        base = now.date() - timedelta(days=now.weekday())
        return base + timedelta(days=weekday_idx)

    diff = weekday_idx - now.weekday()
    if diff <= 0:
        diff += 7
    return now.date() + timedelta(days=diff)


# ===========================================================
# 6) MAIN: PURE time_candidates PARSER
# ===========================================================
def parse_time_expression(raw_text: str, now: datetime, time_candidates=None):
    if not time_candidates:
        time_candidates = []

    date = None
    period = None
    hour = None
    minute = None

    # ---- STEP 1: scan candidates ----
    for t in time_candidates:

        # hour/minute
        h, m = parse_hour_minute(t)
        if h is not None:
            hour, minute = h, m

        # period
        p = parse_period(t)
        if p and period is None:
            period = p

        # absolute date
        d_abs = parse_absolute_date(t, now)
        if d_abs:
            date = d_abs

        # relative date
        d_rel = parse_relative_date(t, now)
        if d_rel and date is None:
            date = d_rel

        # weekday
        d_wd = parse_weekday(t, now)
        if d_wd and date is None:
            date = d_wd

    # ---- STEP 2: default date ----
    if date is None:
        date = now.date()

    # ---- STEP 3: infer / adjust hour ----
    if hour is None:
        # Không có giờ cụ thể → dùng period
        if period == "morning":
            hour, minute = 8, 0
        elif period == "noon":
            hour, minute = 12, 0
        elif period == "afternoon":
            hour, minute = 15, 0
        elif period == "evening":
            hour, minute = 19, 0
        else:
            hour, minute = 9, 0
    else:
        # Có giờ cụ thể nhưng có PERIOD chiều / tối → đẩy lên PM nếu cần
        if period in ["afternoon", "evening"] and 1 <= hour <= 11:
            hour += 12

    return datetime(date.year, date.month, date.day, hour, minute)
