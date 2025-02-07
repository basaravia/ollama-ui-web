import requests
import streamlit as st

# Base URL para la API de Ollama
OLLAMA_API = "http://localhost:11434/api"

def list_models():
    response = requests.get(f"{OLLAMA_API}/tags")
    if response.status_code == 200:
        return response.json().get("models", [])
    return []

def delete_model(model_name):
    response = requests.post(f"{OLLAMA_API}/delete", json={"model": model_name})
    return response.status_code == 200

def download_model(model_name):
    response = requests.post(f"{OLLAMA_API}/pull", json={"model": model_name})
    return response.status_code == 200


def show_model_details(model_name):
    response = requests.post(f"{OLLAMA_API}/show", json={"model": model_name})
    if response.status_code == 200:
        data = response.json()
        return {
            "model_name": model_name,
            # "template": data.get("template", "N/A"),
            "details": data.get("details", "N/A"),
            "model_info": data.get("model_info", "N/A"),
            "modified_at": data.get("modified_at", "N/A")
        }
    return {"error": "No se pudo obtener información del modelo"}


