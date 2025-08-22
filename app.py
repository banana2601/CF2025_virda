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
JENIS_PEMASUKAN = "Pemasukan"
JENIS_PENGELUARAN = "Pengeluaran"

# --- Nama Akun Spesifik (jika diperlukan) ---
AKUN_JAGO_TERSIER = "Jago (tersier)"

# --- Daftar Kategori Transaksi ---
# Daftar ini digunakan untuk dropdown pada form input dan proses filter.
# sorted() digunakan untuk memastikan urutannya sesuai abjad.
KATEGORI_PEMASUKAN = sorted(["Dividen", "Gaji", "Hadiah", "Hibah", "Lainnya", "Reimbursement", "Top Up"])
# Menyamakan kapitalisasi "Top Up" agar konsisten dengan data.
KATEGORI_PENGELUARAN = sorted([
    "Dana Darurat", "Hobi/Keinginan", "Internet", "Investasi/Tabungan",
    "Kendaraan/Mobilitas", "Kesehatan/Perawatan", "Lain-lain", "Main/Jajan",
    "Makan", "Pengembangan Diri", "Reimbursement", "Tak Terduga", "Tempat Tinggal",
    "Top Up" 
])

# --- Daftar Pilihan Akun ---
PILIHAN_AKUN = [
    "BNI", "Cash", "Jago", AKUN_JAGO_TERSIER, "GoPay", "ShopeePay", "DANA", "OVO"
]

# --- Kamus (Dictionary) untuk Logo Akun ---
# Memetakan nama akun ke URL logo mereka untuk tampilan yang lebih menarik.
SEMUA_AKUN_DENGAN_LOGO = {
    "BNI": "https://upload.wikimedia.org/wikipedia/id/thumb/5/55/BNI_logo.svg/1280px-BNI_logo.svg.png",
    "Cash": "https://upload.wikimedia.org/wikipedia/commons/d/d8/Indonesia_2016_100000r_o.jpg",
    "Jago": "https://upload.wikimedia.org/wikipedia/commons/c/c0/Logo-jago.svg",
    AKUN_JAGO_TERSIER: "https://upload.wikimedia.org/wikipedia/commons/c/c0/Logo-jago.svg",
    "GoPay": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Gopay_logo.svg/2560px-Gopay_logo.svg.png",
    "ShopeePay": "https://upload.wikimedia.org/wikipedia/commons/f/fe/Shopee.svg",
    "DANA": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Logo_dana_blue.svg/2560px-Logo_dana_blue.svg.png",
    "OVO": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Logo_ovo_purple.svg/2560px-Logo_ovo_purple.svg.png"
}

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
# --- FUNGSI-FUNGSI UNTUK SETIAP HALAMAN ---
# ===================================================================================

