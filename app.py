import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import geopandas as gpd
import pandas as pd
import io
import tempfile
import os
import zipfile
import fiona
from shapely.geometry import shape

# --- INISIALISASI KML SUPPORT ---
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

st.set_page_config(page_title="Tikon App - Monitoring Titik Kontrol", layout="wide")

# --- 1. MEMORI APLIKASI (SESSION STATE) ---
if 'filtered_gdf' not in st.session_state:
    st.session_state.filtered_gdf = gpd.GeoDataFrame()
if 'aoi_display' not in st.session_state:
    st.session_state.aoi_display = None # Untuk nyimpen geometri AOI yang digambar/upload

# --- 2. DATABASE MASTER ---
@st.cache_data
def load_master_data():
    gdf = gpd.read_file("data_tikon.shp")
    return gdf.to_crs(epsg=4326)

with st.spinner("Memuat Database Master..."):
    gdf_master = load_master_data()

# --- 3. SIDEBAR (MENU KIRI) ---
with st.sidebar:
    st.title("⚙️ Konfigurasi")
    st.subheader("Opsi A: Upload AOI")
    uploaded_file = st.file_uploader("Upload SHP(ZIP), KML, KMZ:", type=['zip', 'geojson', 'kml', 'kmz'])
    
    st.write("---")
    st.subheader("Opsi B: Gambar Manual")
    st.info("Gunakan ikon kotak/polygon di peta sebelah kanan untuk membuat AOI sendiri.")
    
    st.write("---")
    st.subheader("Parameter")
    buffer_meters = st.number_input("Lebar Buffer (Meter):", min_value=0, value=5000, step=1000)
    
    if st.button("🗑️ Reset Semua Data"):
        st.session_state.filtered_gdf = gpd.GeoDataFrame()
        st.session_state.aoi_display = None
        st.rerun()

# --- 4. LOGIKA PEMROSESAN ---
# Variabel bantuan untuk judul
nama_area = "Custom AOI" if uploaded_file is None else os.path.splitext(uploaded_file.name)[0]
st.title(f"📍 Tikon App - Monitoring Ketersediaan Titik Kontrol: {nama_area}")

# A. Jika ada file yang diupload
if uploaded_file is not None:
    ext = uploaded_file.name.split('.')[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.' + ext) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    try:
        if ext == 'kml': aoi_raw = gpd.read_file(tmp_path, driver='KML')
        elif ext == 'kmz':
            with zipfile.ZipFile(tmp_path, 'r') as kmz:
                kml_n = [f for f in kmz.namelist() if f.endswith('.kml')][0]
                kmz.extract(kml_n, tempfile.gettempdir())
                aoi_raw = gpd.read_file(os.path.join(tempfile.gettempdir(), kml_n), driver='KML')
        else: aoi_raw = gpd.read_file(tmp_path)
        
        aoi_raw = aoi_raw.to_crs(epsg=4326)
        # Hitung Bounding Box Buffer
        utm_aoi = aoi_raw.estimate_utm_crs()
        aoi_box = aoi_raw.to_crs(utm_aoi).buffer(buffer_meters).envelope.to_crs(4326)
        
        st.session_state.aoi_display = aoi_box
        st.session_state.filtered_gdf = gdf_master[gdf_master.geometry.within(aoi_box.unary_union)].copy()
    finally:
        os.remove(tmp_path)

# --- 5. VISUALISASI PETA ---
m = folium.Map(location=[-2.5, 118.0], zoom_start=5)

# Pasang Alat Gambar (Draw Tools)
draw_tool = Draw(
    export=False,
    position='topleft',
    draw_options={'polyline': False, 'circlemarker': False, 'marker': False, 'circle': False}
)
draw_tool.add_to(m)

# Jika ada AOI (baik dari upload atau memori), tampilin di peta
if st.session_state.aoi_display is not None:
    folium.GeoJson(
        st.session_state.aoi_display,
        style_function=lambda x: {'color': 'yellow', 'fillColor': 'yellow', 'fillOpacity': 0.15}
    ).add_to(m)
    
    # Auto-zoom ke AOI
    b = st.session_state.aoi_display.total_bounds
    m.fit_bounds([[b[1], b[0]], [b[3], b[2]]])

    # Gambar Titik-titiknya
    for idx, row in st.session_state.filtered_gdf.iterrows():
        popup_txt = f"<b>Titik:</b> {row.get('NAMOBJ','N/A')}<br><b>Tahun:</b> {row.get('ACQ_TAHUN','N/A')}"
        folium.Marker([row.geometry.y, row.geometry.x], popup=folium.Popup(popup_txt, max_width=200), icon=folium.Icon(color="green")).add_to(m)

# Jalankan Peta dan Tangkap Input Gambar Manual
map_output = st_folium(m, width="100%", height=500)

# B. Jika user nggambar manual di peta
if map_output["last_active_drawing"]:
    geom_drawn = shape(map_output["last_active_drawing"]["geometry"])
    aoi_manual = gpd.GeoSeries([geom_drawn], crs=4326)
    
    # Proses Buffer Box untuk hasil gambar manual
    utm_manual = aoi_manual.estimate_utm_crs()
    aoi_box_manual = aoi_manual.to_crs(utm_manual).buffer(buffer_meters).envelope.to_crs(4326)
    
    # Update Memori
    st.session_state.aoi_display = aoi_box_manual
    st.session_state.filtered_gdf = gdf_master[gdf_master.geometry.within(aoi_box_manual.unary_union)].copy()
    st.rerun() # Refresh biar titiknya langsung nongol

# --- 6. TABEL DATA & EXPORT ---
if not st.session_state.filtered_gdf.empty:
    gdf_final = st.session_state.filtered_gdf.copy()
    
    # Re-calculate UTM (untuk tabel)
    utm_crs = gdf_final.estimate_utm_crs()
    utm_points = gdf_final.to_crs(utm_crs)
    gdf_final['UTM_X'] = utm_points.geometry.x.round(3)
    gdf_final['UTM_Y'] = utm_points.geometry.y.round(3)
    gdf_final['Zona_UTM'] = utm_crs.name
    
    st.write("---")
    st.success(f"✅ Ditemukan {len(gdf_final)} Titik Kontrol")
    
    tabel_tampil = gdf_final.drop(columns='geometry')
    st.dataframe(tabel_tampil, use_container_width=True)

    # TOMBOL DOWNLOAD
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        buf_xl = io.BytesIO()
        with pd.ExcelWriter(buf_xl, engine='openpyxl') as wr: tabel_tampil.to_excel(wr, index=False)
        st.download_button(f"📥 Download Excel ({nama_area})", data=buf_xl.getvalue(), file_name=f"Tikon_{nama_area}.xlsx")
    with col_dl2:
        buf_shp = io.BytesIO()
        with tempfile.TemporaryDirectory() as td:
            p_shp = os.path.join(td, "export.shp")
            gdf_final.to_file(p_shp)
            with zipfile.ZipFile(buf_shp, 'w') as zf:
                for f in os.listdir(td): zf.write(os.path.join(td, f), arcname=f)
        st.download_button(f"🗺️ Download SHP ({nama_area})", data=buf_shp.getvalue(), file_name=f"SHP_Tikon_{nama_area}.zip")