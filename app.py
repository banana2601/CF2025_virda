import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- FUNGSI DATABASE ---
def init_db():
    conn = sqlite3.connect('keuangan.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal DATE,
            deskripsi TEXT,
            jenis TEXT,
            jumlah REAL
        )
    ''')
    conn.commit()
    return conn

# --- INTERFACE APLIKASI ---
def main():
    # Inisialisasi Database
    conn = init_db()

    st.set_page_config(page_title="Catatan Keuangan", page_icon="💰", layout="centered")
    st.title("💰 Catatan Keuangan Pribadi")

    # Form input di dalam expander
    with st.expander("📝 Tambah Transaksi Baru", expanded=False):
        with st.form("form_transaksi", clear_on_submit=True):
            tanggal = st.date_input("Tanggal")
            deskripsi = st.text_input("Deskripsi Transaksi")
            jenis = st.selectbox("Jenis", ["Pengeluaran", "Pemasukan"])
            jumlah = st.number_input("Jumlah (Rp)", min_value=0.0, format="%.2f")

            submitted = st.form_submit_button("Simpan")

            if submitted:
                c = conn.cursor()
                c.execute("INSERT INTO transaksi (tanggal, deskripsi, jenis, jumlah) VALUES (?, ?, ?, ?)",
                        (tanggal, deskripsi, jenis, jumlah))
                conn.commit()
                st.success("Transaksi berhasil disimpan!")
                st.balloons()

    # --- Dashboard ---
    st.header("📊 Dashboard")
    query = "SELECT * FROM transaksi ORDER BY tanggal DESC"
    df = pd.read_sql_query(query, conn)

    if not df.empty:
        total_pemasukan = df[df['jenis'] == 'Pemasukan']['jumlah'].sum()
        total_pengeluaran = df[df['jenis'] == 'Pengeluaran']['jumlah'].sum()
        saldo_akhir = total_pemasukan - total_pengeluaran

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pemasukan", f"Rp {total_pemasukan:,.0f}")
        col2.metric("Total Pengeluaran", f"Rp {total_pengeluaran:,.0f}")
        col3.metric("Saldo Akhir", f"Rp {saldo_akhir:,.0f}")

        # --- Tampilkan Data ---
        st.header("Riwayat Transaksi")
        st.dataframe(df[['tanggal', 'deskripsi', 'jenis', 'jumlah']])
    else:
        st.info("Belum ada data transaksi. Silakan tambahkan transaksi baru.")

if __name__ == "__main__":
    main()