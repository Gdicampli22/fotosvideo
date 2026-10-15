import io
import os
import sqlite3
import zipfile
from datetime import datetime
import streamlit as st
from PIL import Image

# Configuración de la página
st.set_page_config(
    page_title="Galería y Carga para Fiestas",
    page_icon="🎉",
    layout="wide",
)

# Directorio donde se guardarán físicamente los archivos subidos
UPLOAD_DIR = "uploaded_media"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Configuración de la base de datos SQLite
DB_PATH = "fiesta_galeria.db"


def init_db():
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  conn.commit()
  conn.close()


init_db()


def save_media_to_db(filename, file_path, file_type):
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO media (filename, file_path, file_type) VALUES (?, ?, ?)",
      (filename, file_path, file_type),
  )
  conn.commit()
  conn.close()


def get_all_media():
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, filename, file_path, file_type, upload_date FROM media"
      " ORDER BY id DESC"
  )
  rows = cursor.fetchall()
  conn.close()
  return rows


# --- Interfaz Principal ---
st.title("🎉 Galería y Carga de Recuerdos de la Fiesta")
st.markdown(
    "Sube tus fotos y videos en lote, previsualízalos en mosaico y descárgalos"
    " todos juntos cuando quieras."
)

st.sidebar.header("📤 Panel de Carga")
uploaded_files = st.sidebar.file_uploader(
    "Selecciona fotos y/o videos",
    type=["jpg", "jpeg", "png", "mp4", "mov", "avi"],
    accept_multiple_files=True,
)

if uploaded_files:
  if st.sidebar.button("Guardar todo en la Base de Datos"):
    with st.spinner("Guardando archivos..."):
      for uploaded_file in uploaded_files:
        # Evitar colisiones de nombres usando timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_filename = f"{timestamp}_{uploaded_file.name}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)

        # Guardar archivo físicamente
        with open(file_path, "wb") as f:
          f.write(uploaded_file.getbuffer())

        # Determinar tipo
        file_type = (
            "video" if uploaded_file.type.startswith("video") else "image"
        )

        # Registrar en SQLite
        save_media_to_db(uploaded_file.name, file_path, file_type)

    st.sidebar.success(
        f"¡Se han guardado {len(uploaded_files)} archivos exitosamente!"
    )
    st.rerun()

st.divider()

# --- Sección de Visualización y Descarga ---
media_records = get_all_media()

if not media_records:
  st.info(
      "Aún no hay fotos ni videos cargados. ¡Usa el panel lateral para subir"
      " los primeros!"
  )
else:
  col_header1, col_header2 = st.columns([3, 1])
  with col_header1:
    st.subheader(f"🖼️ Mosaico de Recuerdos ({len(media_records)} archivos)")

  with col_header2:
    # Botón para descargar todo en un ZIP
    if st.button("📥 Descargar Todo (ZIP)"):
      zip_buffer = io.BytesIO()
      with zipfile.ZipFile(
          zip_buffer, "w", zipfile.ZIP_DEFLATED
      ) as zip_file:
        for record in media_records:
          f_path = record[2]
          f_name = record[1]
          if os.path.exists(f_path):
            zip_file.write(f_path, arcname=f_name)
      zip_buffer.seek(0)

      st.download_button(
          label="📦 Clic aquí para descargar el .ZIP",
          data=zip_buffer,
          file_name=f"recuerdos_fiesta_{datetime.now().strftime('%Y%m%d')}.zip",
          mime="application/zip",
      )

  st.markdown("---")

  # Mostrar en Mosaico (Columnas dinámicas, ej. 4 columnas)
  cols_per_row = 4
  rows = [
      media_records[i : i + cols_per_row]
      for i in range(0, len(media_records), cols_per_row)
  ]

  for row in rows:
    cols = st.columns(cols_per_row)
    for idx, record in enumerate(row):
      media_id, original_name, file_path, file_type, upload_date = record
      with cols[idx]:
        if os.path.exists(file_path):
          if file_type == "image":
            img = Image.open(file_path)
            st.image(img, caption=original_name, use_container_width=True)
          else:
            st.video(file_path)
            st.caption(original_name)
        else:
          st.error(f"Archivo no encontrado: {original_name}")