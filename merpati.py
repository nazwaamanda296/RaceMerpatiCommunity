import streamlit as st
import sqlite3
import hashlib
from datetime import date
import pandas as pd

DB_PATH = "sia_merpati.db"

# =========================================================
# DATABASE
# =========================================================
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Tabel user
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # Tabel akun
    cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        )
    """)

    # Tabel transaksi (satu baris = 1 transaksi debit-kredit)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_date TEXT NOT NULL,
            description TEXT NOT NULL,
            debit_account_id INTEGER NOT NULL,
            credit_account_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY(debit_account_id) REFERENCES accounts(id),
            FOREIGN KEY(credit_account_id) REFERENCES accounts(id)
        )
    """)

    # Seed user admin
    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            "INSERT INTO users(username,password_hash) VALUES (?,?)",
            ("admin", hash_password("admin123"))
        )

    # Seed akun standar
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

# =========================================================
# AUTH
# =========================================================
def authenticate(username: str, password: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE username=? AND password_hash=?",
        (username, hash_password(password)),
    )
    row = cur.fetchone()
    conn.close()
    return row

# =========================================================
# DATA AKUN & TRANSAKSI
# =========================================================
def get_accounts():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM accounts ORDER BY code")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_account(code: str, name: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO accounts(code,name) VALUES (?,?)", (code, name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_account(account_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM accounts WHERE id=?", (account_id,))
    conn.commit()
    conn.close()

def create_transaction(tx_date, description, debit_id, credit_id, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO transactions(tx_date,description,debit_account_id,credit_account_id,amount)
        VALUES (?,?,?,?,?)
        """,
        (tx_date, description, debit_id, credit_id, amount),
    )
    conn.commit()
    conn.close()

def get_transactions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT t.id, t.tx_date, t.description,
               da.code AS debit_code, da.name AS debit_name,
               ca.code AS credit_code, ca.name AS credit_name,
               t.amount
        FROM transactions t
        JOIN accounts da ON da.id = t.debit_account_id
        JOIN accounts ca ON ca.id = t.credit_account_id
        ORDER BY t.tx_date, t.id
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_transaction(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions WHERE id=?", (tx_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_transaction(tx_id, tx_date, description, debit_id, credit_id, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE transactions
        SET tx_date=?, description=?, debit_account_id=?, credit_account_id=?, amount=?
        WHERE id=?
        """,
        (tx_date, description, debit_id, credit_id, amount, tx_id),
    )
    conn.commit()
    conn.close()

def delete_transaction(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()

# =========================================================
# LAPORAN
# =========================================================
def trial_balance():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT a.id, a.code, a.name,
               SUM(CASE WHEN t.debit_account_id = a.id THEN t.amount ELSE 0 END) AS total_debit,
               SUM(CASE WHEN t.credit_account_id = a.id THEN t.amount ELSE 0 END) AS total_credit
        FROM accounts a
        LEFT JOIN transactions t
          ON t.debit_account_id = a.id OR t.credit_account_id = a.id
        GROUP BY a.id, a.code, a.name
        HAVING total_debit > 0 OR total_credit > 0
        ORDER BY a.code
        """
    )
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return pd.DataFrame(columns=["Kode", "Nama Akun", "Debit", "Kredit"])
    df = pd.DataFrame(rows)
    df.columns = ["id", "Kode", "Nama Akun", "Debit", "Kredit"]
    return df[["Kode", "Nama Akun", "Debit", "Kredit"]]

def income_statement():
    tb = trial_balance()
    if tb.empty:
        return None
    tb["Kode"] = tb["Kode"].astype(str)

    pendapatan = tb[tb["Kode"].str.startswith("4")]["Kredit"].sum()
    hpp        = tb[tb["Kode"].str.startswith("5101")]["Debit"].sum()
    beban      = tb[tb["Kode"].str.startswith("6")]["Debit"].sum()

    laba_kotor  = pendapatan - hpp
    laba_bersih = laba_kotor - beban

    return {
        "pendapatan": pendapatan,
        "hpp": hpp,
        "laba_kotor": laba_kotor,
        "beban": beban,
        "laba_bersih": laba_bersih,
    }

def ledger_per_account():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT t.id, t.tx_date, t.description,
               da.code AS debit_code, da.name AS debit_name,
               ca.code AS credit_code, ca.name AS credit_name,
               t.amount
        FROM transactions t
        JOIN accounts da ON da.id = t.debit_account_id
        JOIN accounts ca ON ca.id = t.credit_account_id
        ORDER BY t.tx_date, t.id
        """
    )
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return {}

    ledger = {}
    for r in rows:
        amt = r["amount"]

        key_d = (r["debit_code"], r["debit_name"])
        ledger.setdefault(key_d, [])
        ledger[key_d].append(
            {
                "Tanggal": r["tx_date"],
                "ID": r["id"],
                "Keterangan": r["description"],
                "Debit": amt,
                "Kredit": 0.0,
            }
        )

        key_c = (r["credit_code"], r["credit_name"])
        ledger.setdefault(key_c, [])
        ledger[key_c].append(
            {
                "Tanggal": r["tx_date"],
                "ID": r["id"],
                "Keterangan": r["description"],
                "Debit": 0.0,
                "Kredit": amt,
            }
        )

    return ledger

# Helper: ubah rows transaksi jadi DataFrame rapi
def transactions_to_df(rows):
    if not rows:
        return pd.DataFrame(
            columns=[
                "ID",
                "Tanggal",
                "Keterangan",
                "Kode Debit",
                "Nama Debit",
                "Kode Kredit",
                "Nama Kredit",
                "Jumlah",
            ]
        )
    data = []
    for r in rows:
        data.append(
            {
                "ID": r["id"],
                "Tanggal": r["tx_date"],
                "Keterangan": r["description"],
                "Kode Debit": r["debit_code"],
                "Nama Debit": r["debit_name"],
                "Kode Kredit": r["credit_code"],
                "Nama Kredit": r["credit_name"],
                "Jumlah": r["amount"],
            }
        )
    return pd.DataFrame(data)

# =========================================================
# STYLING – TEMA MOBILE PASTEL
# =========================================================
def inject_css():
    st.markdown(
        """
        <style>
        /* Hilangkan header / toolbar Streamlit dan space atas */
        header, .stApp > header,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        .viewerBadge_container__1QSob {
            display: none !important;
            visibility: none !important;
            height: 0 !important;
        }
        .main {
            padding-top: 0 !important;
            margin-top: -40px !important;
        }
        .block-container {
            padding-top: 12px !important;
        }
        
        /* Global theme */
        .stApp {
            background-color: #fff8f0;
            color: #111827;
            font-family: "SF Pro Text", "Segoe UI", system-ui, sans-serif;
        }

        /* Sidebar enhanced pastel */
        [data-testid="stSidebar"] {
            background: linear-gradient(135deg, #ffe6f0 0%, #ffd6e8 100%);
            border-right: none;
            box-shadow: 8px 0 24px rgba(255, 105, 180, 0.25);
            padding-top: 30px;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 24px;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label {
            color: #7a1053;
            font-weight: 700;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            letter-spacing: 0.05em;
        }

        /* Radio menu styled as chips with hover and transition */
        [data-baseweb="radio"] label {
            border-radius: 9999px !important;
            padding: 8px 16px !important;
            background-color: #ffd6e8;
            margin-bottom: 8px;
            cursor: pointer;
            font-weight: 600;
            color: #6f1d4a;
            transition: background-color 0.3s ease, color 0.3s ease, transform 0.2s ease;
            box-shadow: 0 1px 3px rgba(111, 29, 74, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        [data-baseweb="radio"] label:hover {
            background-color: #ff9aca !important;
            color: #4a044e !important;
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(255, 105, 180, 0.35);
        }
        [data-baseweb="radio"] input:checked + div {
            background-color: #f95aad !important;
            color: #380233 !important;
            box-shadow: 0 4px 12px rgba(249, 90, 173, 0.6);
            transform: translateY(-2px);
        }

        /* Login card */
        .login-card {
            background: #fefce8;
            border-radius: 28px;
            padding: 28px 32px 24px 32px;
            border: 2px solid #fde68a;
            box-shadow: 0 24px 40px rgba(15,23,42,0.16);
        }
        .login-title {
            font-size: 24px;
            font-weight: 800;
            color: #1f2937;
            text-align: center;
            letter-spacing: 0.03em;
        }
        .login-sub {
            font-size: 13px;
            color: #4b5563;
            text-align: center;
            margin-top: 4px;
            margin-bottom: 18px;
        }
        .login-btn > button { width: 100%; }

        /* Tombol umum */
        .stButton>button {
            border-radius: 999px;
            border: none;
            font-weight: 600;
            padding: 8px 18px;
            background-color: #111827;
            color: #f9fafb;
            transition: background-color 0.3s ease;
        }
        .stButton>button:hover { background-color: #020617; }

        /* Dashboard title */
        .dash-title {
            font-size: 22px;
            font-weight: 800;
            color: #1f2937;
        }
        .dash-sub {
            font-size: 13px;
            color: #4b5563;
            margin-bottom: 18px;
        }

        .dash-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.9rem;
        }

        .dash-card {
            border-radius: 22px;
            padding: 12px 14px 10px 14px;
            box-shadow: 0 14px 28px rgba(15,23,42,0.14);
            background: #bae6fd;
            border: none;
        }
        .dash-card.pink { background:#fecdd3; }
        .dash-card.yellow { background:#fde68a; }
        .dash-card.lilac { background:#e9d5ff; }
        .dash-card.mint { background:#bbf7d0; }

        .dash-card-title {
            font-size: 15px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 4px;
        }
        .dash-card-sub {
            font-size: 12px;
            color: #374151;
        }
        .dash-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 20px 36px rgba(15,23,42,0.2);
        }

        /* Shell laporan */
        .report-shell {
            background-color: #f1f5f9;
            border-radius: 26px;
            padding: 22px;
            border: 2px solid #cbd5f5;
            box-shadow: 0 20px 36px rgba(15,23,42,0.18);
        }
        .report-header-box {
            background: #f9a8d4;
            color: #3b0764;
            text-align: center;
            padding: 8px 14px;
            border-radius: 18px;
            font-weight: 700;
            margin-bottom: 14px;
        }
        .report-footer-box {
            background: #bbf7d0;
            color: #14532d;
            padding: 6px 14px;
            border-radius: 16px;
            font-size: 13px;
            font-weight: 600;
            text-align: center;
            margin-top: 10px;
        }

        /* ========== FIX: SIDEBAR TOGGLE ========== */
        [data-testid="collapsedControl"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
        }
        [data-testid="stSidebarNav"] {
            display: block !important;
        }
        section[data-testid="stSidebar"] {
            display: block !important;
        }
        button[kind="header"] {
            display: block !important;
            visibility: visible !important;
        }
        /* ========================================== */

        </style>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# UI HELPER
# =========================================================
def top_bar():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"Masuk sebagai: {st.session_state.username}")
    with col2:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.page = "Login"
            st.rerun()

def back_to_dashboard():
    if st.button("Kembali ke Dashboard"):
        st.session_state.page = "Dashboard"
        st.rerun()

# =========================================================
# PAGES
# =========================================================
def page_login():
    inject_css()
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="login-title">MERPATI SIA</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="login-sub">Sistem informasi akuntansi sederhana untuk mencatat transaksi hingga laporan keuangan.</div>',
            unsafe_allow_html=True,
        )

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        st.markdown('<div class="login-btn">', unsafe_allow_html=True)
        if st.button("Masuk"):
            user = authenticate(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "Dashboard"
                st.rerun()
            else:
                st.error("Username atau password salah.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.caption("Contoh akun: admin / admin123")
        st.markdown("</div>", unsafe_allow_html=True)

def page_dashboard():
    inject_css()
    top_bar()

    # ===================== DATA DASAR =====================
    rows = get_transactions()
    if rows:
        data = []
        for r in rows:
            data.append(
                {
                    "ID": r["id"],
                    "Tanggal": r["tx_date"],
                    "Keterangan": r["description"],
                    "Kode Debit": r["debit_code"],
                    "Nama Debit": r["debit_name"],
                    "Kode Kredit": r["credit_code"],
                    "Nama Kredit": r["credit_name"],
                    "Jumlah": r["amount"],
                }
            )
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame(
            columns=[
                "ID",
                "Tanggal",
                "Keterangan",
                "Kode Debit",
                "Nama Debit",
                "Kode Kredit",
                "Nama Kredit",
                "Jumlah",
            ]
        )

    tb = trial_balance()
    laba = income_statement()

    # ===================== RINGKASAN ANGKA =====================
    total_tx = len(df)
    total_nominal = float(df["Jumlah"].sum()) if not df.empty else 0.0

    # Total penjualan (akun 4101 di kredit)
    if not df.empty:
        total_penjualan = df[df["Kode Kredit"] == "4101"]["Jumlah"].sum()
    else:
        total_penjualan = 0.0

    # Total pembelian (asumsi: Persediaan 1103 lawan Kas 1101 / Hutang 2101)
    if not df.empty:
        df_beli = df[
            ((df["Kode Debit"] == "1103") & (df["Kode Kredit"].isin(["1101", "2101"])))
            | ((df["Kode Kredit"] == "1103") & (df["Kode Debit"].isin(["1101", "2101"])))
        ]
        total_pembelian = df_beli[df_beli["Kode Debit"] == "1103"]["Jumlah"].sum()
    else:
        total_pembelian = 0.0

    # Saldo Kas, Piutang, Hutang dari neraca saldo
    saldo_kas = saldo_piutang = saldo_hutang = 0.0
    if not tb.empty:
        tb["Kode"] = tb["Kode"].astype(str)

        def ambil_saldo(kode):
            row = tb[tb["Kode"] == kode]
            if row.empty:
                return 0.0
            r = row.iloc[0]
            return float(r["Debit"] - r["Kredit"])

        saldo_kas = ambil_saldo("1101")       # Kas
        saldo_piutang = ambil_saldo("1102")   # Piutang Usaha
        saldo_hutang = ambil_saldo("2101")    # Hutang Usaha

    # Laba bersih dari laporan laba rugi
    laba_bersih = laba["laba_bersih"] if laba else 0.0

    # ===================== UI DASHBOARD =====================
    st.markdown('<div class="dash-panel">', unsafe_allow_html=True)
    st.markdown('<div class="dash-title">Dashboard MERPATI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="dash-sub">Ringkasan transaksi, posisi kas, piutang, hutang, dan laba rugi usaha.</div>',
        unsafe_allow_html=True,
    )

    # ---------- Baris 1: Ringkasan utama ----------
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="dash-card yellow">
                <div class="dash-card-title">Jumlah Transaksi</div>
                <div class="dash-card-sub">{total_tx} transaksi tercatat</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="dash-card mint">
                <div class="dash-card-title">Total Penjualan</div>
                <div class="dash-card-sub">Rp {total_penjualan:,.0f}</div>
            </div>
            """.replace(",", "."),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="dash-card lilac">
                <div class="dash-card-title">Total Pembelian</div>
                <div class="dash-card-sub">Rp {total_pembelian:,.0f}</div>
            </div>
            """.replace(",", "."),
            unsafe_allow_html=True,
        )

    st.write("")

    # ---------- Baris 2: Posisi keuangan ----------
    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown(
            f"""
            <div class="dash-card pink">
                <div class="dash-card-title">Saldo Kas (1101)</div>
                <div class="dash-card-sub">Rp {saldo_kas:,.0f}</div>
            </div>
            """.replace(",", "."),
            unsafe_allow_html=True,
        )
    with c5:
        st.markdown(
            f"""
            <div class="dash-card yellow">
                <div class="dash-card-title">Saldo Piutang (1102)</div>
                <div class="dash-card-sub">Rp {saldo_piutang:,.0f}</div>
            </div>
            """.replace(",", "."),
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(
            f"""
            <div class="dash-card mint">
                <div class="dash-card-title">Saldo Hutang (2101)</div>
                <div class="dash-card-sub">Rp {saldo_hutang:,.0f}</div>
            </div>
            """.replace(",", "."),
            unsafe_allow_html=True,
        )

    st.write("")

    # ---------- Baris 3: Ringkasan laba rugi ----------
    c7, c8, c9 = st.columns(3)
    if laba:
        with c7:
            st.markdown(
                f"""
                <div class="dash-card lilac">
                    <div class="dash-card-title">Pendapatan</div>
                    <div class="dash-card-sub">Rp {laba['pendapatan']:,.0f}</div>
                </div>
                """.replace(",", "."),
                unsafe_allow_html=True,
            )
        with c8:
            st.markdown(
                f"""
                <div class="dash-card pink">
                    <div class="dash-card-title">Total Beban</div>
                    <div class="dash-card-sub">Rp {laba['beban']:,.0f}</div>
                </div>
                """.replace(",", "."),
                unsafe_allow_html=True,
            )
        with c9:
            st.markdown(
                f"""
                <div class="dash-card yellow">
                    <div class="dash-card-title">Laba Bersih</div>
                    <div class="dash-card-sub">Rp {laba_bersih:,.0f}</div>
                </div>
                """.replace(",", "."),
                unsafe_allow_html=True,
            )
    else:
        with c7:
            st.markdown(
                """
                <div class="dash-card lilac">
                    <div class="dash-card-title">Laba Rugi</div>
                    <div class="dash-card-sub">Belum ada data.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    # ===================== MENU CEPAT =====================
    st.subheader("Menu Cepat")
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        if st.button("Pencatatan Transaksi"):
            st.session_state.page = "Transaksi"
            st.rerun()
        if st.button("Penjualan"):
            st.session_state.page = "Penjualan"
            st.rerun()
    with mc2:
        if st.button("Pembelian"):
            st.session_state.page = "Pembelian"
            st.rerun()
        if st.button("Jurnal Umum"):
            st.session_state.page = "Jurnal"
            st.rerun()
    with mc3:
        if st.button("Buku Besar"):
            st.session_state.page = "Buku Besar"
            st.rerun()
        if st.button("Laba Rugi"):
            st.session_state.page = "Laba Rugi"
            st.rerun()

    st.write("")

    # ===================== TRANSAKSI TERBARU =====================
    st.subheader("5 Transaksi Terbaru")
    if df.empty:
        st.info("Belum ada transaksi.")
    else:
        # urutkan dari terbaru
        df_sorted = df.sort_values(["Tanggal", "ID"], ascending=[False, False]).head(5)
        st.table(df_sorted[["Tanggal", "Keterangan", "Kode Debit", "Kode Kredit", "Jumlah"]])

    st.markdown('</div>', unsafe_allow_html=True)

def page_transaksi():
    inject_css()
    top_bar()

    st.markdown('<div class="report-shell">', unsafe_allow_html=True)
    st.markdown('<div class="report-header-box">Pencatatan Transaksi</div>', unsafe_allow_html=True)
    back_to_dashboard()

    tab1, tab2 = st.tabs(["Input Transaksi", "Edit / Hapus Transaksi"])

    accounts = get_accounts()
    akun_map = {f"{a['code']} - {a['name']}": a["id"] for a in accounts}

    # ---------------- TAB 1 : INPUT TRANSAKSI ----------------
    with tab1:
        tgl = st.date_input("Tanggal", value=date.today(), key="tgl_input")
        desk = st.text_input("Keterangan")

        col1, col2, col3 = st.columns(3)
        with col1:
            debit_label = st.selectbox(
                "Akun Debit",
                list(akun_map.keys()),
                key="debit_input_transaksi"
            )
        with col2:
            kredit_label = st.selectbox(
                "Akun Kredit",
                list(akun_map.keys()),
                key="kredit_input_transaksi"
            )
        with col3:
            nominal = st.number_input("Jumlah", min_value=0.0, step=1000.0)

        if st.button("Simpan Transaksi"):
            if nominal <= 0:
                st.warning("Nominal harus lebih dari 0.")
            elif debit_label == kredit_label:
                st.warning("Akun debit dan kredit tidak boleh sama.")
            else:
                create_transaction(
                    str(tgl),
                    desk,
                    akun_map[debit_label],
                    akun_map[kredit_label],
                    nominal,
                )
                st.success("Transaksi tersimpan.")
                st.rerun()

        st.markdown("---")
        rows = get_transactions()
        if rows:
            df = transactions_to_df(rows)
            st.table(df)
        else:
            st.info("Belum ada transaksi.")

    # ---------------- TAB 2 : EDIT / HAPUS TRANSAKSI ----------------
    with tab2:
        rows = get_transactions()
        if not rows:
            st.info("Belum ada transaksi.")
        else:
            opsi = {
                f"{r['id']} - {r['tx_date']} - {r['description']}": r["id"] for r in rows
            }
            pilih_label = st.selectbox(
                "Pilih transaksi",
                list(opsi.keys()),
                key="pilih_transaksi_edit"
            )
            pilih_id = opsi[pilih_label]
            tx = get_transaction(pilih_id)

            col1, col2 = st.columns(2)
            with col1:
                tgl_e = st.date_input(
                    "Tanggal",
                    value=date.fromisoformat(tx["tx_date"]),
                    key=f"tgl_edit_{pilih_id}"
                )
                desk_e = st.text_input(
                    "Keterangan",
                    value=tx["description"],
                    key=f"desk_edit_{pilih_id}"
                )
            with col2:
                debit_e = st.selectbox(
                    "Akun Debit",
                    list(akun_map.keys()),
                    index=list(akun_map.values()).index(tx["debit_account_id"]),
                    key=f"debit_edit_{pilih_id}"
                )
                kredit_e = st.selectbox(
                    "Akun Kredit",
                    list(akun_map.keys()),
                    index=list(akun_map.values()).index(tx["credit_account_id"]),
                    key=f"kredit_edit_{pilih_id}"
                )
                nominal_e = st.number_input(
                    "Jumlah",
                    min_value=0.0,
                    step=1000.0,
                    value=float(tx["amount"]),
                    key=f"nominal_edit_{pilih_id}"
                )

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Simpan Perubahan", key=f"simpan_edit_{pilih_id}"):
                    if nominal_e <= 0:
                        st.warning("Nominal harus lebih dari 0.")
                    elif debit_e == kredit_e:
                        st.warning("Akun debit dan kredit tidak boleh sama.")
                    else:
                        update_transaction(
                            pilih_id,
                            str(tgl_e),
                            desk_e,
                            akun_map[debit_e],
                            akun_map[kredit_e],
                            nominal_e,
                        )
                        st.success("Transaksi diubah.")
                        st.rerun()
            with c2:
                if st.button("Hapus Transaksi", key=f"hapus_{pilih_id}"):
                    delete_transaction(pilih_id)
                    st.success("Transaksi dihapus.")
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

def page_jurnal():
    inject_css()
    top_bar()

    st.markdown('<div class="report-shell">', unsafe_allow_html=True)
    st.markdown('<div class="report-header-box">Jurnal Umum</div>', unsafe_allow_html=True)
    back_to_dashboard()

    rows = get_transactions()
    if not rows:
        st.info("Belum ada transaksi.")
    else:
        df = transactions_to_df(rows)
        st.table(df)

    st.markdown("</div>", unsafe_allow_html=True)

def page_buku_besar():
    inject_css()
    top_bar()

    st.markdown('<div class="report-shell">', unsafe_allow_html=True)
    st.markdown('<div class="report-header-box">Buku Besar</div>', unsafe_allow_html=True)
    back_to_dashboard()

    ledger = ledger_per_account()
    if not ledger:
        st.info("Belum ada transaksi.")
    else:
        for (kode, nama), entries in ledger.items():
            st.markdown(f"**{kode} - {nama}**")
            df = pd.DataFrame(entries)
            saldo = 0.0
            saldo_list = []
            for _, row in df.iterrows():
                saldo += row["Debit"] - row["Kredit"]
                saldo_list.append(saldo)
            df["Saldo"] = saldo_list
            st.table(df)
            st.markdown("---")

    st.markdown("</div>", unsafe_allow_html=True)

def page_neraca_saldo():
    inject_css()
    top_bar()

    st.markdown('<div class="report-shell">', unsafe_allow_html=True)
    st.markdown('<div class="report-header-box">Neraca Saldo</div>', unsafe_allow_html=True)
    back_to_dashboard()

    tb = trial_balance()
    if tb.empty:
        st.info("Belum ada data.")
    else:
        st.table(tb)
        total_debit = tb["Debit"].sum()
        total_kredit = tb["Kredit"].sum()
        st.markdown(
            f'<div class="report-footer-box">Total Debit: Rp {total_debit:,.0f} | Total Kredit: Rp {total_kredit:,.0f}</div>'.replace(",", "."),
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

def page_laba_rugi():
    inject_css()
    top_bar()

    st.markdown('<div class="report-shell">', unsafe_allow_html=True)
    st.markdown('<div class="report-header-box">Laporan Laba Rugi</div>', unsafe_allow_html=True)
    back_to_dashboard()

    data = income_statement()
    if not data:
        st.info("Belum ada data.")
    else:
        st.markdown('<div class="report-title">Ringkasan Laba Rugi</div>', unsafe_allow_html=True)
        st.write(f"Pendapatan: Rp {data['pendapatan']:,.0f}".replace(",", "."))
        st.write(f"Harga Pokok Penjualan: Rp {data['hpp']:,.0f}".replace(",", "."))
        st.write(f"Laba Kotor: Rp {data['laba_kotor']:,.0f}".replace(",", "."))
        st.write(f"Beban Operasional: Rp {data['beban']:,.0f}".replace(",", "."))
        st.write(f"Laba Bersih: Rp {data['laba_bersih']:,.0f}".replace(",", "."))
        st.markdown(
            '<div class="report-footer-box">Laporan laba rugi disusun dari akun pendapatan, HPP, dan beban.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

def page_akun():
    inject_css()
    top_bar()

    st.markdown('<div class="report-shell">', unsafe_allow_html=True)
    st.markdown('<div class="report-header-box">Daftar Akun</div>', unsafe_allow_html=True)
    back_to_dashboard()

    rows = get_accounts()
    df = pd.DataFrame(rows)
    df.columns = ["ID", "Kode", "Nama"]
    if not df.empty:
        st.table(df.set_index("ID"))
    else:
        st.info("Belum ada akun.")

    st.markdown("---")
    st.subheader("Tambah Akun Baru")
    col1, col2 = st.columns(2)
    with col1:
        code = st.text_input("Kode Akun")
    with col2:
        name = st.text_input("Nama Akun")

    if st.button("Simpan Akun"):
        if not code or not name:
            st.warning("Kode dan nama akun harus diisi.")
        else:
            ok = add_account(code, name)
            if ok:
                st.success("Akun ditambahkan.")
                st.rerun()
            else:
                st.error("Kode akun sudah digunakan.")

    st.markdown("---")
    st.subheader("Hapus Akun")
    if rows:
        opsi = {f"{r['code']} - {r['name']}": r["id"] for r in rows}
        pilih = st.selectbox("Pilih akun", list(opsi.keys()))
        if st.button("Hapus Akun"):
            delete_account(opsi[pilih])
            st.success("Akun dihapus.")
            st.rerun()
    else:
        st.info("Belum ada akun.")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# PAGES TAMBAHAN: PENJUALAN, PEMBELIAN, BUKU PEMBANTU
# =========================================================
def page_penjualan():
    inject_css()
    top_bar()

    st.markdown('<div class="report-shell">', unsafe_allow_html=True)
    st.markdown('<div class="report-header-box">Jurnal Penjualan</div>', unsafe_allow_html=True)
    back_to_dashboard()

    rows = get_transactions()
    df = transactions_to_df(rows)

    # Asumsi: akun 4101 = Penjualan
    df_jual = df[(df["Kode Kredit"] == "4101") | (df["Kode Debit"] == "4101")]

    if df_jual.empty:
        st.info("Belum ada transaksi penjualan.")
    else:
        st.table(df_jual)
        total_penjualan = df_jual[df_jual["Kode Kredit"] == "4101"]["Jumlah"].sum()
        st.markdown(
            f'<div class="report-footer-box">Total Penjualan: Rp {total_penjualan:,.0f}</div>'.replace(",", "."),
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

def page_pembelian():
    inject_css()
    top_bar()

    st.markdown('<div class="report-shell">', unsafe_allow_html=True)
    st.markdown('<div class="report-header-box">Jurnal Pembelian</div>', unsafe_allow_html=True)
    back_to_dashboard()

    rows = get_transactions()
    df = transactions_to_df(rows)

    # Asumsi: 1103 = Persediaan, 1101 = Kas, 2101 = Hutang Usaha
    df_beli = df[
        ((df["Kode Debit"] == "1103") & (df["Kode Kredit"].isin(["1101", "2101"])))
        | ((df["Kode Kredit"] == "1103") & (df["Kode Debit"].isin(["1101", "2101"])))
    ]

    if df_beli.empty:
        st.info("Belum ada transaksi pembelian.")
    else:
        st.table(df_beli)
        total_pembelian = df_beli[df_beli["Kode Debit"] == "1103"]["Jumlah"].sum()
        st.markdown(
            f'<div class="report-footer-box">Total Pembelian: Rp {total_pembelian:,.0f}</div>'.replace(",", "."),
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

def page_buku_pembantu_piutang():
    inject_css()
    top_bar()

    st.markdown('<div class="report-shell">', unsafe_allow_html=True)
    st.markdown('<div class="report-header-box">Buku Besar Pembantu Piutang</div>', unsafe_allow_html=True)
    back_to_dashboard()

    rows = get_transactions()
    df = transactions_to_df(rows)

    # Asumsi: 1102 = Piutang Usaha
    df_piu = df[(df["Kode Debit"] == "1102") | (df["Kode Kredit"] == "1102")]

    if df_piu.empty:
        st.info("Belum ada transaksi piutang.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.markdown("Catatan: nama pelanggan ditulis di kolom Keterangan.", unsafe_allow_html=True)

    for pelanggan, group in df_piu.groupby("Keterangan"):
        st.markdown(f"**Pelanggan: {pelanggan}**")
        group = group.sort_values("Tanggal")

        saldo = 0.0
        saldo_list = []
        for _, row in group.iterrows():
            if row["Kode Debit"] == "1102":
                saldo += row["Jumlah"]
            else:
                saldo -= row["Jumlah"]
            saldo_list.append(saldo)

        group = group.copy()
        group["Saldo Piutang"] = saldo_list

        st.table(group[["Tanggal", "Kode Debit", "Kode Kredit", "Jumlah", "Saldo Piutang"]])
        st.markdown("---")

    st.markdown("</div>", unsafe_allow_html=True)

def page_buku_pembantu_utang():
    inject_css()
    top_bar()

    st.markdown('<div class="report-shell">', unsafe_allow_html=True)
    st.markdown('<div class="report-header-box">Buku Besar Pembantu Utang</div>', unsafe_allow_html=True)
    back_to_dashboard()

    rows = get_transactions()
    df = transactions_to_df(rows)

    # Asumsi: 2101 = Hutang Usaha
    df_hut = df[(df["Kode Debit"] == "2101") | (df["Kode Kredit"] == "2101")]

    if df_hut.empty:
        st.info("Belum ada transaksi utang.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.markdown("Catatan: nama pemasok ditulis di kolom Keterangan.", unsafe_allow_html=True)

    for pemasok, group in df_hut.groupby("Keterangan"):
        st.markdown(f"**Pemasok: {pemasok}**")
        group = group.sort_values("Tanggal")

        saldo = 0.0
        saldo_list = []
        for _, row in group.iterrows():
            # Utang: kredit menambah saldo, debit mengurangi
            if row["Kode Kredit"] == "2101":
                saldo += row["Jumlah"]
            else:
                saldo -= row["Jumlah"]
            saldo_list.append(saldo)

        group = group.copy()
        group["Saldo Utang"] = saldo_list

        st.table(group[["Tanggal", "Kode Debit", "Kode Kredit", "Jumlah", "Saldo Utang"]])
        st.markdown("---")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# MAIN
# =========================================================
def main():
    st.set_page_config(
        page_title="SIA MERPATI",
        layout="wide"
    )

    init_db()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.page = "Login"

    if not st.session_state.logged_in:
        page_login()
        return

    inject_css()

    with st.sidebar:
        st.title("Menu")

        menu_items = [
            "Dashboard",
            "Transaksi",
            "Penjualan",
            "Pembelian",
            "Buku Pembantu Piutang",
            "Buku Pembantu Utang",
            "Jurnal",
            "Buku Besar",
            "Neraca Saldo",
            "Laba Rugi",
            "Akun",
        ]

        current_page = st.session_state.page if st.session_state.page != "Login" else "Dashboard"
        if current_page not in menu_items:
            current_page = "Dashboard"

        page = st.radio(
            "",
            menu_items,
            index=menu_items.index(current_page),
        )
        st.session_state.page = page

    if st.session_state.page == "Dashboard":
        page_dashboard()
    elif st.session_state.page == "Transaksi":
        page_transaksi()
    elif st.session_state.page == "Penjualan":
        page_penjualan()
    elif st.session_state.page == "Pembelian":
        page_pembelian()
    elif st.session_state.page == "Buku Pembantu Piutang":
        page_buku_pembantu_piutang()
    elif st.session_state.page == "Buku Pembantu Utang":
        page_buku_pembantu_utang()
    elif st.session_state.page == "Jurnal":
        page_jurnal()
    elif st.session_state.page == "Buku Besar":
        page_buku_besar()
    elif st.session_state.page == "Neraca Saldo":
        page_neraca_saldo()
    elif st.session_state.page == "Laba Rugi":
        page_laba_rugi()
    elif st.session_state.page == "Akun":
        page_akun()
    else:
        page_dashboard()

if __name__ == "__main__":
    main()
