import io
import os
import sqlite3
import zipfile
from datetime import datetime
import streamlit as st
from PIL import Image

# Configuración de la página
st.set_page_config(
    page_title="Felices 70 Años Hilda - Galería",
    page_icon="✨",
    layout="wide",
)

DB_PATH = "fiesta_galeria.db"
LOGO_PATH = "logo_hilda.jpg"


# --- Inicialización de Base de Datos (con BLOB para SQLite en la nube) ---
def init_db():
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_data BLOB NOT NULL,
            file_type TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  conn.commit()
  conn.close()


init_db()


def save_media_to_db(filename, file_data, file_type):
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO media (filename, file_data, file_type) VALUES (?, ?, ?)",
      (filename, file_data, file_type),
  )
  conn.commit()
  conn.close()


def get_all_media():
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, filename, file_data, file_type, upload_date FROM media"
      " ORDER BY id DESC"
  )
  rows = cursor.fetchall()
  conn.close()
  return rows


def update_media_name(media_id, new_name):
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute(
      "UPDATE media SET filename = ? WHERE id = ?", (new_name, media_id)
  )
  conn.commit()
  conn.close()


def delete_media_from_db(media_id):
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute("DELETE FROM media WHERE id = ?", (media_id,))
  conn.commit()
  conn.close()


# --- Encabezado Temático ---
if os.path.exists(LOGO_PATH):
  st.image(LOGO_PATH, use_container_width=True)
else:
  st.title("🎉 Felices 70 Años Hilda 🎉")

st.markdown(
    "<h3 style='text-align: center; color: #d4af37;'>Galería de Recuerdos"
    " Compartidos</h3>",
    unsafe_allow_html=True,
)
st.write("")

# --- Panel Lateral de Carga ---
st.sidebar.header("📤 Sube tus Fotos y Videos")
st.sidebar.markdown(
    "Compartí los mejores momentos. Podés seleccionar varios a la vez."
)

uploaded_files = st.sidebar.file_uploader(
    "Selecciona archivos",
    type=["jpg", "jpeg", "png", "mp4", "mov", "avi"],
    accept_multiple_files=True,
)

# Validaciones de Carga
if uploaded_files:
  st.sidebar.info(f"📁 Archivos detectados en cola: {len(uploaded_files)}")

  if st.sidebar.button("💾 Guardar en la Galería"):
    with st.spinner("Guardando archivos en la base de datos..."):
      success_count = 0
      for uploaded_file in uploaded_files:
        try:
          file_bytes = uploaded_file.read()
          file_type = (
              "video" if uploaded_file.type.startswith("video") else "image"
          )
          save_media_to_db(uploaded_file.name, file_bytes, file_type)
          success_count += 1
        except Exception as e:
          st.sidebar.error(f"Error al guardar {uploaded_file.name}: {e}")

    if success_count > 0:
      st.sidebar.success(
          f"¡Éxito! Se cargaron correctamente **{success_count}** archivos."
      )
      st.rerun()
else:
  st.sidebar.warning("⚠️ Ningún archivo seleccionado todavía.")

st.divider()

# --- Sección de Visualización, Edición y Descarga ---
media_records = get_all_media()

if not media_records:
  st.info(
      "📸 Aún no hay fotos ni videos cargados. ¡Sé el primero en subir los"
      " recuerdos desde el panel lateral!"
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
          media_id, filename, file_data, file_type, _ = record
          zip_file.writestr(filename, file_data)
      zip_buffer.seek(0)

      st.download_button(
          label="📦 Descargar .ZIP completo",
          data=zip_buffer,
          file_name=f"recuerdos_70_hilda_{datetime.now().strftime('%Y%m%d')}.zip",
          mime="application/zip",
      )

  st.markdown("---")

  # Mostrar en Mosaico (3 columnas para dar espacio cómodo a los botones de edición)
  cols_per_row = 3
  rows = [
      media_records[i : i + cols_per_row]
      for i in range(0, len(media_records), cols_per_row)
  ]

  for row in rows:
    cols = st.columns(cols_per_row)
    for idx, record in enumerate(row):
      media_id, filename, file_data, file_type, upload_date = record
      with cols[idx]:
        with st.container(border=True):
          # Renderizar imagen o video desde bytes
          if file_type == "image":
            image = Image.open(io.BytesIO(file_data))
            st.image(image, use_container_width=True)
          else:
            st.video(file_data)

          st.caption(f"Archivo: **{filename}**")

          # Sección desplegable para gestionar (cambiar nombre o borrar)
          with st.expander("⚙️ Opciones de edición"):
            new_name = st.text_input(
                "Nuevo nombre", value=filename, key=f"name_{media_id}"
            )
            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
              if st.button("💾 Cambiar", key=f"btn_rename_{media_id}"):
                if new_name and new_name != filename:
                  update_media_name(media_id, new_name)
                  st.success("¡Nombre actualizado!")
                  st.rerun()

            with col_btn2:
              if st.button(
                  "🗑️ Borrar", key=f"btn_delete_{media_id}", type="primary"
              ):
                delete_media_from_db(media_id)
                st.warning("Archivo eliminado.")
                st.rerun()