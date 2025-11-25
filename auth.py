import hashlib
from models.database import get_conn  

def authenticate(username: str, password: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE username=? AND password_hash=?",
        (username, hashlib.sha256(password.encode()).hexdigest()),
    )
    row = cur.fetchone()
    conn.close()
    return row
