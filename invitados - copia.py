import sqlite3
import datetime
import base64
import os
import streamlit as st

# ==========================================
# CONFIGURACIÓN PARA CELULARES
# ==========================================
st.set_page_config(page_title="Saludos para Hilda", page_icon="🥂", layout="centered")

def obtener_video_base64(ruta_video):
    with open(ruta_video, "rb") as vid_file:
        return base64.b64encode(vid_file.read()).decode("utf-8")

# ==========================================
# BASE DE DATOS DE MENSAJES (SEGURO - ACUMULATIVO)
# ==========================================
def inicializar_bd_mensajes():
    conexion = sqlite3.connect("fiesta_galeria.db")
    cursor = conexion.cursor()
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

def guardar_mensaje(nombre, mensaje):
    conexion = sqlite3.connect("fiesta_galeria.db")
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO mensajes (nombre, mensaje, fecha) VALUES (?, ?, ?)", 
                   (nombre, mensaje, datetime.datetime.now()))
    conexion.commit()
    conexion.close()

inicializar_bd_mensajes()

# ==========================================
# INYECCIÓN DE ESTILOS CSS Y FONDO ANIMADO
# ==========================================
video_fondo_b64 = ""
video_path = "Fondodefiesta.mp4"
if os.path.exists(video_path):
    try:
        video_fondo_b64 = obtener_video_base64(video_path)
    except Exception:
        pass

st.markdown(
    f"""
    <style>
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        /* Fondo transparente para ver el video */
        .stApp {{ background: transparent !important; }}

        /* Video de fondo a pantalla completa */
        .video-fondo-html {{
            position: fixed; top: 0; left: 0;
            width: 100vw; height: 100vh;
            object-fit: cover; z-index: -999;
        }}

        /* Capa oscura para que el formulario se lea perfecto y resalte */
        .overlay-oscuro {{
            position: fixed; top: 0; left: 0;
            width: 100vw; height: 100vh;
            background: rgba(0, 0, 0, 0.65); z-index: -998;
        }}

        /* Estilo del formulario flotante (Efecto cristal oscuro) */
        [data-testid="stForm"] {{
            background: rgba(20, 20, 20, 0.85) !important;
            border: 2px solid rgba(212, 175, 55, 0.6) !important;
            border-radius: 15px !important;
            padding: 25px !important;
            box-shadow: 0px 10px 30px rgba(0,0,0,0.9) !important;
            margin-top: 20px;
        }}

        /* Textos dentro de la app */
        p, label {{
            color: #ffffff !important;
            font-weight: 600 !important;
            font-size: 16px !important;
        }}

        /* Botón de envío doradito */
        button[kind="formSubmit"], 
        div[data-testid="stFormSubmitButton"] > button,
        .stButton > button {{ 
            width: 100% !important; 
            background: linear-gradient(135deg, #d4af37 0%, #b5952f 100%) !important;
            color: black !important; 
            font-weight: 900 !important; 
            font-size: 18px !important;
            border-radius: 10px !important; 
            border: none !important; 
            padding: 12px !important; 
            margin-top: 15px !important;
            box-shadow: 0px 4px 15px rgba(212, 175, 55, 0.4) !important;
            opacity: 1 !important;
            visibility: visible !important;
        }}
        
        button[kind="formSubmit"]:hover, 
        div[data-testid="stFormSubmitButton"] > button:hover,
        .stButton > button:hover {{ 
            background: linear-gradient(135deg, #b5952f 0%, #947926 100%) !important;
            color: white !important; 
        }}
    </style>
    
    <video autoplay muted loop playsinline class="video-fondo-html">
        <source src="data:video/mp4;base64,{video_fondo_b64}" type="video/mp4">
    </video>
    <div class="overlay-oscuro"></div>
    """,
    unsafe_allow_html=True
)

# ==========================================
# INTERFAZ DEL INVITADO
# ==========================================
st.markdown("<h1 style='text-align: center; color: #d4af37; font-family: serif; text-shadow: 2px 2px 4px #000;'>✨ 70 Años de Hilda ✨</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>¡Dejale tu mensaje a Hilda para que aparezca en la pantalla gigante del salón!</p>", unsafe_allow_html=True)

with st.form("formulario_saludos", clear_on_submit=True):
    nombre_invitado = st.text_input("Tu Nombre (Ej: Flia. Pérez, Juan, etc.)", max_chars=30)
    
    # Indicador de que pueden usar el teclado del celular
    mensaje_invitado = st.text_area("Tu Mensaje (Podés usar los emojis de tu teclado 🥳)", max_chars=120, placeholder="Escribe un lindo saludo...")
    
    # Selector rápido con MÁS EMOJIS FESTIVOS
    lista_emojis = [
        "Ninguno", 
        "🥂 (Brindis)", 
        "🎂 (Torta grande)", 
        "🍰 (Porción de torta)",
        "🎉 (Fiesta)", 
        "🥳 (Carita festejando)",
        "🍾 (Champagne)",
        "❤️ (Corazón rojo)", 
        "💖 (Corazón brillante)",
        "🥰 (Carita enamorada)",
        "🎈 (Globos)", 
        "🎁 (Regalo)",
        "💐 (Ramo de flores)",
        "💃 (A bailar!)",
        "🎶 (Música)",
        "🌟 (Estrella)"
    ]
    
    emoji_extra = st.selectbox("O sumale un emoji rápido:", lista_emojis)
    
    enviado = st.form_submit_button("Enviar Saludo a la Pantalla 🥂")

    if enviado:
        if nombre_invitado.strip() and mensaje_invitado.strip():
            
            # Si eligió un emoji del selector, se lo sumamos al final del mensaje
            mensaje_final = mensaje_invitado.strip()
            if emoji_extra != "Ninguno":
                solo_emoji = emoji_extra.split(" ")[0] # Extrae solo el icono (ej: "🥂")
                mensaje_final = f"{mensaje_final} {solo_emoji}"

            # Guardamos en la base de datos
            guardar_mensaje(nombre_invitado.strip(), mensaje_final)
            
            st.success("¡Tu mensaje fue enviado con éxito! 🎈 Mirá la pantalla.")
            st.balloons()
        else:
            st.error("⚠️ Por favor, completá tu nombre y el mensaje.")