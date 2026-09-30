import sqlite3
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS videos(
    id TEXT PRIMARY KEY, title TEXT, created_at INTEGER, cover TEXT);
CREATE TABLE IF NOT EXISTS snapshots(
    video_id TEXT, taken_at INTEGER,
    views INTEGER, likes INTEGER, comments INTEGER, shares INTEGER);
CREATE INDEX IF NOT EXISTS idx_snap ON snapshots(video_id, taken_at);
CREATE TABLE IF NOT EXISTS account_snapshots(
    taken_at INTEGER, followers INTEGER, following INTEGER,
    likes INTEGER, videos INTEGER);
CREATE TABLE IF NOT EXISTS promotions(
    id INTEGER PRIMARY KEY AUTOINCREMENT, video_id TEXT, started TEXT,
    goal TEXT, spend REAL, views INTEGER DEFAULT 0, followers INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0, profile_views INTEGER DEFAULT 0, note TEXT);
CREATE TABLE IF NOT EXISTS queue(
    id INTEGER PRIMARY KEY AUTOINCREMENT, file TEXT, caption TEXT,
    platforms TEXT, run_at INTEGER, status TEXT DEFAULT 'pending',
    results TEXT DEFAULT '{}');
"""


@contextmanager
def conn():
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    try:
        yield c
        c.commit()
    finally:
        c.close()
