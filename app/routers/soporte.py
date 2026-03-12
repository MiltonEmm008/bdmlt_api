from fastapi import APIRouter

from app.schemas.schemas import SoporteChatRequest, SoporteChatResponse
from app.services.soporte_chat_service import enviar_mensaje, estado_soporte, limpiar_chat


router = APIRouter(prefix="/soporte", tags=["Soporte"])


@router.get("/health")
def health_soporte():
    """Salud del módulo de soporte (config y estado en RAM)."""
    return estado_soporte()


@router.post("/chat", response_model=SoporteChatResponse)
def chat_soporte(payload: SoporteChatRequest):
    """
    Chat de soporte BDMLT con memoria en RAM (ventana deslizante).

    - Si no envías `session_id`, se crea una conversación nueva.
    - La memoria se recorta automáticamente para evitar crecer sin límite.
    """
    sid, reply, mem = enviar_mensaje(session_id=payload.session_id, message=payload.message)
    return SoporteChatResponse(session_id=sid, reply=reply, memory_messages=mem)


@router.delete("/chat/{session_id}")
def limpiar(session_id: str):
    """Borra el historial en RAM de una sesión de chat."""
    limpiar_chat(session_id)
    return {"mensaje": f"Chat '{session_id}' limpiado"}

