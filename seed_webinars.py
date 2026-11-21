"""Seed WebiMeet with 6 realistic webinars, starter chat and demo RSVP tickets.

Idempotent: running it again resets the sample data. Your own data is never
touched unless you explicitly re-run this file.
"""

import os
import sqlite3
from datetime import datetime, timezone

from db import DB_PATH, init_db

WEBINARS = [
    {
        "title": "Python Full-Stack Architecture: From Idea to Production",
        "speaker": "Raj Gautam",
        "category": "Python / Full-Stack",
        "mode": "live",
        "video_url": "https://meet.jit.si/WebiMeet-1",
        "description": "Design scalable Flask + SQLite applications, structure clean blueprints, and ship with confidence.",
        "slides_url": "https://github.com/Rg100152/webimeet#readme",
        "starts_at": "LIVE NOW",
        "duration": "75 min",
        "attendees": 142,
        "accent": "rose",
        "icon": "🐍",
    },
    {
        "title": "Ethical Hacking Live Lab: Reconnaissance to Reporting",
        "speaker": "Raj Gautam",
        "category": "Cybersecurity",
        "mode": "live",
        "video_url": "https://meet.jit.si/WebiMeet-2",
        "description": "A hands-on, legal penetration-testing workflow with live tooling demonstrations and a reporting template.",
        "slides_url": "https://github.com/Rg100152/webimeet#readme",
        "starts_at": "LIVE NOW",
        "duration": "90 min",
        "attendees": 87,
        "accent": "violet",
        "icon": "🛡️",
    },
    {
        "title": "Data Mining Mastery: Turning Raw Data into Decisions",
        "speaker": "Raj Gautam",
        "category": "Data Science",
        "mode": "live",
        "video_url": "https://meet.jit.si/WebiMeet-3",
        "description": "Practical cleaning, pattern discovery and visualization techniques you can apply to any dataset.",
        "slides_url": "https://github.com/Rg100152/webimeet#readme",
        "starts_at": "Starts in 25 min",
        "duration": "60 min",
        "attendees": 56,
        "accent": "emerald",
        "icon": "📊",
    },
    {
        "title": "Modern Web UI/UX: Building Cinematic Dark Interfaces",
        "speaker": "Raj Gautam",
        "category": "Design / Frontend",
        "mode": "recorded",
        "video_url": "https://www.youtube.com/embed/aqz-KE-bpKQ",
        "description": "Layout rhythm, neon accents, glass surfaces and motion that feels premium without heavy libraries.",
        "slides_url": "https://github.com/Rg100152/webimeet#readme",
        "starts_at": "On Demand",
        "duration": "48 min",
        "attendees": 1240,
        "accent": "sky",
        "icon": "🎨",
    },
    {
        "title": "Git & GitHub for Developers: Zero to Confident",
        "speaker": "Raj Gautam",
        "category": "Developer Tools",
        "mode": "recorded",
        "video_url": "https://www.youtube.com/embed/8JJ101D3knE",
        "description": "Branches, pull requests, conflict resolution and the workflow that keeps repositories clean.",
        "slides_url": "https://github.com/Rg100152/webimeet#readme",
        "starts_at": "On Demand",
        "duration": "52 min",
        "attendees": 890,
        "accent": "amber",
        "icon": "🐙",
    },
    {
        "title": "REST API Design Patterns That Actually Scale",
        "speaker": "Raj Gautam",
        "category": "Backend Engineering",
        "mode": "recorded",
        "video_url": "https://www.youtube.com/embed/-Ml2MEdXlCU",
        "description": "Versioning, pagination, incremental polling and caching patterns used in production APIs.",
        "slides_url": "https://github.com/Rg100152/webimeet#readme",
        "starts_at": "On Demand",
        "duration": "41 min",
        "attendees": 613,
        "accent": "ocean",
        "icon": "⚙️",
    },
]

