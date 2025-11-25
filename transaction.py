import pandas as pd
from models.database import get_conn

def create_transaction(tx_date, description, debit_id, credit_id, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions(tx_date,description,debit_account_id,credit_account_id,amount)
        VALUES (?,?,?,?,?)
    """, (tx_date, description, debit_id, credit_id, amount))
    conn.commit()
    conn.close()

def get_transactions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.id, t.tx_date, t.description,
               da.code AS debit_code, da.name AS debit_name,
               ca.code AS credit_code, ca.name AS credit_name,
               t.amount
        FROM transactions t
        JOIN accounts da ON da.id = t.debit_account_id
        JOIN accounts ca ON ca.id = t.credit_account_id
        ORDER BY t.tx_date, t.id
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_transaction(tx_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions WHERE id=?", (tx_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_transaction(tx_id, tx_date, description, debit_id, credit_id, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE transactions
        SET tx_date=?, description=?, debit_account_id=?, credit_account_id=?, amount=?
        WHERE id=?
    """, (tx_date, description, debit_id, credit_id, amount, tx_id))
    conn.commit()
    conn.close()

def delete_transaction(tx_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()

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

def trial_balance_before_adjustment():
    """
    Return trial balance excluding transactions with 'penyesuaian' in description.
    """
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
        WHERE t.description IS NULL OR LOWER(t.description) NOT LIKE '%penyesuaian%'
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

def trial_balance_after_adjustment():
    """
    Return trial balance including all transactions, same as existing trial_balance for clarity.
    """
    return trial_balance()

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
    rows = get_transactions()
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

def transactions_to_df(rows):
    """Ubah rows transaksi (JOIN) ke DataFrame rapi."""
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

def balance_sheet():
    """
    Hitung Laporan Posisi Keuangan (Neraca):
    - Aset  : kode mulai dengan '1'
    - Kewajiban : kode mulai dengan '2'
    - Ekuitas   : kode mulai dengan '3'
    """
    tb = trial_balance()
    if tb.empty:
        return None

    tb["Kode"] = tb["Kode"].astype(str)

    # Kelompok akun
    aset = tb[tb["Kode"].str.startswith("1")].copy()
    kewajiban = tb[tb["Kode"].str.startswith("2")].copy()
    ekuitas = tb[tb["Kode"].str.startswith("3")].copy()

    # Hitung saldo (debit - kredit untuk aset, kebalik untuk kewajiban/ekuitas)
    if not aset.empty:
        aset["Saldo"] = aset["Debit"] - aset["Kredit"]
    else:
        aset["Saldo"] = pd.Series(dtype=float)

    if not kewajiban.empty:
        kewajiban["Saldo"] = kewajiban["Kredit"] - kewajiban["Debit"]
    else:
        kewajiban["Saldo"] = pd.Series(dtype=float)

    if not ekuitas.empty:
        ekuitas["Saldo"] = ekuitas["Kredit"] - ekuitas["Debit"]
    else:
        ekuitas["Saldo"] = pd.Series(dtype=float)

    total_aset = float(aset["Saldo"].sum()) if not aset.empty else 0.0
    total_kewajiban = float(kewajiban["Saldo"].sum()) if not kewajiban.empty else 0.0
    total_ekuitas = float(ekuitas["Saldo"].sum()) if not ekuitas.empty else 0.0

    return {
        "aset": aset[["Kode", "Nama Akun", "Saldo"]],
        "kewajiban": kewajiban[["Kode", "Nama Akun", "Saldo"]],
        "ekuitas": ekuitas[["Kode", "Nama Akun", "Saldo"]],
        "total_aset": total_aset,
        "total_kewajiban": total_kewajiban,
        "total_ekuitas": total_ekuitas,
    }
