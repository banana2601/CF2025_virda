# ===================================================================================
# --- MENGIMPOR LIBRARY YANG DIBUTUHKAN ---
# ===================================================================================
import streamlit as st
import pandas as pd
# Menambahkan timedelta untuk kalkulasi tanggal
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
# Jika ada perubahan nama atau label, cukup ubah di satu tempat ini.

# --- Nama Halaman untuk Navigasi ---
PAGE_CATAT_TRANSAKSI = "Catat Transaksi"
PAGE_LIHAT_SALDO = "Saldo Akun"
PAGE_DAFTAR_TRANSAKSI = "Daftar Transaksi"
PAGE_DASHBOARD = "Dashboard"

# --- Label dan Nama Kolom untuk Data ---
LABEL_NOMINAL = "Nominal (Rp)"
COL_NOMINAL = "nominal_(Rp)" # Sesuai dengan nama kolom di database.

# --- Jenis-Jenis Transaksi ---
JENIS_PEMASUKAN = "Masuk"
JENIS_PENGELUARAN = "Keluar"

# --- Nama Akun Spesifik (jika diperlukan) ---
AKUN_JAGO_TERSIER = "Jago (tersier)"

# --- Daftar Kategori Transaksi ---
# Daftar ini digunakan untuk dropdown pada form input dan proses filter.
# sorted() digunakan untuk memastikan urutannya sesuai abjad.
KATEGORI_PEMASUKAN = sorted(["Dividen", "Gaji", "Hadiah", "Hibah", "Lainnya", "Reimbursement"])
# Menyamakan kapitalisasi "Top Up" agar konsisten dengan data.
KATEGORI_PENGELUARAN = sorted([
    "Hobi/Keinginan", "Internet","Kendaraan/Mobilitas", "Kesehatan/Perawatan", "Lain-lain",
    "Main/Jajan", "Makan", "Pengembangan Diri", "Reimbursement", "Tak Terduga", "Tempat Tinggal",
    "Top Up" 
])

# --- Daftar Pilihan Akun ---
PILIHAN_AKUN = sorted([
    "BNI", "Cash", "Jago", AKUN_JAGO_TERSIER, "GoPay", "ShopeePay", "DANA", "OVO", "Dana Darurat", "Tabungan"
])

# --- Kamus (Dictionary) untuk Logo Akun ---
# Memetakan nama akun ke URL logo mereka untuk tampilan yang lebih menarik.
LOGO_JAGO = "https://upload.wikimedia.org/wikipedia/commons/c/c0/Logo-jago.svg"

SEMUA_AKUN_DENGAN_LOGO = {
    "BNI": "https://upload.wikimedia.org/wikipedia/id/thumb/5/55/BNI_logo.svg/1280px-BNI_logo.svg.png",
    "Cash": "https://upload.wikimedia.org/wikipedia/commons/d/d8/Indonesia_2016_100000r_o.jpg",
    "Jago": LOGO_JAGO,
    AKUN_JAGO_TERSIER: LOGO_JAGO,
    "GoPay": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Gopay_logo.svg/2560px-Gopay_logo.svg.png",
    "ShopeePay": "https://upload.wikimedia.org/wikipedia/commons/f/fe/Shopee.svg",
    "DANA": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Logo_dana_blue.svg/2560px-Logo_dana_blue.svg.png",
    "OVO": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Logo_ovo_purple.svg/2560px-Logo_ovo_purple.svg.png",
    "Dana Darurat": LOGO_JAGO,
    "Tabungan": LOGO_JAGO
}

def custom_divider(margin_top=10, margin_bottom=30, color="#3b3d43", thickness="0.5px"):
    st.markdown(
        f"""
        <hr style="margin-top:{margin_top}px; margin-bottom:{margin_bottom}px; border:{thickness} solid {color};">
        """,
        unsafe_allow_html=True
    )

