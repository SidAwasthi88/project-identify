import mysql.connector
from mysql.connector import errorcode
import hashlib
import os

# ─────────────────────────────────────────────
# CONNECTION CONFIG
# Edit these to match your MySQL server, or set them as
# environment variables (recommended so you're not committing
# a password to your repo).
# ─────────────────────────────────────────────
DB_CONFIG = {
    'host': os.environ.get('IDENTIFY_DB_HOST', 'localhost'),
    'port': int(os.environ.get('IDENTIFY_DB_PORT', 3306)),
    'user': os.environ.get('IDENTIFY_DB_USER', 'identify_user'),
    'password': os.environ.get('IDENTIFY_DB_PASSWORD', 'Identify@123'),
}
DB_NAME = os.environ.get('IDENTIFY_DB_NAME', 'identify_db')


def get_connection():
    """Returns a connection to the identify_db MySQL database."""
    conn = mysql.connector.connect(database=DB_NAME, **DB_CONFIG)
    return conn


def fetch_one_dict(cursor):
    """
    Converts a single fetched row into a dict using the cursor's column names.
    Driver-agnostic — works regardless of whether cursor(dictionary=True) is supported,
    which avoids the 'dictionary is an invalid keyword argument' error some
    mysql-connector installs throw.
    """
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def fetch_all_dict(cursor):
    """Converts all fetched rows into a list of dicts using the cursor's column names."""
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def init_db():
    """Creates the database (if needed) and all tables (if they don't already exist)."""
    # Step 1: connect WITHOUT selecting a database yet, so we can create it if missing
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.close()
    conn.close()

    # Step 2: connect to the actual database and create tables
    conn = get_connection()
    cursor = conn.cursor()

    # --- ADMINS TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            created_by INT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES admins(id)
        ) ENGINE=InnoDB
    """)

    # --- SUBJECTS TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_code VARCHAR(50) NOT NULL,
            course_title VARCHAR(255) NOT NULL,
            program ENUM('BBA', 'BBIS') NOT NULL,
            year ENUM('First', 'Second', 'Third', 'Fourth') NOT NULL,
            semester ENUM('First', 'Second') NOT NULL,
            admin_id INT NOT NULL,
            FOREIGN KEY (admin_id) REFERENCES admins(id)
        ) ENGINE=InnoDB
    """)

    # --- STUDENTS TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            reg_no VARCHAR(50) UNIQUE NOT NULL,
            roll_no INT,
            last_name VARCHAR(100) NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            middle_name VARCHAR(100),
            gender ENUM('Male', 'Female', 'Prefer not to say'),
            program ENUM('BBA', 'BBIS', 'Transfer') NOT NULL,
            year ENUM('First', 'Second', 'Third', 'Fourth'),
            semester ENUM('First', 'Second'),
            face_enrolled TINYINT(1) DEFAULT 0,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)

    # --- SUBJECT-STUDENT ENROLLMENT TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject_students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject_id INT NOT NULL,
            student_id INT NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE(subject_id, student_id)
        ) ENGINE=InnoDB
    """)

    # --- SESSIONS TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject_id INT NOT NULL,
            admin_id INT NOT NULL,
            date VARCHAR(20) NOT NULL,
            start_time VARCHAR(20) NOT NULL,
            end_time VARCHAR(20),
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (admin_id) REFERENCES admins(id)
        ) ENGINE=InnoDB
    """)

    # --- ATTENDANCE TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            student_id INT NOT NULL,
            status ENUM('Present', 'Absent', 'Late') NOT NULL,
            marked_by ENUM('face', 'manual') DEFAULT 'manual',
            marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id),
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE(session_id, student_id)
        ) ENGINE=InnoDB
    """)

    conn.commit()

    # Seed a default admin account if none exists
    cursor.execute("SELECT COUNT(*) AS count FROM admins")
    row = fetch_one_dict(cursor)
    if row['count'] == 0:
        default_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute("""
            INSERT INTO admins (username, password_hash, full_name, created_by)
            VALUES (%s, %s, %s, %s)
        """, ('admin', default_hash, 'System Administrator', None))
        conn.commit()

    cursor.close()
    conn.close()
    print("✅ Database initialized successfully.")


if __name__ == "__main__":
    init_db()