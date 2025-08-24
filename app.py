# ===================================================================================
# --- MENGIMPOR LIBRARY YANG DIBUTUHKAN ---
# ===================================================================================
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
import plotly.express as px

# ===================================================================================
# --- PENGATURAN AWAL HALAMAN STREAMLIT ---
# ===================================================================================
# Mengatur judul, ikon, dan layout halaman agar tampilannya optimal.
st.set_page_config(page_title="Cashflow", page_icon="💸", layout="wide")

# ===================================================================================
# --- DEFINISI KONSTANTA ---
# ===================================================================================
# Menggunakan konstanta membuat kode lebih mudah dibaca dan dikelola.
# Jika ada perubahan, cukup ubah di satu tempat ini.

# --- Nama Halaman untuk Navigasi ---
PAGE_CATAT_TRANSAKSI = "Catat Transaksi"
PAGE_LIHAT_SALDO = "Saldo Akun"
PAGE_DAFTAR_TRANSAKSI = "Daftar Transaksi"
PAGE_DASHBOARD = "Dashboard"

# --- Label dan Nama Kolom untuk Data ---
LABEL_NOMINAL = "Nominal (Rp)"
COL_NOMINAL = "nominal_(Rp)"  # Sesuai dengan nama kolom di database.

# --- Jenis-Jenis Transaksi ---
JENIS_PEMASUKAN = "Masuk"
JENIS_PENGELUARAN = "Keluar"
KATEGORI_TOP_UP = "Top Up"  # Konstanta untuk kategori "Top Up"

# --- Daftar Kategori Transaksi ---
KATEGORI_PEMASUKAN = sorted(["Dividen", "Gaji", "Hadiah", "Hibah", "Lainnya", "Reimbursement", KATEGORI_TOP_UP])
KATEGORI_PENGELUARAN = sorted([
    "Hobi/Keinginan", "Internet", "Kendaraan/Mobilitas", "Kesehatan/Perawatan", "Lain-lain",
    "Main/Jajan", "Makan", "Pengembangan Diri", "Reimbursement", "Tak Terduga", "Tempat Tinggal",
    KATEGORI_TOP_UP
])

# --- Daftar Pilihan Akun ---
PILIHAN_AKUN = sorted([
    "BNI", "Cash", "Jago", "Jago (tersier)", "GoPay", "ShopeePay", "DANA", "OVO", "Dana Darurat", "Tabungan"
])

# --- Kamus (Dictionary) untuk Logo Akun ---
LOGO_JAGO = "https://upload.wikimedia.org/wikipedia/commons/c/c0/Logo-jago.svg"
SEMUA_AKUN_DENGAN_LOGO = {
    "BNI": "https://upload.wikimedia.org/wikipedia/id/thumb/5/55/BNI_logo.svg/1280px-BNI_logo.svg.png",
    "Cash": "https://upload.wikimedia.org/wikipedia/commons/d/d8/Indonesia_2016_100000r_o.jpg",
    "Jago": LOGO_JAGO,
    "Jago (tersier)": LOGO_JAGO,
    "GoPay": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Gopay_logo.svg/2560px-Gopay_logo.svg.png",
    "ShopeePay": "https://upload.wikimedia.org/wikipedia/commons/f/fe/Shopee.svg",
    "DANA": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Logo_dana_blue.svg/2560px-Logo_dana_blue.svg.png",
    "OVO": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Logo_ovo_purple.svg/2560px-Logo_ovo_purple.svg.png",
    "Dana Darurat": LOGO_JAGO,
    "Tabungan": LOGO_JAGO
}

# ===================================================================================
# --- FUNGSI UTILITAS TAMPILAN ---
# ===================================================================================
def custom_divider(margin_top=10, margin_bottom=30, color="#3b3d43", thickness="0.5px"):
    """Menampilkan garis pemisah horizontal dengan gaya kustom."""
    st.markdown(
        f"""<hr style="margin-top:{margin_top}px; margin-bottom:{margin_bottom}px; border:{thickness} solid {color};">""",
        unsafe_allow_html=True
    )

