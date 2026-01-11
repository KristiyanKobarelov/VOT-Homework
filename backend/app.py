import os
import psycopg2
from flask import Flask, request, jsonify
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "apppassword")

def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )

def init_db():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
        conn.commit()
    finally:
        conn.close()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/api/messages", methods=["GET"])
def list_messages():
    init_db()
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC;")
            rows = cur.fetchall()
        return jsonify(rows)
    finally:
        conn.close()

@app.route("/api/messages", methods=["POST"])
def create_message():
    init_db()
    data = request.get_json(force=True, silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "content is required"}), 400

    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO messages (content) VALUES (%s) RETURNING id, content, created_at;",
                (content,),
            )
            row = cur.fetchone()
        conn.commit()
        return jsonify(row), 201
    finally:
        conn.close()

if __name__ == "__main__":
    # локално dev
    app.run(host="0.0.0.0", port=5000)