# semantic_extractor.py

from datetime import datetime
from nlp.preprocess import preprocess, normalize_text, normalize_semantic
from nlp.entity_extractor import extract_entities
from nlp.event_extractor import extract_event_and_reminder
from nlp.time_parser import parse_time_expression


def parse_user_intent(text: str, now: datetime = None):
    now = now or datetime.now()

    # ============================================
    # STEP 1 — semantic normalize toàn câu
    # ============================================
    norm_text = normalize_semantic(normalize_text(text))

    # ============================================
    # STEP 2 — chạy toàn bộ NLP pipeline trên norm_text
    # ============================================
    tokens = preprocess(norm_text)
    entities = extract_entities(norm_text, tokens)
    event, reminder = extract_event_and_reminder(norm_text)

    try:
        parsed_time = parse_time_expression(
            norm_text,
            now,
            time_candidates=entities["time_candidates"]
        )
    except Exception:
        parsed_time = None

    locations = entities["location_candidates"]

    # ============================================
    # STEP 3 — Build output
    # ============================================
    return {
        "event": event or None,
        "start_time": (
            parsed_time.strftime("%Y-%m-%dT%H:%M:%S")
            if parsed_time else None
        ),
        "end_time": None,
        "location": locations[0] if locations else None,
        "reminder_minutes": reminder or None
    }


# Test nhanh
if __name__ == "__main__":
    sample = "22/12/2026"
    print(parse_user_intent(sample))
