import re
from underthesea import word_tokenize


# ================================
# SEMANTIC NORMALIZATION LAYER
# ================================

ABBREVIATIONS = {
    "vs": "với",
    "hp": "họp",
    "mn": "mọi người",
    "tk": "tài khoản",
    "ad": "admin",
    "ny": "người yêu",
    "dg": "đang",
    "bt": "bình thường",
    "bn": "bạn",
}

NO_ACCENT_MAP = {
    "me": "mẹ",
    "bo": "bố",
    "di": "đi",
    "an": "ăn",
    "nha": "nhé",
    "ok": "oke",
}


def normalize_semantic(text: str) -> str:
    tokens = text.split()
    result = []

    for t in tokens:
        if t in ABBREVIATIONS:
            result.append(ABBREVIATIONS[t])
            continue
        if t in NO_ACCENT_MAP:
            result.append(NO_ACCENT_MAP[t])
            continue
        result.append(t)

    return " ".join(result)



# ========================
# COMPONENT 1: PREPROCESS
# ========================

def normalize_text(text: str) -> str:
    """
    1. Lowercase
    2. Giữ lại Unicode tiếng Việt
    3. GIỮ LẠI ký tự / và - để parse ngày
    4. Chuẩn hóa '7 h' -> '7h'
    """
    text = text.lower().strip()

    # GIỮ: số, chữ, tiếng Việt, :, /, -
    text = re.sub(r"[^0-9a-zA-ZÀ-ỹ:/\-\s]", " ", text)

    # Remove duplicate punctuation
    text = re.sub(r"/+", "/", text)
    text = re.sub(r"-+", "-", text)

    # chuẩn hóa 7 h -> 7h
    text = re.sub(r"(\d+)\s*h\b", r"\1h", text)

    # chuẩn hóa 10 : 30 -> 10:30
    text = re.sub(r"(\d+)\s*:\s*(\d+)", r"\1:\2", text)

    text = re.sub(r"\s+", " ", text).strip()
    return text



def tokenize(text: str):
    """
    Underthesea tokenizer
    """
    segmented = word_tokenize(text, format="text")
    tokens = segmented.split()
    return tokens



# =============================================
# FIX 1 — TÁCH TOKEN DẠNG A_nhắc, B_gọi, a_đi
# =============================================

def fix_underscored_glue(tokens):
    fixed = []
    for tok in tokens:
        if "_" in tok:
            parts = tok.split("_")
            if len(parts) == 2 and len(parts[0]) <= 2:
                fixed.extend(parts)
                continue
        fixed.append(tok)
    return fixed



# =============================================
# FIX 2 — TÁCH GIỜ: "10:30" → ["10", ":", "30"]
# =============================================

def fix_colon_tokens(tokens):
    result = []
    for tok in tokens:
        if ":" in tok and tok != ":":
            parts = tok.split(":")
            if len(parts) == 2 and all(x.isdigit() for x in parts if x != ""):
                result.extend([parts[0], ":", parts[1]])
                continue
        result.append(tok)
    return result



# =============================================
# FIX 3 — MERGE TIME TOKENS (7 h → 7h)
# =============================================

def merge_time_tokens(tokens):
    result = []
    i = 0

    while i < len(tokens):
        tok = tokens[i]

        if tok.isdigit() and i + 1 < len(tokens):
            nxt = tokens[i+1]

            if nxt == "h":
                result.append(tok + "h")
                i += 2
                continue

            if nxt.startswith("h") and nxt[1:].isdigit():
                result.append(tok + nxt)
                i += 2
                continue

        result.append(tok)
        i += 1

    return result



# =============================================
# FIX 4 — REMOVE EMPTY / NOISE TOKEN
# =============================================

def clean_noise(tokens):
    cleaned = []
    for t in tokens:
        if t.strip() == "":
            continue
        cleaned.append(t)
    return cleaned



# =============================================
# MAIN PIPELINE
# =============================================

def preprocess(text: str):
    """
    1. normalize_text (GIỮ / và -)
    2. semantic normalize
    3. tokenize
    4. fix underthesea bugs
    5. fix colon tokens
    6. merge time tokens
    7. clean noise
    """
    cleaned = normalize_text(text)

    # Thay từ viết tắt – sau normalize_text mới an toàn
    cleaned = normalize_semantic(cleaned)

    tokens = tokenize(cleaned)
    tokens = fix_underscored_glue(tokens)
    tokens = fix_colon_tokens(tokens)
    tokens = merge_time_tokens(tokens)
    tokens = clean_noise(tokens)

    return tokens