CHAT_SEED = {
    1: [
        ("Aarav", "Good evening everyone! 👋", 0),
        ("Priya", "The architecture diagram is so clean 🔥", 0),
        ("Siddharth", "Raj bhai, blueprint pattern k explanation aur detail me milega kya?", 1),
        ("Neha", "SQLite for 4GB RAM machines — perfect choice", 0),
        ("Karan", "Polling approach is genuinely smarter than WebSockets here 💡", 0),
        ("Ananya", "Can we get the slides link after the session?", 1),
        ("Rohit", "Loving the cinema stage UI 👏", 0),
    ],
    2: [
        ("Dev", "Recon phase starts now?", 1),
        ("Isha", "Good luck everyone 🛡️", 0),
        ("Manav", "Please cover scope boundaries too 🙏", 1),
        ("Tanya", "This lab is amazing 🔥", 0),
    ],
    3: [
        ("Meera", "Dataset k example milenge kya?", 1),
        ("Arjun", "Visualization part best hai 📊", 0),
        ("Sneha", "Joined from Pune! 👋", 0),
    ],
    4: [
        ("Ritika", "That grid rhythm is chef's kiss 👏", 0),
        ("Kabir", "Which font is this?", 1),
        ("Pooja", "Dark theme + rose accent = perfect ❤️", 0),
    ],
    5: [
        ("Nikhil", "Rebase vs merge — final answer please 😄", 1),
        ("Sunita", "Very beginner friendly, thank you!", 0),
    ],
    6: [
        ("Aditya", "after_id polling explained brilliantly 💡", 0),
        ("Deepa", "Pagination example? 🙋", 1),
        ("Vikram", "Bookmarked this session 🔥", 0),
    ],
}


def seed():
    init_db()
    timestamp = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM reactions")
        conn.execute("DELETE FROM chat_messages")
        conn.execute("DELETE FROM registrations")
        conn.execute("DELETE FROM webinars")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('webinars','chat_messages','registrations','reactions')")

        for w in WEBINARS:
            conn.execute(
                """INSERT INTO webinars
                   (title, speaker, category, mode, video_url, description, slides_url,
                    starts_at, duration, attendees, accent, icon)
                   VALUES (:title, :speaker, :category, :mode, :video_url, :description,
                           :slides_url, :starts_at, :duration, :attendees, :accent, :icon)""",
                w,
            )

        for webinar_id, messages in CHAT_SEED.items():
            for offset, (name, message, is_question) in enumerate(messages):
                conn.execute(
                    """INSERT INTO chat_messages
                       (webinar_id, name, message, is_question, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (webinar_id, name, message, is_question,
                     f"{timestamp[:-7]}T{10 + offset // 10:02d}:{(offset * 3) % 60:02d}:00"),
                )

        # Demo RSVPs so /ticket and /certificate are browsable immediately.
        demos = [
            ("WM-DEMO-101", 4, "Demo Attendee", "demo@webimeet.dev", "REGISTERED", "SEAT-21-A7"),
            ("WM-DEMO-202", 1, "Raj Gautam", "graj13099@gmail.com", "ATTENDED", "SEAT-42-RG"),
        ]
        for code, wid, name, email, status, seat in demos:
            conn.execute(
                """INSERT INTO registrations
                   (ticket_code, webinar_id, name, email, seat_code, status, attended_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (code, wid, name, email, seat, status, timestamp if status == "ATTENDED" else None),
            )

        conn.execute(
            "INSERT INTO reactions (webinar_id, emoji) VALUES (1, '🔥'), (1, '👏'), (4, '❤️')"
        )

    print("✅ Seed complete: 6 webinars, sample chat, reactions and 2 demo tickets.")
    print("   Demo ticket (registered): WM-DEMO-101")
    print("   Demo ticket (attended)  : WM-DEMO-202")
    print(f"   Database: {DB_PATH}")


if __name__ == "__main__":
    seed()
