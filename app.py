import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import pandas as pd
import io
import tempfile
import os
import zipfile
import fiona

# Setup KML Support
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

st.set_page_config(page_title="Tikon App - Monitoring Titik Kontrol", layout="wide")

# --- DATABASE MASTER ---
@st.cache_data
def load_master_data():
    gdf = gpd.read_file("data_tikon.shp")
    return gdf.to_crs(epsg=4326)

with st.spinner("Memuat Database Master..."):
    gdf_master = load_master_data()

# --- SIDEBAR: LAYOUT ALA SENIOR ---
with st.sidebar:
    st.title("⚙️ Konfigurasi")
    st.subheader("1. Batas Area Kerja")
    uploaded_file = st.file_uploader("Upload AOI (ZIP, KML, KMZ, GeoJSON):", type=['zip', 'geojson', 'kml', 'kmz'])
    
    st.write("---")
    st.subheader("2. Parameter Bounding Box")
    buffer_meters = st.number_input("Lebar Buffer (Meter):", min_value=0, value=5000, step=1000)
    
    st.write("---")
    st.info("Aplikasi ini otomatis menyaring titik kontrol dan menghitung zona UTM berdasarkan AOI.")

# --- MAIN PANEL ---
# Logika penamaan dinamis
if uploaded_file:
    # Ambil nama file asli tanpa ekstensi buat jadi variabel nama
    nama_area = os.path.splitext(uploaded_file.name)[0]
    st.title(f"📍 Monitoring Ketersediaan: {nama_area}")
else:
    nama_area = "Seluruh_Indonesia"
    st.title("📍 Tikon App - Monitoring Ketersediaan Titik Kontrol")

m = folium.Map(location=[-2.5, 118.0], zoom_start=5)
filtered_gdf = gpd.GeoDataFrame()

if uploaded_file is not None:
    with st.spinner(f"Memproses area {nama_area}..."):
        ext = uploaded_file.name.split('.')[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + ext) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        try:
            # Baca file sesuai format
            if ext == 'kml': aoi_gdf = gpd.read_file(tmp_path, driver='KML')
            elif ext == 'kmz':
                with zipfile.ZipFile(tmp_path, 'r') as kmz:
                    kml_name = [f for f in kmz.namelist() if f.endswith('.kml')][0]
                    kmz.extract(kml_name, tempfile.gettempdir())
                    aoi_gdf = gpd.read_file(os.path.join(tempfile.gettempdir(), kml_name), driver='KML')
            else: aoi_gdf = gpd.read_file(tmp_path)
            
            aoi_gdf = aoi_gdf.to_crs(epsg=4326)

            # Proses Bounding Box
            utm_crs_aoi = aoi_gdf.estimate_utm_crs()
            aoi_utm = aoi_gdf.to_crs(utm_crs_aoi)
            aoi_utm_box = aoi_utm.buffer(buffer_meters).envelope
            aoi_buffered_4326 = aoi_utm_box.to_crs(4326)
            
            # Gambar Peta
            folium.GeoJson(aoi_gdf, style_function=lambda x: {'color': 'red', 'weight': 2, 'fillOpacity': 0}).add_to(m)
            folium.GeoJson(aoi_buffered_4326, style_function=lambda x: {'color': 'yellow', 'fillColor': 'yellow', 'fillOpacity': 0.1}).add_to(m)
            m.fit_bounds([[aoi_buffered_4326.total_bounds[1], aoi_buffered_4326.total_bounds[0]], [aoi_buffered_4326.total_bounds[3], aoi_buffered_4326.total_bounds[2]]])

            # Query Titik
            filtered_gdf = gdf_master[gdf_master.geometry.within(aoi_buffered_4326.unary_union)].copy()

            if not filtered_gdf.empty:
                utm_crs_titik = filtered_gdf.estimate_utm_crs()
                filtered_utm = filtered_gdf.to_crs(utm_crs_titik)
                filtered_gdf['UTM_X'] = filtered_utm.geometry.x.round(3)
                filtered_gdf['UTM_Y'] = filtered_utm.geometry.y.round(3)
                filtered_gdf['Zona_UTM'] = utm_crs_titik.name

                for idx, row in filtered_gdf.iterrows():
                    popup_html = f"<b>Titik:</b> {row.get('NAMOBJ','N/A')}<br><b>Tahun:</b> {row.get('ACQ_TAHUN','N/A')}<br><b>Proyeksi:</b> {row.get('Zona_UTM','N/A')}"
                    folium.Marker([row.geometry.y, row.geometry.x], popup=folium.Popup(popup_html, max_width=250), icon=folium.Icon(color="green")).add_to(m)
        except Exception as e: st.error(f"Error: {e}")
        finally: os.remove(tmp_path)

st_folium(m, width="100%", height=500)

# --- TABEL & DOWNLOAD DENGAN NAMA OTOMATIS ---
if not filtered_gdf.empty:
    st.write("---")
    st.success(f"✅ Ditemukan {len(filtered_gdf)} Titik Kontrol dalam area {nama_area}")
    
    tabel_tampil = filtered_gdf.drop(columns='geometry')
    st.dataframe(tabel_tampil, use_container_width=True)

    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        # Nama file otomatis ngikutin AOI
        excel_name = f"Titik_Kontrol_{nama_area}.xlsx"
        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
            tabel_tampil.to_excel(writer, index=False)
        st.download_button(f"📥 Download Excel ({excel_name})", data=buffer_excel.getvalue(), file_name=excel_name)

    with col_dl2:
        shp_zip_name = f"SHP_Tikon_{nama_area}.zip"
        shp_buffer = io.BytesIO()
        with tempfile.TemporaryDirectory() as tmpdir:
            path_shp = os.path.join(tmpdir, "export.shp")
            filtered_gdf.to_file(path_shp)
            with zipfile.ZipFile(shp_buffer, 'w') as zf:
                for f in os.listdir(tmpdir): zf.write(os.path.join(tmpdir, f), arcname=f)
        st.download_button(f"🗺️ Download SHP ({shp_zip_name})", data=shp_buffer.getvalue(), file_name=shp_zip_name)