# ===================================================================================
# --- KONEKSI KE SUPABASE ---
# ===================================================================================
@st.cache_resource # Decorator ini memastikan koneksi hanya dibuat sekali.
def init_connection():
    """Menginisialisasi koneksi ke Supabase menggunakan kredensial dari secrets."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# Membuat instance klien Supabase yang akan digunakan di seluruh aplikasi.
supabase = init_connection()

# ===================================================================================
# --- FUNGSI UTAMA PENGOLAHAN DATA ---
# ===================================================================================
@st.cache_data(ttl=600) # Cache data selama 10 menit
def get_data():
    """
    Mengambil, membersihkan, dan mengembalikan semua data transaksi
    sebagai sebuah DataFrame Pandas.
    """
    try:
        response = supabase.table("Cashflow").select("*").order("tanggal", desc=True).execute()
        df = pd.DataFrame(response.data)

        if df.empty:
            return df

        # Lakukan pembersihan dan konversi tipe data di sini
        df['jenis'] = df['jenis'].str.strip()
        df['kategori'] = df['kategori'].str.strip()
        df['akun'] = df['akun'].str.strip()
        df['tanggal'] = pd.to_datetime(df['tanggal'])
        df[COL_NOMINAL] = pd.to_numeric(df[COL_NOMINAL])
        
        return df
    except Exception as e:
        st.error(f"Gagal mengambil data dari database: {e}")
        return pd.DataFrame() # Kembalikan DataFrame kosong jika error

# ===================================================================================
# --- FUNGSI-FUNGSI UNTUK SETIAP HALAMAN ---
# ===================================================================================

def halaman_dashboard():
    """
    Menampilkan dashboard analisis visual untuk data pemasukan dan pengeluaran.
    """
    # st.markdown(
    #     """
    #     <style>
    #     .judul-custom {
    #         text-align: center !important;
    #         font-size: 24px !important;
    #         color: #e5e5e5 !important;
    #         font-family: "Courier New", monospace !important;
    #         font-weight: bold !important;
    #         margin-top: 0px !important;
    #         margin-bottom: 14px !important;
    #     }
    #     </style>
    #     <div class="judul-custom">
    #         📊 Dashboard
    #     </div>
    #     """,
    #     unsafe_allow_html=True
    # )
    # 1. Mengambil dan memproses data dasar
    df = get_data() 
    
    if df.empty:
        st.info("Belum ada data transaksi untuk ditampilkan.")
        return

    # 2. Memisahkan data Pemasukan dan Pengeluaran
    df_pengeluaran = df[
        (df['jenis'] == JENIS_PENGELUARAN) &
        (df['kategori'].str.lower() != 'top up')
    ].copy()
    df_pemasukan = df[
        (df['jenis'] == JENIS_PEMASUKAN) &
        (df['kategori'].str.lower() != 'top up')
    ].copy()

    # 3. Widget Filter Tanggal Utama
    with st.expander("Filter Periode"):
        tgl_min_data = df['tanggal'].min().date()
        tgl_max_data = df['tanggal'].max().date()
        
        hari_acuan = tgl_max_data
        default_tgl_awal = hari_acuan.replace(day=1)
        hari_pertama_bulan_depan = (default_tgl_awal + timedelta(days=32)).replace(day=1)
        hari_terakhir_bulan_acuan = hari_pertama_bulan_depan - timedelta(days=1)
        default_tgl_akhir = min(hari_terakhir_bulan_acuan, tgl_max_data)

        col1, col2 = st.columns(2)
        with col1:
            tgl_awal = st.date_input("Dari", value=default_tgl_awal, min_value=tgl_min_data, max_value=tgl_max_data)
        with col2:
            tgl_akhir = st.date_input("Sampai", value=default_tgl_akhir, min_value=tgl_min_data, max_value=tgl_max_data)

        if tgl_awal > tgl_akhir:
            st.error("Tanggal Mulai tidak boleh melebihi Tanggal Selesai.")
            return

    # Filter setiap jenis data berdasarkan rentang tanggal yang dipilih
    df_filtered_pengeluaran = df_pengeluaran[(df_pengeluaran['tanggal'].dt.date >= tgl_awal) & (df_pengeluaran['tanggal'].dt.date <= tgl_akhir)]
    df_filtered_pemasukan = df_pemasukan[(df_pemasukan['tanggal'].dt.date >= tgl_awal) & (df_pemasukan['tanggal'].dt.date <= tgl_akhir)]
    df_filtered_semua = df[(df['tanggal'].dt.date >= tgl_awal) & (df['tanggal'].dt.date <= tgl_akhir)]

    st.markdown(f"###### Periode : &nbsp;&nbsp; {tgl_awal.strftime('%d %B %Y')} — {tgl_akhir.strftime('%d %B %Y')}")

    # 4. Layout Utama Dua Kolom untuk Pemasukan dan Pengeluaran
    col_pengeluaran, col_pemasukan = st.columns(2)

    # --- KOLOM KIRI: PENGELUARAN ---
    with col_pengeluaran:
        if df_filtered_pengeluaran.empty:
            st.info("Tidak ada data pengeluaran pada periode ini.")
        else:
            total_pengeluaran = df_filtered_pengeluaran[COL_NOMINAL].sum()
            formatted_total = f"Rp {total_pengeluaran:,.0f}".replace(',', '.')
            st.metric("Total Pengeluaran", formatted_total)

            pengeluaran_per_kategori = df_filtered_pengeluaran.groupby('kategori')[COL_NOMINAL].sum().sort_values(ascending=False)
            
            fig_pie_pengeluaran = px.pie(
                pengeluaran_per_kategori.reset_index(),
                values=COL_NOMINAL,
                names='kategori',
                hole=0.3
            )
            fig_pie_pengeluaran.update_traces(
                textposition='outside',
                textinfo='percent+label',
                textfont_size=12
            )
            fig_pie_pengeluaran.update_layout(
                margin=dict(t=40, b=60, l=60, r=60),
                showlegend=False, height=400, width=400
            )
            st.plotly_chart(fig_pie_pengeluaran, use_container_width=False)

    # --- KOLOM KANAN: PEMASUKAN ---
    with col_pemasukan:
        if df_filtered_pemasukan.empty:
            st.info("Tidak ada data pemasukan pada periode ini.")
        else:
            total_pemasukan = df_filtered_pemasukan[COL_NOMINAL].sum()
            formatted_total = f"Rp {total_pemasukan:,.0f}".replace(',', '.')
            st.metric("Total Pemasukan", formatted_total)

            pemasukan_per_kategori = df_filtered_pemasukan.groupby('kategori')[COL_NOMINAL].sum().sort_values(ascending=False)

            fig_pie_pemasukan = px.pie(
                pemasukan_per_kategori.reset_index(),
                values=COL_NOMINAL,
                names='kategori',
                hole=0.3
            )
            fig_pie_pemasukan.update_traces(
                textposition='outside',
                textinfo='percent+label',
                textfont_size=12
            )
            fig_pie_pemasukan.update_layout(
                margin=dict(t=40, b=60, l=60, r=60),
                showlegend=False, height=400, width=400
            )
            st.plotly_chart(fig_pie_pemasukan, use_container_width=False)
            
    custom_divider()

    # 5. Bar Chart Pengeluaran (di bawah dua kolom)
    st.markdown("##### Nominal Pengeluaran per Kategori")
    if not df_filtered_pengeluaran.empty:
        pengeluaran_per_kategori_bar = df_filtered_pengeluaran.groupby('kategori')[COL_NOMINAL].sum().sort_values(ascending=False).reset_index()
        fig_bar = px.bar(
            pengeluaran_per_kategori_bar, x='kategori', y=COL_NOMINAL,
            labels={COL_NOMINAL: 'Jumlah Pengeluaran (Rp)', 'kategori': 'Kategori'},
            text=COL_NOMINAL,
        )
        fig_bar.update_traces(texttemplate='Rp %{text:,.0f}', textposition='outside')
        fig_bar.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)

    custom_divider()

    # 6. Tabel Detail Transaksi (di paling bawah)
    st.markdown("##### Detail Transaksi")
    if df_filtered_semua.empty:
        st.warning("Tidak ada transaksi apapun pada rentang waktu yang dipilih.")
    else:
        with st.expander("Filter Transaksi"):
            df_display = df_filtered_semua.copy()
            
            # --- MULAI BAGIAN FILTER DETAIL ---
            df_display['hari'] = df_display['tanggal'].dt.day
            df_display['bulan'] = df_display['tanggal'].dt.month
            df_display['tahun'] = df_display['tanggal'].dt.year

            # --- Baris Filter 1: Tanggal, Bulan, Tahun ---
            time_col1, time_col2, time_col3 = st.columns(3)
            with time_col1:
                unique_years = sorted(df_display['tahun'].unique(), reverse=True)
                selected_year = st.selectbox("Tahun", options=["Semua"] + unique_years)
            with time_col2:
                month_map = {1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"}
                # Opsi bulan hanya dari data yang relevan (setelah filter periode utama)
                unique_months = sorted(df_display['bulan'].unique())
                month_options = {num: month_map[num] for num in unique_months}
                selected_month_name = st.selectbox("Bulan", options=["Semua"] + list(month_options.values()))
            with time_col3:
                selected_day = st.selectbox("Tanggal", options=["Semua"] + list(range(1, 32)))
                
            # --- Baris Filter 2: Jenis, Kategori, Akun ---
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            with filter_col1:
                jenis_filter = st.multiselect("Jenis", options=sorted(df_display['jenis'].unique()), placeholder="Pilih Jenis")
            with filter_col2:
                kategori_filter = st.multiselect("Kategori", options=sorted(df_display['kategori'].unique()), placeholder="Pilih Kategori")
            with filter_col3:
                akun_filter = st.multiselect("Akun", options=sorted(df_display['akun'].unique()), placeholder="Pilih Akun")

            # Terapkan semua filter ke df_display
            if selected_year != "Semua":
                df_display = df_display[df_display['tahun'] == selected_year]
            if selected_month_name != "Semua":
                month_num_to_filter = next(num for num, name in month_map.items() if name == selected_month_name)
                df_display = df_display[df_display['bulan'] == month_num_to_filter]
            if selected_day != "Semua":
                df_display = df_display[df_display['hari'] == selected_day]
            if jenis_filter: df_display = df_display[df_display['jenis'].isin(jenis_filter)]
            if kategori_filter: df_display = df_display[df_display['kategori'].isin(kategori_filter)]
            if akun_filter: df_display = df_display[df_display['akun'].isin(akun_filter)]
            # --- AKHIR BAGIAN FILTER DETAIL ---

        if df_display.empty:
            st.warning("Tidak ada data transaksi yang cocok dengan filter detail Anda.")
        else:
            df_display_final = df_display.sort_values(by='tanggal', ascending=False)
            df_display_final.insert(0, 'No.', range(1, len(df_display_final) + 1))
            df_display_final[COL_NOMINAL] = df_display_final[COL_NOMINAL].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
            
            st.dataframe(
                df_display_final, use_container_width=True, hide_index=True,
                column_config={
                    "id": None, "hari": None, "bulan": None, "tahun": None,
                    "No.": st.column_config.TextColumn("No."),
                    "tanggal": st.column_config.DateColumn("Tanggal", format="YYYY-MM-DD"),
                    "jenis": st.column_config.TextColumn("Jenis"),
                    "kategori": st.column_config.TextColumn("Kategori"),
                    "akun": st.column_config.TextColumn("Akun"),
                    COL_NOMINAL: st.column_config.TextColumn(LABEL_NOMINAL),
                    "deskripsi": st.column_config.TextColumn("Deskripsi"),
                }
            )

def halaman_catat_transaksi():
    """Menampilkan form untuk mencatat transaksi baru (pemasukan atau pengeluaran)."""

    # st.markdown(
    #     """
    #     <style>
    #     .judul-custom {
    #         text-align: center !important;
    #         font-size: 24px !important;
    #         color: #e5e5e5 !important;
    #         font-family: "Courier New", monospace !important;
    #         font-weight: bold !important;
    #         margin-top: 0px !important;
    #         margin-bottom: 14px !important;
    #     }
    #     </style>
    #     <div class="judul-custom">
    #         📝 Catat Transaksi Baru
    #     </div>
    #     """,
    #     unsafe_allow_html=True
    # )
    kir, kan = st.columns(2)
    with kir:
        jenis = st.selectbox("Jenis Transaksi", [JENIS_PEMASUKAN, JENIS_PENGELUARAN])
    with kan:
        kategori = st.selectbox(
            "Kategori Pemasukan" if jenis == JENIS_PEMASUKAN else "Kategori Pengeluaran",
            KATEGORI_PEMASUKAN if jenis == JENIS_PEMASUKAN else KATEGORI_PENGELUARAN
            )

    # Form dimulai setelah pilihan jenis & kategori fix
    with st.form("form_transaksi", clear_on_submit=True):
        tanggal = st.date_input("Tanggal")

        # Kalau Keluar + Top Up → field khusus
        if jenis == JENIS_PENGELUARAN and kategori == "Top Up":
            dari_akun = st.selectbox("Dari Akun", PILIHAN_AKUN)
            ke_akun = st.selectbox("Ke Akun", PILIHAN_AKUN)
            akun = None
        else:
            akun = st.selectbox("Akun", PILIHAN_AKUN)
            dari_akun, ke_akun = None, None

        jumlah_input = st.text_input(LABEL_NOMINAL, placeholder="Contoh: 50000")
        deskripsi = st.text_area("Deskripsi")

        col1, col2 = st.columns([1,3])
        with col1:
            st.form_submit_button("Reset", use_container_width=True)
        with col2:
            submitted = st.form_submit_button("Simpan Transaksi", use_container_width=True)

        # Logika yang dijalankan saat form di-submit.
        if submitted:
            jumlah_str = jumlah_input.replace('.', '').strip()
            if not jumlah_str.isdigit():
                st.error("Input Nominal invalid. Harap masukkan angka saja.")
            elif int(jumlah_str) <= 0:
                st.warning("Jumlah harus lebih besar dari 0.")
            else:
                jumlah_int = int(jumlah_str)

                if jenis == JENIS_PENGELUARAN and kategori == "Top Up":
                    # Baris pertama: keluar dari akun asal
                    data_keluar = {
                        "tanggal": tanggal.strftime("%Y-%m-%d"),
                        "jenis": JENIS_PENGELUARAN,
                        "kategori": "Top Up",
                        "akun": dari_akun,
                        COL_NOMINAL: jumlah_int,
                        "deskripsi": deskripsi,
                    }
                    # Baris kedua: masuk ke akun tujuan
                    data_masuk = {
                        "tanggal": tanggal.strftime("%Y-%m-%d"),
                        "jenis": JENIS_PEMASUKAN,
                        "kategori": "Top Up",
                        "akun": ke_akun,
                        COL_NOMINAL: jumlah_int,
                        "deskripsi": deskripsi,
                    }
                    supabase.table("Cashflow").insert([data_keluar, data_masuk]).execute()
                    st.success(f"Transaksi Top Up {dari_akun} → {ke_akun} Rp{jumlah_int:,.0f}".replace(',', '.') + " berhasil disimpan 👌")

                else:
                    # Transaksi biasa
                    data_to_insert = {
                        "tanggal": tanggal.strftime("%Y-%m-%d"),
                        "jenis": jenis,
                        "kategori": kategori,
                        "akun": akun,
                        COL_NOMINAL: jumlah_int,
                        "deskripsi": deskripsi,
                    }
                    supabase.table("Cashflow").insert(data_to_insert).execute()
                    st.success(f"Transaksi '{kategori}' sebesar Rp{jumlah_int:,.0f}".replace(',', '.') + " berhasil disimpan 👌")

                # Refresh cache & reload
                st.cache_data.clear()
                st.rerun()

def halaman_lihat_saldo():
    """
    Menghitung dan menampilkan saldo kumulatif untuk setiap akun hingga tanggal yang dipilih.
    """
    # st.markdown(
    #     """
    #     <style>
    #     .judul-custom {
    #         text-align: center !important;
    #         font-size: 24px !important;
    #         color: #e5e5e5 !important;
    #         font-family: "Courier New", monospace !important;
    #         font-weight: bold !important;
    #         margin-top: 0px !important;
    #         margin-bottom: 14px !important;
    #     }
    #     </style>
    #     <div class="judul-custom">
    #         💰 Saldo Akun
    #     </div>
    #     """,
    #     unsafe_allow_html=True
    # )
    
    kol1, kol2 = st.columns(2)

    # 1. Mengambil data dari Supabase.
    df = get_data()  # Mengambil data dari fungsi yang sudah didefinisikan sebelumnya.
    
    with kol1:
        # Widget untuk memilih tanggal, dengan nilai default hari ini.
        tanggal_pilihan = st.date_input("Lihat Saldo per Tanggal", value=datetime.now().date())

    # 2. Memproses dan membersihkan data.
    saldo_akun = {}
    if not df.empty:
        # 3. Filter data secara kumulatif
        df_per_tanggal = df[df['tanggal'].dt.date <= tanggal_pilihan].copy()

        # 4. Menghitung saldo jika ada data pada rentang tanggal tersebut.
        if not df_per_tanggal.empty:
            # Agregasi total pemasukan & pengeluaran per akun.
            pemasukan = df_per_tanggal[df_per_tanggal['jenis'] == JENIS_PEMASUKAN].groupby('akun')[COL_NOMINAL].sum()
            pengeluaran = df_per_tanggal[df_per_tanggal['jenis'] == JENIS_PENGELUARAN].groupby('akun')[COL_NOMINAL].sum()
            
            # Menggabungkan data dan menghitung saldo akhir.
            saldo_df = pd.concat([pemasukan, pengeluaran], axis=1).fillna(0)
            saldo_df.columns = ['pemasukan', 'pengeluaran']
            saldo_df['saldo'] = saldo_df['pemasukan'] - saldo_df['pengeluaran']
            saldo_akun = saldo_df['saldo'].to_dict()
    
    with kol2:
        # 5. Menampilkan total saldo dan daftar saldo per akun.
        total_saldo_keseluruhan = sum(saldo_akun.values())
        formatted_total = f"Rp {total_saldo_keseluruhan:,.0f}".replace(',', '.')
        if total_saldo_keseluruhan < 0:
            formatted_total = f"-Rp {abs(total_saldo_keseluruhan):,.0f}".replace(',', '.')

        st.metric(label=f"Total Saldo per {tanggal_pilihan.strftime('%d %B %Y')}", value=formatted_total)

    # Menambahkan CSS custom untuk styling tampilan daftar akun.
    st.markdown("""
    <style>
    .list-logo { height: 40px; width: auto; object-fit: contain; border-radius: 4px; }
    .account-name { font-size: 20px; font-weight: 500; line-height: 1; }
    .account-balance { font-size: 24px; font-weight: 600; }
    .account-balance-negative { color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

    custom_divider()

    # Mengurutkan nama akun berdasarkan saldonya (dari terbesar ke terkecil).
    # Fungsi `saldo_akun.get(akun, 0)` digunakan untuk menangani akun yang belum memiliki transaksi (saldo dianggap 0).
    akun_terurut = sorted(SEMUA_AKUN_DENGAN_LOGO.keys(), key=lambda akun: saldo_akun.get(akun, 0), reverse=True)

    # Loop untuk menampilkan setiap akun, logo, dan saldonya berdasarkan urutan yang sudah dibuat.
    for akun_name in akun_terurut:
        logo_url = SEMUA_AKUN_DENGAN_LOGO[akun_name]
        saldo = saldo_akun.get(akun_name, 0)
        
        col1, col2 = st.columns([3, 2])
        # Kolom kiri: Logo dan nama akun.
        with col1:
            logo_col, name_col = st.columns([1, 4])
            with logo_col:
                st.markdown(f'<img src="{logo_url}" class="list-logo">', unsafe_allow_html=True)
            with name_col:
                st.markdown(f'<span class="account-name">{akun_name}</span>', unsafe_allow_html=True)
        # Kolom kanan: Saldo.
        with col2:
            formatted_saldo = f"Rp {saldo:,.0f}".replace(',', '.')
            if saldo < 0:
                formatted_saldo = f"-Rp {abs(saldo):,.0f}".replace(',', '.')
            color_class = "account-balance-negative" if saldo < 0 else ""
            st.markdown(f'''
                <div style="text-align: right;">
                    <span class="account-balance {color_class}">{formatted_saldo}</span>
                </div>
            ''', unsafe_allow_html=True)
        
        custom_divider()


def tampilkan_form_edit_hapus(df_filtered):
    """
    Menampilkan expander berisi form untuk mengedit atau menghapus transaksi terpilih.
    Fungsi ini dipanggil dari dalam halaman 'Daftar Transaksi'.
    """
    with st.expander("✏️ Edit / Hapus Transaksi", expanded=False):
        # 1. Membuat daftar pilihan transaksi dari data yang sudah difilter.
        pilihan_transaksi = [
            f"{row['id']} -- ({row['tanggal'].strftime('%Y-%m-%d')}) -- {row['kategori']} (Rp {row[COL_NOMINAL]:,}) -- {row['deskripsi']}".replace(',', '.')
            for _, row in df_filtered.iterrows()
        ]
        pilihan_transaksi.insert(0, "Pilih transaksi untuk diedit / dihapus")

        # 2. Dropdown untuk memilih transaksi.
        transaksi_terpilih = st.selectbox("Pilih Data Transaksi", pilihan_transaksi)

        # 3. Jika sebuah transaksi dipilih, tampilkan form edit/hapus.
        if transaksi_terpilih != "Pilih transaksi untuk diedit / dihapus":
            id_terpilih = int(transaksi_terpilih.split(" -- ")[0])
            data_lama = df_filtered[df_filtered['id'] == id_terpilih].iloc[0]

            with st.form("form_edit"):
                st.info(f"Anda sedang mengedit transaksi dengan ID: {id_terpilih}")

                # Input fields diisi dengan data lama sebagai nilai default.
                tanggal_edit = st.date_input("Tanggal", value=pd.to_datetime(data_lama['tanggal']))
                jenis_edit = st.selectbox("Jenis Transaksi", [JENIS_PENGELUARAN, JENIS_PEMASUKAN], index=[JENIS_PENGELUARAN, JENIS_PEMASUKAN].index(data_lama['jenis']))
                
                # Menyesuaikan pilihan kategori berdasarkan jenis transaksi.
                if jenis_edit == JENIS_PEMASUKAN:
                    kategori_index = KATEGORI_PEMASUKAN.index(data_lama['kategori']) if data_lama['kategori'] in KATEGORI_PEMASUKAN else 0
                    kategori_edit = st.selectbox("Kategori", KATEGORI_PEMASUKAN, index=kategori_index)
                else:
                    kategori_index = KATEGORI_PENGELUARAN.index(data_lama['kategori']) if data_lama['kategori'] in KATEGORI_PENGELUARAN else 0
                    kategori_edit = st.selectbox("Kategori", KATEGORI_PENGELUARAN, index=kategori_index)

                akun_edit = st.selectbox("Akun", PILIHAN_AKUN, index=PILIHAN_AKUN.index(data_lama['akun']))
                nominal_edit = st.number_input(LABEL_NOMINAL, value=int(data_lama[COL_NOMINAL]), step=1000)
                deskripsi_edit = st.text_area("Deskripsi", value=data_lama['deskripsi'])

                # Tombol untuk Hapus dan Update.
                delete_col, update_col, cancel_col = st.columns(3)
                with delete_col:
                    delete_button = st.form_submit_button("Hapus Data Transaksi", use_container_width=True)
                with update_col:
                    update_button = st.form_submit_button("Update Data Transaksi", use_container_width=True)
                with cancel_col:
                    cancel_button = st.form_submit_button("Batal", use_container_width=True)

                # Logika saat tombol Update ditekan.
                if update_button:
                    data_baru = {
                        "tanggal": tanggal_edit.strftime("%Y-%m-%d"), "jenis": jenis_edit, "kategori": kategori_edit,
                        "akun": akun_edit, COL_NOMINAL: nominal_edit, "deskripsi": deskripsi_edit
                    }
                    supabase.table("Cashflow").update(data_baru).eq("id", id_terpilih).execute()
                    st.cache_data.clear()
                    st.success("Transaksi berhasil diupdate!")
                    st.session_state.force_close_expander = True
                    st.rerun() # Muat ulang halaman untuk menampilkan data terbaru.

                # Logika saat tombol Hapus ditekan.
                if delete_button:
                    supabase.table("Cashflow").delete().eq("id", id_terpilih).execute()
                    st.cache_data.clear()
                    st.warning("Transaksi berhasil dihapus!")
                    st.session_state.force_close_expander = True
                    st.rerun() # Muat ulang halaman.

                if cancel_button:
                    st.cache_data.clear()
                    st.info("Edit transaksi dibatalkan.")
                    st.session_state.force_close_expander = True
                    st.rerun()


def halaman_daftar_transaksi():
    """Menampilkan semua data transaksi dalam bentuk tabel dengan opsi filter yang lengkap."""
    # st.markdown(
    #     """
    #     <style>
    #     .judul-custom {
    #         text-align: center !important;
    #         font-size: 24px !important;
    #         color: #e5e5e5 !important;
    #         font-family: "Courier New", monospace !important;
    #         font-weight: bold !important;
    #         margin-top: 0px !important;
    #         margin-bottom: 14px !important;
    #     }
    #     </style>
    #     <div class="judul-custom">
    #         🧾 Daftar Transaksi
    #     </div>
    #     """,
    #     unsafe_allow_html=True
    # )

    # 1. Mengambil data dari Supabase, diurutkan berdasarkan tanggal terbaru.
    df_all = get_data() # Panggil fungsi terpusat
    
    if df_all.empty:
        st.info("Belum ada data transaksi.")
        return    
    
    # 2. Memproses dan membersihkan data.
    df = df_all.copy()
    df['jenis'] = df['jenis'].str.strip()
    df['kategori'] = df['kategori'].str.strip()
    df['akun'] = df['akun'].str.strip()
    df['tanggal'] = pd.to_datetime(df['tanggal'])
    df[COL_NOMINAL] = pd.to_numeric(df[COL_NOMINAL])

    # 3. Expander untuk menampung widget filter.
    with st.expander("🔍 Filter Transaksi"):
        df['hari'] = df['tanggal'].dt.day
        df['bulan'] = df['tanggal'].dt.month
        df['tahun'] = df['tanggal'].dt.year
        
        time_col1, time_col2, time_col3 = st.columns(3)
        with time_col1:
            unique_years = sorted(df['tahun'].unique(), reverse=True)
            selected_year = st.selectbox("Tahun", options=["Semua"] + unique_years)
        with time_col2:
            month_map = {
                1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
                7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
            }
            unique_months = sorted(df['bulan'].unique())
            month_options = {num: month_map[num] for num in unique_months}
            selected_month_name = st.selectbox("Bulan", options=["Semua"] + list(month_options.values()))
        with time_col3:
            selected_day = st.selectbox("Tanggal", options=["Semua"] + list(range(1, 32)))
            
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            jenis_filter = st.multiselect("Jenis", options=df['jenis'].unique(), placeholder="Pilih Jenis")
        with filter_col2:
            kategori_filter = st.multiselect("Kategori", options=sorted(df['kategori'].unique()), placeholder="Pilih Kategori")
        with filter_col3:
            akun_filter = st.multiselect("Akun", options=df['akun'].unique(), placeholder="Pilih Akun")

    # 4. Menerapkan semua filter ke DataFrame.
    df_filtered = df.copy()
    if selected_year != "Semua":
        df_filtered = df_filtered[df_filtered['tahun'] == selected_year]
    if selected_month_name != "Semua":
        month_num_to_filter = next(num for num, name in month_map.items() if name == selected_month_name)
        df_filtered = df_filtered[df_filtered['bulan'] == month_num_to_filter]
    if selected_day != "Semua":
        df_filtered = df_filtered[df_filtered['hari'] == selected_day]
    if jenis_filter:
        df_filtered = df_filtered[df_filtered['jenis'].isin(jenis_filter)]
    if kategori_filter:
        df_filtered = df_filtered[df_filtered['kategori'].isin(kategori_filter)]
    if akun_filter:
        df_filtered = df_filtered[df_filtered['akun'].isin(akun_filter)]

    # 5. Menampilkan hasil data yang telah difilter.
    st.subheader("Data Transaksi")
    if df_filtered.empty:
        st.warning("Tidak ada data yang cocok dengan filter Anda.")
        return
    
    df_display = df_filtered.sort_values(by='id', ascending=False)
    df_display[COL_NOMINAL] = df_display[COL_NOMINAL].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
    df_display.insert(0, 'No.', range(1, len(df_display) + 1))
    
    st.dataframe(df_display, use_container_width=True, hide_index=True,
        column_config={
            "hari": None, "bulan": None, "tahun": None,
            "id": st.column_config.TextColumn("ID"),
            "No.": st.column_config.TextColumn("No."),
            "tanggal": st.column_config.DateColumn("Tanggal", format="YYYY-MM-DD"),
            "jenis": st.column_config.TextColumn("Jenis"),
            "kategori": st.column_config.TextColumn("Kategori"),
            "akun": st.column_config.TextColumn("Akun"),
            COL_NOMINAL: st.column_config.TextColumn(LABEL_NOMINAL),
            "deskripsi": st.column_config.TextColumn("Deskripsi"),
        }
    )
    
    # Memanggil fungsi untuk menampilkan form edit/hapus di bawah tabel.
    tampilkan_form_edit_hapus(df_filtered)

# ===================================================================================
# --- STRUKTUR UTAMA APLIKASI (ROUTER) ---
# ===================================================================================
def main():
    """Fungsi utama yang menjalankan aplikasi dan mengatur navigasi antar halaman."""
    st.markdown(
    """
    <style>
    /* Import font dari Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600&family=Dancing+Script:wght@600&display=swap');

    .judul-atas {
        text-align: center !important;
        font-size: 12px !important;
        color: #4a4a4a !important;
        font-family: 'Poppins', sans-serif !important;
        margin-bottom: 0px !important;
    }

    .judul-bawah {
        text-align: center !important;
        font-size: 36px !important;
        color: #e5e5e5 !important;
        font-family: 'Dancing Script', cursive !important;
        margin-top: 0px !important;
        margin-bottom: 25px !important;
    }
    </style>

    <div class="judul-atas">Langkah Awal Menuju</div>
    <div class="judul-bawah">✨ <em>Financial Freedom</em> ✨</div>
    """,
    unsafe_allow_html=True
    )
 
    menu = st.selectbox(
        "📌 Menu",
        [PAGE_DASHBOARD, PAGE_LIHAT_SALDO, PAGE_CATAT_TRANSAKSI, PAGE_DAFTAR_TRANSAKSI],
        format_func=lambda x: {
            PAGE_DASHBOARD: "📊 Dashboard",
            PAGE_LIHAT_SALDO: "💰 Saldo Akun",
            PAGE_CATAT_TRANSAKSI: "📝 Catat Transaksi",
            PAGE_DAFTAR_TRANSAKSI: "🧾 Daftar Transaksi"
        }[x],
    )

    # Simpan ke session_state
    st.session_state.page = menu

    custom_divider()

    # Menggunakan st.session_state untuk menyimpan halaman yang sedang aktif.
    # Ini adalah cara sederhana untuk membuat aplikasi multi-halaman di Streamlit.
    if "page" not in st.session_state:
        st.session_state.page = PAGE_DASHBOARD

    # Menampilkan halaman yang sesuai berdasarkan session_state.
    if st.session_state.page == PAGE_DASHBOARD:
        halaman_dashboard()
    elif st.session_state.page == PAGE_CATAT_TRANSAKSI:
        halaman_catat_transaksi()
    elif st.session_state.page == PAGE_LIHAT_SALDO:
        halaman_lihat_saldo()
    elif st.session_state.page == PAGE_DAFTAR_TRANSAKSI:
        halaman_daftar_transaksi()

# ===================================================================================
# --- TITIK MASUK EKSEKUSI PROGRAM ---
# ===================================================================================
# Blok ini memastikan fungsi main() hanya dijalankan saat script dieksekusi langsung.
if __name__ == "__main__":
    main()
