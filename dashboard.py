import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from pathlib import Path

# ==============================
# KONFIGURASI HALAMAN
# ==============================
st.set_page_config(page_title="Bike Sharing Dashboard", page_icon="🚲", layout="wide")

# ==============================
# LOAD & CLEAN DATA
# ==============================
@st.cache_data
def load_data():
    # Menggunakan pathlib untuk membangun path yang dinamis sesuai arahan reviewer
    current_dir = Path(__file__).parent
    data_path = current_dir / "main_data.csv"
    
    df = pd.read_csv(data_path)
    
    # Hanya ubah tipe data tanggal
    df['dteday'] = pd.to_datetime(df['dteday'])
    
    # Cek apakah kolom demand_category sudah ada. Jika belum, lakukan binning
    if 'demand_category' not in df.columns:
        df['demand_category'] = pd.qcut(df['cnt'], q=3, labels=['Low Demand', 'Medium Demand', 'High Demand'])
    
    return df

day_df = load_data()

# ==============================
# SIDEBAR (FILTER)
# ==============================
st.sidebar.title("🚲 Bike Sharing")

# Dapatkan rentang tanggal minimum dan maksimum dari data
min_date = day_df["dteday"].min().date()
max_date = day_df["dteday"].max().date()

# Komponen Filter Tanggal
date_range = st.sidebar.date_input(
    label='Filter Rentang Waktu',
    min_value=min_date,
    max_value=max_date,
    value=[min_date, max_date]
)

# Cek apakah user sudah memilih 2 tanggal (awal dan akhir)
if len(date_range) == 2:
    start_date, end_date = date_range
    # Terapkan filter pada dataset
    main_df = day_df[(day_df["dteday"].dt.date >= start_date) & (day_df["dteday"].dt.date <= end_date)]
else:
    # Jika user baru memilih 1 tanggal, tampilkan pesan informatif
    st.sidebar.info("Anda baru memilih satu tanggal. Untuk sementara, dashboard menampilkan seluruh data.")
    main_df = day_df

# ==============================
# MAIN DASHBOARD
# ==============================
st.title("🚲 Bike Sharing Data Analytics Dashboard")

# Teks pengantar
st.markdown("Dashboard ini merangkum hasil analisis tiga pertanyaan bisnis beserta analisis lanjutan (*Clustering*) dari data penyewaan sepeda harian.")

# Menampilkan 4 Kolom Metrik
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_rentals = main_df['cnt'].sum()
    st.metric("Total Penyewaan", value=f"{total_rentals:,}")
with col2:
    total_registered = main_df['registered'].sum()
    st.metric("Pengguna Registered", value=f"{total_registered:,}")
with col3:
    total_casual = main_df['casual'].sum()
    st.metric("Pengguna Casual", value=f"{total_casual:,}")
with col4:
    avg_rentals = round(main_df['cnt'].mean()) if not main_df.empty else 0
    st.metric("Rata-rata Harian", value=f"{avg_rentals:,}")

st.markdown("---")

# ==============================
# VISUALISASI DATA
# ==============================
# 1. Pengaruh Cuaca (Typo string yang terputus sudah diperbaiki di sini)
st.subheader("1. Pengaruh Kondisi Cuaca terhadap Penyewaan")
weather_eda_df = main_df.groupby('weathersit', observed=True)[['casual', 'registered']].mean().round(2).reset_index()
weather_melted = pd.melt(weather_eda_df, id_vars=['weathersit'], value_vars=['casual', 'registered'], var_name='User Type', value_name='Average Rentals')

fig1, ax1 = plt.subplots(figsize=(10, 5))
sns.barplot(x='weathersit', y='Average Rentals', hue='User Type', data=weather_melted, palette=['#72B3E7', '#1F77B4'], ax=ax1)
ax1.set_xlabel("Kondisi Cuaca")
ax1.set_ylabel("Rata-rata Penyewaan")
ax1.grid(axis='y', linestyle='--', alpha=0.7)
st.pyplot(fig1)

# 2. Tren Pertumbuhan Bulanan
st.subheader("2. Tren Pertumbuhan Bulanan (2011 vs 2012)")
monthly_eda_df = main_df.groupby(['yr', 'mnth'], observed=True).agg({'cnt': 'sum'}).reset_index()

if len(monthly_eda_df) > 1:
    fig2, ax2 = plt.subplots(figsize=(12, 5))
    sns.lineplot(data=monthly_eda_df, x='mnth', y='cnt', hue='yr', marker='o', linewidth=2.5, palette=['#85C1E9', '#1B4F72'], ax=ax2)
    ax2.set_xticks(range(1, 13))
    ax2.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'])
    ax2.set_xlabel("Bulan")
    ax2.set_ylabel("Total Penyewaan")
    ax2.grid(True, linestyle='--', alpha=0.6)
    st.pyplot(fig2)
else:
    st.info("Rentang waktu yang dipilih terlalu singkat. Silakan perlebar rentang tanggal untuk melihat garis tren pertumbuhan.")

# 3. Hari Kerja vs Hari Libur
st.subheader("3. Pola Penyewaan: Hari Kerja vs Hari Libur")
workingday_eda_df = main_df.groupby('workingday', observed=True)[['casual', 'registered']].mean().round(2).reset_index()
workingday_melted = pd.melt(workingday_eda_df, id_vars=['workingday'], value_vars=['casual', 'registered'], var_name='User Type', value_name='Average Rentals')

fig3, ax3 = plt.subplots(figsize=(10, 5))
sns.barplot(x='workingday', y='Average Rentals', hue='User Type', data=workingday_melted, palette=['#A5D6A7', '#2E7D32'], ax=ax3)
ax3.set_xlabel("Kategori Hari")
ax3.set_ylabel("Rata-rata Penyewaan")
ax3.grid(axis='y', linestyle='--', alpha=0.7)
st.pyplot(fig3)

# 4. Clustering (High Demand)
st.subheader("4. Analisis Lanjutan: Distribusi Cuaca pada Hari 'High Demand'")
high_demand_weather = main_df[main_df['demand_category'] == 'High Demand'].groupby('weathersit', observed=True)['cnt'].count().reset_index()
high_demand_weather.rename(columns={'cnt': 'jumlah_hari'}, inplace=True)

if not high_demand_weather.empty and high_demand_weather['jumlah_hari'].sum() > 0:
    fig4, ax4 = plt.subplots(figsize=(8, 4))
    sns.barplot(x='weathersit', y='jumlah_hari', data=high_demand_weather, hue='weathersit', palette='Blues_r', legend=False, ax=ax4)
    ax4.set_xlabel("Kondisi Cuaca")
    ax4.set_ylabel("Jumlah Hari")
    ax4.grid(axis='y', linestyle='--', alpha=0.7)
    st.pyplot(fig4)
else:
    st.info("Tidak ada hari dengan kategori 'High Demand' pada rentang waktu yang Anda pilih.")

st.caption("Copyright © 2023 - Bike Sharing Data Analysis")
