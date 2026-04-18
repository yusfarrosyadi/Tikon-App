# 📍 Tikon App: Monitoring Titik Kontrol

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![GIS](https://img.shields.io/badge/GIS-Geospatial-green?style=for-the-badge)

Aplikasi web berbasis Python (Streamlit) yang dirancang untuk membantu Surveyor Pemetaan dalam melakukan filter, buffering, dan ekstraksi data Titik Kontrol (GCP/ICP) yang tersedia dalam database secara otomatis berdasarkan area kerja (AOI).

## 🚀 Fitur Utama
- **Multi-format Support:** Mendukung upload AOI dalam format `.zip` (Shapefile), `KML`, `KMZ`, dan `GeoJSON`.
- **Automatic Bounding Box:** Membuat blok kotak (envelope) otomatis berdasarkan jarak buffer yang ditentukan.
- **Smart Spatial Query:** Menyaring titik kontrol dari database master yang masuk ke dalam area box.
- **Automatic UTM Projection:** Menghitung nilai koordinat Easting (X), Northing (Y), dan Zona UTM secara otomatis sesuai lokasi titik.
- **Export Ready:** Download hasil saringan langsung ke format **Excel (.xlsx)** dan **Shapefile (.zip)**.

## 📖 Petunjuk Penggunaan (WebApp Dashboard)

### 1. Memuat Area Kerja (AOI)
* **Upload File:** Gunakan panel di sebelah kiri (Sidebar) untuk mengunggah file batas area. Format yang didukung: `.zip` (Shapefile), `.kml`, `.kmz`, atau `.geojson`.
* **Auto-Naming:** Judul dashboard dan nama file hasil unduhan akan menyesuaikan secara otomatis dengan nama file AOI yang Anda unggah.

### 2. Pengaturan Blok Kotak (Buffer)
* **Input Jarak:** Masukkan nilai buffer dalam satuan **Meter**. Sistem secara otomatis akan membuat *Bounding Box* (kotak persegi) yang melingkupi AOI ditambah jarak buffer tersebut.
* **Visualisasi:** Garis **Merah** adalah AOI asli Anda, sedangkan area **Kuning** adalah blok kotak hasil buffer yang digunakan untuk pencarian titik.

### 3. Interaksi Peta & Data
* **Klik Titik:** Klik pada marker hijau untuk melihat informasi detail mengenai Nama Titik, Tahun Akuisisi, dan Proyeksi/Zona UTM.
* **Tabel Atribut:** Data yang muncul di tabel bawah peta adalah titik yang secara spasial berada di dalam blok kotak.
* **Ekspor Data:** Anda dapat mengunduh hasil filter langsung ke format **Excel (.xlsx)** atau **Shapefile (.zip)** yang sudah menyertakan kalkulasi koordinat UTM Easting (X) dan Northing (Y).

## 🛠️ Persyaratan Sistem
Sebelum menjalankan aplikasi, pastikan Anda memiliki:
1. Python 3.9+
2. Library: `streamlit`, `geopandas`, `folium`, `streamlit-folium`, `openpyxl`, `fiona`.
3. Database master bernama `data_tikon.shp` di folder yang sama.

## 💻 Cara Menjalankan
1. Clone repository ini.
2. Siapkan file database `data_tikon.shp` (tidak disertakan dalam repo ini demi keamanan data).
3. Jalankan perintah:
   ```bash
   streamlit run app.py