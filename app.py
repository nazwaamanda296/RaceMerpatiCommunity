import streamlit as st

from models.database import init_db
from libs import inject_css

from screens.login import page_login
from screens.dashboard import page_dashboard
from screens.transactions import page_transaksi
from screens.penjualan import page_penjualan
from screens.pembelian import page_pembelian
from screens.pembantu_piutang import page_buku_pembantu_piutang
from screens.pembantu_utang import page_buku_pembantu_utang
from screens.journal import page_jurnal
from screens.ledger import page_buku_besar
from screens.trial_balance import page_neraca_saldo
from screens.income_statement import page_laba_rugi
from screens.accounts import page_akun
from screens.posisi_keuangan import page_posisi_keuangan   
from screens.jurnal_penyesuaian import page_jurnal_penyesuaian
from screens.inventory import main as page_inventory
from screens.jurnal_penutup import page_jurnal_penutup


def rerun():
    """Simple wrapper to trigger a Streamlit rerun using the public API."""
    st.rerun()


def main():
    st.set_page_config(
        page_title="SIA MERPATI",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # --- inisialisasi database ---
    init_db()

    # --- inisialisasi session state login ---
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.page = "Login"

    # --- kalau belum login, tampilkan halaman login saja ---
    if not st.session_state.logged_in:
        page_login()
        return

    # --- CSS global ---
    inject_css()

    # --- Sidebar button style injection to adjust width and font ---
    st.markdown(
        """
        <style>
        .sidebar .sidebar-content button.sidebar-button,
        .sidebar .sidebar-content button.sidebar-button-selected {
            font-family: 'Poppins', sans-serif;
            min-width: 200px;
            max-width: 220px;
            height: auto;
            padding: 8px 12px;
            white-space: normal; /* Allow wrapping */
            overflow-wrap: break-word;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            line-clamp: 2;
            box-orient: vertical;
            text-align: left;
            border-radius: 6px;
            margin-bottom: 6px;
            border: none;
            cursor: pointer;
            color: #333333;
            background-color: #f0f0f0;
            transition: background-color 0.3s ease;
        }
        .sidebar .sidebar-content button.sidebar-button-selected {
            background-color: #70577a;
            color: white;
            font-weight: 600;
        }
        .sidebar .sidebar-content button.sidebar-button:hover {
            background-color: #d8bfd8;
            color: #4a2c68;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ================= SIDEBAR MENU =================
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
            "Persediaan",
            "Jurnal Penyesuaian",
            "Buku Besar",
            "Neraca Saldo",
            "Laba Rugi",
            "Laporan Posisi Keuangan",   
            "Akun",
            "Jurnal Penutup",
        ]

        # halaman aktif terakhir (supaya tetap kepilih setelah rerun)
        current_page = (
            st.session_state.page
            if st.session_state.page != "Login"
            else "Dashboard"
        )
        if current_page not in menu_items:
            current_page = "Dashboard"

        # Use styled buttons instead of radio for menu selection
        for item in menu_items:
            is_selected = item == current_page
            button_class = "sidebar-button-selected" if is_selected else "sidebar-button"

            if st.button(item, key=f"sidebar_{item}"):
                st.session_state.page = item
                rerun()

        # --- LOGOUT BUTTON ---
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.page = "Login"
            rerun()

    # ================= ROUTING HALAMAN =================
    p = st.session_state.page

    if p == "Dashboard":
        page_dashboard()
    elif p == "Transaksi":
        page_transaksi()
    elif p == "Penjualan":
        page_penjualan()
    elif p == "Pembelian":
        page_pembelian()
    elif p == "Buku Pembantu Piutang":
        page_buku_pembantu_piutang()
    elif p == "Buku Pembantu Utang":
        page_buku_pembantu_utang()
    elif p == "Jurnal":
        page_jurnal()
    elif p == "Persediaan":
        page_inventory()
    elif p == "Jurnal Penyesuaian":
        page_jurnal_penyesuaian()
    elif p == "Buku Besar":
        page_buku_besar()
    elif p == "Neraca Saldo":
        page_neraca_saldo()
    elif p == "Laba Rugi":
        page_laba_rugi()
    elif p == "Laporan Posisi Keuangan":   
        page_posisi_keuangan()
    elif p == "Akun":
        page_akun()
    elif p == "Jurnal Penutup":
        page_jurnal_penutup()
    else:
        page_dashboard()


if __name__ == "__main__":
    main()
