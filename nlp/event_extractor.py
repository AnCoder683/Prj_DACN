# nlp/event_extractor.py — VERSION 6.0 (fixed event + time interference)
import re

REMIND_KEYWORDS = ["nhắc tôi", "remind me", "bảo tôi", "nhắc"]

TIME_WORDS = [
    "lúc", "vào", "khi",
    "sáng", "trưa", "chiều", "tối", "đêm",
    "mai", "mốt", "nay", "kia", "hôm", "ngày", "tuần", "tháng", "năm"
]

LOCATION_MARKERS = ["ở", "tại", "đến"]

REMINDER_PATTERNS = [
    r"trước\s+\d+\s*(phút|p|giờ|h)",
    r"\d+\s*(phút|p|giờ|h)\s*sau"
]

TIME_PATTERNS = [
    r"\b\d{1,2}:\d{2}\b",
    r"\b\d{1,2}h\d{1,2}\b",
    r"\b\d{1,2}h\b",
    r"\b\d{1,2}[/-]\d{1,2}\b",
]

VERB_PREFIXES = [
    "đi", "ăn", "uống", "xem", "chơi", "mua", "gặp",
    "gọi", "làm", "họp", "hẹn", "nhắn", "gửi", "qua",
]


# ==================================================================
# Clean helpers
# ==================================================================
def remove_time_chunks(text):
    # Xóa các pattern dạng 10:30, 10h30, 10h, 12/12...
    for pat in TIME_PATTERNS:
        text = re.sub(pat, " ", text)

    # Xóa cụm dạng "8 giờ"
    text = re.sub(r"\b\d{1,2}\s*giờ\b", " ", text)

    # Xóa từ chỉ buổi/thời gian quá mạnh tay -> giữ lại một số
    for w in TIME_WORDS:
        text = re.sub(rf"\b{w}\b", " ", text)

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def remove_location(text):
    for mk in LOCATION_MARKERS:
        pos = text.find(f" {mk} ")
        if pos != -1:
            return text[:pos].strip()
    return text


# ==================================================================
# MAIN FIXED EVENT EXTRACTOR
# ==================================================================
def extract_event_and_reminder(raw_text: str):
    text = raw_text.lower()

    # --------------------------------------------------------------
    # 1) REMINDER DETECTION
    # --------------------------------------------------------------
    reminder_minutes = None
    for pat in REMINDER_PATTERNS:
        m = re.search(pat, text)
        if m:
            num = int(re.search(r"\d+", m.group()).group())
            unit = m.group(1)
            reminder_minutes = num * 60 if unit in ["giờ", "h"] else num
            break

    # --------------------------------------------------------------
    # 2) CHECK "NHẮC TÔI"
    # --------------------------------------------------------------
    pos = None
    key = None
    for kw in REMIND_KEYWORDS:
        p = text.find(kw)
        if p != -1 and (pos is None or p < pos):
            pos = p
            key = kw

    # ==============================================================  
    # CASE A — CÓ KEYWORD “NHẮC”
    # ==============================================================  
    if pos is not None:
        before = text[:pos].strip()
        before_clean = remove_location(remove_time_chunks(before))
        if before_clean:
            return before_clean, reminder_minutes

        after = text[pos + len(key):].strip()

        for pat in REMINDER_PATTERNS:
            after = re.sub(pat, "", after)

        after = remove_location(remove_time_chunks(after))

        if after:
            return after, reminder_minutes

        return None, reminder_minutes

    # ==================================================================
    # CASE B — KHÔNG CÓ “NHẮC”: AUTO DETECT EVENT (đã fix)
    # ==================================================================

    tokens = text.split()
    event_tokens = []
    found_verb = False

    for w in tokens:

        # ----------------------------------------------
        # 1) Tìm V (động từ bắt đầu event)
        # ----------------------------------------------
        if not found_verb:
            if w in VERB_PREFIXES:
                found_verb = True
                event_tokens.append(w)
            continue

        # ----------------------------------------------
        # 2) Nếu đã vào event rồi → cần quyết định dừng hay tiếp tục
        # ----------------------------------------------

        # STOP nếu token là giờ (10h, 8h30, 7 giờ)
        if re.match(r"\d{1,2}h\d*", w) or re.match(r"\d{1,2}\s*giờ", w):
            break

        # STOP nếu là ngày/tháng thật
        if re.match(r"\d{1,2}[/-]\d{1,2}", w):
            break

        # STOP khi TIME_WORD thật sự kết thúc event
        if w in TIME_WORDS:
            # Các period có thể nằm trong event nếu đứng liền sau động từ (ăn tối)
            if w in ["sáng", "trưa", "chiều", "tối", "đêm"]:
                # Nếu event đang dạng "ăn tối ..." -> CHO QUA
                if len(event_tokens) == 1:
                    event_tokens.append(w)
                    continue
                # Sau đó mà gặp buổi nữa thì stop
                else:
                    break
            break

        # STOP nếu thấy location marker → event kết thúc
        if w in LOCATION_MARKERS:
            break

        # ----------------------------------------------
        # 3) Token hợp lệ của event → append
        # ----------------------------------------------
        event_tokens.append(w)

    event = " ".join(event_tokens).strip()
    return (event or None), reminder_minutes
