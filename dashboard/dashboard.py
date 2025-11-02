import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from pathlib import Path  # <-- 1. IMPORT LIBRARY PATHLIB

# Konfigurasi halaman (opsional tapi disarankan)
st.set_page_config(
    page_title="Dashboard Kualitas Udara (PM10)",
    page_icon="💨",
    layout="wide"
)

# --- 2. FUNGSI PEMUATAN DATA (DIPERBAIKI) ---
@st.cache_data  # <-- Menggunakan cache agar data dimuat sekali saja
def load_data(file_name):
    """
    Fungsi ini memuat data dan menggunakan pathlib untuk
    memastikan path file benar saat di-deploy.
    """
    # Membuat path absolut ke file CSV
    # Path(__file__) adalah path ke app.py
    # .parent adalah folder tempat app.py berada
    # / file_name adalah nama file datanya
    try:
        DATA_PATH = Path(__file__).parent / file_name
        df = pd.read_csv(DATA_PATH)
        
        # Tambahkan kolom timestamp di sini setelah memuat
        df['timestamp'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
        return df
    except FileNotFoundError:
        st.error(f"Error: File '{file_name}' tidak ditemukan.")
        st.error(f"Pastikan '{file_name}' ada di folder yang sama dengan app.py di repositori GitHub Anda.")
        return None
    except Exception as e:
        st.error(f"Terjadi error saat memuat data: {e}")
        return None

# --- Judul Utama Dashboard ---
st.title("💨 Dashboard Kualitas Udara: Analisis PM10")
st.write("Stasiun: **Shunyi** (Data dari 2013-2017)")

# --- 3. MEMUAT DATA MENGGUNAKAN FUNGSI ---
df = load_data("main_data.csv")

# Hentikan eksekusi jika data gagal dimuat
if df is None:
    st.stop()

# --- Sidebar (Opsional) ---
st.sidebar.header("Tentang Dashboard Ini")
st.sidebar.info(
    "Dashboard ini menjawab dua pertanyaan utama "
    "menggunakan data kualitas udara Shunyi:\n"
    "1. Jam puncak rata-rata PM10.\n"
    "2. Tren bulanan rata-rata PM10."
)

# ==============================================================================
# PERTANYAAN 1: Di jam berapakah rata-rata PM10 mencapai puncaknya?
# ==============================================================================
st.header("Pola PM10 Harian (Rata-Rata Seluruh Tahun)")
st.write("Analisis ini menunjukkan jam-jam di mana konsentrasi PM10 cenderung tinggi atau rendah dalam siklus 24 jam.")

# Kalkulasi: Rata-rata PM10 per jam
try:
    hourly_avg_pm10 = df.groupby('hour')['PM10'].mean().reset_index()

    # Temukan jam puncak
    peak_hour_data = hourly_avg_pm10.loc[hourly_avg_pm10['PM10'].idxmax()]
    peak_hour = int(peak_hour_data['hour'])
    peak_value = peak_hour_data['PM10']

    # Tampilkan jawaban dalam bentuk metrik
    st.metric(
        label=f"Jam Puncak PM10 🏆",
        value=f"Jam {peak_hour}:00",
        help=f"Rata-rata konsentrasi PM10 tertinggi terjadi pada jam {peak_hour}:00, mencapai {peak_value:.2f} µg/m³."
    )

    # Visualisasi: Line Chart dengan Altair
    chart_hourly = alt.Chart(hourly_avg_pm10).mark_line(point=True).encode(
        x=alt.X('hour', title='Jam dalam Sehari', axis=alt.Axis(format='d', values=list(range(0, 24)))), # Format 'd' (digit)
        y=alt.Y('PM10', title='Rata-rata Konsentrasi PM10 (µg/m³)'),
        tooltip=[
            alt.Tooltip('hour', title='Jam'),
            alt.Tooltip('PM10', title='Rata-rata PM10', format='.2f')
        ]
    ).interactive()

    st.altair_chart(chart_hourly, use_container_width=True)

except Exception as e:
    st.error(f"Error saat menganalisis data per jam: {e}")

# Pemisah
st.divider()

# ==============================================================================
# PERTANYAAN 2: Bagaimana tren rata-rata PM10 bulanan?
# ==============================================================================
st.header("Tren PM10 Bulanan (Berdasarkan Tahun)")
st.write("Analisis ini menunjukkan bagaimana konsentrasi PM10 berfluktuasi dari bulan ke bulan untuk tahun yang dipilih.")

# --- Widget Interaktif: Pilihan Tahun ---
# Ambil daftar tahun unik dari data
all_years = sorted(df['year'].unique())

# Buat selectbox, set default ke 2015 sesuai permintaan awal
default_index_2015 = all_years.index(2015) if 2015 in all_years else 0
selected_year = st.selectbox(
    "Pilih Tahun untuk Ditanalisis:",
    options=all_years,
    index=default_index_2015
)

# Kalkulasi: Filter data berdasarkan tahun yang dipilih
try:
    df_filtered_year = df[df['year'] == selected_year]
    
    if df_filtered_year.empty:
        st.warning(f"Tidak ada data PM10 untuk tahun {selected_year}.")
    else:
        # Rata-rata PM10 per bulan
        monthly_avg_pm10 = df_filtered_year.groupby('month')['PM10'].mean().reset_index()

        # Visualisasi: Line Chart dengan Altair
        chart_monthly = alt.Chart(monthly_avg_pm10).mark_line(point=True).encode(
            x=alt.X('month', title='Bulan', axis=alt.Axis(format='d', values=list(range(1, 13)))),
            y=alt.Y('PM10', title=f'Rata-rata PM10 (µg/m³) - Tahun {selected_year}'),
            tooltip=[
                alt.Tooltip('month', title='Bulan'),
                alt.Tooltip('PM10', title='Rata-rata PM10', format='.2f')
            ]
        ).interactive()

        st.altair_chart(chart_monthly, use_container_width=True)

except Exception as e:
    st.error(f"Error saat menganalisis data per bulan: {e}")

# ==============================================================================
# Tampilkan Data Mentah (Opsional)
# ==============================================================================
with st.expander("Tampilkan Data Mentah (Sudah Diproses)"):
    # Tampilkan df.head() agar tidak terlalu berat
    st.dataframe(df.head(100))
