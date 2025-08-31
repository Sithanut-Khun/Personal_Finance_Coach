# src/auth.py
import hashlib
from datetime import datetime
import random
import string
from src.database import get_connection

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_user_id():
    timestamp = int(datetime.now().timestamp())
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"USR{timestamp}{suffix}"

def create_user(email, password, username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        conn.close()
        return False
    user_id = generate_user_id()
    hashed_password = hash_password(password)
    cur.execute(
        "INSERT INTO users (user_id, email, password_hash, username) VALUES (%s, %s, %s, %s)",
        (user_id, email, hashed_password, username),
    )
    conn.commit()
    conn.close()
    return True

def authenticate(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    hashed = hash_password(password)
    cursor.execute("SELECT user_id, username FROM users WHERE email = %s AND password_hash = %s", (email, hashed))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result if result else None

def reset_password(user_id, email, new_password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE user_id = %s AND email = %s", (user_id, email))
    if cursor.fetchone():
        hashed = hash_password(new_password)
        cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (hashed, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    else:
        cursor.close()
        conn.close()
        return False

def update_username(user_id, new_username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET username = %s WHERE user_id = %s", (new_username, user_id))
    conn.commit()
    cursor.close()
    conn.close()