# ===================================================================================
# --- KONEKSI KE SUPABASE & PENGAMBILAN DATA ---
# ===================================================================================
@st.cache_resource
def init_connection():
    """Menginisialisasi koneksi ke Supabase."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

@st.cache_data(ttl=600)  # Cache data selama 10 menit
def get_data():
    """
    Mengambil, membersihkan, dan mengembalikan semua data transaksi.
    Data di-cache untuk mengurangi query berulang ke database.
    """
    try:
        response = supabase.table("Cashflow").select("*").order("tanggal", desc=True).execute()
        df = pd.DataFrame(response.data)

        if df.empty:
            return df

        # Pembersihan dan konversi tipe data terpusat
        for col in ['jenis', 'kategori', 'akun']:
            if col in df.columns:
                df[col] = df[col].str.strip()
        df['tanggal'] = pd.to_datetime(df['tanggal'])
        df[COL_NOMINAL] = pd.to_numeric(df[COL_NOMINAL])
        
        return df
    except Exception as e:
        st.error(f"Gagal mengambil data dari database: {e}")
        return pd.DataFrame()

# ===================================================================================
# --- FUNGSI-FUNGSI PEMBANTU (HELPER FUNCTIONS) ---
# ===================================================================================

# --- Helper untuk Halaman Dashboard ---
def _create_date_filters(df):
    """
    Membuat dan menampilkan widget filter tanggal dengan logika default yang cerdas.
    Default: Tanggal 1 bulan berjalan s/d hari ini.
    Fallback: Tanggal terawal di bulan berjalan s/d hari ini.
    """
    with st.expander("Filter Periode", expanded=False): # Dibuat expanded=False agar lebih terlihat
        # Jika tidak ada data sama sekali, jangan tampilkan filter.
        if df.empty:
            st.warning("Belum ada data transaksi untuk difilter.")
            return None, None

        # 1. Tentukan batas absolut (tanggal paling awal dan akhir di seluruh data)
        tgl_min_data = df['tanggal'].min().date()
        tgl_max_data = df['tanggal'].max().date()

        # 2. Tentukan logika default berdasarkan tanggal hari ini
        today = datetime.now().date()
        first_day_of_current_month = today.replace(day=1)

        # 3. Filter data hanya untuk periode bulan berjalan (dari tgl 1 s/d hari ini)
        mask_current_month = (df['tanggal'].dt.date >= first_day_of_current_month) & (df['tanggal'].dt.date <= today)
        df_current_month = df[mask_current_month]

        # 4. Tentukan nilai default untuk widget date_input
        if not df_current_month.empty:
            # Jika ADA data di bulan ini, gunakan tanggal paling awal dari data tsb
            # dan tanggal hari ini sebagai default.
            default_tgl_awal = df_current_month['tanggal'].min().date()
            default_tgl_akhir = today
        else:
            # Jika TIDAK ada data sama sekali di bulan ini, fallback ke tanggal transaksi terakhir.
            # Ini mencegah error dan menampilkan data relevan terakhir.
            default_tgl_awal = tgl_max_data
            default_tgl_akhir = tgl_max_data
        
        # Pastikan default tidak di luar rentang absolut (untuk keamanan)
        default_tgl_awal = max(default_tgl_awal, tgl_min_data)
        default_tgl_akhir = min(default_tgl_akhir, tgl_max_data)


        # 5. Tampilkan widget di Streamlit
        col1, col2 = st.columns(2)
        tgl_awal = col1.date_input("Dari", 
                                   value=default_tgl_awal, 
                                   min_value=tgl_min_data, 
                                   max_value=tgl_max_data)
        tgl_akhir = col2.date_input("Sampai", 
                                    value=default_tgl_akhir, 
                                    min_value=tgl_min_data, 
                                    max_value=tgl_max_data)

    # Validasi standar
    if tgl_awal > tgl_akhir:
        st.error("Tanggal Mulai tidak boleh melebihi Tanggal Selesai.")
        return None, None

    return tgl_awal, tgl_akhir

def _display_summary_pie_chart(df, title):
    """Menampilkan metrik total dan diagram lingkaran untuk data yang diberikan."""
    if df.empty:
        st.info(f"Tidak ada data {title.lower()} pada periode ini.")
        return

    total = df[COL_NOMINAL].sum()
    formatted_total = f"Rp {total:,.0f}".replace(',', '.')
    st.metric(f"Total {title}", formatted_total)

    data_per_kategori = df.groupby('kategori')[COL_NOMINAL].sum().sort_values(ascending=False)
    
    fig = px.pie(
        data_per_kategori.reset_index(),
        values=COL_NOMINAL,
        names='kategori',
        hole=0.3
    )
    fig.update_traces(textposition='outside', textinfo='percent+label', textfont_size=12)
    fig.update_layout(
        margin={'t': 40, 'b': 60, 'l': 60, 'r': 60},
        showlegend=False, height=400, width=400
    )
    st.plotly_chart(fig, use_container_width=False)

def _apply_detailed_filters(df):
    """Menerapkan filter detail (tahun, bulan, hari, jenis, dll.) pada DataFrame."""
    df_display = df.copy()
    df_display['hari'] = df_display['tanggal'].dt.day
    df_display['bulan'] = df_display['tanggal'].dt.month
    df_display['tahun'] = df_display['tanggal'].dt.year

    # Baris Filter 1: Waktu
    col1, col2, col3 = st.columns(3)
    selected_year = col1.selectbox("Tahun", options=["Semua"] + sorted(df_display['tahun'].unique(), reverse=True))
    month_map = {i: datetime(2000, i, 1).strftime('%B') for i in range(1, 13)}
    unique_months = sorted(df_display['bulan'].unique())
    month_options = {num: month_map[num] for num in unique_months}
    selected_month_name = col2.selectbox("Bulan", options=["Semua"] + list(month_options.values()))
    selected_day = col3.selectbox("Tanggal", options=["Semua"] + list(range(1, 32)))

    # Baris Filter 2: Atribut Transaksi
    col4, col5, col6 = st.columns(3)
    jenis_filter = col4.multiselect("Jenis", options=sorted(df_display['jenis'].unique()))
    kategori_filter = col5.multiselect("Kategori", options=sorted(df_display['kategori'].unique()))
    akun_filter = col6.multiselect("Akun", options=sorted(df_display['akun'].unique()))

    # Logika penerapan filter
    if selected_year != "Semua": df_display = df_display[df_display['tahun'] == selected_year]
    if selected_month_name != "Semua":
        month_num = next(num for num, name in month_map.items() if name == selected_month_name)
        df_display = df_display[df_display['bulan'] == month_num]
    if selected_day != "Semua": df_display = df_display[df_display['hari'] == selected_day]
    if jenis_filter: df_display = df_display[df_display['jenis'].isin(jenis_filter)]
    if kategori_filter: df_display = df_display[df_display['kategori'].isin(kategori_filter)]
    if akun_filter: df_display = df_display[df_display['akun'].isin(akun_filter)]
    
    return df_display

# --- Helper untuk Halaman Catat Transaksi ---
def _handle_submission(submitted, form_data):
    """Memproses logika submit form, termasuk validasi dan penyimpanan data."""
    if not submitted:
        return

    # Validasi input nominal
    jumlah_str = form_data['jumlah_input'].replace('.', '').strip()
    if not jumlah_str.isdigit() or int(jumlah_str) <= 0:
        st.error("Input Nominal tidak valid. Harap masukkan angka yang lebih besar dari 0.")
        return

    jumlah_int = int(jumlah_str)
    
    # Memproses transaksi Top Up (dua entri: keluar dan masuk)
    if form_data['jenis'] == JENIS_PENGELUARAN and form_data['kategori'] == KATEGORI_TOP_UP:
        if form_data['dari_akun'] == form_data['ke_akun']:
            st.warning("Akun 'Dari' dan 'Ke' tidak boleh sama.")
            return
        
        data_keluar = {
            "tanggal": form_data['tanggal'].strftime("%Y-%m-%d"), "jenis": JENIS_PENGELUARAN,
            "kategori": KATEGORI_TOP_UP, "akun": form_data['dari_akun'],
            COL_NOMINAL: jumlah_int, "deskripsi": form_data['deskripsi'],
        }
        data_masuk = {
            "tanggal": form_data['tanggal'].strftime("%Y-%m-%d"), "jenis": JENIS_PEMASUKAN,
            "kategori": KATEGORI_TOP_UP, "akun": form_data['ke_akun'],
            COL_NOMINAL: jumlah_int, "deskripsi": form_data['deskripsi'],
        }
        supabase.table("Cashflow").insert([data_keluar, data_masuk]).execute()
        st.success(f"Top Up {form_data['dari_akun']} → {form_data['ke_akun']} Rp{jumlah_int:,.0f}".replace(',', '.') + " berhasil.")

    # Memproses transaksi reguler (satu entri)
    else:
        data_to_insert = {
            "tanggal": form_data['tanggal'].strftime("%Y-%m-%d"), "jenis": form_data['jenis'],
            "kategori": form_data['kategori'], "akun": form_data['akun'],
            COL_NOMINAL: jumlah_int, "deskripsi": form_data['deskripsi'],
        }
        supabase.table("Cashflow").insert(data_to_insert).execute()
        st.success(f"Transaksi '{form_data['kategori']}' Rp{jumlah_int:,.0f}".replace(',', '.') + " berhasil disimpan.")

    # Membersihkan cache dan memuat ulang halaman untuk menampilkan data terbaru
    st.cache_data.clear()
    st.rerun()

# --- Helper untuk Halaman Daftar Transaksi (Edit/Hapus) ---
def _handle_edit_form_actions(buttons, id_terpilih, form_values):
    """Menangani aksi update, delete, atau cancel pada form edit."""
    if buttons['update']:
        supabase.table("Cashflow").update(form_values).eq("id", id_terpilih).execute()
        st.success("Transaksi berhasil diupdate!")
    elif buttons['delete']:
        supabase.table("Cashflow").delete().eq("id", id_terpilih).execute()
        st.warning("Transaksi berhasil dihapus!")
    elif buttons['cancel']:
        st.info("Aksi dibatalkan.")
    
    # Jika ada aksi, bersihkan cache dan muat ulang
    st.cache_data.clear()
    st.rerun()
    
# ===================================================================================
# --- FUNGSI-FUNGSI UTAMA HALAMAN ---
# ===================================================================================

def halaman_dashboard():
    """Menampilkan dashboard analisis visual untuk data pemasukan dan pengeluaran."""
    df = get_data()
    if df.empty:
        st.info("Belum ada data transaksi untuk ditampilkan.")
        return

    # 1. Filter Tanggal Utama
    tgl_awal, tgl_akhir = _create_date_filters(df)
    if tgl_awal is None:
        return

    st.markdown(f"###### Periode : &nbsp;&nbsp; {tgl_awal.strftime('%d %B %Y')} — {tgl_akhir.strftime('%d %B %Y')}")

    # 2. Filter data berdasarkan rentang tanggal dan jenis transaksi (kecuali Top Up)
    mask_tanggal = (df['tanggal'].dt.date >= tgl_awal) & (df['tanggal'].dt.date <= tgl_akhir)
    mask_bukan_top_up = df['kategori'] != KATEGORI_TOP_UP
    
    df_filtered_pengeluaran = df[mask_tanggal & mask_bukan_top_up & (df['jenis'] == JENIS_PENGELUARAN)]
    df_filtered_pemasukan = df[mask_tanggal & mask_bukan_top_up & (df['jenis'] == JENIS_PEMASUKAN)]
    df_filtered_semua = df[mask_tanggal]

    # 3. Tampilkan Ringkasan & Diagram Pie
    col_pengeluaran, col_pemasukan = st.columns(2)
    with col_pengeluaran:
        _display_summary_pie_chart(df_filtered_pengeluaran, "Pengeluaran")
    with col_pemasukan:
        _display_summary_pie_chart(df_filtered_pemasukan, "Pemasukan")
    
    custom_divider()

    # 4. Tampilkan Diagram Batang Pengeluaran
    st.markdown("##### Nominal Pengeluaran per Kategori")
    if not df_filtered_pengeluaran.empty:
        pengeluaran_per_kategori = df_filtered_pengeluaran.groupby('kategori')[COL_NOMINAL].sum().sort_values(ascending=False).reset_index()
        fig_bar = px.bar(
            pengeluaran_per_kategori, x='kategori', y=COL_NOMINAL,
            labels={COL_NOMINAL: 'Jumlah Pengeluaran (Rp)', 'kategori': 'Kategori'},
            text=COL_NOMINAL
        )
        fig_bar.update_traces(texttemplate='Rp %{text:,.0f}', textposition='outside')
        fig_bar.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)

    custom_divider()

    # 5. Tampilkan Tabel Detail Transaksi dengan Filter
    st.markdown("##### Detail Transaksi")
    if df_filtered_semua.empty:
        st.warning("Tidak ada transaksi pada rentang waktu yang dipilih.")
        return
        
    with st.expander("Filter Detail Transaksi"):
        df_display = _apply_detailed_filters(df_filtered_semua)

    if df_display.empty:
        st.warning("Tidak ada data yang cocok dengan filter detail Anda.")
    else:
        df_display = df_display.sort_values(by='tanggal', ascending=False).reset_index(drop=True)
        df_display.insert(0, 'No.', range(1, len(df_display) + 1))
        df_display[COL_NOMINAL] = df_display[COL_NOMINAL].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
        
        st.dataframe(
            df_display, use_container_width=True, hide_index=True,
            column_config={
                "id": None, "hari": None, "bulan": None, "tahun": None,
                "No.": st.column_config.TextColumn("No."),
                "tanggal": st.column_config.DateColumn("Tanggal", format="YYYY-MM-DD"),
            }
        )

def halaman_catat_transaksi():
    """Menampilkan form untuk mencatat transaksi baru."""
    st.session_state.setdefault("jenis", JENIS_PEMASUKAN)
    st.session_state.setdefault("kategori", KATEGORI_PEMASUKAN[0])
    st.session_state.setdefault("akun", PILIHAN_AKUN[0])
    st.session_state.setdefault("tanggal", datetime.now().date())
    
    # Pilihan Jenis & Kategori di luar form agar dinamis
    col1, col2 = st.columns(2)
    jenis = col1.selectbox("Jenis Transaksi", [JENIS_PEMASUKAN, JENIS_PENGELUARAN], key="jenis")
    
    kategori_options = KATEGORI_PEMASUKAN if jenis == JENIS_PEMASUKAN else KATEGORI_PENGELUARAN
    if st.session_state.kategori not in kategori_options:
        st.session_state.kategori = kategori_options[0]
        
    kategori = col2.selectbox("Kategori", kategori_options, key="kategori")

    with st.form("form_transaksi", clear_on_submit=True):
        tanggal = st.date_input("Tanggal", key="tanggal")
        
        # Logika kondisional untuk menampilkan field yang relevan
        if jenis == JENIS_PENGELUARAN and kategori == KATEGORI_TOP_UP:
            dari_akun = st.selectbox("Dari Akun", PILIHAN_AKUN, key="dari_akun")
            ke_akun = st.selectbox("Ke Akun", PILIHAN_AKUN, key="ke_akun")
            akun = None # Tidak digunakan untuk Top Up
        else:
            akun = st.selectbox("Akun", PILIHAN_AKUN, key="akun")
            dari_akun, ke_akun = None, None

        jumlah_input = st.text_input(LABEL_NOMINAL, placeholder="Contoh: 50000 atau 50.000 sama aja")
        deskripsi = st.text_area("Deskripsi")
        
        # Tombol form
        _, col_submit = st.columns([4, 1])
        submitted = col_submit.form_submit_button("Simpan", use_container_width=True)

        # Kumpulkan semua data dari form untuk diproses
        form_data = {
            "jenis": jenis, "kategori": kategori, "tanggal": tanggal,
            "akun": akun, "dari_akun": dari_akun, "ke_akun": ke_akun,
            "jumlah_input": jumlah_input, "deskripsi": deskripsi
        }

    # Proses submit di luar form untuk menjaga state
    _handle_submission(submitted, form_data)


def halaman_lihat_saldo():
    """Menghitung dan menampilkan saldo kumulatif untuk setiap akun."""
    col1, col2 = st.columns(2)
    df = get_data()
    
    tanggal_pilihan = col1.date_input("Lihat Saldo per Tanggal", value=datetime.now().date())

    saldo_akun = {}
    if not df.empty:
        df_per_tanggal = df[df['tanggal'].dt.date <= tanggal_pilihan].copy()

        if not df_per_tanggal.empty:
            pemasukan = df_per_tanggal[df_per_tanggal['jenis'] == JENIS_PEMASUKAN].groupby('akun')[COL_NOMINAL].sum()
            pengeluaran = df_per_tanggal[df_per_tanggal['jenis'] == JENIS_PENGELUARAN].groupby('akun')[COL_NOMINAL].sum()
            
            saldo_df = pd.concat([pemasukan, pengeluaran], axis=1).fillna(0)
            saldo_df.columns = ['pemasukan', 'pengeluaran']
            saldo_df['saldo'] = saldo_df['pemasukan'] - saldo_df['pengeluaran']
            saldo_akun = saldo_df['saldo'].to_dict()
    
    total_saldo = sum(saldo_akun.values())
    formatted_total = f"Rp {total_saldo:,.0f}".replace(',', '.')
    if total_saldo < 0:
        formatted_total = f"-Rp {abs(total_saldo):,.0f}".replace(',', '.')
    col2.metric(label=f"Total Saldo per {tanggal_pilihan.strftime('%d %B %Y')}", value=formatted_total)

    custom_divider()

    # Menampilkan daftar saldo per akun, diurutkan berdasarkan saldo terbesar
    akun_terurut = sorted(SEMUA_AKUN_DENGAN_LOGO.keys(), key=lambda akun: saldo_akun.get(akun, 0), reverse=True)

    for akun_name in akun_terurut:
        logo_url = SEMUA_AKUN_DENGAN_LOGO.get(akun_name, "")
        saldo = saldo_akun.get(akun_name, 0)
        formatted_saldo = f"Rp {saldo:,.0f}".replace(',', '.')
        if saldo < 0:
            formatted_saldo = f"-Rp {abs(saldo):,.0f}".replace(',', '.')
        
        col1, col2 = st.columns([1, 1])
        col1.markdown(f'<h5><img src="{logo_url}" height="30">&nbsp;&nbsp;{akun_name}</h5>', unsafe_allow_html=True)
        color = "red" if saldo < 0 else "inherit"
        col2.markdown(f'<h5 style="text-align: right; color: {color};">{formatted_saldo}</h5>', unsafe_allow_html=True)
        custom_divider(margin_top=15, margin_bottom=15)


def tampilkan_form_edit_hapus(df_filtered):
    """Menampilkan expander berisi form untuk mengedit atau menghapus transaksi."""
    with st.expander("✏️ Edit / Hapus Transaksi"):
        pilihan = [f"{row['id']} -- {row['tanggal'].strftime('%d/%m')} -- {row['kategori']} -- Rp {row[COL_NOMINAL]:,.0f} -- {row['deskripsi']}".replace(',', '.') for _, row in df_filtered.iterrows()]
        transaksi_terpilih_str = st.selectbox("Pilih Transaksi", ["Pilih..."] + pilihan)

        if transaksi_terpilih_str == "Pilih...":
            return

        id_terpilih = int(transaksi_terpilih_str.split(" -- ")[0])
        data_lama = df_filtered[df_filtered['id'] == id_terpilih].iloc[0]

        with st.form("form_edit"):
            st.info(f"Mengedit Transaksi ID: {id_terpilih}")
            
            tanggal_edit = st.date_input("Tanggal", value=data_lama['tanggal'].date())
            jenis_edit = st.selectbox("Jenis", [JENIS_PEMASUKAN, JENIS_PENGELUARAN], index=[JENIS_PEMASUKAN, JENIS_PENGELUARAN].index(data_lama['jenis']))
            
            # Logika pemilihan kategori yang disederhanakan
            kategori_options = KATEGORI_PEMASUKAN if jenis_edit == JENIS_PEMASUKAN else KATEGORI_PENGELUARAN
            kategori_index = kategori_options.index(data_lama['kategori']) if data_lama['kategori'] in kategori_options else 0
            kategori_edit = st.selectbox("Kategori", kategori_options, index=kategori_index)
            
            akun_edit = st.selectbox("Akun", PILIHAN_AKUN, index=PILIHAN_AKUN.index(data_lama['akun']))
            nominal_edit = st.number_input(LABEL_NOMINAL, value=int(data_lama[COL_NOMINAL]), step=1000)
            deskripsi_edit = st.text_area("Deskripsi", value=data_lama['deskripsi'])

            # Tombol Aksi
            col1, col2, col3 = st.columns(3)
            update_button = col1.form_submit_button("Update", use_container_width=True)
            cancel_button = col2.form_submit_button("Batal", use_container_width=True)
            delete_button = col3.form_submit_button("Hapus", use_container_width=True)

            # Pengumpulan data dan status tombol untuk diproses
            form_values = {
                "tanggal": tanggal_edit.strftime("%Y-%m-%d"), "jenis": jenis_edit, "kategori": kategori_edit,
                "akun": akun_edit, COL_NOMINAL: nominal_edit, "deskripsi": deskripsi_edit
            }
            button_states = {"update": update_button, "delete": delete_button, "cancel": cancel_button}

            if any(button_states.values()):
                _handle_edit_form_actions(button_states, id_terpilih, form_values)


def halaman_daftar_transaksi():
    """Menampilkan semua data transaksi dalam tabel dengan opsi filter."""
    df_all = get_data()
    if df_all.empty:
        st.info("Belum ada data transaksi.")
        return
    
    with st.expander("🔍 Filter Transaksi"):
        df_filtered = _apply_detailed_filters(df_all)

    st.subheader("Data Transaksi")
    if df_filtered.empty:
        st.warning("Tidak ada data yang cocok dengan filter Anda.")
        return
    
    df_display = df_filtered.sort_values(by='id', ascending=False).reset_index(drop=True)
    df_display.insert(0, 'No.', range(1, len(df_display) + 1))
    df_display[COL_NOMINAL] = df_display[COL_NOMINAL].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
    
    st.dataframe(df_display, use_container_width=True, hide_index=True, column_config={
        "id": st.column_config.TextColumn("ID"),
        "No.": st.column_config.TextColumn("No."),
        "tanggal": st.column_config.DateColumn("Tanggal", format="YYYY-MM-DD"),
        "hari": None, "bulan": None, "tahun": None,
    })
    
    # Fungsi form edit/hapus dipanggil dengan data yang sudah difilter
    tampilkan_form_edit_hapus(df_filtered)

# ===================================================================================
# --- STRUKTUR UTAMA APLIKASI (ROUTER) ---
# ===================================================================================
def main():
    """Fungsi utama yang menjalankan aplikasi dan mengatur navigasi antar halaman."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600&family=Dancing+Script:wght@600&display=swap');
    .judul-atas { text-align: center; font-size: 12px; color: #4a4a4a; font-family: 'Poppins', sans-serif; margin-bottom: 0px; }
    .judul-bawah { text-align: center; font-size: 36px; color: #e5e5e5; font-family: 'Dancing Script', cursive; margin-top: 0px; margin-bottom: 25px; }
    </style>
    <div class="judul-atas">Langkah Awal Menuju</div>
    <div class="judul-bawah">✨ <em>Financial Freedom</em> ✨</div>
    """, unsafe_allow_html=True)

    # Menu navigasi utama
    menu_options = {
        PAGE_DASHBOARD: "📊 Dashboard",
        PAGE_LIHAT_SALDO: "💰 Saldo Akun",
        PAGE_CATAT_TRANSAKSI: "📝 Catat Transaksi",
        PAGE_DAFTAR_TRANSAKSI: "🧾 Daftar Transaksi"
    }
    menu = st.selectbox(
        "📌 Menu",
        options=list(menu_options.keys()),
        format_func=lambda key: menu_options[key],
    )
    
    custom_divider()

    # Router untuk menampilkan halaman yang sesuai
    if menu == PAGE_DASHBOARD:
        halaman_dashboard()
    elif menu == PAGE_CATAT_TRANSAKSI:
        halaman_catat_transaksi()
    elif menu == PAGE_LIHAT_SALDO:
        halaman_lihat_saldo()
    elif menu == PAGE_DAFTAR_TRANSAKSI:
        halaman_daftar_transaksi()

# ===================================================================================
# --- TITIK MASUK EKSEKUSI PROGRAM ---
# ===================================================================================
if __name__ == "__main__":
    main()