import base64
import os
import random
import sqlite3
import time
from datetime import datetime, timedelta
import streamlit as st

# ==========================================
# 🎛️ PANEL DE PARAMETRIZACIÓN Y DISEÑO
# ==========================================
ANCHO_MAX_FOTO = "85vw"
ALTURA_MAX_FOTO = "58vh" 

POSICION_MARQUESINA_MENSAJES = "25px" 

ANCHO_BARRAS = "94vw"
TAMAÑO_FUENTE_MENSAJES = "42px" 
TAMAÑO_FUENTE_INSTRUCCIONES = "28px" 
VELOCIDAD_MENSAJES = "35s" 
VELOCIDAD_INSTRUCCIONES = "25s" 
TIEMPO_CAMBIO_FOTOS = 10 

st.set_page_config(
    page_title="Proyector - 70 Años de Hilda",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def obtener_imagen_base64(ruta_imagen):
    with open(ruta_imagen, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def obtener_video_base64(ruta_video):
    with open(ruta_video, "rb") as vid_file:
        return base64.b64encode(vid_file.read()).decode("utf-8")

def obtener_audio_base64(ruta_audio):
    with open(ruta_audio, "rb") as aud_file:
        return base64.b64encode(aud_file.read()).decode("utf-8")

def inicializar_base_datos():
    try:
        conexion = sqlite3.connect("fiesta_galeria.db")
        cursor = conexion.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS configuracion (id INTEGER PRIMARY KEY, modo_video_activo INTEGER)")
        cursor.execute("SELECT COUNT(*) FROM configuracion WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO configuracion (id, modo_video_activo) VALUES (1, 0)")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mensajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                mensaje TEXT,
                fecha DATETIME
            )
        """)
        conexion.commit()
        conexion.close()
    except Exception:
        pass

def obtener_parametro_modo_fiesta():
    try:
        inicializar_base_datos()
        conexion = sqlite3.connect("fiesta_galeria.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT modo_video_activo FROM configuracion WHERE id = 1")
        resultado = cursor.fetchone()
        conexion.close()
        return bool(resultado[0]) if resultado else False
    except Exception:
        return False

# ==========================================
# LÓGICA INTELIGENTE DE TIEMPOS (10 min y 20 min)
# ==========================================
def obtener_mensajes_marquesina():
    try:
        conexion = sqlite3.connect("fiesta_galeria.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre, mensaje, fecha FROM mensajes ORDER BY id ASC")
        todos = cursor.fetchall()
        conexion.close()
        
        if not todos:
            return "<span class='marquesina-titulo'>✨ ESPERANDO NUEVOS MENSAJES ✨</span>"

        ahora = datetime.now()
        ultimo_mensaje = todos[-1]
        fecha_str_ultimo = ultimo_mensaje[2]
        if "." in fecha_str_ultimo:
            fecha_ultimo_msj = datetime.strptime(fecha_str_ultimo, "%Y-%m-%d %H:%M:%S.%f")
        else:
            fecha_ultimo_msj = datetime.strptime(fecha_str_ultimo, "%Y-%m-%d %H:%M:%S")

        minutos_inactividad = (ahora - fecha_ultimo_msj).total_seconds() / 60.0
        resultados_a_mostrar = []
        
        if minutos_inactividad > 20:
            resultados_a_mostrar = [(row[0], row[1]) for row in todos]
        else:
            for nombre, msj, f_str in todos:
                try:
                    if "." in f_str:
                        f_msj = datetime.strptime(f_str, "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        f_msj = datetime.strptime(f_str, "%Y-%m-%d %H:%M:%S")
                    
                    if (ahora - f_msj).total_seconds() / 60.0 <= 10:
                        resultados_a_mostrar.append((nombre, msj))
                except Exception:
                    pass 

        if not resultados_a_mostrar:
            return "<span class='marquesina-titulo'>✨ ESPERANDO NUEVOS MENSAJES ✨</span>"

        textos = []
        for nombre, msj in resultados_a_mostrar:
            textos.append(f"<span class='marquesina-titulo'>🥂 {nombre}:</span> {msj}")
            
        if len(resultados_a_mostrar) < 4:
            textos.extend(textos)
            
        return " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;⭐&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ".join(textos)
        
    except Exception as e:
        return f"<span class='marquesina-titulo'>⚠️ ERROR LEYENDO BD:</span> {e}"


activar_video_fiesta = obtener_parametro_modo_fiesta()
texto_dinamico_mensajes = obtener_mensajes_marquesina()

# ==========================================
# INYECCIÓN DE AUDIO, VIDEO Y ESTILOS CSS
# ==========================================
video_fondo_b64 = ""
video_path = "Fondodefiesta.mp4"
if os.path.exists(video_path):
    try:
        video_fondo_b64 = obtener_video_base64(video_path)
    except Exception:
        pass

audio_fondo_b64 = ""
audio_path = "musica.mp3"
if os.path.exists(audio_path):
    try:
        audio_fondo_b64 = obtener_audio_base64(audio_path)
    except Exception:
        pass

# Generamos la etiqueta de audio solo si el archivo existe
html_audio = ""
if audio_fondo_b64:
    html_audio = f"""
    <audio autoplay loop style="display:none;">
        <source src="data:audio/mp3;base64,{audio_fondo_b64}" type="audio/mp3">
    </audio>
    """

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        .block-container {{
            padding-top: 0.1rem; padding-bottom: 0rem;
            padding-left: 0.5rem; padding-right: 0.5rem;
            max-width: 100%;
        }}

        .stApp {{ background: transparent !important; }}

        .video-fondo-html {{
            position: fixed; top: 0; left: 0;
            width: 100vw; height: 100vh;
            object-fit: cover; z-index: -999;
        }}

        .overlay-oscuro {{
            position: fixed; top: 0; left: 0;
            width: 100vw; height: 100vh;
            background: rgba(0, 0, 0, 0.45); z-index: -998;
        }}

        .contenedor-foto-central {{
            display: flex; justify-content: center; align-items: center;
            width: 100%; height: 58vh; margin: 0 auto; overflow: hidden;
        }}

        .foto-proyector {{
            max-width: {ANCHO_MAX_FOTO} !important; max-height: {ALTURA_MAX_FOTO} !important;
            width: auto !important; height: auto !important;
            object-fit: contain !important; border-radius: 12px;
            box-shadow: 0px 15px 45px rgba(0,0,0,0.8);
            border: 3px solid rgba(212, 175, 55, 0.7); background-color: rgba(0, 0, 0, 0.6);
        }}

        @keyframes efectoFade {{ 0% {{ opacity: 0; transform: scale(0.97); }} 100% {{ opacity: 1; transform: scale(1); }} }}
        @keyframes efectoZoomIn {{ 0% {{ opacity: 0; transform: scale(1.05); }} 100% {{ opacity: 1; transform: scale(1); }} }}
        @keyframes efectoSlideLeft {{ 0% {{ opacity: 0; transform: translateX(40px); }} 100% {{ opacity: 1; transform: translateX(0); }} }}
        @keyframes efectoRotateIn {{ 0% {{ opacity: 0; transform: rotate(-2deg) scale(0.98); }} 100% {{ opacity: 1; transform: rotate(0deg) scale(1); }} }}
        .transicion-fade {{ animation: efectoFade 1.2s ease-in-out; }}
        .transicion-zoom {{ animation: efectoZoomIn 1.2s ease-in-out; }}
        .transicion-slide {{ animation: efectoSlideLeft 1s ease-in-out; }}
        .transicion-rotate {{ animation: efectoRotateIn 1.2s ease-in-out; }}

        .marquesina-contenedor {{
            position: fixed; bottom: {POSICION_MARQUESINA_MENSAJES}; left: 50%; transform: translateX(-50%);
            width: {ANCHO_BARRAS};
            background: linear-gradient(135deg, rgba(17,17,17,0.95) 0%, rgba(34,34,34,0.95) 100%);
            border: 3px solid #d4af37; border-radius: 16px; padding: 15px 20px;
            box-shadow: 0px 10px 30px rgba(0,0,0, 0.8); z-index: 99; overflow: hidden; white-space: nowrap;
        }}

        .marquesina-animada {{
            display: inline-block; padding-left: 100%;
            animation: deslizarMensajes {VELOCIDAD_MENSAJES} linear infinite;
            color: #ffffff; font-size: {TAMAÑO_FUENTE_MENSAJES};
            font-family: 'Helvetica Neue', sans-serif; font-weight: 600;
        }}

        @keyframes deslizarMensajes {{ 0% {{ transform: translate(0, 0); }} 100% {{ transform: translate(-100%, 0); }} }}
        .marquesina-titulo {{ color: #d4af37; font-weight: bold; }}

        .instrucciones-contenedor {{
            width: {ANCHO_BARRAS};
            margin: 0 auto 10px auto; 
            background: rgba(10, 10, 10, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; padding: 4px 20px;
            box-shadow: 0px 4px 15px rgba(0,0,0, 0.8); z-index: 100; overflow: hidden; white-space: nowrap;
        }}

        .instrucciones-animada {{
            display: inline-block; padding-left: 100%;
            animation: deslizarInstrucciones {VELOCIDAD_INSTRUCCIONES} linear infinite;
            color: #dddddd; font-size: {TAMAÑO_FUENTE_INSTRUCCIONES};
            font-family: 'Dancing Script', cursive, sans-serif; 
            font-weight: 700; letter-spacing: 1px;
        }}

        @keyframes deslizarInstrucciones {{ 0% {{ transform: translate(0, 0); }} 100% {{ transform: translate(-100%, 0); }} }}
        
        .instrucciones-destaque {{
            color: #d4af37; font-weight: bold; 
            font-family: 'Helvetica Neue', sans-serif;
            font-style: normal; letter-spacing: 1px; font-size: 22px;
        }}

    </style>

    <video autoplay muted loop playsinline class="video-fondo-html">
        <source src="data:video/mp4;base64,{video_fondo_b64}" type="video/mp4">
    </video>
    <div class="overlay-oscuro"></div>
    {html_audio}
""",
    unsafe_allow_html=True,
)