def halaman_dashboard():
    """
    Menampilkan dashboard analisis visual untuk data pengeluaran.
    Fungsi ini mengambil data, memfilternya, dan menampilkannya dalam bentuk
    metrik, tabel, pie chart, dan bar chart.
    """
    st.header("📊 Dashboard Analisis Pengeluaran")

    # 1. Mengambil data dari Supabase.
    response = supabase.table("Cashflow").select("*").execute()
    data = response.data
    
    # Menangani kasus jika tidak ada data sama sekali.
    if not data:
        st.info("Belum ada data transaksi untuk ditampilkan di dashboard.")
        return

    # 2. Memproses dan membersihkan data.
    df = pd.DataFrame(data)
    
    # Membersihkan spasi ekstra pada kolom teks untuk menghindari error saat filter.
    df['jenis'] = df['jenis'].str.strip()
    df['kategori'] = df['kategori'].str.strip()
    df['akun'] = df['akun'].str.strip()

    # Mengonversi kolom ke tipe data yang benar.
    df['tanggal'] = pd.to_datetime(df['tanggal'])
    df[COL_NOMINAL] = pd.to_numeric(df[COL_NOMINAL])

    # 3. Filter data khusus untuk dashboard.
    # Hanya data 'Pengeluaran' yang dianalisis.
    # Filter dibuat case-insensitive dengan .str.lower() 
    # Ini memastikan semua variasi 'Top Up', 'top up', 'TOP UP', dll. akan dikecualikan.
    df_pengeluaran = df[
        (df['jenis'] == JENIS_PENGELUARAN) &
        (df['kategori'].str.lower() != 'top up')
    ].copy()

    # Menangani kasus jika tidak ada data pengeluaran yang relevan.
    if df_pengeluaran.empty:
        st.info("Belum ada data pengeluaran (selain Top Up) untuk dianalisis.")
        return

    # 4. Membuat widget filter tanggal.
    st.markdown("### Rentang Waktu")
    
    # Menentukan batas minimum dan maksimum tanggal dari keseluruhan data yang ada.
    tgl_min_data = df_pengeluaran['tanggal'].min().date()
    tgl_max_data = df_pengeluaran['tanggal'].max().date()

    # Mengatur default tanggal ke bulan PALING BARU yang ada datanya.
    hari_acuan = tgl_max_data
    default_tgl_awal = hari_acuan.replace(day=1)
    
    # --- PERBAIKAN: Memastikan nilai default tanggal akhir tidak melebihi data maksimum ---
    # 1. Hitung hari terakhir pada bulan acuan tersebut.
    hari_pertama_bulan_depan = (default_tgl_awal + timedelta(days=32)).replace(day=1)
    hari_terakhir_bulan_acuan = hari_pertama_bulan_depan - timedelta(days=1)
    # 2. Bandingkan dengan tanggal data terakhir, ambil yang lebih kecil.
    # Ini mencegah error jika data terakhir bukan di akhir bulan.
    default_tgl_akhir = min(hari_terakhir_bulan_acuan, tgl_max_data)


    col1, col2 = st.columns(2)
    with col1:
        # 'value' diatur ke default yang sudah dihitung (aman dari error).
        # 'min_value' dan 'max_value' tetap dibatasi oleh data transaksi yang ada.
        tgl_awal = st.date_input(
            "Tanggal Mulai", 
            value=default_tgl_awal, 
            min_value=tgl_min_data, 
            max_value=tgl_max_data
        )
    with col2:
        # 'value' diatur ke default yang sudah dihitung.
        tgl_akhir = st.date_input(
            "Tanggal Selesai", 
            value=default_tgl_akhir, 
            min_value=tgl_min_data, 
            max_value=tgl_max_data
        )

    # Validasi input tanggal.
    if tgl_awal > tgl_akhir:
        st.error("Tanggal Mulai tidak boleh melebihi Tanggal Selesai.")
        return

    # Menerapkan filter tanggal ke DataFrame.
    df_filtered = df_pengeluaran[
        (df_pengeluaran['tanggal'].dt.date >= tgl_awal) & 
        (df_pengeluaran['tanggal'].dt.date <= tgl_akhir)
    ]

    st.markdown("---")

    # Menangani kasus jika tidak ada data pada rentang waktu yang dipilih.
    if df_filtered.empty:
        st.warning("Tidak ada data pengeluaran pada rentang waktu yang dipilih.")
        return

    # 5. Menampilkan visualisasi data.
    st.subheader(f"Periode : &nbsp;&nbsp; {tgl_awal.strftime('%d %B %Y')} — {tgl_akhir.strftime('%d %B %Y')}")
    
    # Metrik total pengeluaran.
    total_pengeluaran = df_filtered[COL_NOMINAL].sum()
    formatted_total = f"Rp {total_pengeluaran:,.0f}".replace(',', '.')
    st.metric("Total Pengeluaran di Periode Ini", formatted_total)

    # Agregasi data untuk chart (pengeluaran per kategori).
    pengeluaran_per_kategori = df_filtered.groupby('kategori')[COL_NOMINAL].sum().sort_values(ascending=False)
    
    # Layout 2 kolom untuk tabel dan pie chart.
    col1, col2 = st.columns(2)
    with col1:
        # Tabel persentase.
        st.markdown("###### Data per Kategori")
        df_persentase = pengeluaran_per_kategori.reset_index()
        df_persentase.columns = ['Kategori', 'Total']
        # Kalkulasi persentase HARUS menggunakan data 'Total' yang masih numerik.
        if total_pengeluaran > 0:
            df_persentase['Persentase'] = (df_persentase['Total'] / total_pengeluaran * 100)
        else:
            df_persentase['Persentase'] = 0
        
        # Format kolom 'Total' menjadi string dengan pemisah titik.
        # Konversi ini dilakukan SETELAH semua kalkulasi selesai.
        df_persentase['Total'] = df_persentase['Total'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
        
        st.dataframe(
            df_persentase,
            use_container_width=True, hide_index=True,
            column_config={
                "Kategori": st.column_config.TextColumn("Kategori"),
                # Tipe kolom diubah menjadi TextColumn untuk menampilkan string yang sudah diformat.
                "Total": st.column_config.TextColumn("Total (Rp)"),
                "Persentase": st.column_config.ProgressColumn(
                    "Persentase", format="%.2f %%", min_value=0, max_value=100
                ),
            }
        )
    with col2:
        # Pie chart (menggunakan data numerik sebelum diformat).
        st.markdown("###### Diagram Persentase")
        # Untuk pie chart, kita tetap menggunakan data asli yang numerik.
        df_pie = pengeluaran_per_kategori.reset_index()
        df_pie.columns = ['Kategori', 'Total']
        if not df_pie.empty and df_pie['Total'].sum() > 0:
            fig = px.pie(df_pie, values='Total', names='Kategori', hole=.2)
            fig.update_traces(textposition='outside', textinfo='percent+label', textfont_size=14)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tidak ada data untuk ditampilkan pada diagram.")


    # Bar chart (juga menggunakan data numerik).
    st.markdown("##### Diagram Nominal")
    df_bar = pengeluaran_per_kategori.reset_index()
    df_bar.columns = ['Kategori', 'Total']
    if not df_bar.empty:
        fig_bar = px.bar(
            df_bar, x='Kategori', y='Total',
            labels={'Total': 'Jumlah Pengeluaran (Rp)', 'Kategori': 'Kategori'},
            text='Total',
        )
        fig_bar.update_traces(texttemplate='Rp %{text:,.0f}', textposition='outside')
        fig_bar.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)
    st.divider()

    # Tabel detail transaksi.
    st.markdown("#### Detail Transaksi Pengeluaran")
    df_display = df_filtered.copy()
    df_display.insert(0, 'No.', range(1, len(df_display) + 1))
    df_display[COL_NOMINAL] = df_display[COL_NOMINAL].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
    st.dataframe(
        df_display, 
        use_container_width=True, hide_index=True,
        column_config={
            "id": None, "hari": None, "bulan": None, "tahun": None, "jenis": None,
            "No.": st.column_config.TextColumn("No.", width="small"),
            "tanggal": st.column_config.DateColumn("Tanggal", format="YYYY-MM-DD"),
            "kategori": st.column_config.TextColumn("Kategori"),
            "akun": st.column_config.TextColumn("Akun"),
            COL_NOMINAL: st.column_config.TextColumn(LABEL_NOMINAL),
            "deskripsi": st.column_config.TextColumn("Deskripsi"),
        }
    )

