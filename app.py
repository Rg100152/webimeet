"""WebiMeet — Live & On-Demand Webinar Hub by Raj Gautam.

A lightweight full-stack Flask application: webinar lobby, 70/30 interactive
theater room, real-time chat + Q&A (incremental polling), RSVP tickets,
attendance-tracked certificates, host studio and a master portfolio hub.

Run:
    python seed_webinars.py
    python app.py
"""

import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

from db import close_db, init_db
from routes.api_routes import api_bp
from routes.webinar_routes import webinar_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEVELOPER = {
    "name": "Raj Gautam",
    "role": "Lead Host & Architect",
    "email": "graj13099@gmail.com",
    "contact": "+91 9555785729",
    "instagram": "@linux.userraj",
    "github": "Rg100152",
    "github_url": "https://github.com/Rg100152",
}

# The 9 projects showcased in the master portfolio hub.
PORTFOLIO_PROJECTS = [
    {
        "name": "AeroCast",
        "tagline": "Golang + Open-Meteo Weather Intelligence",
        "description": "Real-time forecast dashboards with clean Go APIs and live weather telemetry.",
        "stack": ["Golang", "Open-Meteo", "REST API"],
        "icon": "🌤️",
        "accent": "sky",
        "repo": "https://github.com/Rg100152/AeroCast",
        "demo": "#",
    },
    {
        "name": "FishWorld",
        "tagline": "Cinematic Sea Fish Encyclopedia & Vlog Hub",
        "description": "An immersive marine-life archive with species profiles and video storytelling.",
        "stack": ["HTML5", "CSS3", "JavaScript"],
        "icon": "🐠",
        "accent": "ocean",
        "repo": "https://github.com/Rg100152/FishWorld",
        "demo": "#",
    },
    {
        "name": "Serpentia",
        "tagline": "100 World Snakes Scientific Infographic Archive",
        "description": "A research-grade visual catalog of 100 snake species with distribution maps.",
        "stack": ["HTML5", "CSS3", "Data Viz"],
        "icon": "🐍",
        "accent": "emerald",
        "repo": "https://github.com/Rg100152/Serpentia",
        "demo": "#",
    },
    {
        "name": "QuizeTalk",
        "tagline": "Gamified Quiz Builder & Discussion Stage",
        "description": "Build, host and discuss live quizzes with scoring and team leaderboards.",
        "stack": ["Python", "Flask", "SQLite"],
        "icon": "🧠",
        "accent": "violet",
        "repo": "https://github.com/Rg100152/QuizeTalk",
        "demo": "#",
    },
    {
        "name": "VidyaPlan",
        "tagline": "Collaborative Study Group & Pomodoro Planner",
        "description": "Study rooms, shared goals and focus timers for disciplined learning sprints.",
        "stack": ["JavaScript", "LocalStorage", "PWA"],
        "icon": "📚",
        "accent": "amber",
        "repo": "https://github.com/Rg100152/VidyaPlan",
        "demo": "#",
    },
    {
        "name": "GyanVault",
        "tagline": "Command-Search Educational Resource Library",
        "description": "A keyboard-first resource vault with instant fuzzy search and tagging.",
        "stack": ["Python", "SQLite", "CLI"],
        "icon": "🗂️",
        "accent": "rose",
        "repo": "https://github.com/Rg100152/GyanVault",
        "demo": "#",
    },
    {
        "name": "ExamPulse 1000",
        "tagline": "CBT Mock Exam Platform",
        "description": "1,000+ practice questions across Python, Data Mining, .NET and Web Design.",
        "stack": ["Python", "Flask", "SQLite"],
        "icon": "📝",
        "accent": "sky",
        "repo": "https://github.com/Rg100152/ExamPulse-1000",
        "demo": "#",
    },
    {
        "name": "MentorBridge",
        "tagline": "1-on-1 Mentorship Matching & Jitsi Call Platform",
        "description": "Match learners with mentors and jump straight into a Jitsi video session.",
        "stack": ["Flask", "Jitsi", "SQLite"],
        "icon": "🤝",
        "accent": "violet",
        "repo": "https://github.com/Rg100152/MentorBridge",
        "demo": "#",
    },
    {
        "name": "WebiMeet",
        "tagline": "Live Webinar, Chat, RSVP Ticket & Certificate Engine",
        "description": "The platform you are looking at — broadcast theater, live Q&A and instant credentials.",
        "stack": ["Flask", "SQLite", "Vanilla JS"],
        "icon": "🎥",
        "accent": "rose",
        "repo": "https://github.com/Rg100152/webimeet",
        "demo": "/lobby",
        "featured": True,
    },
]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("WEBIMEET_SECRET", "webimeet-raj-gautam-2026")
app.config["JSON_SORT_KEYS"] = False

init_db()
app.teardown_appcontext(close_db)

app.register_blueprint(webinar_bp)
app.register_blueprint(api_bp)


@app.context_processor
def inject_template_globals():
    return {
        "developer": DEVELOPER,
        "projects": PORTFOLIO_PROJECTS,
        "brand": "WebiMeet",
        "current_year": datetime.now(timezone.utc).year,
    }


@app.errorhandler(404)
def page_not_found(_error):
    if request.path.startswith("/api/"):
        return jsonify(error="Endpoint not found"), 404
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(_error):
    if request.path.startswith("/api/"):
        return jsonify(error="Internal server error"), 500
    return render_template("404.html"), 500


@app.get("/health")
def health():
    return jsonify(status="ok", service="WebiMeet", by=DEVELOPER["name"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
