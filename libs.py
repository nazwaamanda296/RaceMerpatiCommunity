import streamlit as st
import hashlib

def rerun():
    """Simple wrapper to trigger a Streamlit rerun using the public API."""
    st.rerun()

def inject_css():
    st.markdown("""
        <style>
        /* Import Poppins font from Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;700;800&display=swap');

        /* General dash card style */
        .dash-card {
            padding: 20px 25px;
            border-radius: 20px;
            margin-bottom: 22px;
            font-weight: 700;
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #333;
        }
        .dash-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
        }

        /* Pastel colors */
        .yellow {
            background: linear-gradient(135deg, #FFF6CC, #FFE99C);
            color: #665500;
        }
        .mint {
            background: linear-gradient(135deg, #D7F3E3, #A3E4C7);
            color: #1A4D3E;
        }
        .lilac {
            background: linear-gradient(135deg, #E9D8FD, #C8A2F8);
            color: #4B2961;
        }
        .pink {
            background: linear-gradient(135deg, #FFD7E3, #FFA3B1);
            color: #610433;
        }
        /* New pastel blue and green */
        .pastel-blue {
            background: linear-gradient(135deg, #D0E7FF, #A3C8FF);
            color: #1A3A66;
        }
        .pastel-green {
            background: linear-gradient(135deg, #DFFFE9, #A6FFC1);
            color: #1A593A;
        }

        /* Titles inside dash cards */
        .dash-card-title {
            font-size: 1.3rem;
            margin-bottom: 8px;
            letter-spacing: 0.03em;
        }

        /* Subtitles inside dash cards */
        .dash-card-sub {
            font-size: 1.15rem;
            opacity: 0.85;
            font-weight: 500;
        }

        /* Dashboard panels */
        .dash-panel {
            padding: 25px 30px;
            background-color: #f7f1e1;
            border-radius: 22px;
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.05);
            margin-bottom: 30px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Added styles for report box layouts */
        .report-shell {
            padding: 20px 25px;
            border-radius: 20px;
            margin-bottom: 22px;
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
            background-color: #fff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #333;

            /* New added styles to fix text overflow */
            max-width: 100%;
            word-wrap: break-word;
            overflow-wrap: break-word;
            white-space: normal;
            box-sizing: border-box;
        }

        /* Updated styles for report header box to enlarge for longer text */
        .report-header-box {
            font-weight: 700;
            font-size: 1.5rem;  /* increased font size */
            padding: 15px 40px;  /* increased horizontal padding */
            margin-bottom: 18px;
            border-radius: 14px;
            background: linear-gradient(135deg, #A3C8FF, #D7F3E3);
            color: #1A3A66;
            box-shadow: 0 6px 12px rgba(26, 58, 102, 0.2);
            user-select: none;

            /* New added styles to fix text overflow */
            max-width: 100%;
            word-wrap: break-word;
            overflow-wrap: break-word;
            white-space: normal;
            box-sizing: border-box;
        }

        .report-footer-box {
            font-weight: 600;
            font-size: 1.15rem;
            padding: 12px 20px;
            margin-top: 18px;
            border-radius: 14px;
            background: linear-gradient(135deg, #D7F3E3, #A3E4C7);
            color: #1A4D3E;
            box-shadow: 0 5px 10px rgba(26, 77, 62, 0.15);
            text-align: right;
            user-select: none;
        }

        /* Quick menu buttons */
        .stButton > button {
            padding: 12px 28px !important;
            border-radius: 14px !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            margin-bottom: 8px !important;
            box-shadow: 0 3px 10px rgba(0,0,0,0.12) !important;
            color: #fff !important;
            border: none !important;
            cursor: pointer !important;
            width: 100%;
            transition: background-color 0.3s ease, box-shadow 0.3s ease;
        }
        .stButton > button:focus {
            outline: none !important;
        }
        /* Colors for quick menu buttons, pastel themed with pink, blue, purple, green cycle */
        .stButton > button:enabled:nth-child(4n+1) {
            background-color: #FFB6C1 !important; /* pastel pink */
            color: #610433 !important;
        }
        .stButton > button:enabled:nth-child(4n+2) {
            background-color: #A3C8FF !important; /* pastel blue */
            color: #1A3A66 !important;
        }
        .stButton > button:enabled:nth-child(4n+3) {
            background-color: #C8A2F8 !important; /* lilac/purple */
            color: #4B2961 !important;
        }
        .stButton > button:enabled:nth-child(4n) {
            background-color: #A3E4C7 !important; /* pastel green */
            color: #1A4D3E !important;
        }
        .stButton > button:enabled:hover:nth-child(4n+1) {
            background-color: #FFA3B1 !important;
            box-shadow: 0 5px 15px rgba(97, 4, 51, 0.6) !important;
        }
        .stButton > button:enabled:hover:nth-child(4n+2) {
            background-color: #82B0FF !important;
            box-shadow: 0 5px 15px rgba(26, 58, 102, 0.6) !important;
        }
        .stButton > button:enabled:hover:nth-child(4n+3) {
            background-color: #B593F8 !important;
            box-shadow: 0 5px 15px rgba(75, 41, 97, 0.6) !important;
        }
        .stButton > button:enabled:hover:nth-child(4n) {
            background-color: #8DD7B0 !important;
            box-shadow: 0 5px 15px rgba(26, 77, 62, 0.6) !important;
        }

        /* --- New Sidebar Styling Enhance --- */
        /* Style the sidebar container */
        [data-testid="stSidebarNav"] {
            background: linear-gradient(135deg, #A3C8FF, #D7F3E3);
            padding: 25px 15px 25px 25px;
            border-radius: 0 25px 25px 0;
            box-shadow: 3px 0 15px rgba(0, 0, 0, 0.1);
        }

        /* Sidebar title */
        [data-testid="stSidebarNav"]>div > h1, [data-testid="stSidebarNav"] > div > h2 {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 900;
            font-size: 2rem;
            color: #1A3A66;
            letter-spacing: 0.08em;
            margin-bottom: 30px;
            text-align: center;
            user-select: none;
        }

        /* Sidebar buttons container */
        .sidebar-button {
            margin-bottom: 10px;
        }

        /* Highlight selected button */
        .sidebar-button-selected > button {
            background-color: #82B0FF !important;
            color: white !important;
            box-shadow: 0 6px 12px rgba(26, 58, 102, 0.8) !important;
        }

        /* Table styles */
        /* Targets Streamlit tables and dataframes */
        div[data-testid="stTable"] table, div[data-testid="stDataFrame"] table {
            border-collapse: separate !important;
            border-spacing: 0 !important;
            width: 100%;
            border: 1px solid #ddd;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 0.9rem;
            color: #333;
        }
        div[data-testid="stTable"] th, div[data-testid="stDataFrame"] th {
            background: linear-gradient(135deg, #A3C8FF, #D7F3E3);
            color: #1A3A66;
            font-weight: 700;
            padding: 4px 6px;
            border-bottom: 2px solid #777;
            text-align: left;
        }
        div[data-testid="stTable"] td, div[data-testid="stDataFrame"] td {
            padding: 4px 6px;
            border-bottom: 1px solid #eee;
        }
        /* Striped rows */
        div[data-testid="stTable"] tbody tr:nth-child(odd),
        div[data-testid="stDataFrame"] tbody tr:nth-child(odd) {
            background-color: #f7f9fc;
        }
        /* Hover highlight */
        div[data-testid="stTable"] tbody tr:hover,
        div[data-testid="stDataFrame"] tbody tr:hover {
            background-color: #ddeeff;
            cursor: pointer;
        }

        /* --- Login Screen Styling --- */
        .stApp {
            height: 100vh;
            background: linear-gradient(135deg, #82B0FF, #FFB6C1);
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Container for the login form */
        .css-1lcbmhc.egzxvld0 { /* This targets Streamlit's main content container, adjust if needed */
            background: transparent !important;
            box-shadow: none !important;
        }

        .login-title {
            font-size: 3rem;
            font-weight: 800;
            color: #ffffff;
            text-align: center;
            margin-bottom: 10px;
            letter-spacing: 0.12em;
            text-shadow: 1px 1px 5px rgba(0,0,0,0.5);
            font-family: 'Poppins', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        .login-sub {
            font-size: 1.25rem;
            font-weight: 500;
            color: #f0e6f6;
            text-align: center;
            margin-bottom: 30px;
            letter-spacing: 0.07em;
            font-style: italic;
            font-family: 'Poppins', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px 15px;
            margin-bottom: 20px;
            border-radius: 8px;
            border: 1px solid #ccc;
            font-size: 1.1rem;
            font-family: 'Poppins', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: white;
            color: black;
            font-weight: 400;
            box-shadow: none;
            transition: background 0.3s ease, box-shadow 0.3s ease;
            cursor: text;
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
        }

        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            box-shadow: 0 0 3px 2px rgba(0, 123, 255, 0.6);
            background: white;
        }

        /* Style the login button */
        .stButton > button {
            background: linear-gradient(135deg, #ff8fa3, #ff4d6d) !important;
            color: white !important;
            font-size: 1.2rem !important;
            font-weight: 700 !important;
            padding: 14px 30px !important;
            border-radius: 18px !important;
            border: none !important;
            box-shadow: 0 6px 15px rgba(255, 77, 109, 0.6) !important;
            transition: background 0.3s ease, box-shadow 0.3s ease !important;
            width: 100%;
            cursor: pointer !important;
            font-family: 'Poppins', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, #ff4d6d, #ff1a3c) !important;
            box-shadow: 0 8px 20px rgba(255, 26, 60, 0.8) !important;
        }
        </style>
    """, unsafe_allow_html=True)

