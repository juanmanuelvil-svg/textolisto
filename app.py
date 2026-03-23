import streamlit as st
import google.generativeai as genai
import urllib.parse
from gtts import gTTS
import io
from PIL import Image

# ==========================================
# CONFIGURACIÓN INICIAL
# ==========================================
NUMERO_WHATSAPP = "525500000000" # Pon el número de quien va a imprimir, con código 52, sin el símbolo +

# LLAVE DE SEGURIDAD (Se conectará en Streamlit más adelante)
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] 

# Configurar la API de Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# CONFIGURACIÓN VISUAL Y LETRAS GRANDES
# ==========================================
st.set_page_config(page_title="TextoListo", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 80px;
        font-size: 24px !important;
        font-weight: bold;
        border-radius: 15px;
    }
    .stTextArea textarea {
        font-size: 22px !important;
        line-height: 1.5;
    }
    p, div, label {
        font-size: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# MEMORIA DE LA APP 
# ==========================================
if "texto_acumulado" not in st.session_state:
    st.session_state.texto_acumulado = ""

# ==========================================
# FUNCIONES DE INTELIGENCIA ARTIFICIAL
# ==========================================
def procesar_imagen(imagen_capturada):
    img = Image.open(imagen_capturada)
    prompt = """
    Eres un asistente amable para un adulto mayor en México. Extrae todo el texto de esta imagen. 
    Corrige la ortografía si es necesario, pero mantén la idea original tal cual. 
    Si es una lista, usa viñetas. Devuelve SOLO el texto limpio y claro, sin explicaciones tuyas.
    """
    respuesta = model.generate_content([prompt, img])
    return respuesta.text

def procesar_audio(audio_capturado):
    audio_data = {"mime_type": "audio/wav", "data": audio_capturado.getvalue()}
    prompt = """
    Eres un asistente amable para un adulto mayor en México. Transcribe el siguiente audio.
    Corrige muletillas (como "este", "eh") y faltas de ortografía, dándole un formato claro y fácil de leer.
    Devuelve SOLO el texto limpio, sin explicaciones tuyas.
    """
    respuesta = model.generate_content([prompt, audio_data])
    return respuesta.text

def generar_audio_voz(texto):
    tts = gTTS(text=texto, lang='es', tld='com.mx')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    return audio_bytes

# ==========================================
# INTERFAZ DE USUARIO 
# ==========================================
st.title("📝 TextoListo")
st.write("Toma fotos o graba un audio para convertirlos en texto.")

st.info("🔒 **Consejo de seguridad:** Por favor, NO tomes fotos ni dictes contraseñas, tarjetas de crédito, o información de tu banco.")

col1, col2 = st.columns(2)

with col1:
    foto = st.camera_input("📷 Tomar Foto")
    if foto:
        with st.spinner("⏳ Leyendo la foto, dame unos segunditos..."):
            texto_nuevo = procesar_imagen(foto)
            st.session_state.texto_acumulado += f"\n\n{texto_nuevo}"
            st.success("¡Foto agregada con éxito!")

with col2:
    audio = st.audio_input("🎙️ Grabar Audio")
    if audio:
        with st.spinner("⏳ Escuchando tu mensaje..."):
            texto_nuevo = procesar_audio(audio)
            st.session_state.texto_acumulado += f"\n\n{texto_nuevo}"
            st.success("¡Audio agregado con éxito!")

st.divider()

if st.session_state.texto_acumulado.strip() != "":
    st.subheader("👀 Revisa tu mensaje:")
    
    texto_final = st.text_area(
        "Si hay algún error, puedes tocar aquí y corregirlo:", 
        value=st.session_state.texto_acumulado.strip(), 
        height=300
    )
    
    if st.button("🔊 Leer texto en voz alta"):
        with st.spinner("Preparando el audio..."):
            audio_generado = generar_audio_voz(texto_final)
            st.audio(audio_generado, format='audio/mp3')

    st.divider()
    
    mensaje_whatsapp = f"Hola, por favor ayúdame a pasar el siguiente texto a un documento de Word e imprimirlo:\n\n{texto_final}\n\n¡Muchas gracias!"
    mensaje_codificado = urllib.parse.quote(mensaje_whatsapp)
    enlace_whatsapp = f"https://wa.me/{NUMERO_WHATSAPP}?text={mensaje_codificado}"
    
    st.link_button("✅ LISTO: Enviar por WhatsApp", enlace_whatsapp, type="primary")

    st.write("---")
    if st.button("🗑️ Borrar todo y empezar de cero"):
        st.session_state.texto_acumulado = ""
        st.rerun()