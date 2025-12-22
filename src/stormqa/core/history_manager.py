import sqlite3
import time
from pathlib import Path

DB_FILE = Path("stormqa_history.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS test_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            test_type TEXT,
            target_url TEXT,
            total_requests INTEGER,
            avg_latency REAL,
            p95_latency REAL,
            error_rate REAL,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_test_result(data: dict):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        total = data.get('total_requests', 0)
        failed = data.get('failed_requests', 0)
        error_rate = (failed / total * 100) if total > 0 else 0
        
        status = "UNKNOWN"
        if "test_result" in data:
            status = data["test_result"].get("status", "UNKNOWN").upper()

        c.execute('''
            INSERT INTO test_runs (timestamp, test_type, target_url, total_requests, avg_latency, p95_latency, error_rate, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            time.strftime("%Y-%m-%d %H:%M"),
            "LOAD",
            data.get("url", "N/A"),
            total,
            data.get("avg_response_time_ms", 0),
            data.get("p95_latency", 0),
            error_rate,
            status
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[History] Error saving result: {e}")

def get_recent_history(limit=50):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM test_runs ORDER BY id DESC LIMIT ?', (limit,))
        rows = c.fetchall()
        conn.close()
        
        result = [dict(row) for row in rows]
        return result[::-1]
    except:
        return []

def clear_history():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('DELETE FROM test_runs') 
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[History] Error clearing DB: {e}")
        return False