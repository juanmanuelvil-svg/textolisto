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
# SISTEMA DE MEMORIA A PRUEBA DE ERRORES
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
# FUNCIONES DE INTELIGENCIA ARTIFICIAL (MEJORADAS PARA TABLAS)
# ==========================================
def procesar_imagen(imagen_file):
    img = Image.open(imagen_file)
    # INSTRUCCIÓN MEJORADA PARA TABLAS EN FOTOS
    prompt = """Extrae todo el texto de esta imagen de forma clara y limpia. Corrige ortografía. 
    SI ENCUENTRAS TABLAS O CIFRAS: NO uses formato de tabla con rayitas (|). Conviértelas en una lista fácil de leer renglón por renglón (Ejemplo: 'Concepto: X - Total: $Y').
    Devuelve SOLO el texto, sin saludos ni explicaciones tuyas."""
    respuesta = model.generate_content([prompt, img])
    return respuesta.text

def procesar_audio(audio_file):
    audio_data = {"mime_type": audio_file.type, "data": audio_file.getvalue()}
    prompt = "Transcribe el siguiente audio. Quita muletillas y corrige la ortografía. Devuelve SOLO el texto, sin saludos."
    respuesta = model.generate_content([prompt, audio_data])
    return respuesta.text

def procesar_pdf(pdf_file):
    pdf_data = {"mime_type": "application/pdf", "data": pdf_file.getvalue()}
    # INSTRUCCIÓN MEJORADA PARA TABLAS EN PDF
    prompt = """Lee este documento PDF. Extrae el texto de forma clara. 
    SI ENCUENTRAS TABLAS O CIFRAS: NO uses formato de tabla con rayitas (|). Conviértelas en una lista fácil de leer renglón por renglón (Ejemplo: 'Concepto: X - Total: $Y').
    Devuelve SOLO el texto, sin saludos ni explicaciones tuyas."""
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
st.write("Convierte fotos, PDF o audios en texto limpio. **Puedes agregar tantos como necesites.**")
st.info("🔒 **Consejo:** No subas tarjetas de crédito, contraseñas o datos del banco.")
st.divider()

# --- SECCIÓN 1: TIEMPO REAL ---
st.subheader("Opción A: Usa la cámara o micrófono ahora")
col1, col2 = st.columns(2)

with col1:
    foto_camara = st.camera_input("📷 Toca para tomar foto")
    if foto_camara:
        with st.spinner("⏳ Leyendo la foto..."):
            texto = procesar_imagen(foto_camara)
            agregar_texto(texto)
            st.success("¡Foto agregada al texto!")

with col2:
    audio_grabado = st.audio_input("🎙️ Toca para grabar voz")
    if audio_grabado:
        with st.spinner("⏳ Escuchando tu mensaje..."):
            texto = procesar_audio(audio_grabado)
            agregar_texto(texto)
            st.success("¡Mensaje agregado al texto!")

st.divider()

# --- SECCIÓN 2: SUBIR ARCHIVOS ---
st.subheader("Opción B: Selecciona archivos de tu teléfono")
st.write("Puedes seleccionar varios archivos al mismo tiempo.")

archivos_subidos = st.file_uploader(
    "Toca aquí para buscar en tu teléfono:", 
    type=['png', 'jpg', 'jpeg', 'pdf', 'mp3', 'wav', 'm4a', 'ogg', 'opus'],
    accept_multiple_files=True 
)

if archivos_subidos and st.button("✅ PROCESAR ARCHIVOS SELECCIONADOS", type="secondary", use_container_width=True):
    with st.spinner("⏳ Leyendo tus archivos, no cierres la pantalla..."):
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
            st.success("¡Archivos procesados y agregados al texto!")

# ==========================================
# REVISIÓN Y ENVÍO (Con Deshacer)
# ==========================================
if st.session_state.texto_acumulado.strip():
    st.divider()
    st.subheader("👀 Paso 3: Revisa tu mensaje")
    
    if len(st.session_state.historial) > 0:
        if st.button("↩️ Me equivoqué, borrar lo último que agregué"):
            st.session_state.texto_acumulado = st.session_state.historial.pop()
            st.rerun()

    st.write("Si hay un error en alguna letra, toca el cuadro blanco y corrígelo con tu teclado.")
    
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
