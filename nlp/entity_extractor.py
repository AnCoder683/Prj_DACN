from underthesea import ner
import re, unicodedata


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


# ===========================================================
# HELPER: REMOVE STOP TOKENS (location trimming)
# ===========================================================
STOP_TOKENS = [
    "vào", "lúc", "ngày", "sáng", "trưa", "chiều", "tối", "đêm",
    "mai", "mốt", "nay", "kia", "hôm", "thứ", "tuần", "nhắc", 
]


def cut_tail(chunk: str) -> str:
    parts = chunk.split()
    result = []
    for p in parts:
        if p in STOP_TOKENS:
            break
        result.append(p)
    return " ".join(result)


# ===========================================================
# MAIN FUNCTION
# ===========================================================
def extract_entities(text: str, tokens: list):

    clean = text.lower()

    # =======================================================
    # 1. NER LOCATION
    # =======================================================
    raw_ner = ner(clean)
    ner_loc_raw = []
    for item in raw_ner:
        if isinstance(item, tuple) and len(item) >= 2:
            word, tag = item[0], item[1]
            if "LOC" in tag.upper():
                ner_loc_raw.append((word, tag))

    # =======================================================
    # 2. TIME CANDIDATE EXTRACTION — CHẾ ĐỘ B (TOKEN RỜI)
    # =======================================================
    time_patterns = [

        # ----- HOUR + MINUTE -----
        r"\b\d{1,2}\s*giờ\s*\d{1,2}\b",         
        r"\b\d{1,2}h\d{1,2}\b",                 
        r"\b\d{1,2}:\d{2}\b",                   

        # ----- HOUR ONLY -----
        r"\b\d{1,2}\s*giờ(?!\s*\d)\b",
        r"\b\d{1,2}h\b",

        # ----- PERIOD -----
        r"\bsáng\b",
        r"\btrưa\b",
        r"\bchiều\b",
        r"\btối\b",
        r"\bđêm\b",

        # ----- RELATIVE DATE -----
        r"\bmai\b",
        r"\bmốt\b",
        r"\bnay\b",
        r"\bhôm nay\b",
        r"\bhôm sau\b",
        r"\bngày kia\b",

        # ============================
        #      ABSOLUTE DATE
        # ============================

        # 22/12, 22-12, 22/12/2026, 22-12-2026
        r"\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b",

        # ngày 22/12, ngày 22-12, ngày 22/12/2026
        r"ngày\s*\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?",

        # ngày 22 tháng 12, ngày 22 tháng 12 năm 2026
        r"ngày\s+\d{1,2}\s+tháng\s+\d{1,2}(\s+năm\s+\d{2,4})?",

        # 22 tháng 12, 22 tháng 12 năm 2026
        r"\b\d{1,2}\s*tháng\s*\d{1,2}(\s*năm\s*\d{2,4})?",

        # ----- WEEKDAY -----
        r"thứ\s*\d",
        r"thứ\s+(hai|ba|tư|năm|sáu|bảy)",
        r"(thứ\s+\w+)\s+(tuần\s+(sau|tới|này))",
    ]
    
    time_candidates = []
    for pat in time_patterns:
        for m in re.finditer(pat, clean):
            time_candidates.append(m.group(0).strip())

    # remove duplicates but keep order
    seen = set()
    final_time = []
    for t in time_candidates:
        if t not in seen:
            final_time.append(t)
            seen.add(t)

    time_candidates = final_time

    # =======================================================
    # 3. LOCATION EXTRACTION
    # =======================================================
    def extract_location_v2(text, tokens, ner_raw):
        clean = text.lower()
        loc_candidates = []

        # Merge NER LOC
        chunks = []
        buf = []
        for item in ner_raw:
            w, tag = item[0], item[1]
            if "LOC" in tag.upper():
                buf.append(w)
            else:
                if buf:
                    chunks.append(" ".join(buf))
                    buf = []
        if buf:
            chunks.append(" ".join(buf))

        loc_candidates.extend(chunks)

        # Regex based location
        regex_list = [
            r"\bvăn phòng\s+[a-zA-ZÀ-ỹ0-9 ]+",
            r"\bnhà hàng\s+[a-zA-ZÀ-ỹ0-9 ]+",
            r"\bsiêu thị\s+[a-zA-ZÀ-ỹ0-9 ]+",
            r"\bchung cư\s+[a-zA-ZÀ-ỹ0-9 ]+",
            r"\bquán\s+[a-zA-ZÀ-ỹ0-9 ]+",
            r"\bphòng\s+(?!chi nhánh)[a-zA-ZÀ-ỹ0-9 ]+",
            r"\bcông viên\b",
            r"\bbệnh viện\s+[a-zA-ZÀ-ỹ0-9 ]+",
            r"\btrường\s+[a-zA-ZÀ-ỹ0-9 ]+",
            r"\bnhà\s+[a-zA-ZÀ-ỹ0-9 ]+",
        ]


        for rg in regex_list:
            found = re.findall(rg, clean)
            for f in found:
                loc_candidates.append(cut_tail(f.strip()))

        # Unique
        return list(dict.fromkeys(loc_candidates))

    location_candidates = extract_location_v2(text, tokens, ner_loc_raw)

    # =======================================================
    # 4. OTHER TOKENS
    # =======================================================
    remove = set()

    # remove time tokens from other_tokens
    for t in time_candidates:
        for p in t.split():
            remove.add(p)

    remove.update(["lúc", "vào", "tại", "ở", "ngày"])

    # Build other token list
    other_tokens = []
    for t in tokens:
        p = t.replace("_", " ")
        if p in remove:
            continue
        other_tokens.append(t)

    return {
        "time_candidates": time_candidates,
        "location_candidates": location_candidates,
        "other_tokens": other_tokens
    }
