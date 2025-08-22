import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- PENGATURAN AWAL ---
st.set_page_config(page_title="Cashflow", page_icon="💸", layout="centered")

# --- KONEKSI & INISIALISASI DATABASE ---lom baru: kategori dan akun
def init_db():
    conn = sqlite3.connect('cashflow.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal DATE NOT NULL,
            jenis TEXT NOT NULL,
            kategori TEXT NOT NULL,
            akun TEXT NOT NULL,
            jumlah REAL NOT NULL,
            deskripsi TEXT
        )
    ''')
    conn.commit()
    return conn

# --- FUNGSI-FUNGSI UTAMA APLIKASI ---

# 1. Fungsi untuk halaman "Catat Transaksi"
def halaman_catat_transaksi(conn):
    st.header("📝 Catat Transaksi Baru")

    KATEGORI_PEMASUKAN = ["Gaji", "Dividen", "Hibah", "Hadiah", "Lainnya"]
    KATEGORI_PENGELUARAN = ["Dana Darurat", "Hobi/Keinginan", "Internet", "Investasi/Tabungan", "Kendaraan/Mobilitas", "Kesehatan/Perawatan",
                            "Lain-lain", "Main/Jajan", "Makan", "Tak Terduga", "Pengembangan Diri", "Reimbursement", "Tempat Tinggal"]
    PILIHAN_AKUN = ["BNI", "Cash", "Jago", "Jago (tersier)", "GoPay", "ShopeePay", "DANA", "OVO"]

    jenis = st.selectbox("Jenis Transaksi", ["Pengeluaran", "Pemasukan"])

    def reset_form():
        st.session_state["jumlah_input"] = ""
        st.session_state["deskripsi_input"] = ""
        # Anda bisa menambahkan reset untuk field lain jika diperlukan
        # Contoh: st.session_state["tanggal_input"] = datetime.now()

    with st.form("form_transaksi", clear_on_submit=True):
        
        # Semua parameter 'key' dari widget di bawah ini sudah DIHAPUS
        tanggal = st.date_input("Tanggal")
        
        if jenis == "Pemasukan":
            kategori = st.selectbox("Kategori Pemasukan", KATEGORI_PEMASUKAN)
        else:
            kategori = st.selectbox("Kategori Pengeluaran", KATEGORI_PENGELUARAN)

        akun = st.selectbox("Akun", PILIHAN_AKUN)
        jumlah_input = st.text_input(label="Jumlah (Rp)", placeholder="Contoh: 50000")
        deskripsi = st.text_area("Deskripsi")

        # Membuat dua kolom untuk kedua tombol
        col1, col2 = st.columns([1, 4])
        with col1:
            # Tombol Reset juga merupakan submit button, tapi kita tidak akan melakukan apa-apa dengannya
            st.form_submit_button("Reset", on_click=reset_form, use_container_width=True)
        with col2:
            submitted = st.form_submit_button("Simpan Transaksi", use_container_width=True)

        if submitted:
            jumlah_str = jumlah_input.replace('.', '').strip()
            
            # Validasi input
            if not jumlah_str.isdigit():
                st.error("Input jumlah tidak valid. Harap masukkan angka saja.")
            elif int(jumlah_str) <= 0:
                st.warning("Jumlah harus lebih besar dari 0.")
            else:
                # Jika semua validasi lolos
                jumlah = int(jumlah_str)
                c = conn.cursor()
                c.execute(
                    "INSERT INTO transaksi (tanggal, jenis, kategori, akun, jumlah, deskripsi) VALUES (?, ?, ?, ?, ?, ?)",
                    (tanggal, jenis, kategori, akun, jumlah, deskripsi)
                )
                conn.commit()
                st.success(f"Transaksi '{kategori}' sebesar Rp{jumlah:,.0f}".replace(',', '.') + " berhasil disimpan 👌")
                st.balloons()
                
# 2. Fungsi untuk halaman "Lihat Saldo Akun"
def halaman_lihat_saldo(conn):
    st.header("💰 Saldo per Akun")

    # 1. Daftar semua akun yang ingin ditampilkan, beserta URL logonya
    # Anda bisa mencari dan mengganti URL logonya jika mau
    SEMUA_AKUN = {
        "BNI": "https://upload.wikimedia.org/wikipedia/id/thumb/5/55/BNI_logo.svg/1280px-BNI_logo.svg.png",
        "Cash": "https://upload.wikimedia.org/wikipedia/commons/d/d8/Indonesia_2016_100000r_o.jpg",
        "Jago": "https://upload.wikimedia.org/wikipedia/commons/c/c0/Logo-jago.svg",
        "Jago (tersier)": "https://upload.wikimedia.org/wikipedia/commons/c/c0/Logo-jago.svg",
        "GoPay": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Gopay_logo.svg/2560px-Gopay_logo.svg.png",
        "ShopeePay": "https://upload.wikimedia.org/wikipedia/commons/f/fe/Shopee.svg",
        "DANA": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Logo_dana_blue.svg/2560px-Logo_dana_blue.svg.png",
        "OVO": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Logo_ovo_purple.svg/2560px-Logo_ovo_purple.svg.png"
    }
    
    st.markdown("""
    <style>
    .list-logo {
        height: 40px;           /* Ukuran tinggi logo */
        width: auto;            /* Lebar otomatis agar proporsional */
        object-fit: contain;    /* Memastikan seluruh logo terlihat */
        border-radius: 4px;
    }
    .account-name {
        font-size: 24px;        /* FONT NAMA AKUN DIPERBESAR */
        font-weight: 500;
        line-height: 1.5;         /* Menyesuaikan alignment vertikal */
    }
    .account-balance {
        font-size: 26px;        /* FONT SALDO DIPERBESAR */
        font-weight: 600;
    }
    .account-balance-negative {
        color: #ff4b4b;         /* Warna merah untuk saldo minus */
    }
    </style>
    """, unsafe_allow_html=True)

    # Proses pengambilan dan perhitungan data tidak berubah
    df = pd.read_sql_query("SELECT * FROM transaksi", conn)
    saldo_akun = {}
    if not df.empty:
        pemasukan = df[df['jenis'] == 'Pemasukan'].groupby('akun')['jumlah'].sum()
        pengeluaran = df[df['jenis'] == 'Pengeluaran'].groupby('akun')['jumlah'].sum()
        saldo_df = pd.concat([pemasukan, pengeluaran], axis=1).fillna(0)
        saldo_df.columns = ['pemasukan', 'pengeluaran']
        saldo_df['saldo'] = saldo_df['pemasukan'] - saldo_df['pengeluaran']
        saldo_akun = saldo_df['saldo'].to_dict()

    # Hitung total saldo dari semua akun
    total_saldo_keseluruhan = sum(saldo_akun.values())

    if total_saldo_keseluruhan < 0:
        formatted_total = f"-Rp {abs(total_saldo_keseluruhan):,.0f}".replace(',', '.')
    else:
        formatted_total = f"Rp {total_saldo_keseluruhan:,.0f}".replace(',', '.')
    
    st.metric(label="Total Saldo", value=formatted_total)
    st.markdown("---")
    
    for akun_name, logo_url in SEMUA_AKUN.items():
        saldo = saldo_akun.get(akun_name, 0)
        
        col1, col2 = st.columns([3, 2])

        with col1:
            logo_col, name_col = st.columns([1, 4])
            with logo_col:
                st.markdown(f'<img src="{logo_url}" class="list-logo">', unsafe_allow_html=True)
            with name_col:
                st.markdown(f'<span class="account-name">{akun_name}</span>', unsafe_allow_html=True)
        
        with col2:
            if saldo < 0:
                formatted_saldo = f"-Rp {abs(saldo):,.0f}".replace(',', '.')
            else:
                formatted_saldo = f"Rp {saldo:,.0f}".replace(',', '.')
            
            color_class = "account-balance-negative" if saldo < 0 else ""
            
            st.markdown(f'''
                <div style="text-align: right;">
                    <span class="account-balance {color_class}">{formatted_saldo}</span>
                </div>
            ''', unsafe_allow_html=True)

        st.divider()

# 3. Fungsi untuk halaman "Daftar Transaksi"
def halaman_daftar_transaksi(conn):
    st.header("🧾 Daftar Semua Transaksi")
    df = pd.read_sql_query("SELECT tanggal, jenis, kategori, akun, jumlah, deskripsi FROM transaksi ORDER BY tanggal DESC", conn)

    if df.empty:
        st.info("Belum ada data transaksi.")
    else:
        st.dataframe(df, use_container_width=True)


# --- STRUKTUR UTAMA APLIKASI ---
def main():
    conn = init_db()
    st.title("Langkah awal menuju ✨*Financial Freedom*✨")
    # st.markdown("""
    # <h1 style="text-align: wide; background: -webkit-linear-gradient(#00F260, #0575E6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
    #     Langkah awal menuju ✨Financial Freedom✨
    # </h1>
    # """, unsafe_allow_html=True)

    # --- BAGIAN NAVIGASI MENGGUNAKAN TOMBOL ---    
    # 1. Buat beberapa kolom untuk menampung tombol
    col1, col2, col3 = st.columns(3)

    # 2. Letakkan tombol di setiap kolom
    with col1:
        if st.button("📝 Catat Transaksi", use_container_width=True):
            st.session_state.page = "Catat Transaksi"
    with col2:
        if st.button("💰 Lihat Saldo Akun", use_container_width=True):
            st.session_state.page = "Lihat Saldo Akun"
    with col3:
        if st.button("🧾 Daftar Transaksi", use_container_width=True):
            st.session_state.page = "Daftar Transaksi"

    # Garis pemisah untuk estetika
    st.markdown("---")

    # 3. Inisialisasi halaman default jika belum ada
    if "page" not in st.session_state:
        st.session_state.page = "Catat Transaksi"

    # 4. Tampilkan halaman berdasarkan state yang tersimpan
    if st.session_state.page == "Catat Transaksi":
        halaman_catat_transaksi(conn)
    elif st.session_state.page == "Lihat Saldo Akun":
        halaman_lihat_saldo(conn)
    elif st.session_state.page == "Daftar Transaksi":
        halaman_daftar_transaksi(conn)
    
    conn.close()

if __name__ == "__main__":
    main()
