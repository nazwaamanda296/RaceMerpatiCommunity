import pandas as pd
from models.database import get_conn

def income_statement(start_date=None, end_date=None):
    """
    Generate detailed income statement data with optional date filtering.

    Parameters:
    - start_date (str or None): start date filter in 'YYYY-MM-DD' format
    - end_date (str or None): end date filter in 'YYYY-MM-DD' format

    Returns:
    - dict: structured income statement data including sections and totals
    """

    # Prepare SQL with optional date filters
    sql = """
        SELECT a.code, a.name,
               SUM(CASE WHEN t.debit_account_id = a.id THEN t.amount ELSE 0 END) AS total_debit,
               SUM(CASE WHEN t.credit_account_id = a.id THEN t.amount ELSE 0 END) AS total_credit
        FROM accounts a
        LEFT JOIN transactions t
          ON t.debit_account_id = a.id OR t.credit_account_id = a.id
    """
    params = []
    if start_date and end_date:
        sql += " WHERE t.tx_date BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    elif start_date:
        sql += " WHERE t.tx_date >= ?"
        params.append(start_date)
    elif end_date:
        sql += " WHERE t.tx_date <= ?"
        params.append(end_date)

    sql += """
        GROUP BY a.id, a.code, a.name
        HAVING total_debit > 0 OR total_credit > 0
        ORDER BY a.code
    """

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    df = pd.DataFrame(rows, columns=["code", "name", "debit", "credit"])
    df["code"] = df["code"].astype(str)

    # Define account groups by prefix
    # Pendapatan (Revenue): codes starting with '41'
    pendapatan_df = df[df["code"].str.startswith("41")]
    # Harga Pokok Penjualan (Cost of Goods Sold): codes starting with '51'
    hpp_df = df[df["code"].str.startswith("51")]
    # Beban Operasional (Operating Expenses): codes starting with '61'
    beban_op_df = df[df["code"].str.startswith("61")]
    # Pendapatan Lain-lain (Other Income): codes starting with '71'
    pendapatan_lain_df = df[df["code"].str.startswith("71")]
    # Beban Lain-lain (Other Expenses): codes starting with '72'
    beban_lain_df = df[df["code"].str.startswith("72")]

    # Aggregation helper functions
    def net_credit(df):
        return df["credit"].sum() - df["debit"].sum()

    def net_debit(df):
        return df["debit"].sum() - df["credit"].sum()

    # Calculate totals per group
    total_pendapatan = net_credit(pendapatan_df)
    total_hpp = net_debit(hpp_df)
    total_beban_op = net_debit(beban_op_df)
    total_pendapatan_lain = net_credit(pendapatan_lain_df)
    total_beban_lain = net_debit(beban_lain_df)

    # Laba Kotor (Gross Profit): Pendapatan - HPP
    laba_kotor = total_pendapatan - total_hpp
    # Laba Bersih (Net Profit): Laba Kotor - Beban Operasional + Pendapatan Lain-lain - Beban Lain-lain
    laba_bersih = laba_kotor - total_beban_op + total_pendapatan_lain - total_beban_lain

    # Build structured detailed items for UI rendering
    def build_items(df, is_credit=True):
        items = []
        for _, row in df.iterrows():
            amount = row["credit"] - row["debit"] if is_credit else row["debit"] - row["credit"]
            items.append({
                "code": row["code"],
                "name": row["name"],
                "amount": amount,
            })
        return items

    income_statement_data = {
        "pendapatan": {
            "total": total_pendapatan,
            "items": build_items(pendapatan_df, is_credit=True),
        },
        "hpp": {
            "total": total_hpp,
            "items": build_items(hpp_df, is_credit=False),
        },
        "beban_operasional": {
            "total": total_beban_op,
            "items": build_items(beban_op_df, is_credit=False),
        },
        "pendapatan_lain": {
            "total": total_pendapatan_lain,
            "items": build_items(pendapatan_lain_df, is_credit=True),
        },
        "beban_lain": {
            "total": total_beban_lain,
            "items": build_items(beban_lain_df, is_credit=False),
        },
        "laba_kotor": laba_kotor,
        "laba_bersih": laba_bersih,
    }

    return income_statement_data
