"""
database.py - SQLite Database Operations for PaasA Numerology AI
Author: Bhavya Sharma | Enrollment: 2450850380 | MCSP-232

Handles all database interactions:
  - Table creation / initialization
  - Session management (create, retrieve, delete)
  - User profile storage
  - Numerology data persistence
  - Chat history management
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = 'numerology.db'


# ─────────────────────────────────────────────────────────────────────────────
# Database Initialization
# ─────────────────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """
    Create and return a new SQLite database connection.
    Uses Row factory for dict-like row access.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db() -> None:
    """
    Initialize the database schema.
    Creates all required tables if they do not already exist.
    Called once at application startup.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript('''
        -- Users table: stores basic user profile data
        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT    NOT NULL,
            dob       TEXT    NOT NULL,
            gender    TEXT    NOT NULL CHECK(gender IN ('Male', 'Female')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(full_name, dob)
        );

        -- Sessions table: one session per numerology reading
        CREATE TABLE IF NOT EXISTS sessions (
            session_id  TEXT    PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            is_active   INTEGER DEFAULT 1,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        -- Numerology data: complete calculation results per session
        CREATE TABLE IF NOT EXISTS numerology_data (
            data_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT    NOT NULL,
            name_number INTEGER NOT NULL,
            mulank      INTEGER NOT NULL,
            bhagyank    INTEGER NOT NULL,
            kua_number  INTEGER NOT NULL,
            loshu_grid  TEXT    NOT NULL,  -- JSON blob
            planes      TEXT    NOT NULL,  -- JSON blob
            insights    TEXT,              -- JSON blob from Gemini
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

        -- Chat history: message log for each session
        CREATE TABLE IF NOT EXISTS chat_history (
            chat_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT    NOT NULL,
            role       TEXT    NOT NULL CHECK(role IN ('user', 'assistant')),
            message    TEXT    NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );
    ''')

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# User Operations
# ─────────────────────────────────────────────────────────────────────────────

def create_or_get_user(full_name: str, dob: str, gender: str) -> int:
    """
    Insert a new user or retrieve existing user's ID.
    Uses UNIQUE(full_name, dob) constraint for deduplication.

    Args:
        full_name: User's full name
        dob:       Date of birth (DD-MM-YYYY)
        gender:    'Male' or 'Female'
    Returns:
        user_id integer
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT OR IGNORE INTO users (full_name, dob, gender) VALUES (?, ?, ?)',
            (full_name, dob, gender)
        )
        conn.commit()
        cursor.execute(
            'SELECT user_id FROM users WHERE full_name = ? AND dob = ?',
            (full_name, dob)
        )
        row = cursor.fetchone()
        return row['user_id']
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Session Operations
# ─────────────────────────────────────────────────────────────────────────────

