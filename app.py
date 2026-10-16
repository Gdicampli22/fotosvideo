import io
import os
import time
import zipfile
from datetime import datetime
import streamlit as st
from supabase import create_client, Client

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Felices 70 Años Hilda - Galería",
    page_icon="✨",
    layout="wide",
)

LOGO_PATH = "logo_hilda.jpg"
BUCKET_NAME = "fotos_fiesta"

# ==========================================
# CONEXIÓN A SUPABASE (NEXUS ERP)
# ==========================================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# ==========================================
# FUNCIONES DE SUPABASE STORAGE
# ==========================================
def get_all_media():
    try:
        # Listamos los archivos del bucket
        archivos = supabase.storage.from_(BUCKET_NAME).list()
        
        # Filtramos solo imágenes y videos, y los ordenamos por fecha de creación (los más nuevos primero)
        archivos_validos = [
            f for f in archivos 
            if f["name"].lower().endswith((".png", ".jpg", ".jpeg", ".mp4", ".mov", ".avi"))
        ]
        return sorted(archivos_validos, key=lambda x: x.get("created_at", ""), reverse=True)
    except Exception as e:
        st.error(f"Error conectando a Supabase: {e}")
        return []

def rename_media(old_name, new_name):
    try:
        supabase.storage.from_(BUCKET_NAME).move(old_name, new_name)
        return True
    except Exception as e:
        st.error(f"Error al renombrar: {e}")
        return False

def delete_media(filename):
    try:
        supabase.storage.from_(BUCKET_NAME).remove([filename])
        return True
    except Exception as e:
        st.error(f"Error al borrar: {e}")
        return False

# ==========================================
# ENCABEZADO TEMÁTICO
# ==========================================
if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, use_container_width=True)
else:
    st.title("🎉 Felices 70 Años Hilda 🎉")

st.markdown(
    "<h3 style='text-align: center; color: #d4af37;'>Galería de Recuerdos Compartidos</h3>",
    unsafe_allow_html=True,
)
st.write("")

# ==========================================
# PANEL LATERAL DE CARGA
# ==========================================
st.sidebar.header("📤 Sube tus Fotos y Videos")
st.sidebar.markdown("Compartí los mejores momentos. Podés seleccionar varios a la vez.")

uploaded_files = st.sidebar.file_uploader(
    "Selecciona archivos",
    type=["jpg", "jpeg", "png", "mp4", "mov", "avi"],
    accept_multiple_files=True,
)

if uploaded_files:
    st.sidebar.info(f"📁 Archivos detectados en cola: {len(uploaded_files)}")

    if st.sidebar.button("💾 Guardar en la Galería"):
        with st.spinner("Guardando archivos en la nube de Supabase..."):
            success_count = 0
            for uploaded_file in uploaded_files:
                try:
                    # Limpiamos el nombre y le agregamos un timestamp para que no se pisen
                    nombre_limpio = uploaded_file.name.replace(' ', '_')
                    nombre_unico = f"{int(time.time())}_{nombre_limpio}"
                    
                    file_bytes = uploaded_file.read()
                    
                    supabase.storage.from_(BUCKET_NAME).upload(
                        file=file_bytes,
                        path=nombre_unico,
                        file_options={"content-type": uploaded_file.type}
                    )
                    success_count += 1
                except Exception as e:
                    st.sidebar.error(f"Error al guardar {uploaded_file.name}: {e}")

            if success_count > 0:
                st.sidebar.success(f"¡Éxito! Se cargaron correctamente **{success_count}** archivos.")
                time.sleep(1.5) # Pausa cortita para que el usuario lea el mensaje
                st.rerun()
else:
    st.sidebar.warning("⚠️ Ningún archivo seleccionado todavía.")

st.divider()

# ==========================================
# SECCIÓN DE VISUALIZACIÓN, EDICIÓN Y DESCARGA
# ==========================================
media_records = get_all_media()

if not media_records:
    st.info("📸 Aún no hay fotos ni videos cargados. ¡Sé el primero en subir los recuerdos desde el panel lateral!")
else:
    col_header1, col_header2 = st.columns([3, 1])
    
    with col_header1:
        st.subheader(f"🖼️ Mosaico de Recuerdos ({len(media_records)} archivos)")

    with col_header2:
        # Botón para descargar todo en un ZIP desde la Nube
        if st.button("📥 Descargar Todo (ZIP)"):
            with st.spinner("Descargando de Supabase y preparando el ZIP..."):
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for record in media_records:
                        filename = record["name"]
                        # Descargamos los bytes de Supabase en memoria
                        file_bytes = supabase.storage.from_(BUCKET_NAME).download(filename)
                        zip_file.writestr(filename, file_bytes)
                
                zip_buffer.seek(0)

                st.download_button(
                    label="📦 Descargar .ZIP completo",
                    data=zip_buffer,
                    file_name=f"recuerdos_70_hilda_{datetime.now().strftime('%Y%m%d')}.zip",
                    mime="application/zip",
                )

    st.markdown("---")

    # ==========================================
    # MOSTRAR EN MOSAICO (3 COLUMNAS)
    # ==========================================
    cols_per_row = 3
    rows = [
        media_records[i : i + cols_per_row]
        for i in range(0, len(media_records), cols_per_row)
    ]

    for row in rows:
        cols = st.columns(cols_per_row)
        for idx, record in enumerate(row):
            filename = record["name"]
            
            # Pedimos a Supabase la URL pública para poder mostrar la imagen rápido
            public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(filename)
            
            with cols[idx]:
                with st.container(border=True):
                    
                    # Renderizar imagen o video desde la URL de la nube
                    if filename.lower().endswith((".mp4", ".mov", ".avi")):
                        st.video(public_url)
                    else:
                        st.image(public_url, use_container_width=True)

                    st.caption(f"Archivo: **{filename}**")

                    # Sección desplegable para gestionar (cambiar nombre o borrar)
                    with st.expander("⚙️ Opciones de edición"):
                        # Nota: En Supabase la extensión es obligatoria al cambiar el nombre
                        new_name = st.text_input("Nuevo nombre (con extensión)", value=filename, key=f"name_{filename}")
                        
                        col_btn1, col_btn2 = st.columns(2)

                        with col_btn1:
                            if st.button("💾 Cambiar", key=f"btn_rename_{filename}"):
                                if new_name and new_name != filename:
                                    if rename_media(filename, new_name):
                                        st.success("¡Nombre actualizado!")
                                        time.sleep(1)
                                        st.rerun()

                        with col_btn2:
                            if st.button("🗑️ Borrar", key=f"btn_delete_{filename}", type="primary"):
                                if delete_media(filename):
                                    st.warning("Archivo eliminado.")
                                    time.sleep(1)
                                    st.rerun()