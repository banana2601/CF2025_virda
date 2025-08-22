import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- PENGATURAN AWAL ---
st.set_page_config(page_title="Cashflow", page_icon="💸", layout="centered")

# --- KONEKSI KE SUPABASE ---
@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

# --- FUNGSI-FUNGSI UTAMA APLIKASI ---

def halaman_catat_transaksi():
    st.header("📝 Catat Transaksi Baru")

    KATEGORI_PEMASUKAN = ["Gaji", "Dividen", "Hibah", "Hadiah", "Lainnya"]
    KATEGORI_PENGELUARAN = ["Dana Darurat", "Hobi/Keinginan", "Internet", "Investasi/Tabungan", "Kendaraan/Mobilitas", "Kesehatan/Perawatan",
                             "Lain-lain", "Main/Jajan", "Makan", "Tak Terduga", "Pengembangan Diri", "Reimbursement", "Tempat Tinggal"]
    PILIHAN_AKUN = ["BNI", "Cash", "Jago", "Jago (tersier)", "GoPay", "ShopeePay", "DANA", "OVO"]

    jenis = st.selectbox("Jenis Transaksi", ["Pengeluaran", "Pemasukan"])

    with st.form("form_transaksi", clear_on_submit=True):
        tanggal = st.date_input("Tanggal")
        
        if jenis == "Pemasukan":
            kategori = st.selectbox("Kategori Pemasukan", KATEGORI_PEMASUKAN)
        else:
            kategori = st.selectbox("Kategori Pengeluaran", KATEGORI_PENGELUARAN)

        akun = st.selectbox("Akun", PILIHAN_AKUN)
        jumlah_input = st.text_input(label="Jumlah (Rp)", placeholder="Contoh: 50000")
        deskripsi = st.text_area("Deskripsi")

        submitted = st.form_submit_button("Simpan Transaksi", use_container_width=True)

        if submitted:
            jumlah_str = jumlah_input.replace('.', '').strip()
            
            if not jumlah_str.isdigit():
                st.error("Input jumlah tidak valid. Harap masukkan angka saja.")
            elif int(jumlah_str) <= 0:
                st.warning("Jumlah harus lebih besar dari 0.")
            else:
                jumlah_int = int(jumlah_str)
                
                data_to_insert = {
                    "tanggal": tanggal.strftime("%Y-%m-%d"),
                    "jenis": jenis,
                    "kategori": kategori,
                    "akun": akun,
                    "jumlah": jumlah_int,
                    "deskripsi": deskripsi
                }
                
                # Mengirim data ke tabel 'Cashflow' di Supabase
                supabase.table("Cashflow").insert(data_to_insert).execute()
                
                st.success(f"Transaksi '{kategori}' sebesar Rp{jumlah_int:,.0f}".replace(',', '.') + " berhasil disimpan 👌")
                st.balloons()
                
def halaman_lihat_saldo():
    st.header("💰 Saldo per Akun")

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
    .list-logo { height: 40px; width: auto; object-fit: contain; border-radius: 4px; }
    .account-name { font-size: 18px; font-weight: 500; line-height: 2.5; }
    .account-balance { font-size: 20px; font-weight: 600; }
    .account-balance-negative { color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

    # Mengambil data dari tabel 'Cashflow' di Supabase
    response = supabase.table("Cashflow").select("akun, jenis, jumlah").execute()
    data = response.data
    
    saldo_akun = {}
    if data:
        df = pd.DataFrame(data)
        df['jumlah'] = pd.to_numeric(df['jumlah'])
        
        pemasukan = df[df['jenis'] == 'Pemasukan'].groupby('akun')['jumlah'].sum()
        pengeluaran = df[df['jenis'] == 'Pengeluaran'].groupby('akun')['jumlah'].sum()
        saldo_df = pd.concat([pemasukan, pengeluaran], axis=1).fillna(0)
        saldo_df.columns = ['pemasukan', 'pengeluaran']
        saldo_df['saldo'] = saldo_df['pemasukan'] - saldo_df['pengeluaran']
        saldo_akun = saldo_df['saldo'].to_dict()

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

def halaman_daftar_transaksi():
    st.header("🧾 Daftar Semua Transaksi")

    # Mengambil data dari tabel 'Cashflow' di Supabase
    response = supabase.table("Cashflow").select("tanggal, jenis, kategori, akun, jumlah, deskripsi").order("tanggal", desc=True).execute()
    data = response.data
    
    if not data:
        st.info("Belum ada data transaksi.")
    else:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

# --- STRUKTUR UTAMA APLIKASI ---
def main():
    st.title("Langkah awal menuju ✨*Financial Freedom*✨")
 
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📝 Catat Transaksi", use_container_width=True):
            st.session_state.page = "Catat Transaksi"
    with col2:
        if st.button("💰 Lihat Saldo Akun", use_container_width=True):
            st.session_state.page = "Lihat Saldo Akun"
    with col3:
        if st.button("🧾 Daftar Transaksi", use_container_width=True):
            st.session_state.page = "Daftar Transaksi"

    st.markdown("---")

    if "page" not in st.session_state:
        st.session_state.page = "Catat Transaksi"

    if st.session_state.page == "Catat Transaksi":
        halaman_catat_transaksi()
    elif st.session_state.page == "Lihat Saldo Akun":
        halaman_lihat_saldo()
    elif st.session_state.page == "Daftar Transaksi":
        halaman_daftar_transaksi()

if __name__ == "__main__":
    main()