def create_session(user_id: int, session_id: str) -> str:
    """
    Create a new session record for a user.

    Args:
        user_id:    ID of the user
        session_id: Pre-generated unique session identifier
    Returns:
        session_id string
    """
    conn = get_connection()
    try:
        conn.execute(
            'INSERT INTO sessions (session_id, user_id) VALUES (?, ?)',
            (session_id, user_id)
        )
        conn.commit()
        return session_id
    finally:
        conn.close()


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve session details by session_id.

    Args:
        session_id: Session identifier string
    Returns:
        Dictionary of session data or None if not found
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            '''SELECT s.session_id, s.created_at, s.is_active,
                      u.full_name, u.dob, u.gender
               FROM sessions s
               JOIN users u ON s.user_id = u.user_id
               WHERE s.session_id = ?''',
            (session_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def close_session(session_id: str) -> None:
    """Mark a session as inactive."""
    conn = get_connection()
    try:
        conn.execute(
            'UPDATE sessions SET is_active = 0 WHERE session_id = ?',
            (session_id,)
        )
        conn.commit()
    finally:
        conn.close()


def delete_session(session_id: str) -> bool:
    """
    Permanently delete a session and all related data.
    Cascades to numerology_data and chat_history tables.

    Returns:
        True if deleted, False if session not found
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            'DELETE FROM sessions WHERE session_id = ?',
            (session_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Numerology Data Operations
# ─────────────────────────────────────────────────────────────────────────────

def save_numerology_data(session_id: str, numbers: dict,
                          loshu_grid: dict, planes: dict,
                          insights: Optional[dict] = None) -> None:
    """
    Persist the complete numerology calculation results.

    Args:
        session_id:  Active session ID
        numbers:     Core numbers dict (name_number, mulank, bhagyank, kua_number)
        loshu_grid:  Lo Shu Grid data dict
        planes:      Plane analysis dict
        insights:    AI-generated insights dict (optional)
    """
    conn = get_connection()
    try:
        conn.execute(
            '''INSERT INTO numerology_data
               (session_id, name_number, mulank, bhagyank, kua_number,
                loshu_grid, planes, insights)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                session_id,
                numbers['name_number'],
                numbers['mulank'],
                numbers['bhagyank'],
                numbers['kua_number'],
                json.dumps(loshu_grid),
                json.dumps(planes),
                json.dumps(insights) if insights else None,
            )
        )
        conn.commit()
    finally:
        conn.close()


def get_numerology_data(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve numerology data for a session.

    Returns:
        Dictionary with all numerology results, or None
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            'SELECT * FROM numerology_data WHERE session_id = ?',
            (session_id,)
        )
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data['loshu_grid'] = json.loads(data['loshu_grid'])
            data['planes'] = json.loads(data['planes'])
            if data['insights']:
                data['insights'] = json.loads(data['insights'])
            return data
        return None
    finally:
        conn.close()


def update_insights(session_id: str, insights: dict) -> None:
    """Update the insights field for an existing numerology record."""
    conn = get_connection()
    try:
        conn.execute(
            'UPDATE numerology_data SET insights = ? WHERE session_id = ?',
            (json.dumps(insights), session_id)
        )
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Chat History Operations
# ─────────────────────────────────────────────────────────────────────────────

def save_chat_message(session_id: str, role: str, message: str) -> None:
    """
    Store a single chat message (user or assistant).

    Args:
        session_id: Active session ID
        role:       'user' or 'assistant'
        message:    Message text content
    """
    conn = get_connection()
    try:
        conn.execute(
            'INSERT INTO chat_history (session_id, role, message) VALUES (?, ?, ?)',
            (session_id, role, message)
        )
        conn.commit()
    finally:
        conn.close()


def get_chat_history(session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieve recent chat history for a session.

    Args:
        session_id: Session identifier
        limit:      Maximum number of messages to return
    Returns:
        List of message dictionaries ordered by creation time
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            '''SELECT role, message, created_at
               FROM chat_history
               WHERE session_id = ?
               ORDER BY created_at ASC
               LIMIT ?''',
            (session_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_chat_message_count(session_id: str) -> int:
    """Count total messages in a session (for rate limiting)."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            '''SELECT COUNT(*) as cnt FROM chat_history
               WHERE session_id = ? AND role = 'user'
               AND DATE(created_at) = DATE('now')''',
            (session_id,)
        )
        return cursor.fetchone()['cnt']
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# History / Search Operations
# ─────────────────────────────────────────────────────────────────────────────

def search_sessions_by_name(name: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Search sessions by user name (case-insensitive partial match).

    Args:
        name:  Search query string
        limit: Maximum results to return
    Returns:
        List of matching session summaries
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            '''SELECT s.session_id, u.full_name, u.dob, u.gender, s.created_at
               FROM sessions s
               JOIN users u ON s.user_id = u.user_id
               WHERE u.full_name LIKE ?
               ORDER BY s.created_at DESC
               LIMIT ?''',
            (f'%{name}%', limit)
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_sessions(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve all sessions ordered by creation time (newest first)."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            '''SELECT s.session_id, u.full_name, u.dob, u.gender, s.created_at
               FROM sessions s
               JOIN users u ON s.user_id = u.user_id
               ORDER BY s.created_at DESC
               LIMIT ?''',
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