def halaman_catat_transaksi():
    """Menampilkan form untuk mencatat transaksi baru (pemasukan atau pengeluaran)."""
    st.header(f"📝 {PAGE_CATAT_TRANSAKSI} Baru")
    
    # Pilihan jenis transaksi.
    jenis = st.selectbox("Jenis Transaksi", [JENIS_PENGELUARAN, JENIS_PEMASUKAN])

    # Menggunakan st.form agar input tidak langsung di-submit setiap kali diubah.
    with st.form("form_transaksi", clear_on_submit=True):
        # Input fields untuk data transaksi.
        tanggal = st.date_input("Tanggal")
        kategori = st.selectbox(
            "Kategori Pemasukan" if jenis == JENIS_PEMASUKAN else "Kategori Pengeluaran",
            KATEGORI_PEMASUKAN if jenis == JENIS_PEMASUKAN else KATEGORI_PENGELUARAN
        )
        akun = st.selectbox("Akun", PILIHAN_AKUN)
        jumlah_input = st.text_input(label=LABEL_NOMINAL, placeholder="Contoh: 50000")
        deskripsi = st.text_area("Deskripsi")

        # Tombol form.
        col1, col2 = st.columns([1, 3])
        with col1:
            st.form_submit_button("Reset", use_container_width=True)
        with col2:
            submitted = st.form_submit_button("Simpan Transaksi", use_container_width=True)

        # Logika yang dijalankan saat form di-submit.
        if submitted:
            # Membersihkan dan memvalidasi input nominal.
            jumlah_str = jumlah_input.replace('.', '').strip()
            if not jumlah_str.isdigit():
                st.error("Input jumlah tidak valid. Harap masukkan angka saja.")
            elif int(jumlah_str) <= 0:
                st.warning("Jumlah harus lebih besar dari 0.")
            else:
                # Jika valid, siapkan data dan kirim ke Supabase.
                jumlah_int = int(jumlah_str)
                data_to_insert = {
                    "tanggal": tanggal.strftime("%Y-%m-%d"), "jenis": jenis, "kategori": kategori,
                    "akun": akun, COL_NOMINAL: jumlah_int, "deskripsi": deskripsi
                }
                supabase.table("Cashflow").insert(data_to_insert).execute()
                st.success(f"Transaksi '{kategori}' sebesar Rp{jumlah_int:,.0f}".replace(',', '.') + " berhasil disimpan 👌")
                st.balloons()

