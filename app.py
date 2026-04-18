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

# --- MENGAKTIFKAN KUNCI INGGRIS BUAT BACA KML/KMZ ---
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'
# ---------------------------------------------------

st.set_page_config(page_title="Tikon App - Monitoring Titik Kontrol", layout="wide")

st.title("📍 Tikon App - Monitoring Ketersediaan Titik Kontrol")
st.write("Upload batas area (AOI), atur jarak buffer, dan sistem otomatis membuat blok kotak (Bounding Box) untuk mencari titik kontrol.")

@st.cache_data
def load_master_data():
    gdf = gpd.read_file("data_tikon.shp")
    return gdf.to_crs(epsg=4326)

with st.spinner("Memuat Master Database..."):
    gdf_master = load_master_data()

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("1. Upload Area Kerja (AOI)")
    st.info("Format: ZIP (SHP), GeoJSON, KML, atau KMZ.")
    uploaded_file = st.file_uploader("Pilih file batas area:", type=['zip', 'geojson', 'kml', 'kmz'])
    
    st.write("---")
    st.subheader("2. Pengaturan Blok Kotak (Buffer)")
    buffer_meters = st.number_input("Lebar Buffer Area (Meter):", min_value=0, value=5000, step=1000)

with col2:
    st.subheader("3. Peta Visualisasi")
    m = folium.Map(location=[-2.5, 118.0], zoom_start=5)
    filtered_gdf = gpd.GeoDataFrame()
    base_filename = "Area_Kerja" # Nama default kalau nggak ada file

    if uploaded_file is not None:
        # Ambil nama file tanpa ekstensi (Contoh: "02 AOI.zip" jadi "02 AOI")
        base_filename = os.path.splitext(uploaded_file.name)[0]
        
        with st.spinner("Membaca dan memproses area kerja lu..."):
            ext = uploaded_file.name.split('.')[-1].lower()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.' + ext) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            try:
                # --- LOGIKA MEMBACA BERBAGAI FORMAT FILE ---
                if ext == 'kml':
                    aoi_gdf = gpd.read_file(tmp_path, driver='KML')
                elif ext == 'kmz':
                    with zipfile.ZipFile(tmp_path, 'r') as kmz:
                        kml_name = [f for f in kmz.namelist() if f.endswith('.kml')][0]
                        kmz.extract(kml_name, tempfile.gettempdir())
                        extracted_kml_path = os.path.join(tempfile.gettempdir(), kml_name)
                        aoi_gdf = gpd.read_file(extracted_kml_path, driver='KML')
                else:
                    aoi_gdf = gpd.read_file(tmp_path)
                
                aoi_gdf = aoi_gdf.to_crs(epsg=4326)

                # --- PROSES BUFFERING MENJADI KOTAK (ENVELOPE) ---
                utm_crs_aoi = aoi_gdf.estimate_utm_crs()
                aoi_utm = aoi_gdf.to_crs(utm_crs_aoi)
                aoi_utm_buffered = aoi_utm.buffer(buffer_meters)
                aoi_utm_box = aoi_utm_buffered.envelope
                aoi_buffered_4326 = aoi_utm_box.to_crs(4326)
                
                # --- VISUALISASI PETA ---
                folium.GeoJson(
                    aoi_gdf,
                    style_function=lambda x: {'fillColor': 'none', 'color': 'red', 'weight': 2}
                ).add_to(m)

                if buffer_meters >= 0:
                    folium.GeoJson(
                        aoi_buffered_4326,
                        style_function=lambda x: {'fillColor': 'yellow', 'color': 'yellow', 'weight': 2, 'fillOpacity': 0.15}
                    ).add_to(m)

                bounds = aoi_buffered_4326.total_bounds
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

                # --- SPATIAL QUERY BERDASARKAN KOTAK ---
                filtered_gdf = gdf_master[gdf_master.geometry.within(aoi_buffered_4326.unary_union)].copy()

                if not filtered_gdf.empty:
                    utm_crs_titik = filtered_gdf.estimate_utm_crs()
                    filtered_utm = filtered_gdf.to_crs(utm_crs_titik)
                    
                    filtered_gdf['UTM_X'] = filtered_utm.geometry.x.round(3)
                    filtered_gdf['UTM_Y'] = filtered_utm.geometry.y.round(3)
                    filtered_gdf['Zona_UTM'] = utm_crs_titik.name

                    # Nempelin titik ke peta dengan Pop-up Custom
                    for idx, row in filtered_gdf.iterrows():
                        nama_titik = row.get('NAMOBJ', 'N/A')
                        tahun = row.get('ACQ_TAHUN', 'N/A')
                        zona = row.get('Zona_UTM', 'N/A')

                        popup_html = f"""
                        <div style='min-width: 150px; font-family: sans-serif;'>
                            <b>Nama Titik:</b> {nama_titik}<br>
                            <b>Tahun:</b> {tahun}<br>
                            <b>Proyeksi:</b> {zona}
                        </div>
                        """

                        folium.Marker(
                            location=[row.geometry.y, row.geometry.x],
                            popup=folium.Popup(popup_html, max_width=300),
                            icon=folium.Icon(color="green", icon="info-sign")
                        ).add_to(m)
                    
            except Exception as e:
                st.error(f"Gagal memproses file: {e}. Pastikan file valid.")
            finally:
                os.remove(tmp_path) 
                
    st_folium(m, width="100%", height=500)

# --- BAGIAN TABEL & TOMBOL DOWNLOAD EXCEL/SHP ---
if not filtered_gdf.empty:
    st.write("---")
    st.subheader(f"✅ Ditemukan {len(filtered_gdf)} Titik Kontrol dalam AOI")
    
    tabel_tampil = filtered_gdf.drop(columns='geometry')
    st.dataframe(tabel_tampil, use_container_width=True)

    st.write("**Silakan pilih format download hasil saringan:**")
    
    # Bikin tombolnya sejajar (2 Kolom)
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        # 1. DOWNLOAD EXCEL
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            tabel_tampil.to_excel(writer, index=False, sheet_name='Titik_Kontrol')
        
        st.download_button(
            label="📥 Download Data (Excel .xlsx)",
            data=excel_buffer.getvalue(),
            file_name=f'Titik_Kontrol_{base_filename}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    with col_dl2:
        # 2. DOWNLOAD SHAPEFILE (Bentuk ZIP)
        shp_buffer = io.BytesIO()
        
        # Bikin folder sementara buat nyimpen file-file SHP (.shp, .dbf, .shx, dll)
        with tempfile.TemporaryDirectory() as tmpdir:
            # Nama file di dalam zip-nya kita bikin agak pendek
            export_path = os.path.join(tmpdir, f"Tikon_{base_filename[:15]}.shp")
            
            # Export data yang udah ada info UTM-nya jadi SHP
            filtered_gdf.to_file(export_path, driver='ESRI Shapefile')
            
            # Bungkus semua rombongan SHP itu jadi satu file ZIP
            with zipfile.ZipFile(shp_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file in os.listdir(tmpdir):
                    zf.write(os.path.join(tmpdir, file), arcname=file)

        st.download_button(
            label="🗺️ Download Data (Shapefile .zip)",
            data=shp_buffer.getvalue(),
            file_name=f'Titik_Kontrol_{base_filename}_SHP.zip',
            mime='application/zip'
        )