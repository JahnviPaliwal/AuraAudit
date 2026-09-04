import sqlite3
import json
import os
import shutil
from datetime import datetime

DB_PATH = "/tmp/runs.db" if os.environ.get("VERCEL") else "runs.db"

def init_db():
    if os.environ.get("VERCEL") and not os.path.exists(DB_PATH) and os.path.exists("runs.db"):
        try:
            shutil.copy("runs.db", DB_PATH)
        except Exception:
            pass
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            filename TEXT,
            match_rate REAL,
            precision REAL,
            recall REAL,
            audit_results_json TEXT,
            eval_report_json TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_run(run_id: str, filename: str, match_rate: float, precision: float, recall: float, audit_results: dict, eval_report: dict):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.utcnow().isoformat()
    audit_results_json = json.dumps(audit_results)
    eval_report_json = json.dumps(eval_report)
    
    cursor.execute("""
        INSERT INTO runs (id, timestamp, filename, match_rate, precision, recall, audit_results_json, eval_report_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (run_id, timestamp, filename, match_rate, precision, recall, audit_results_json, eval_report_json))
    
    conn.commit()
    conn.close()

def get_runs():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, timestamp, filename, match_rate, precision, recall FROM runs ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    
    runs = []
    for r in rows:
        runs.append({
            "id": r["id"],
            "timestamp": r["timestamp"],
            "filename": r["filename"],
            "match_rate": r["match_rate"],
            "precision": r["precision"],
            "recall": r["recall"]
        })
        
    conn.close()
    return runs

def get_run(run_id: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
        
    run_detail = {
        "id": row["id"],
        "timestamp": row["timestamp"],
        "filename": row["filename"],
        "match_rate": row["match_rate"],
        "precision": row["precision"],
        "recall": row["recall"],
        "audit_results": json.loads(row["audit_results_json"]),
        "eval_report": json.loads(row["eval_report_json"])
    }
    
    conn.close()
    return run_detail
