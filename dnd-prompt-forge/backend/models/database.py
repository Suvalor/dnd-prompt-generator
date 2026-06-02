"""
DND Prompt Forge - 数据库模块
SQLite 连接管理，保留现有表，新增 quota_usage 和 request_logs 表
"""

import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Dict, List

from config import settings

_db_lock = threading.Lock()

SCHEMA_SQL = """
-- 保留现有表
CREATE TABLE IF NOT EXISTS prompt_requests (
    id TEXT PRIMARY KEY,
    created_at TEXT,
    output_type TEXT,
    race TEXT,
    class_role TEXT,
    style TEXT,
    mood TEXT,
    description TEXT,
    target_model TEXT,
    template_version TEXT,
    memory_rule_version TEXT,
    main_prompt TEXT,
    short_prompt TEXT,
    negative_prompt TEXT,
    mode TEXT DEFAULT 'fallback',
    provider TEXT,
    latency_ms INTEGER
);

CREATE TABLE IF NOT EXISTS feedback_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT,
    request_id TEXT,
    feedback TEXT,
    reason TEXT,
    comment TEXT,
    input_snapshot TEXT,
    output_snapshot TEXT
);

CREATE TABLE IF NOT EXISTS memory_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT,
    updated_at TEXT,
    status TEXT,
    rule_key TEXT,
    rule_text TEXT,
    trigger_reason TEXT,
    times_seen INTEGER DEFAULT 1,
    version TEXT
);

-- 新增表：quota_usage（配额使用记录）
CREATE TABLE IF NOT EXISTS quota_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    ip_hash TEXT NOT NULL,
    fingerprint_hash TEXT,
    cookie_hash TEXT,
    endpoint TEXT NOT NULL,
    mode TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_quota_ip ON quota_usage(ip_hash, created_at);
CREATE INDEX IF NOT EXISTS idx_quota_fingerprint ON quota_usage(fingerprint_hash, created_at);
CREATE INDEX IF NOT EXISTS idx_quota_cookie ON quota_usage(cookie_hash, created_at);
CREATE INDEX IF NOT EXISTS idx_quota_created ON quota_usage(created_at);

-- 新增表：request_logs（请求日志/审计）
CREATE TABLE IF NOT EXISTS request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    ip_hash TEXT,
    endpoint TEXT,
    input_summary TEXT,
    output_summary TEXT,
    status TEXT,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_request_logs_created ON request_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_request_logs_status ON request_logs(status);
"""


class Database:
    """SQLite 数据库连接管理器，线程安全。"""

    def __init__(self, db_path: str) -> None:
        """初始化数据库管理器。"""
        self._db_path = db_path
        self._local = threading.local()

    def _get_connection(self) -> sqlite3.Connection:
        """获取当前线程的数据库连接。"""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            self._local.connection = conn
        return self._local.connection

    @contextmanager
    def connection(self):
        """获取数据库连接的上下文管理器。"""
        conn = self._get_connection()
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise

    @contextmanager
    def transaction(self, conn: sqlite3.Connection):
        """事务上下文管理器。"""
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def init_schema(self, conn: sqlite3.Connection) -> None:
        """初始化数据库表结构。"""
        conn.executescript(SCHEMA_SQL)

    def execute(self, sql: str, params: tuple = (), conn: sqlite3.Connection | None = None) -> sqlite3.Cursor:
        """执行 SQL 语句。"""
        if conn is None:
            conn = self._get_connection()
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor

    def fetchone(self, sql: str, params: tuple = (), conn: sqlite3.Connection | None = None) -> Dict[str, Any] | None:
        """查询单条记录。"""
        if conn is None:
            conn = self._get_connection()
        cursor = conn.execute(sql, params)
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self, sql: str, params: tuple = (), conn: sqlite3.Connection | None = None) -> List[Dict[str, Any]]:
        """查询多条记录。"""
        if conn is None:
            conn = self._get_connection()
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def insert(self, sql: str, params: tuple = (), conn: sqlite3.Connection | None = None) -> int:
        """插入记录并返回 lastrowid。"""
        if conn is None:
            conn = self._get_connection()
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid


db = Database(settings.db_path)


def init_database() -> None:
    """初始化数据库连接和表结构。"""
    with db.connection() as conn:
        db.init_schema(conn)
