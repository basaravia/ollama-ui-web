import os
import pandas as pd
import json
import base64
import sys
sys.path.append('./')
from utils.handle_api import list_models, delete_model, download_model, show_model_details
import streamlit as st


# Configuración de colores
theme_primary = "#ffdd00"
theme_secondary = "#72787a"
theme_accent = "#0f265c"


def encode_image(uploaded_image):
    """Codifica la imagen en base64 para enviarla al modelo."""
    try:
        if uploaded_image is None:
            return None
        image_bytes = uploaded_image.read()  # Leer el contenido binario
        return base64.b64encode(image_bytes).decode("utf-8")
    except Exception as e:
        # st.error(f"Error al codificar la imagen: {str(e)}")
        print(f"Error al codificar la imagen: {str(e)}")
        return None
    
st.set_page_config(page_title="Ollama Streamlit App", layout="wide")
st.markdown(
    f"""
    <style>
        .stApp {{ background-color: {theme_primary}; }}
        .stButton>button {{ background-color: {theme_accent}; color: white; }}
        .stSelectbox>div {{ background-color: {theme_secondary}; color: white; }}
        .stTextInput>div>input {{ background-color: white; color: black; }}
    </style>
    """,
    unsafe_allow_html=True
)

# Interfaz de Streamlit
tabs = ["Manejo de Modelos", "Chat de Texto e Imagen"]
tab = st.sidebar.radio("Selecciona una opción", tabs)

if tab == "Manejo de Modelos":
    st.title("📦 Manejo de Modelos en Ollama")
    models = list_models()
    
    if models:
        st.write("### Modelos Descargados")
        model_names = [m["name"] for m in models]
        selected_model = st.selectbox("Selecciona un modelo para ver detalles", model_names)
        model_details = show_model_details(selected_model)
        
        st.write(f"### Detalles de modelo {selected_model} modificado en {model_details['modified_at']}")
        # details_df = pd.DataFrame([model_details])
        pd_ft_details = pd.json_normalize(model_details["details"]).T
        pd_ft_model_info = pd.json_normalize(model_details["model_info"]).T

        details_df = pd.concat([pd_ft_details,pd_ft_model_info])
        st.table(details_df)
        
        if st.button("Eliminar Modelo"):
            if delete_model(selected_model):
                st.success(f"Modelo {selected_model} eliminado correctamente.")
            else:
                st.error("Error al eliminar el modelo.")
    else:
        st.warning("No hay modelos descargados.")
    
    st.write("### Descargar o Subir Modelo")
    new_model_name = st.text_input("Nombre del modelo en el hub de Ollama:")
    if st.button("Descargar Modelo") and new_model_name:
        if download_model(new_model_name):
            st.success(f"Modelo {new_model_name} descargado correctamente.")
        else:
            st.error("Error al descargar el modelo.")
    
    uploaded_file = st.file_uploader("Subir artefacto GGUF", type=["gguf"])
    if uploaded_file:
        with open(os.path.join("./", uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("Archivo GGUF subido correctamente.")
    
    st.markdown("---")
    st.markdown("📌 **Autor**: Alexander Saravia | 📧 Contacto: asaravia@example.com")
    # st.image("logo.png", width=100)

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if tab == "Chat de Texto e Imagen":
    st.title("💬 Chat con Modelos de IA")
    
    # Obtener modelos disponibles
    try:
        response = requests.get(f"{OLLAMA_API}/tags")
        response.raise_for_status()
        available_models = response.json().get("models", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener modelos: {str(e)}")
        available_models = []

    # Lista de nombres de modelos
    model_names = [m["name"] for m in available_models]
    selected_model = st.selectbox("Selecciona un modelo", model_names if model_names else ["No disponible"])

    stream_enabled = st.checkbox("Habilitar Streaming")
    raw_mode = st.checkbox("Activar Modo Raw")
    response_format = st.selectbox("Formato de Respuesta", ["Texto", "JSON"])
    chat_history = st.session_state["chat_history"]
    print("Incial : ",chat_history)
    user_input = st.text_area("Escribe tu mensaje:")
    uploaded_image = st.file_uploader("Subir Imagen", type=["jpg", "png", "jpeg"])
    
    # Enviar mensaje
    if st.button("Enviar Mensaje") and user_input:
        try:
            encoded_image = encode_image(uploaded_image) if uploaded_image else None

            # Si es la primera vez, agregar un mensaje del sistema
            if not chat_history or chat_history[0]["role"] != "system":
                system_message = {"role": "system", "content": "Eres un asistente virtual muy util y brindas infromacion consisa de maximo 200 caracteres en español"}
                chat_history.insert(0, system_message)

            # Agregar mensaje del usuario
            message = {"role": "user", "content": user_input}
            if encoded_image:
                message["images"] = [encoded_image]
            chat_history.append(message)

            # Construir payload
            payload = {
                "model": selected_model,
                "messages": [message], #chat_history[-3:],
                "stream": stream_enabled,
                # "format": "json" if response_format == "JSON" else "text"
            }
            print(payload)
            # Enviar solicitud a Ollama
            response = requests.post(f"{OLLAMA_API}/chat", json=payload, timeout=5*60)
            # time.sleep(15)
            response.raise_for_status()
            
            # Procesar respuesta del modelo
            response_data = response.json()
            assistant_response = response_data.get("message", {}).get("content", "Error en la respuesta")

            # Guardar respuesta del asistente
            chat_history.append({"role": "assistant", "content": assistant_response})
            st.session_state["chat_history"] = chat_history  # Guardar en sesión

        except requests.exceptions.RequestException as e:
            st.error(f"Error en la solicitud al modelo: {str(e)}")
        except Exception as e:
            st.error(f"Error inesperado: {str(e)}")

    # Mostrar historial de conversación
    if chat_history:
        st.write("### Historial de Conversación")
        for msg in chat_history:
            role = "🤖" if msg["role"] == "assistant" else "🧑"
            st.write(f"{role}: {msg['content']}")
    print("Final : ",chat_history)

    st.markdown("---")
    st.markdown("📌 **Autor**: Alexander Saravia | 📧 Contacto: asaravia@example.com")