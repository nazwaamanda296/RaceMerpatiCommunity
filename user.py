from models.database import get_conn

def get_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY username")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_user(username: str, password: str) -> bool:
    import hashlib

    conn = get_conn()
    cur = conn.cursor()
    try:
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        cur.execute("INSERT INTO users(username, password_hash) VALUES (?, ?)", (username, pw_hash))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def delete_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
