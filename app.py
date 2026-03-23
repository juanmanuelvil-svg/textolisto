import streamlit as st
import google.generativeai as genai
import urllib.parse
from gtts import gTTS
import io
from PIL import Image

# ==========================================
# CONFIGURACIÓN INICIAL
# ==========================================
# Pon el número de quien va a imprimir, con código 52, sin el símbolo +
NUMERO_WHATSAPP = "525500000000" 

# Conexión con Google Gemini
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except KeyError:
    st.error("Falta la llave de Google en los Secrets.")
    st.stop()

# ==========================================
# CONFIGURACIÓN VISUAL (Letras grandes)
# ==========================================
st.set_page_config(page_title="TextoListo", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    .stButton>button { height: 80px; font-size: 24px !important; font-weight: bold; border-radius: 15px; }
    .stTextArea textarea { font-size: 22px !important; line-height: 1.5; }
    p, div, label { font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

if "texto_acumulado" not in st.session_state:
    st.session_state.texto_acumulado = ""

# ==========================================
# FUNCIONES DE INTELIGENCIA ARTIFICIAL
# ==========================================
def procesar_imagen(imagen):
    img = Image.open(imagen)
    prompt = "Extrae todo el texto de esta imagen de forma clara y limpia. Corrige ortografía. Devuelve SOLO el texto, sin saludos ni explicaciones."
    return model.generate_content([prompt, img]).text

def procesar_audio(audio):
    audio_data = {"mime_type": "audio/wav", "data": audio.getvalue()}
    prompt = "Transcribe el siguiente audio. Quita muletillas y corrige la ortografía. Devuelve SOLO el texto, sin saludos ni explicaciones."
    return model.generate_content([prompt, audio_data]).text

def generar_voz(texto):
    tts = gTTS(text=texto, lang='es', tld='com.mx')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    return audio_bytes.getvalue()

# ==========================================
# INTERFAZ PARA EL ADULTO MAYOR
# ==========================================
st.title("📝 TextoListo")
st.write("Toma una foto de tu documento o graba un mensaje con tu voz para pasarlo a texto.")

st.info("🔒 **Consejo:** No tomes fotos de tarjetas de crédito, contraseñas o datos del banco.")

# --- BOTONES PRINCIPALES ---
col1, col2 = st.columns(2)

with col1:
    foto = st.camera_input("📷 Tomar Foto")
    if foto:
        with st.spinner("⏳ Leyendo la foto..."):
            texto_nuevo = procesar_imagen(foto)
            st.session_state.texto_acumulado += f"\n\n{texto_nuevo}"
            st.success("¡Foto leída!")

with col2:
    audio = st.audio_input("🎙️ Grabar Voz")
    if audio:
        with st.spinner("⏳ Escuchando tu mensaje..."):
            texto_nuevo = procesar_audio(audio)
            st.session_state.texto_acumulado += f"\n\n{texto_nuevo}"
            st.success("¡Mensaje escuchado!")

# --- REVISIÓN Y ENVÍO ---
if st.session_state.texto_acumulado.strip():
    st.divider()
    st.subheader("👀 Revisa tu mensaje:")
    st.write("Puedes tocar el cuadro blanco para corregir alguna palabra con el teclado si lo necesitas.")
    
    # Cuadro donde el usuario puede editar el texto si la IA se equivocó
    texto_final = st.text_area("Mensaje listo:", value=st.session_state.texto_acumulado.strip(), height=250)
    
    # Botón para que la app le lea el texto en voz alta
    if st.button("🔊 Escuchar en voz alta"):
        st.audio(generar_voz(texto_final), format='audio/mp3', autoplay=True)

    st.divider()
    
    # Prepara el mensaje para WhatsApp
    mensaje_whatsapp = urllib.parse.quote(f"Hola, por favor ayúdame a pasar este texto a Word e imprimirlo:\n\n{texto_final}")
    enlace_whatsapp = f"https://wa.me/{NUMERO_WHATSAPP}?text={mensaje_whatsapp}"
    
    # Botón final
    st.link_button("✅ ENVIAR POR WHATSAPP", enlace_whatsapp, type="primary", use_container_width=True)

    st.write("---")
    if st.button("🗑️ Borrar todo y empezar de cero"):
        st.session_state.texto_acumulado = ""
        st.rerun()
