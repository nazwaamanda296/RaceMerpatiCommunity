from models.database import get_conn

def get_accounts():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM accounts ORDER BY code")
    rows = cur.fetchall()
    conn.close()
    return rows
