from __future__ import annotations

import json
import mimetypes
import os
import random
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from data import TEAMS, TEAM_BY_ID, SLOT_CONFIG, RANKING_DATE
from engine import initial_state, simulate_qualifiers, perform_draw, simulate_final_tournament

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DB_PATH = Path(os.environ.get("WC_DB_PATH", ROOT / "worldcups.sqlite3"))
PORT = int(os.environ.get("PORT", "8000"))
DB_LOCK = threading.Lock()

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with DB_LOCK, db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS simulations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                year INTEGER NOT NULL,
                host_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                state_json TEXT NOT NULL
            )
        """)
        conn.commit()

def save_state(state):
    stamp = now_iso()
    state["updatedAt"] = stamp
    with DB_LOCK, db() as conn:
        conn.execute("""
            UPDATE simulations
            SET name=?, year=?, host_id=?, status=?, updated_at=?, state_json=?
            WHERE id=?
        """, (
            state["name"], state["year"], state["hostId"], state["status"],
            stamp, json.dumps(state, separators=(",", ":")), state["id"]
        ))
        conn.commit()

def get_state(sim_id):
    with db() as conn:
        row = conn.execute("SELECT state_json FROM simulations WHERE id=?", (sim_id,)).fetchone()
    return json.loads(row["state_json"]) if row else None

def list_simulations():
    with db() as conn:
        rows = conn.execute("""
            SELECT id, name, year, host_id, status, created_at, updated_at
            FROM simulations ORDER BY updated_at DESC
        """).fetchall()
    return [
        {
            "id": r["id"], "name": r["name"], "year": r["year"], "hostId": r["host_id"],
            "hostName": TEAM_BY_ID.get(r["host_id"], {}).get("name", r["host_id"]),
            "status": r["status"], "createdAt": r["created_at"], "updatedAt": r["updated_at"]
        }
        for r in rows
    ]

class Handler(BaseHTTPRequestHandler):
    server_version = "WorldCupLab/1.0"

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def send_json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            raise ValueError("Request body too large")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def serve_file(self, path):
        try:
            full = path.resolve()
            if STATIC.resolve() not in full.parents and full != STATIC.resolve():
                self.send_error(403)
                return
            if not full.exists() or not full.is_file():
                self.send_error(404)
                return
            data = full.read_bytes()
            mime = mimetypes.guess_type(str(full))[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", mime + ("; charset=utf-8" if mime.startswith("text/") else ""))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except OSError:
            self.send_error(404)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/teams":
            self.send_json({
                "rankingDate": RANKING_DATE,
                "count": len(TEAMS),
                "fifaMembers": sum(t["isFifaMember"] for t in TEAMS),
                "teams": TEAMS,
            })
            return
        if path == "/api/meta":
            self.send_json({
                "rankingDate": RANKING_DATE,
                "slots": SLOT_CONFIG,
                "format": "48 teams · 12 groups of 4 · top two + 8 best third-placed teams advance",
            })
            return
        if path == "/api/simulations":
            self.send_json({"simulations": list_simulations()})
            return
        match = re.fullmatch(r"/api/simulations/([a-f0-9-]+)", path)
        if match:
            state = get_state(match.group(1))
            if not state:
                self.send_json({"error": "Simulation not found"}, 404)
            else:
                self.send_json(state)
            return
        if path == "/":
            self.serve_file(STATIC / "index.html")
            return
        if path.startswith("/static/"):
            rel = path.removeprefix("/static/")
            self.serve_file(STATIC / rel)
            return
        self.send_error(404)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/simulations":
                body = self.read_json()
                name = str(body.get("name", "")).strip()[:80] or "Untitled World Cup"
                year = int(body.get("year", 2030))
                host_id = str(body.get("hostId", ""))
                if host_id not in TEAM_BY_ID:
                    self.send_json({"error": "Choose a valid host team."}, 400)
                    return
                if year < 2026 or year > 2200:
                    self.send_json({"error": "Year must be between 2026 and 2200."}, 400)
                    return
                sim_id = str(uuid.uuid4())
                created = now_iso()
                seed = random.SystemRandom().randint(1, 2_000_000_000)
                state = initial_state(sim_id, name, year, host_id, seed, created)
                with DB_LOCK, db() as conn:
                    conn.execute("""
                        INSERT INTO simulations
                        (id, name, year, host_id, status, created_at, updated_at, state_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (sim_id, name, year, host_id, state["status"], created, created,
                          json.dumps(state, separators=(",", ":"))))
                    conn.commit()
                self.send_json(state, 201)
                return

            match = re.fullmatch(r"/api/simulations/([a-f0-9-]+)/(qualifiers|draw|finals|reset)", path)
            if match:
                sim_id, action = match.groups()
                state = get_state(sim_id)
                if not state:
                    self.send_json({"error": "Simulation not found"}, 404)
                    return
                if action == "qualifiers":
                    state = simulate_qualifiers(state)
                elif action == "draw":
                    state = perform_draw(state)
                elif action == "finals":
                    state = simulate_final_tournament(state)
                elif action == "reset":
                    state = initial_state(
                        state["id"], state["name"], state["year"], state["hostId"],
                        state["seed"], state["createdAt"]
                    )
                save_state(state)
                self.send_json(state)
                return

            self.send_json({"error": "Unknown endpoint"}, 404)
        except (ValueError, KeyError) as exc:
            self.send_json({"error": str(exc)}, 400)
        except Exception as exc:
            self.send_json({"error": f"Simulation error: {exc}"}, 500)

    def do_DELETE(self):
        path = urlparse(self.path).path
        match = re.fullmatch(r"/api/simulations/([a-f0-9-]+)", path)
        if not match:
            self.send_json({"error": "Unknown endpoint"}, 404)
            return
        sim_id = match.group(1)
        with DB_LOCK, db() as conn:
            cur = conn.execute("DELETE FROM simulations WHERE id=?", (sim_id,))
            conn.commit()
        if cur.rowcount == 0:
            self.send_json({"error": "Simulation not found"}, 404)
        else:
            self.send_json({"ok": True})

if __name__ == "__main__":
    init_db()
    print(f"World Cup Lab running at http://localhost:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
