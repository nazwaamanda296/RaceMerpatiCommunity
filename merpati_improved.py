import streamlit as st
import pandas as pd
import numpy as np
from libs import inject_css, top_bar, back_to_dashboard
from models.transaction import get_transactions, trial_balance, income_statement

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
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("")

    # ---------- Baris 2: Posisi keuangan ----------
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("")

    # ---------- Baris 3: Ringkasan laba rugi ----------
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)

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


def inject_css():
    st.markdown(
        """
        <style>
        /* base styles for dashboard panels */
        .dash-panel {
            background-color: #f5f5f7;
            padding: 1.5rem;
            border-radius: 15px;
        }
        .dash-title {
            font-size: 2rem;
            font-weight: 700;
            color: #222222;
            margin-bottom: 0.3rem;
        }
        .dash-sub {
            font-size: 1.2rem;
            color: #666666;
            margin-bottom: 1.5rem;
            font-weight: 500;
        }
        .dash-card {
            padding: 1rem;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            margin-bottom: 1rem;
            box-shadow: 1px 2px 6px rgb(0 0 0 / 0.1);
            text-align: center;
        }
        .dash-card-title {
            font-size: 1rem;
            margin-bottom: 0.3rem;
        }
        .dash-card-sub {
            font-size: 1.6rem;
        }
        .summary-box {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 1rem 1.5rem;
            box-shadow: 0 2px 4px rgb(0 0 0 / 0.05);
            margin-bottom: 1.5rem;
        }
        /* color themes */
        .yellow {
            background-color: #facc15; /* tailwind yellow-400 */
            color: #202020;
        }
        .mint {
            background-color: #6ee7b7; /* tailwind green-300 */
            color: #1f2937;
        }
        .lilac {
            background-color: #c4b5fd; /* tailwind purple-300 */
            color: #1e3a8a;
        }
        .pink {
            background-color: #f9a8d4; /* tailwind pink-300 */
            color: #772244;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
