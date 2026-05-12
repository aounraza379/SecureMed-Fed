import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "users.db")

def init_db():
    """Initializes the database and creates a default admin."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        # Create default admin if not exists
        try:
            initial_pwd = os.environ.get("INITIAL_ADMIN_PWD", "admin@123")
            hashed_pw = generate_password_hash(initial_pwd)
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                           ("admin_alpha", hashed_pw, "admin"))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # User already exists

def verify_user(username, password):
    """Verifies credentials and returns the user role if successful."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result and check_password_hash(result[0], password):
            return result[1] # Returns 'doctor', 'admin', etc.
    return None

def register_user(username, password, role):
    """Adds a new user to the database with a hashed password."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            hashed_pw = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                           (username, hashed_pw, role))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False # User already exists