if activar_video_fiesta:
    if os.path.exists(video_path):
        st.video(video_path, format="video/mp4", autoplay=True, loop=True, muted=True)
else:
    st.markdown(
        f"""
        <h1 style='text-align: center; color: #d4af37; font-size: 32px; margin-bottom: 5px; font-family:serif; text-shadow: 2px 2px 6px rgba(0,0,0,0.8);'>✨ 70 Años de Hilda ✨</h1>
        
        <div class="instrucciones-contenedor">
            <div class="instrucciones-animada">
                <span class="instrucciones-destaque">📲 PARTICIPÁ:</span> Escaneá el CÓDIGO QR del salón con tu celular y dejale tu saludo a Hilda. 🎂 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                <span class="instrucciones-destaque">📸 SUMATE:</span> ¡Tu mensaje saldrá en vivo en esta pantalla! 🎉 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    lista_fotos = [archivo for archivo in os.listdir(".") if archivo.lower().endswith((".png", ".jpg", ".jpeg"))]
    if os.path.exists("uploaded_media"):
        lista_fotos += [os.path.join("uploaded_media", a) for a in os.listdir("uploaded_media") if a.lower().endswith((".png", ".jpg", ".jpeg"))]

    if lista_fotos:
        if "indice_foto" not in st.session_state:
            st.session_state.indice_foto = 0

        foto_actual = lista_fotos[st.session_state.indice_foto % len(lista_fotos)]
        efectos_disponibles = ["transicion-fade", "transicion-zoom", "transicion-slide", "transicion-rotate"]

        if "efecto_actual" not in st.session_state:
            st.session_state.efecto_actual = random.choice(efectos_disponibles)

        try:
            imagen_b64 = obtener_imagen_base64(foto_actual)
            extension = foto_actual.split(".")[-1].lower()
            tipo_mime = "image/png" if extension == "png" else "image/jpeg"

            st.markdown(
                f"""
                <div class="{st.session_state.efecto_actual}">
                    <div class="contenedor-foto-central">
                        <img src="data:{tipo_mime};base64,{imagen_b64}" class="foto-proyector" />
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )
        except Exception:
            pass

        st.session_state.indice_foto += 1
        st.session_state.efecto_actual = random.choice(efectos_disponibles)
    else:
        st.error("⚠️ No se encontraron imágenes en el directorio para la galería.")

    st.markdown(
        f"""
        <div class="marquesina-contenedor">
            <div class="marquesina-animada">
                {texto_dinamico_mensajes} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

time.sleep(TIEMPO_CAMBIO_FOTOS)
st.rerun()