def halaman_lihat_saldo():
    """
    Menghitung dan menampilkan saldo kumulatif untuk setiap akun hingga tanggal yang dipilih.
    """
    st.header("💰 Saldo per Akun")

    # Widget untuk memilih tanggal, dengan nilai default hari ini.
    tanggal_pilihan = st.date_input("Lihat Saldo per Tanggal", value=datetime.now().date())

    # Menambahkan CSS custom untuk styling tampilan daftar akun.
    st.markdown("""
    <style>
    .list-logo { height: 40px; width: auto; object-fit: contain; border-radius: 4px; }
    .account-name { font-size: 18px; font-weight: 500; line-height: 2.5; }
    .account-balance { font-size: 20px; font-weight: 600; }
    .account-balance-negative { color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

    # 1. Mengambil data dari Supabase.
    response = supabase.table("Cashflow").select("*").execute()
    data = response.data
    
    saldo_akun = {}
    if data:
        # 2. Memproses dan membersihkan data.
        df = pd.DataFrame(data)
        
        # Membersihkan spasi ekstra.
        df['jenis'] = df['jenis'].str.strip()
        df['kategori'] = df['kategori'].str.strip()
        df['akun'] = df['akun'].str.strip()
        
        # Mengonversi tipe data.
        df[COL_NOMINAL] = pd.to_numeric(df[COL_NOMINAL])
        df['tanggal'] = pd.to_datetime(df['tanggal'])

        # 3. Filter data secara kumulatif.
        # Hanya transaksi hingga tanggal yang dipilih yang akan dihitung.
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

    # 5. Menampilkan total saldo dan daftar saldo per akun.
    total_saldo_keseluruhan = sum(saldo_akun.values())
    formatted_total = f"Rp {total_saldo_keseluruhan:,.0f}".replace(',', '.')
    if total_saldo_keseluruhan < 0:
        formatted_total = f"-Rp {abs(total_saldo_keseluruhan):,.0f}".replace(',', '.')
    
    st.metric(label=f"Total Saldo per {tanggal_pilihan.strftime('%d %B %Y')}", value=formatted_total)
    st.markdown("---")
    
    # Loop untuk menampilkan setiap akun, logo, dan saldonya.
    for akun_name, logo_url in SEMUA_AKUN_DENGAN_LOGO.items():
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
        st.divider()

def tampilkan_form_edit_hapus(df_filtered):
    """
    Menampilkan expander berisi form untuk mengedit atau menghapus transaksi terpilih.
    Fungsi ini dipanggil dari dalam halaman 'Daftar Transaksi'.
    """
    with st.expander("✏️ Edit / Hapus Transaksi"):
        # 1. Membuat daftar pilihan transaksi dari data yang sudah difilter.
        pilihan_transaksi = [
            f"{row['id']} - {row['tanggal'].strftime('%Y-%m-%d')} - {row['kategori']} (Rp {row[COL_NOMINAL]:,})".replace(',', '.')
            for _, row in df_filtered.iterrows()
        ]
        pilihan_transaksi.insert(0, "Pilih transaksi untuk diedit / dihapus")

        # 2. Dropdown untuk memilih transaksi.
        transaksi_terpilih = st.selectbox("Pilih Transaksi", pilihan_transaksi)

        # 3. Jika sebuah transaksi dipilih, tampilkan form edit/hapus.
        if transaksi_terpilih != "Pilih transaksi untuk diedit / dihapus":
            id_terpilih = int(transaksi_terpilih.split(" - ")[0])
            data_lama = df_filtered[df_filtered['id'] == id_terpilih].iloc[0]

            with st.form("form_edit"):
                st.info(f"Anda sedang mengedit transaksi ID: {id_terpilih}")

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
                delete_col, update_col = st.columns(2)
                with delete_col:
                    delete_button = st.form_submit_button("Hapus", use_container_width=True, type="primary")
                with update_col:
                    update_button = st.form_submit_button("Update", use_container_width=True)

                # Logika saat tombol Update ditekan.
                if update_button:
                    data_baru = {
                        "tanggal": tanggal_edit.strftime("%Y-%m-%d"), "jenis": jenis_edit, "kategori": kategori_edit,
                        "akun": akun_edit, COL_NOMINAL: nominal_edit, "deskripsi": deskripsi_edit
                    }
                    supabase.table("Cashflow").update(data_baru).eq("id", id_terpilih).execute()
                    st.success("Transaksi berhasil diupdate!")
                    st.rerun() # Muat ulang halaman untuk menampilkan data terbaru.

                # Logika saat tombol Hapus ditekan.
                if delete_button:
                    supabase.table("Cashflow").delete().eq("id", id_terpilih).execute()
                    st.warning("Transaksi berhasil dihapus!")
                    st.rerun() # Muat ulang halaman.

def halaman_daftar_transaksi():
    """Menampilkan semua data transaksi dalam bentuk tabel dengan opsi filter yang lengkap."""
    st.header(f"🧾 {PAGE_DAFTAR_TRANSAKSI}")
    
    # 1. Mengambil data dari Supabase, diurutkan berdasarkan tanggal terbaru.
    response = supabase.table("Cashflow").select("*").order("tanggal", desc=True).execute()
    data = response.data
    
    if not data:
        st.info("Belum ada data transaksi.")
        return

    # 2. Memproses dan membersihkan data.
    df = pd.DataFrame(data)
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

    df_display = df_filtered.copy()
    df_display[COL_NOMINAL] = df_display[COL_NOMINAL].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
    df_display.insert(0, 'No.', range(1, len(df_display) + 1))
    
    st.dataframe(df_display, use_container_width=True, hide_index=True,
        column_config={
            "id": None, "hari": None, "bulan": None, "tahun": None,
            "No.": st.column_config.TextColumn("No.", width="small"),
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
    st.title("Langkah awal menuju ✨*Financial Freedom*✨")
    
    # Membuat tombol navigasi dalam layout 2x2.
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    with row1_col1:
        if st.button(f"📊 {PAGE_DASHBOARD}", use_container_width=True):
            st.session_state.page = PAGE_DASHBOARD
    with row1_col2:
        if st.button(f"📝 {PAGE_CATAT_TRANSAKSI}", use_container_width=True):
            st.session_state.page = PAGE_CATAT_TRANSAKSI
    with row2_col1:
        if st.button(f"💰 {PAGE_LIHAT_SALDO}", use_container_width=True):
            st.session_state.page = PAGE_LIHAT_SALDO
    with row2_col2:
        if st.button(f"🧾 {PAGE_DAFTAR_TRANSAKSI}", use_container_width=True):
            st.session_state.page = PAGE_DAFTAR_TRANSAKSI

    st.markdown("---")

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
