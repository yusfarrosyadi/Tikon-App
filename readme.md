# 📍 Tikon App: Smart Spatial Query & Monitoring

Aplikasi web berbasis Python (Streamlit) yang dirancang untuk membantu **Surveyor Pemetaan** dalam melakukan filter, buffering, dan ekstraksi data Titik Kontrol (GCP/ICP) secara otomatis berdasarkan area kerja (AOI).

## 🚀 Fitur Utama
- **Multi-format Support:** Mendukung upload AOI dalam format `.zip` (Shapefile), `KML`, `KMZ`, dan `GeoJSON`.
- **Automatic Bounding Box:** Membuat blok kotak (envelope) otomatis berdasarkan jarak buffer yang ditentukan.
- **Smart Spatial Query:** Menyaring titik kontrol dari database master yang masuk ke dalam area box.
- **Automatic UTM Projection:** Menghitung nilai koordinat Easting (X), Northing (Y), dan Zona UTM secara otomatis sesuai lokasi titik.
- **Export Ready:** Download hasil saringan langsung ke format **Excel (.xlsx)** dan **Shapefile (.zip)**.

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