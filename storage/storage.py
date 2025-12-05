import sqlite3

DB_PATH = "events.db"


# ==========================================================
# KẾT NỐI DB
# ==========================================================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ==========================================================
# TẠO BẢNG
# ==========================================================
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            location TEXT,
            reminder_minutes INTEGER DEFAULT 0,
            reminded INTEGER DEFAULT 0,
            complete INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


# ==========================================================
# UTIL: CHUẨN HÓA TIME
# ==========================================================
def normalize_time(value):
    if not value:
        return None
    return value.replace("T", " ").strip()


# ==========================================================
# THÊM SỰ KIỆN
# ==========================================================
def insert_event(data):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO events (event, start_time, end_time, location, reminder_minutes)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["event"],
        normalize_time(data["start_time"]),
        normalize_time(data.get("end_time")),
        data.get("location"),
        int(data.get("reminder_minutes") or 0),
    ))

    conn.commit()
    conn.close()


# ==========================================================
# LẤY EVENT (UI)
# ==========================================================
def get_upcoming_events():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, event, start_time, reminder_minutes, location, complete, reminded
        FROM events
        ORDER BY datetime(start_time) ASC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


# ==========================================================
# XÓA
# ==========================================================
def delete_event(event_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()


# ==========================================================
# SỬA SỰ KIỆN
# ==========================================================
def update_event(event_id, data):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE events
        SET event = ?, start_time = ?, end_time = ?, location = ?, reminder_minutes = ?, reminded = 0
        WHERE id = ?
    """, (
        data["event"],
        normalize_time(data["start_time"]),
        normalize_time(data.get("end_time")),
        data.get("location"),
        int(data.get("reminder_minutes") or 0),
        event_id,
    ))

    conn.commit()
    conn.close()


# ==========================================================
# UPDATE reminded
# ==========================================================
def set_reminded(event_id, value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE events SET reminded = ? WHERE id = ?", (int(value), event_id))
    conn.commit()
    conn.close()


# ==========================================================
# UPDATE complete
# ==========================================================
def set_complete(event_id, value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE events SET complete = ? WHERE id = ?", (int(value), event_id))
    conn.commit()
    conn.close()
