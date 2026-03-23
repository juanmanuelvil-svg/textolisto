import streamlit as st
import google.generativeai as genai
import urllib.parse
from gtts import gTTS
import io
from PIL import Image

# ==========================================
# CONFIGURACIÓN INICIAL
# ==========================================
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
    .stButton>button { height: 90px; font-size: 26px !important; font-weight: bold; border-radius: 18px; }
    .stTextArea textarea { font-size: 24px !important; line-height: 1.6; }
    p, div, label { font-size: 22px !important; }
    h3 { font-size: 28px !important; margin-top: 25px !important; }
    </style>
    """, unsafe_allow_html=True)

if "texto_acumulado" not in st.session_state:
    st.session_state.texto_acumulado = ""

# ==========================================
# FUNCIONES DE INTELIGENCIA ARTIFICIAL 
# ==========================================
def procesar_imagen(imagen_file):
    img = Image.open(imagen_file)
    prompt = "Extrae todo el texto de esta imagen de forma clara y limpia. Corrige ortografía. Devuelve SOLO el texto, sin saludos ni explicaciones."
    respuesta = model.generate_content([prompt, img])
    return respuesta.text

def procesar_audio(audio_file):
    audio_data = {"mime_type": audio_file.type, "data": audio_file.getvalue()}
    prompt = "Transcribe el siguiente audio. Quita muletillas y corrige la ortografía. Devuelve SOLO el texto, sin saludos ni explicaciones."
    respuesta = model.generate_content([prompt, audio_data])
    return respuesta.text

def procesar_pdf(pdf_file):
    pdf_data = {"mime_type": "application/pdf", "data": pdf_file.getvalue()}
    prompt = "Lee todo este documento PDF. Extrae y resume el texto de forma clara, con viñetas si es necesario. Devuelve SOLO el texto, sin saludos ni explicaciones."
    respuesta = model.generate_content([prompt, pdf_data])
    return respuesta.text

def generar_voz(texto):
    tts = gTTS(text=texto, lang='es', tld='com.mx')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    return audio_bytes.getvalue()

# ==========================================
# INTERFAZ PARA EL ADULTO MAYOR
# ==========================================
st.title("📝 TextoListo")
st.write("Convierte tus fotos, documentos PDF o notas de voz en texto limpio.")

st.info("🔒 **Consejo:** No subas fotos ni dictes tarjetas de crédito, contraseñas o datos del banco.")

st.divider()

# --- SECCIÓN 1: TIEMPO REAL ---
st.subheader("Opción A: Usa la cámara o micrófono ahora")
col1, col2 = st.columns(2)

with col1:
    foto_camara = st.camera_input("📷 Toca para tomar foto")
    if foto_camara:
        with st.spinner("⏳ Leyendo la foto..."):
            texto_nuevo = procesar_imagen(foto_camara)
            st.session_state.texto_acumulado += f"\n\n{texto_nuevo}"
            st.success("¡Foto leída!")

with col2:
    audio_grabado = st.audio_input("🎙️ Toca para grabar voz")
    if audio_grabado:
        with st.spinner("⏳ Escuchando tu mensaje..."):
            texto_nuevo = procesar_audio(audio_grabado)
            st.session_state.texto_acumulado += f"\n\n{texto_nuevo}"
            st.success("¡Mensaje escuchado!")

st.divider()

# --- SECCIÓN 2: SUBIR ARCHIVOS DE WHATSAPP O CORREO ---
st.subheader("Opción B: Selecciona archivos de tu teléfono")
st.write("Sube las fotos, PDF o notas de voz que te mandaron por WhatsApp o correo.")

archivos_subidos = st.file_uploader(
    "Toca aquí para buscar en tu teléfono:", 
    type=['png', 'jpg', 'jpeg', 'pdf', 'mp3', 'wav', 'm4a', 'ogg', 'opus'],
    accept_multiple_files=True 
)

if archivos_subidos and st.button("✅ PROCESAR ARCHIVOS SELECCIONADOS", type="secondary", use_container_width=True):
    with st.spinner("⏳ Leyendo tus archivos..."):
        for archivo in archivos_subidos:
            tipo_mime = archivo.type
            
            if tipo_mime.startswith("image/"):
                texto_nuevo = procesar_imagen(archivo)
            elif tipo_mime.startswith("audio/") or tipo_mime in ["audio/ogg", "audio/opus"]:
                texto_nuevo = procesar_audio(archivo)
            elif tipo_mime == "application/pdf":
                texto_nuevo = procesar_pdf(archivo)
            else:
                continue 
                
            st.session_state.texto_acumulado += f"\n\n{texto_nuevo}"
        st.success("¡Archivos procesados!")

# ==========================================
# REVISIÓN Y ENVÍO
# ==========================================
if st.session_state.texto_acumulado.strip():
    st.divider()
    st.subheader("👀 Paso 3: Revisa tu mensaje")
    st.write("Si hay un error, toca el cuadro blanco y corrígelo con el teclado.")
    
    texto_final = st.text_area("Mensaje listo:", value=st.session_state.texto_acumulado.strip(), height=300)
    
    if st.button("🔊 Escuchar en voz alta"):
        st.audio(generar_voz(texto_final), format='audio/mp3', autoplay=True)

    st.divider()
    
    # LA MEJORA APLICADA: Botón universal de WhatsApp
    mensaje_wpp = urllib.parse.quote(f"Hola, por favor ayúdame a pasar este texto a un Word e imprimirlo:\n\n{texto_final}")
    enlace_wpp = f"https://api.whatsapp.com/send?text={mensaje_wpp}"
    
    st.link_button("✅ ENVIAR POR WHATSAPP", enlace_wpp, type="primary", use_container_width=True)

    st.write("---")
    if st.button("🗑️ Borrar todo y empezar de cero"):
        st.session_state.texto_acumulado = ""
        st.rerun()
