import sqlite3
from pathlib import Path

DB = Path("data/bilisoul.sqlite3")

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.executescript("""
    CREATE TABLE IF NOT EXISTS videos(
      bvid TEXT PRIMARY KEY, title TEXT, url TEXT, transcript_path TEXT,
      analysis TEXT, comments_json TEXT, score REAL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS drafts(
      id INTEGER PRIMARY KEY AUTOINCREMENT, bvid TEXT, kind TEXT,
      target TEXT, body TEXT, status TEXT DEFAULT 'pending',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS events(
      id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT, detail TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    columns = {row[1] for row in c.execute("PRAGMA table_info(videos)")}
    if "comments_json" not in columns:
        c.execute("ALTER TABLE videos ADD COLUMN comments_json TEXT")
    return c

def seen(bvid):
    c = connect()
    row = c.execute("SELECT 1 FROM videos WHERE bvid=?", (bvid,)).fetchone()
    c.close()
    return row is not None

def save_video(v):
    c = connect()
    c.execute("""INSERT OR REPLACE INTO videos
      (bvid,title,url,transcript_path,analysis,comments_json,score)
      VALUES(?,?,?,?,?,?,?)""",
      (v["bvid"], v["title"], v["url"], v.get("transcript_path"),
       v.get("analysis"), v.get("comments_json"), v.get("score", 0)))
    c.commit()
    c.close()

def add_draft(bvid, kind, target, body):
    c = connect()
    updated = c.execute("""UPDATE drafts SET target=?, body=?, created_at=CURRENT_TIMESTAMP
        WHERE id=(SELECT id FROM drafts WHERE bvid=? AND kind=? AND status='pending'
                  ORDER BY id DESC LIMIT 1)""",
        (target, body, bvid, kind))
    if updated.rowcount == 0:
        c.execute("INSERT INTO drafts(bvid,kind,target,body) VALUES(?,?,?,?)",
                  (bvid, kind, target, body))
    c.commit()
    c.close()
