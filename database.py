import sqlite3
from libs_utils import hash_password

DB_PATH = "sia_merpati.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_date TEXT NOT NULL,
            description TEXT NOT NULL,
            debit_account_id INTEGER NOT NULL,
            credit_account_id INTEGER NOT NULL,
            amount REAL NOT NULL
        )
    """)

    # Create inventory table for persediaan
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT NOT NULL,
            kode_barang TEXT NOT NULL,
            nama_barang TEXT NOT NULL,
            satuan TEXT NOT NULL,
            jumlah_masuk INTEGER DEFAULT 0,
            jumlah_keluar INTEGER DEFAULT 0,
            harga_per_unit REAL NOT NULL
        )
    """)

    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            "INSERT INTO users(username,password_hash) VALUES (?,?)",
            ("admin", hash_password("admin123"))
        )

    cur.execute("SELECT COUNT(*) AS c FROM accounts")
    if cur.fetchone()["c"] == 0:
        akun_awal = [
            ("1101", "Kas"),
            ("1102", "Piutang Usaha"),
            ("1103", "Persediaan Barang Dagang"),
            ("2101", "Hutang Usaha"),
            ("3101", "Modal Pemilik"),
            ("4101", "Penjualan"),
            ("5101", "Harga Pokok Penjualan"),
            ("6101", "Beban Gaji"),
            ("6102", "Beban Listrik dan Air"),
        ]
        cur.executemany("INSERT INTO accounts(code,name) VALUES (?,?)", akun_awal)

    conn.commit()
    conn.close()
