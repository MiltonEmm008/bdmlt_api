from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

MODEL = "qwen2.5:3b"

SYSTEM_PROMPT = """Eres un asistente virtual útil y amigable.
Respondes de forma clara y concisa en el idioma del usuario."""

# Memoria por usuario: { user_id: [mensajes] }
conversations: dict[str, list] = {}


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

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + windowed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    reply = response.choices[0].message.content

    # Guardar respuesta del asistente
    history.append({"role": "assistant", "content": reply})

    return {
        "user_id": req.user_id,
        "reply": reply,
        "history_length": len(history)
    }


@app.delete("/chat/{user_id}")
async def clear_history(user_id: str):
    conversations.pop(user_id, None)
    return {"message": f"Historial de '{user_id}' borrado"}


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL}