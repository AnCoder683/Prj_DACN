# main.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import json          

from nlp import parse_user_intent
from storage.storage import (
    init_db,
    insert_event,
    get_upcoming_events,
    delete_event,
    update_event,
    get_conn,
    set_reminded,
    set_complete,
)

app = Flask(__name__)

# ============================================
# INIT DB
# ============================================
init_db()


# ============================================
# INDEX
# ============================================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form.get("text_input", "").strip()
        parsed = parse_user_intent(text, now=datetime.now())

        if parsed["event"] and parsed["start_time"]:
            insert_event(parsed)

        return redirect(url_for("events"))

    return render_template("index.html")


# ============================================
# EVENTS PAGE (FE polling reload HTML)
# ============================================
@app.route("/events")
def events():
    return render_template("events.html", events=get_upcoming_events())


# ============================================
# NLP PARSER API
# ============================================
@app.route("/api/parse", methods=["POST"])
def api_parse():
    data = request.get_json() or {}
    parsed = parse_user_intent(data.get("text", ""), now=datetime.now())
    return parsed


# ============================================
# GET 1 EVENT (popup edit)
# ============================================
@app.route("/api/event/<int:event_id>")
def api_get_event(event_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    r = cur.fetchone()
    conn.close()

    if not r:
        return jsonify({"error": "not_found"}), 404

    return {
        "id": r[0],
        "event": r[1],
        "start_time": r[2],
        "end_time": r[3],
        "location": r[4],
        "reminder_minutes": r[5],
        "reminded": r[6],
        "complete": r[7],
    }


# ============================================
# EDIT EVENT
# ============================================
@app.route("/event/edit/<int:event_id>", methods=["GET", "POST"])
def edit_event_route(event_id):

    if request.method == "POST":
        data = {
            "event": request.form["event"],
            "start_time": request.form["start_time"],
            "end_time": request.form["end_time"] or None,
            "location": request.form["location"],
            "reminder_minutes": int(request.form["reminder_minutes"] or 0),
        }

        update_event(event_id, data)
        return redirect(url_for("events"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = cur.fetchone()
    conn.close()

    return render_template("edit_event.html", event=row)


# ============================================
# DELETE EVENT
# ============================================
@app.route("/event/delete/<int:event_id>")
def delete_event_route(event_id):
    delete_event(event_id)
    return redirect(url_for("events"))


# ============================================
# UPDATE REMINDED (từ polling popup)
# ============================================
@app.route("/api/event/reminded/<int:event_id>", methods=["POST"])
def api_set_reminded(event_id):
    data = request.get_json() or {}
    value = int(data.get("reminded", 0))
    set_reminded(event_id, value)
    return {"status": "ok"}


# ============================================
# UPDATE COMPLETE CHECKBOX
# ============================================
@app.route("/api/event/complete/<int:event_id>", methods=["POST"])
def api_set_complete_route(event_id):
    data = request.get_json() or {}
    value = int(data.get("complete", 0))
    set_complete(event_id, value)
    return {"status": "ok"}


# ============================================
# ADVANCED SEARCH
# ============================================
@app.route("/search-advanced")
def search_advanced():

    keyword    = request.args.get("keyword", "")
    location   = request.args.get("location", "")
    start_date = request.args.get("start_date", "")
    end_date   = request.args.get("end_date", "")

    conn = get_conn()
    cur = conn.cursor()

    query = """
        SELECT id, event, start_time, reminder_minutes, location, complete, reminded
        FROM events
        WHERE 1=1
    """
    params = []

    if keyword:
        query += " AND event LIKE ?"
        params.append(f"%{keyword}%")

    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")

    if start_date and not end_date:
        end_date = start_date

    if start_date:
        query += " AND DATE(start_time) >= DATE(?)"
        params.append(start_date)

    if end_date:
        query += " AND DATE(start_time) <= DATE(?)"
        params.append(end_date)

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return render_template("search_advanced.html", events=rows)

# ============================================
# XPort
# ============================================

@app.route("/export/json")
def export_json():
    rows = get_upcoming_events()

    data = []
    for r in rows:
        data.append({
            "id": r[0],
            "event": r[1],
            "start_time": r[2],
            "reminder_minutes": r[3],
            "location": r[4],
            "complete": r[5],
            "reminded": r[6],
        })

    return jsonify(data)

# ============================================
# IPort
# ============================================

@app.route("/import/json", methods=["POST"])
def import_json():
    file = request.files.get("file")
    if not file:
        return {"status": "error", "message": "No file uploaded"}, 400

    try:
        raw = file.read().decode("utf-8")
        data = json.loads(raw)

        conn = get_conn()
        cur = conn.cursor()

        # XÓA DỮ LIỆU CŨ TRƯỚC
        cur.execute("DELETE FROM events")
        conn.commit()

        # RESET ID TỰ TĂNG
        cur.execute("DELETE FROM sqlite_sequence WHERE name='events'")
        conn.commit()

        # IMPORT DATA MỚI
        for ev in data:
            if "event" not in ev or "start_time" not in ev:
                continue  # skip entry lỗi

            cur.execute("""
                INSERT INTO events (event, start_time, end_time, location,
                                    reminder_minutes, reminded, complete)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                ev.get("event"),
                ev.get("start_time").replace("T", " "),
                ev.get("end_time"),
                ev.get("location"),
                int(ev.get("reminder_minutes") or 0),
                0,  # reset reminded
                int(ev.get("complete") or 0)
            ))

        conn.commit()
        conn.close()

        return {"status": "ok"}

    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


# ============================================
# RUN
# ============================================
if __name__ == "__main__":
    app.run(debug=True)
