import base64
import os
import random
import time
import sqlite3
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# ==========================================
# 🎛️ PANEL DE PARAMETRIZACIÓN Y DISEÑO
# ==========================================
ANCHO_MAX_FOTO = "85vw"
ALTURA_MAX_FOTO = "58vh" 

POSICION_MARQUESINA_MENSAJES = "25px" 

ANCHO_BARRAS = "94vw"
TAMAÑO_FUENTE_MENSAJES = "58px"  
TAMAÑO_FUENTE_INSTRUCCIONES = "32px" 
VELOCIDAD_MENSAJES = "45s"  
VELOCIDAD_INSTRUCCIONES = "25s" 
TIEMPO_CAMBIO_FOTOS = 10 

st.set_page_config(
    page_title="Proyector - 70 Años de Hilda",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================
# CONEXIÓN A SUPABASE (NEXUS ERP)
# ==========================================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

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
# LÓGICA DE FOTOS EN LA NUBE
# ==========================================
@st.cache_data(ttl=60)
def obtener_nombres_fotos_supabase():
    try:
        archivos = supabase.storage.from_("fotos_fiesta").list()
        nombres = [f["name"] for f in archivos if f["name"].lower().endswith((".png", ".jpg", ".jpeg"))]
        return nombres
    except Exception as e:
        return []

@st.cache_data(ttl=600)
def obtener_foto_base64_desde_nube(nombre_foto):
    try:
        file_bytes = supabase.storage.from_("fotos_fiesta").download(nombre_foto)
        b64_encoded = base64.b64encode(file_bytes).decode("utf-8")
        extension = nombre_foto.split(".")[-1].lower()
        tipo_mime = "image/png" if extension == "png" else "image/jpeg"
        return f"data:{tipo_mime};base64,{b64_encoded}"
    except Exception as e:
        return None

# ==========================================
# LÓGICA DE MENSAJES (CORREGIDA ZONA HORARIA)
# ==========================================
def obtener_mensajes_marquesina():
    try:
        respuesta = supabase.table("mensajes").select("*").order("id").execute()
        todos = respuesta.data 
        
        if not todos:
            return "<span class='marquesina-titulo'>✨ ESPERANDO NUEVOS MENSAJES ✨</span>"

        # Capturamos la hora actual tanto en UTC como en hora local del servidor
        ahora_utc = datetime.utcnow()
        ahora_local = datetime.now()
        resultados_recientes = []
        
        for row in todos:
            try:
                f_str = row["fecha"].replace("T", " ")[:19]
                f_msj = datetime.strptime(f_str, "%Y-%m-%d %H:%M:%S")
                
                # Comparamos ambas diferencias y nos quedamos con la menor 
                # (esto soluciona el problema de las zonas horarias entre Streamlit y Supabase)
                dif_utc = abs((ahora_utc - f_msj).total_seconds() / 60.0)
                dif_local = abs((ahora_local - f_msj).total_seconds() / 60.0)
                
                minutos_pasados = min(dif_utc, dif_local)
                
                if minutos_pasados <= 10:
                    resultados_recientes.append((row["nombre"], row["mensaje"]))
            except Exception:
                pass 

        if resultados_recientes:
            # Damos prioridad estricta a los mensajes nuevos
            resultados_a_mostrar = resultados_recientes
        else:
            # Si pasaron 10 min en silencio, muestra el historial completo
            resultados_a_mostrar = [(row["nombre"], row["mensaje"]) for row in todos]

        textos = []
        for nombre, msj in resultados_a_mostrar:
            textos.append(f"<span class='marquesina-titulo'>🥂 {nombre}:</span> {msj}")
            
        if len(resultados_a_mostrar) < 4:
            textos.extend(textos)
            textos.extend(textos)
            
        return " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;⭐&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ".join(textos)
        
    except Exception as e:
        return f"<span class='marquesina-titulo'>⚠️ ERROR LEYENDO BD:</span> {e}"

activar_video_fiesta = obtener_parametro_modo_fiesta()
texto_dinamico_mensajes = obtener_mensajes_marquesina()

# ==========================================
# AUDIO, VIDEO Y ESTILOS CSS PRINCIPALES
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

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        [data-testid="stAppViewContainer"], 
        [data-testid="stAppViewBlockContainer"], 
        .stApp {{ opacity: 1 !important; transition: none !important; }}
        
        [data-testid="stStatusWidget"] {{ visibility: hidden !important; display: none !important; }}
        
        .block-container {{ padding-top: 0.1rem; padding-bottom: 0rem; padding-left: 0.5rem; padding-right: 0.5rem; max-width: 100%; }}
        .stApp {{ background: transparent !important; }}

        .video-fondo-html {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; object-fit: cover; z-index: -999; }}
        .overlay-oscuro {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0, 0, 0, 0.45); z-index: -998; }}

        .contenedor-foto-central {{ display: flex; justify-content: center; align-items: center; width: 100%; height: 58vh; margin: 0 auto; overflow: hidden; }}
        
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
            width: {ANCHO_BARRAS}; background: linear-gradient(135deg, rgba(17,17,17,0.95) 0%, rgba(34,34,34,0.95) 100%);
            border: 3px solid #d4af37; border-radius: 16px; 
            padding: 20px 25px; 
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
            width: {ANCHO_BARRAS}; margin: 0 auto 10px auto; 
            background: rgba(10, 10, 10, 0.75); border: 1px solid rgba(255, 255, 255, 0.2); 
            border-radius: 10px; padding: 4px 20px; box-shadow: 0px 4px 15px rgba(0,0,0, 0.8); 
            z-index: 100; overflow: hidden; white-space: nowrap;
        }}

        .instrucciones-animada {{
            display: inline-block; padding-left: 100%;
            animation: deslizarInstrucciones {VELOCIDAD_INSTRUCCIONES} linear infinite;
            color: #dddddd; font-size: {TAMAÑO_FUENTE_INSTRUCCIONES};
            font-family: 'Dancing Script', cursive, sans-serif; font-weight: 700; letter-spacing: 1px;
        }}

        @keyframes deslizarInstrucciones {{ 0% {{ transform: translate(0, 0); }} 100% {{ transform: translate(-100%, 0); }} }}
        
        .instrucciones-destaque {{
            color: #d4af37; font-weight: bold; font-family: 'Helvetica Neue', sans-serif; font-style: normal; letter-spacing: 1px; font-size: 26px; 
        }}
    </style>

    <video autoplay muted loop playsinline class="video-fondo-html">
        <source src="data:video/mp4;base64,{video_fondo_b64}" type="video/mp4">
    </video>
    <div class="overlay-oscuro"></div>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# RENDERIZADO PRINCIPAL
