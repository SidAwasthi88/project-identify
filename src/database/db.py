"""
db.py — Database connection and table creation using MySQL
Run init_db() once to create all tables.

Connection details:
    Host: localhost
    User: identify_user
    Password: Identify@123
    Database: identify_db
"""

import mysql.connector
import os

# ─────────────────────────────────────────────
# DATABASE CONFIG
# ─────────────────────────────────────────────

DB_CONFIG = {
    "host": "localhost",
    "user": "identify_user",
    "password": "Identify@123",
    "database": "identify_db"
}


def get_connection():
    """Returns a connection to the MySQL database."""
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn


def init_db():
    """Creates all tables if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # --- ADMINS TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(150) NOT NULL,
            created_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES admins(id)
        )
    """)

    # --- SUBJECTS TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_code VARCHAR(50) NOT NULL,
            course_title VARCHAR(150) NOT NULL,
            program ENUM('BBA', 'BBIS') NOT NULL,
            year ENUM('First', 'Second', 'Third', 'Fourth') NOT NULL,
            semester ENUM('First', 'Second') NOT NULL,
            admin_id INT NOT NULL,
            FOREIGN KEY (admin_id) REFERENCES admins(id)
        )
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
            face_enrolled TINYINT DEFAULT 0,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- SUBJECT-STUDENT ENROLLMENT TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject_students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject_id INT NOT NULL,
            student_id INT NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE KEY unique_enrollment (subject_id, student_id)
        )
    """)

    # --- SESSIONS TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject_id INT NOT NULL,
            admin_id INT NOT NULL,
            date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME,
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (admin_id) REFERENCES admins(id)
        )
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
            UNIQUE KEY unique_attendance (session_id, student_id)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized successfully.")


if __name__ == "__main__":
    init_db()