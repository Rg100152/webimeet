"""Lightweight JSON APIs for incremental chat polling, reactions and attendance."""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from db import execute, fetch_all, fetch_one

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/chat/<int:webinar_id>")
def get_chat(webinar_id):
    """Return only messages/reactions newer than ``after_id``.

    The browser calls this every 2 seconds with the highest id it has seen, so
    payloads stay tiny and no WebSocket server is required (4GB-RAM friendly).
    """
    after_id = request.args.get("after_id", default=0, type=int) or 0

    if fetch_one("SELECT 1 FROM webinars WHERE id = ?", (webinar_id,)) is None:
        return jsonify(error="Webinar not found"), 404

    messages = fetch_all(
        """SELECT id, name, message, is_question,
                  strftime('%H:%M', created_at) AS time_label
           FROM chat_messages
           WHERE webinar_id = ? AND id > ?
           ORDER BY id ASC LIMIT 100""",
        (webinar_id, after_id),
    )
    reactions = fetch_all(
        """SELECT id, emoji FROM reactions
           WHERE webinar_id = ? AND id > ?
           ORDER BY id ASC LIMIT 50""",
        (webinar_id, after_id),
    )
    latest = fetch_one(
        "SELECT MAX(id) AS max_id FROM ("
        "SELECT MAX(id) AS id FROM chat_messages WHERE webinar_id = ? "
        "UNION ALL SELECT MAX(id) AS id FROM reactions WHERE webinar_id = ?)",
        (webinar_id, webinar_id),
    )
    return jsonify(
        messages=[dict(m) for m in messages],
        reactions=[dict(r) for r in reactions],
        max_id=(latest["max_id"] or 0) if latest else 0,
        server_time=datetime.now(timezone.utc).strftime("%H:%M"),
    )


@api_bp.post("/chat/<int:webinar_id>")
def post_chat(webinar_id):
    payload = request.get_json(silent=True) or request.form
    name = str(payload.get("name", "")).strip()[:40]
    message = str(payload.get("message", "")).strip()[:500]
    is_question = 1 if str(payload.get("is_question", "")).lower() in ("1", "true", "on", "yes") else 0

    if fetch_one("SELECT 1 FROM webinars WHERE id = ?", (webinar_id,)) is None:
        return jsonify(error="Webinar not found"), 404
    if not name or not message:
        return jsonify(error="Name and message are required"), 400

    cursor = execute(
        """INSERT INTO chat_messages (webinar_id, name, message, is_question)
           VALUES (?, ?, ?, ?)""",
        (webinar_id, name, message, is_question),
    )
    row = fetch_one(
        """SELECT id, name, message, is_question,
                  strftime('%H:%M', created_at) AS time_label
           FROM chat_messages WHERE id = ?""",
        (cursor.lastrowid,),
    )
    return jsonify(message=dict(row)), 201


@api_bp.post("/reactions/<int:webinar_id>")
def post_reaction(webinar_id):
    payload = request.get_json(silent=True) or request.form
    emoji = str(payload.get("emoji", ""))[:8]
    allowed = {"🔥", "👏", "❤️", "💡", "🎉", "🙌"}
    if emoji not in allowed:
        return jsonify(error="Unsupported reaction"), 400
    if fetch_one("SELECT 1 FROM webinars WHERE id = ?", (webinar_id,)) is None:
        return jsonify(error="Webinar not found"), 404

    cursor = execute(
        "INSERT INTO reactions (webinar_id, emoji) VALUES (?, ?)",
        (webinar_id, emoji),
    )
    return jsonify(id=cursor.lastrowid, emoji=emoji), 201


@api_bp.post("/attend")
def mark_attendance():
    payload = request.get_json(silent=True) or request.form
    ticket_code = str(payload.get("ticket_code", "")).strip().upper()
    registration = fetch_one(
        "SELECT id, status FROM registrations WHERE ticket_code = ?", (ticket_code,)
    )
    if registration is None:
        return jsonify(error="Invalid ticket code"), 404

    if registration["status"] != "ATTENDED":
        execute(
            "UPDATE registrations SET status = 'ATTENDED', attended_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), registration["id"]),
        )
    return jsonify(status="ATTENDED", ticket_code=ticket_code, certificate_unlocked=True)


@api_bp.get("/stats")
def stats():
    row = fetch_one(
        """SELECT
             (SELECT COUNT(*) FROM webinars) AS webinars,
             (SELECT COUNT(*) FROM webinars WHERE mode = 'live') AS live,
             (SELECT COUNT(*) FROM chat_messages) AS messages,
             (SELECT COUNT(*) FROM registrations) AS registrations,
             (SELECT COUNT(*) FROM registrations WHERE status = 'ATTENDED') AS attended"""
    )
    return jsonify(dict(row))