# ==========================================

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

    lista_nombres_fotos = obtener_nombres_fotos_supabase()

    if lista_nombres_fotos:
        if "indice_foto" not in st.session_state:
            st.session_state.indice_foto = 0

        nombre_actual = lista_nombres_fotos[st.session_state.indice_foto % len(lista_nombres_fotos)]
        nombre_siguiente = lista_nombres_fotos[(st.session_state.indice_foto + 1) % len(lista_nombres_fotos)]
        
        foto_actual_b64 = obtener_foto_base64_desde_nube(nombre_actual)
        foto_siguiente_b64 = obtener_foto_base64_desde_nube(nombre_siguiente)
        
        efectos_disponibles = ["transicion-fade", "transicion-zoom", "transicion-slide", "transicion-rotate"]
        if "efecto_actual" not in st.session_state:
            st.session_state.efecto_actual = random.choice(efectos_disponibles)

        if foto_actual_b64:
            st.markdown(
                f"""
                <img src="{foto_siguiente_b64}" style="display:none;" />
                <div class="{st.session_state.efecto_actual}">
                    <div class="contenedor-foto-central">
                        <img src="{foto_actual_b64}" class="foto-proyector" />
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.session_state.indice_foto += 1
        st.session_state.efecto_actual = random.choice(efectos_disponibles)
    else:
        st.markdown("""
            <div style="display:flex; justify-content:center; align-items:center; height:58vh;">
                <h2 style="color:white; background:rgba(0,0,0,0.7); padding:20px; border-radius:10px;">
                    📸 Subiendo fotos al álbum...
                </h2>
            </div>
        """, unsafe_allow_html=True)

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

# ==========================================
# BOTÓN DE AUDIO (ARRIBA A LA DERECHA, AISLADO)
# ==========================================
if audio_fondo_b64:
    st.markdown("""
    <style>
        /* Forzamos el iframe a la esquina superior derecha */
        iframe[title="streamlit_components.v1.html"] {
            position: fixed !important;
            top: 20px !important; 
            right: 20px !important;
            width: 55px !important;
            height: 55px !important;
            z-index: 99999 !important;
            border: none !important;
            background: transparent !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    html_boton_audio = f"""
    <div style="display: flex; justify-content: flex-end; align-items: flex-start; height: 100%; padding: 5px;">
        <button id="btn-audio" onclick="toggleAudio()" style="background: rgba(10,10,10,0.8); border: 2px solid #d4af37; border-radius: 50%; width: 45px; height: 45px; font-size: 22px; cursor: pointer; color: white; display:flex; justify-content:center; align-items:center; transition: 0.3s;">
            🔇
        </button>
    </div>
    <script>
        try {{
            // Usamos window.parent para esquivar el bloqueo de Streamlit Cloud
            let contextoSeguro = window.parent || window;
            
            if (!contextoSeguro.audioFiesta) {{
                contextoSeguro.audioFiesta = new Audio("data:audio/mp3;base64,{audio_fondo_b64}");
                contextoSeguro.audioFiesta.loop = true;
            }}
            
            var btn = document.getElementById("btn-audio");
            
            function actualizarBoton() {{
                if (!contextoSeguro.audioFiesta.paused) {{
                    btn.innerHTML = "🔊";
                    btn.style.opacity = "0.3"; 
                }} else {{
                    btn.innerHTML = "🔇";
                    btn.style.opacity = "1";
                }}
            }}

            actualizarBoton();

            window.toggleAudio = function() {{
                if (contextoSeguro.audioFiesta.paused) {{
                    contextoSeguro.audioFiesta.play();
                }} else {{
                    contextoSeguro.audioFiesta.pause();
                }}
                actualizarBoton();
            }}
        }} catch(e) {{
            console.log("Error de audio en la nube:", e);
        }}
    </script>
    """
    components.html(html_boton_audio, height=60)

time.sleep(TIEMPO_CAMBIO_FOTOS)
st.rerun()