def top_bar():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"Masuk sebagai: {st.session_state.get('username', '')}")
    with col2:
        if st.button("Logout", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.page = "Login"
            rerun()

def back_to_dashboard():
    if st.button("Kembali ke Dashboard", key="back_to_dashboard_btn"):
        st.session_state.page = "Dashboard"
        rerun()

from fpdf import FPDF
import io

def format_rupiah(value: float) -> str:
    """Format number to Rupiah currency string with dots as thousand separator and 2 decimals.""" 
    if value is None:
        return ""
    return "Rp {:,.2f}".format(value).replace(",", ".")

def generate_income_statement_pdf(data, start_date=None, end_date=None):
    """
    Generate a PDF bytes of the income statement report.
    Args:
        data (dict): Income statement data dictionary.
        start_date (str): Start date filter.
        end_date (str): End date filter.
    Returns:
        bytes: PDF data in bytes.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Laporan Laba Rugi", ln=True, align="C")

    if start_date and end_date:
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Periode: {start_date} s/d {end_date}", ln=True, align="C")

    pdf.ln(10)

    def add_section(title, section_data, is_credit=True):
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)  # dark blue
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.set_text_color(0, 0, 0)  # black
        if section_data and section_data.get("items"):
            for item in section_data["items"]:
                amount_str = format_rupiah(item["amount"])
                pdf.cell(150, 8, f"{item['code']} {item['name']}", border=0)
                pdf.cell(40, 8, amount_str, border=0, align='R')
                pdf.ln()
        total_str = format_rupiah(section_data.get("total", 0))
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(150, 8, "TOTAL", border=0)
        pdf.cell(40, 8, total_str, border=0, align='R')
        pdf.ln(10)

    add_section("Pendapatan", data.get("pendapatan", {}), is_credit=True)
    add_section("Harga Pokok Penjualan", data.get("hpp", {}), is_credit=False)
    add_section("Beban Operasional", data.get("beban_operasional", {}), is_credit=False)
    add_section("Pendapatan Lain-lain", data.get("pendapatan_lain", {}), is_credit=True)
    add_section("Beban Lain-lain", data.get("beban_lain", {}), is_credit=False)

    pdf.set_font("Arial", 'B', 14)
