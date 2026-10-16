import base64
import os
from datetime import datetime
import streamlit as st
from supabase import create_client, Client

# ==========================================
# CONFIGURACIÓN DE PÁGINA (Para Celulares)
# ==========================================
st.set_page_config(
    page_title="Saludos para Hilda", 
    page_icon="🥂", 
    layout="centered"
)

# ==========================================
# CONEXIÓN A SUPABASE (NEXUS ERP)
# ==========================================
# Se conecta usando el mismo secrets.toml de la carpeta .streamlit
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def guardar_mensaje(nombre, mensaje):
    try:
        # Preparamos los datos a enviar
        datos = {
            "nombre": nombre,
            "mensaje": mensaje,
            "fecha": datetime.now().isoformat()
        }
        # Insertamos en la tabla 'mensajes' de la nube
        supabase.table("mensajes").insert(datos).execute()
        return True
    except Exception as e:
        st.error(f"Error al enviar el mensaje: {e}")
        return False

def obtener_video_base64(ruta_video):
    with open(ruta_video, "rb") as vid_file:
        return base64.b64encode(vid_file.read()).decode("utf-8")

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
        
        .stApp {{ background: transparent !important; }}

        /* Fondo animado adaptado a pantallas verticales (celulares) */
        .video-fondo-html {{
            position: fixed; top: 0; left: 0;
            width: 100vw; height: 100vh;
            object-fit: cover; z-index: -999;
        }}

        .overlay-oscuro {{
            position: fixed; top: 0; left: 0;
            width: 100vw; height: 100vh;
            background: rgba(0, 0, 0, 0.65); z-index: -998;
        }}

        /* Estilos del formulario de mensajes */
        [data-testid="stForm"] {{
            background: rgba(20, 20, 20, 0.85) !important;
            border: 2px solid rgba(212, 175, 55, 0.6) !important;
            border-radius: 15px !important;
            padding: 25px !important;
            box-shadow: 0px 10px 30px rgba(0,0,0,0.9) !important;
            margin-top: 20px;
        }}

        p, label {{ color: #ffffff !important; font-weight: 600 !important; font-size: 16px !important; }}

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
            opacity: 1 !important; visibility: visible !important;
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
st.markdown("<p style='text-align: center; text-shadow: 1px 1px 3px #000;'>¡Dejale tu mensaje a Hilda para que aparezca en la pantalla gigante del salón!</p>", unsafe_allow_html=True)

# Formulario de carga
with st.form("formulario_saludos", clear_on_submit=True):
    nombre_invitado = st.text_input("Tu Nombre (Ej: Flia. Pérez, Juan, etc.)", max_chars=30)
    mensaje_invitado = st.text_area("Tu Mensaje (Podés usar los emojis de tu teclado 🥳)", max_chars=120, placeholder="Escribe un lindo saludo...")
    
    # Emojis rápidos por si a la gente grande le cuesta buscar en el teclado
    lista_emojis = [
        "Ninguno", "🥂 (Brindis)", "🎂 (Torta grande)", "🍰 (Porción de torta)",
        "🎉 (Fiesta)", "🥳 (Carita festejando)", "🍾 (Champagne)", "❤️ (Corazón rojo)", 
        "💖 (Corazón brillante)", "🥰 (Carita enamorada)", "🎈 (Globos)", 
        "🎁 (Regalo)", "💐 (Ramo de flores)", "💃 (A bailar!)", "🎶 (Música)", "🌟 (Estrella)"
    ]
    
    emoji_extra = st.selectbox("O sumale un emoji rápido:", lista_emojis)
    enviado = st.form_submit_button("Enviar Saludo a la Pantalla 🥂")

    if enviado:
        if nombre_invitado.strip() and mensaje_invitado.strip():
            mensaje_final = mensaje_invitado.strip()
            # Si eligió un emoji del selector, se lo pegamos al final del mensaje
            if emoji_extra != "Ninguno":
                solo_emoji = emoji_extra.split(" ")[0] 
                mensaje_final = f"{mensaje_final} {solo_emoji}"

            if guardar_mensaje(nombre_invitado.strip(), mensaje_final):
                st.success("¡Tu mensaje fue enviado con éxito a la nube! 🎈 Mirá la pantalla.")
                st.balloons()
        else:
            st.error("⚠️ Por favor, completá tu nombre y el mensaje.")