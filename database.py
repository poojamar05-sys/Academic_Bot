import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "academic.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            unit_number INTEGER NOT NULL,
            pdf_path TEXT,
            FOREIGN KEY(subject_id) REFERENCES subjects(id),
            UNIQUE(subject_id, unit_number)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id INTEGER NOT NULL,
            topic_code TEXT NOT NULL,
            topic_name TEXT NOT NULL,
            FOREIGN KEY(unit_id) REFERENCES units(id),
            UNIQUE(unit_id, topic_code)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            page_number INTEGER,
            content TEXT NOT NULL,
            FOREIGN KEY(topic_id) REFERENCES topics(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_bank (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            question TEXT NOT NULL,
            question_type TEXT DEFAULT 'general',
            answer TEXT,
            FOREIGN KEY(topic_id) REFERENCES topics(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS practice_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            unit TEXT,
            topic TEXT,
            score INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    subjects = [
        "Cloud Computing",
        "Distributed Computing",
        "Cryptography and Cybersecurity",
        "Computer Networks",
        "Compiler Design",
        "Big Data Analytics"
    ]

    for subject in subjects:
        cursor.execute(
            "INSERT OR IGNORE INTO subjects (name) VALUES (?)",
            (subject,)
        )

    conn.commit()
    conn.close()


def get_subjects():
    conn = get_connection()

    rows = conn.execute("""
        SELECT id, name
        FROM subjects
        ORDER BY name
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_units(subject_name):
    conn = get_connection()

    row = conn.execute("""
        SELECT id
        FROM subjects
        WHERE name = ?
    """, (subject_name,)).fetchone()

    if not row:
        conn.close()
        return []

    units = conn.execute("""
        SELECT id, unit_number, pdf_path
        FROM units
        WHERE subject_id = ?
        ORDER BY unit_number
    """, (row["id"],)).fetchall()

    conn.close()

    return [dict(unit) for unit in units]


def get_topics(subject_name, unit_number):
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            t.id,
            t.topic_code,
            t.topic_name
        FROM topics t
        JOIN units u ON t.unit_id = u.id
        JOIN subjects s ON u.subject_id = s.id
        WHERE s.name = ?
        AND u.unit_number = ?
        ORDER BY t.topic_code
    """, (subject_name, unit_number)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_topic(subject_name, unit_number, topic_code):
    conn = get_connection()

    row = conn.execute("""
        SELECT
            t.id,
            t.topic_code,
            t.topic_name
        FROM topics t
        JOIN units u ON t.unit_id = u.id
        JOIN subjects s ON u.subject_id = s.id
        WHERE s.name = ?
        AND u.unit_number = ?
        AND t.topic_code = ?
    """, (subject_name, unit_number, topic_code)).fetchone()

    conn.close()

    return dict(row) if row else None


def get_chunks(topic_id):
    conn = get_connection()

    rows = conn.execute("""
        SELECT id, page_number, content
        FROM chunks
        WHERE topic_id = ?
        ORDER BY page_number, id
    """, (topic_id,)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def clear_unit(subject_name, unit_number):
    conn = get_connection()

    subject = conn.execute("""
        SELECT id
        FROM subjects
        WHERE name = ?
    """, (subject_name,)).fetchone()

    if not subject:
        conn.close()
        return

    unit = conn.execute("""
        SELECT id
        FROM units
        WHERE subject_id = ?
        AND unit_number = ?
    """, (subject["id"], unit_number)).fetchone()

    if unit:
        topic_rows = conn.execute("""
            SELECT id FROM topics WHERE unit_id = ?
        """, (unit["id"],)).fetchall()

        for topic in topic_rows:
            conn.execute(
                "DELETE FROM chunks WHERE topic_id = ?",
                (topic["id"],)
            )

            conn.execute(
                "DELETE FROM question_bank WHERE topic_id = ?",
                (topic["id"],)
            )

        conn.execute(
            "DELETE FROM topics WHERE unit_id = ?",
            (unit["id"],)
        )

        conn.execute(
            "DELETE FROM units WHERE id = ?",
            (unit["id"],)
        )

    conn.commit()
    conn.close()


def save_unit(subject_name, unit_number, pdf_path, topics_data):
    conn = get_connection()

    subject = conn.execute("""
        SELECT id FROM subjects WHERE name = ?
    """, (subject_name,)).fetchone()

    if not subject:
        conn.close()
        return None

    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO units
        (subject_id, unit_number, pdf_path)
        VALUES (?, ?, ?)
    """, (
        subject["id"],
        unit_number,
        pdf_path
    ))

    unit = cursor.execute("""
        SELECT id
        FROM units
        WHERE subject_id = ?
        AND unit_number = ?
    """, (
        subject["id"],
        unit_number
    )).fetchone()

    unit_id = unit["id"]

    for topic in topics_data:
        cursor.execute("""
            INSERT OR REPLACE INTO topics
            (unit_id, topic_code, topic_name)
            VALUES (?, ?, ?)
        """, (
            unit_id,
            topic["code"],
            topic["name"]
        ))

    conn.commit()
    conn.close()

    return unit_id


def get_topic_id(unit_id, topic_code):
    conn = get_connection()

    row = conn.execute("""
        SELECT id
        FROM topics
        WHERE unit_id = ?
        AND topic_code = ?
    """, (unit_id, topic_code)).fetchone()

    conn.close()

    return row["id"] if row else None


def save_chunk(topic_id, page_number, content):
    conn = get_connection()

    conn.execute("""
        INSERT INTO chunks
        (topic_id, page_number, content)
        VALUES (?, ?, ?)
    """, (
        topic_id,
        page_number,
        content
    ))

    conn.commit()
    conn.close()


def save_question(topic_id, question, question_type="2-mark", answer=None):
    conn = get_connection()

    conn.execute("""
        INSERT INTO question_bank
        (topic_id, question, question_type, answer)
        VALUES (?, ?, ?, ?)
    """, (
        topic_id,
        question,
        question_type,
        answer
    ))

    conn.commit()
    conn.close()