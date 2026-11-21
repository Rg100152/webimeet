"""Page routes: lobby, theater room, host studio, RSVP, ticket and certificate."""

import random
import re
import string
from datetime import datetime, timezone

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from db import execute, fetch_all, fetch_one
from qrcode import qr_svg

webinar_bp = Blueprint("webinar", __name__)


def _new_ticket_code():
    """Generate a short, human-friendly, unique ticket code."""
    year = datetime.now(timezone.utc).year
    while True:
        suffix = "".join(random.choices(string.digits, k=4))
        code = f"WM-{year}-{suffix}"
        if fetch_one("SELECT 1 FROM registrations WHERE ticket_code = ?", (code,)) is None:
            return code


@webinar_bp.get("/")
@webinar_bp.get("/lobby")
def lobby():
    webinars = fetch_all("SELECT * FROM webinars ORDER BY id DESC")
    live = [w for w in webinars if w["mode"] == "live"]
    recorded = [w for w in webinars if w["mode"] == "recorded"]
    featured = live[0] if live else (webinars[0] if webinars else None)

    stats = {
        "live": len(live),
        "recorded": len(recorded),
        "watching": sum(w["attendees"] for w in live),
    }
    return render_template(
        "index.html",
        webinars=webinars,
        live=live,
        recorded=recorded,
        featured=featured,
        stats=stats,
        active_page="lobby",
    )


@webinar_bp.get("/room/<int:webinar_id>")
def room(webinar_id):
    webinar = fetch_one("SELECT * FROM webinars WHERE id = ?", (webinar_id,))
    if webinar is None:
        abort(404)

    ticket_code = request.args.get("ticket", "").strip().upper()
    registration = None
    if ticket_code:
        registration = fetch_one(
            "SELECT * FROM registrations WHERE ticket_code = ? AND webinar_id = ?",
            (ticket_code, webinar_id),
        )
        if registration is not None and registration["status"] != "ATTENDED":
            execute(
                "UPDATE registrations SET status = 'ATTENDED', attended_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), registration["id"]),
            )
            registration = fetch_one("SELECT * FROM registrations WHERE id = ?", (registration["id"],))

    messages = fetch_all(
        """SELECT id, name, message, is_question,
                  strftime('%H:%M', created_at) AS time_label
           FROM chat_messages
           WHERE webinar_id = ?
           ORDER BY id DESC LIMIT 60""",
        (webinar_id,),
    )
    return render_template(
        "room.html",
        webinar=webinar,
        registration=registration,
        messages=list(reversed(messages)),
        preview=request.args.get("preview") == "1",
        active_page="room",
    )


@webinar_bp.route("/host", methods=["GET", "POST"])
def host():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        speaker = request.form.get("speaker", "").strip()
        category = request.form.get("category", "").strip()
        mode = request.form.get("mode", "live").strip()
        video_url = request.form.get("video_url", "").strip()
        description = request.form.get("description", "").strip()
        slides_url = request.form.get("slides_url", "").strip()

        if mode not in ("live", "recorded"):
            mode = "live"
        if not title or not speaker:
            flash("Title and speaker name are required.", "error")
            return render_template("host.html", active_page="host")

        if mode == "live" and video_url:
            # Accept either a full Jitsi URL or just a room name.
            if not video_url.startswith("http"):
                video_url = f"https://meet.jit.si/WebiMeet-{video_url}"

        execute(
            """INSERT INTO webinars
               (title, speaker, category, mode, video_url, description, slides_url,
                starts_at, duration, attendees, accent, icon)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                title,
                speaker,
                category or "Technology",
                mode,
                video_url,
                description,
                slides_url,
                request.form.get("starts_at", "Starting soon").strip(),
                request.form.get("duration", "60 min").strip(),
                0,
                request.form.get("accent", "rose").strip(),
                "🎬",
            ),
        )
        flash(f'Webinar "{title}" is live in your studio.', "success")
        return redirect(url_for("webinar.lobby"))

    return render_template("host.html", active_page="host")


@webinar_bp.post("/register")
def register():
    webinar_id = request.form.get("webinar_id", type=int)
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()

    webinar = fetch_one("SELECT id FROM webinars WHERE id = ?", (webinar_id,)) if webinar_id else None
    if webinar is None:
        abort(404)
    if not name or not email or "@" not in email:
        flash("Please enter a valid name and email address.", "error")
        return redirect(url_for("webinar.lobby"))

    ticket_code = _new_ticket_code()
    seat_code = f"SEAT-{random.randint(10, 90)}-{string.ascii_uppercase[random.randint(0, 25)]}{random.randint(10, 99)}"
    execute(
        """INSERT INTO registrations (ticket_code, webinar_id, name, email, seat_code)
           VALUES (?, ?, ?, ?, ?)""",
        (ticket_code, webinar_id, name, email, seat_code),
    )
    return redirect(url_for("webinar.ticket", ticket_code=ticket_code))


@webinar_bp.get("/ticket/<ticket_code>")
def ticket(ticket_code):
    registration = fetch_one(
        """SELECT r.*, w.title, w.speaker, w.mode, w.starts_at, w.duration, w.category
           FROM registrations r JOIN webinars w ON w.id = r.webinar_id
           WHERE r.ticket_code = ?""",
        (ticket_code.upper(),),
    )
    if registration is None:
        abort(404)
    verify_url = f"https://github.com/Rg100152/webimeet/ticket/{registration['ticket_code']}"
    return render_template(
        "ticket.html",
        registration=registration,
        qr_svg=qr_svg(verify_url),
        verify_url=verify_url,
        active_page="ticket",
    )


@webinar_bp.get("/certificate/<ticket_code>")
def certificate(ticket_code):
    registration = fetch_one(
        """SELECT r.*, w.title, w.speaker, w.mode, w.category, w.starts_at
           FROM registrations r JOIN webinars w ON w.id = r.webinar_id
           WHERE r.ticket_code = ?""",
        (ticket_code.upper(),),
    )
    if registration is None:
        abort(404)

    attended = registration["status"] == "ATTENDED"
    verify_hash = re.sub(r"[^A-Z0-9]", "", registration["ticket_code"].upper()) + "-" + str(registration["id"] * 7919)
    verify_url = f"https://github.com/Rg100152/webimeet/certificate/{registration['ticket_code']}"
    return render_template(
        "certificate.html",
        registration=registration,
        attended=attended,
        verify_hash=verify_hash,
        qr_svg=qr_svg(verify_url),
        verify_url=verify_url,
        active_page="certificate",
    )


@webinar_bp.get("/portfolio")
def portfolio():
    return render_template("portfolio.html", active_page="portfolio")
