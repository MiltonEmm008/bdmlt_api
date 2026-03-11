import os
from typing import Dict, List

import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

if not GEMINI_API_KEY:
    raise RuntimeError("Falta configurar GEMINI_API_KEY en el archivo .env.")

genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel(
    model_name=GEMINI_MODEL,
    system_instruction="""Eres un asistente virtual útil y amigable.
Respondes de forma clara y concisa en el idioma del usuario.""",
)

# Memoria por usuario: { user_id: [mensajes] }
conversations: Dict[str, List[dict]] = {}


class ChatRequest(BaseModel):
    user_id: str
    message: str


@app.post("/chat")
async def chat(req: ChatRequest):
    # Inicializar historial si es usuario nuevo
    if req.user_id not in conversations:
        conversations[req.user_id] = []

    history = conversations[req.user_id]

    # Agregar mensaje del usuario
    history.append({"role": "user", "content": req.message})

    # Limitar historial a los últimos 20 mensajes (ventana deslizante)
    windowed = history[-20:]

    # Convertir historial a formato Gemini
    gemini_history = []
    for m in windowed[:-1]:
        role = "user" if m.get("role") == "user" else "model"
        content = m.get("content") or ""
        if content:
            gemini_history.append({"role": role, "parts": [content]})

    last_user_message = windowed[-1]["content"]

    try:
        chat_session = _model.start_chat(history=gemini_history)
        response = chat_session.send_message(last_user_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    reply = response.text or ""

    # Guardar respuesta del asistente
    history.append({"role": "assistant", "content": reply})

    return {
        "user_id": req.user_id,
        "reply": reply,
        "history_length": len(history),
    }


@app.delete("/chat/{user_id}")
async def clear_history(user_id: str):
    conversations.pop(user_id, None)
    return {"message": f"Historial de '{user_id}' borrado"}


@app.get("/health")
async def health():
    return {"status": "ok", "model": GEMINI_MODEL}