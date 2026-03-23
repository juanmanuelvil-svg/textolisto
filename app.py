import streamlit as st
import google.generativeai as genai
import urllib.parse
from gtts import gTTS
import io
from PIL import Image

# ==========================================
# CONFIGURACIÓN INICIAL
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except KeyError:
    st.error("Falta la llave de Google en los Secrets de Streamlit.")
    st.stop()

st.set_page_config(page_title="TextoListo", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    .stButton>button { height: 90px; font-size: 24px !important; font-weight: bold; border-radius: 18px; }
    .stTextArea textarea { font-size: 24px !important; line-height: 1.6; }
    p, div, label { font-size: 22px !important; }
    h3 { font-size: 28px !important; margin-top: 25px !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# SISTEMA DE MEMORIA
# ==========================================
if "texto_acumulado" not in st.session_state:
    st.session_state.texto_acumulado = ""
if "historial" not in st.session_state:
    st.session_state.historial = []

def guardar_pasado():
    st.session_state.historial.append(st.session_state.texto_acumulado)

def agregar_texto(texto_nuevo):
    guardar_pasado()
    if st.session_state.texto_acumulado == "":
        st.session_state.texto_acumulado = texto_nuevo
    else:
        st.session_state.texto_acumulado += f"\n\n{texto_nuevo}"

def guardar_edicion_manual():
    st.session_state.texto_acumulado = st.session_state.editor_texto

# ==========================================
# FUNCIONES DE INTELIGENCIA ARTIFICIAL
# ==========================================
def procesar_imagen(imagen_file):
    img = Image.open(imagen_file)
    prompt = """Extrae todo el texto de esta imagen de forma clara y limpia. Corrige ortografía. 
    SI ENCUENTRAS TABLAS O CIFRAS: Conviértelas en una lista fácil de leer renglón por renglón.
    Devuelve SOLO el texto, sin saludos ni explicaciones."""
    respuesta = model.generate_content([prompt, img])
    return respuesta.text

def procesar_audio(audio_file):
    audio_data = {"mime_type": audio_file.type, "data": audio_file.getvalue()}
    prompt = "Transcribe este audio. Quita muletillas y corrige la ortografía. Devuelve SOLO el texto, sin saludos."
    respuesta = model.generate_content([prompt, audio_data])
    return respuesta.text

def procesar_pdf(pdf_file):
    pdf_data = {"mime_type": "application/pdf", "data": pdf_file.getvalue()}
    prompt = """Lee este PDF. Extrae el texto de forma clara. 
    SI ENCUENTRAS TABLAS O CIFRAS: Conviértelas en una lista fácil de leer renglón por renglón.
    Devuelve SOLO el texto, sin saludos."""
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
st.write("Convierte fotos, documentos o tu voz en texto limpio.")
st.info("🔒 **Consejo:** No tomes fotos de tarjetas, contraseñas o datos del banco.")
st.divider()

# --- OPCIÓN 1: GRABAR VOZ ---
st.subheader("🎙️ Opción 1: Dictar un mensaje")
audio_grabado = st.audio_input("Toca el micrófono para hablar")
if audio_grabado:
    with st.spinner("⏳ Escuchando tu mensaje..."):
        texto = procesar_audio(audio_grabado)
        agregar_texto(texto)
        st.success("¡Mensaje agregado!")

st.divider()

# --- OPCIÓN 2: LA SOLUCIÓN NATIVA PARA CÁMARA Y ARCHIVOS ---
st.subheader("📷 Opción 2: Tomar Foto o Subir Documento")
st.write("💡 Toca el botón de abajo. **Tu celular te preguntará si quieres abrir tu Cámara** o elegir una foto de tu galería.")

archivos_subidos = st.file_uploader(
    "Toca aquí para abrir cámara o archivos:", 
    type=['png', 'jpg', 'jpeg', 'pdf', 'mp3', 'wav', 'm4a', 'ogg', 'opus'],
    accept_multiple_files=True 
)

if archivos_subidos and st.button("✅ PROCESAR DOCUMENTOS / FOTOS", type="secondary", use_container_width=True):
    with st.spinner("⏳ Leyendo... no cierres la pantalla..."):
        textos_nuevos = []
        for archivo in archivos_subidos:
            tipo = archivo.type
            if tipo.startswith("image/"): 
                textos_nuevos.append(procesar_imagen(archivo))
            elif tipo.startswith("audio/") or tipo in ["audio/ogg", "audio/opus"]: 
                textos_nuevos.append(procesar_audio(archivo))
            elif tipo == "application/pdf": 
                textos_nuevos.append(procesar_pdf(archivo))
        
        if textos_nuevos:
            texto_unido = "\n\n".join(textos_nuevos)
            agregar_texto(texto_unido)
            st.success("¡Texto extraído con éxito!")

# ==========================================
# REVISIÓN Y ENVÍO
# ==========================================
if st.session_state.texto_acumulado.strip():
    st.divider()
    st.subheader("👀 Paso 3: Revisa tu mensaje")
    
    if len(st.session_state.historial) > 0:
        if st.button("↩️ Me equivoqué, borrar lo último que agregué"):
            st.session_state.texto_acumulado = st.session_state.historial.pop()
            st.rerun()

    st.write("Toca el cuadro blanco si necesitas corregir alguna letra.")
    
    texto_final = st.text_area("Mensaje listo:", value=st.session_state.texto_acumulado.strip(), height=300, key="editor_texto", on_change=guardar_edicion_manual)
    
    if st.button("🔊 Escuchar en voz alta"):
        st.audio(generar_voz(texto_final), format='audio/mp3', autoplay=True)

    st.divider()
    
    mensaje_wpp = urllib.parse.quote(f"Hola, por favor ayúdame a pasar este texto a un Word e imprimirlo:\n\n{texto_final}")
    enlace_wpp = f"https://api.whatsapp.com/send?text={mensaje_wpp}"
    
    st.link_button("✅ ENVIAR POR WHATSAPP", enlace_wpp, type="primary", use_container_width=True)

    st.write("---")
    if st.button("🗑️ Borrar TODO y empezar de cero"):
        st.session_state.texto_acumulado = ""
        st.session_state.historial = []
        st.rerun()
