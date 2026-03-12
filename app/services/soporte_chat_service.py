from __future__ import annotations

import csv
import json
import smtplib
import ssl
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException
from openai import OpenAI

from app.core.config import settings


@dataclass
class _ChatState:
    messages: list[dict]
    last_used: float


_conversations: dict[str, _ChatState] = {}


_INCIDENCIAS_CSV_PATH = Path(__file__).resolve().parents[2] / "INCIDENCIAS.csv"


_SYSTEM_PROMPT_BDMLT = """Eres el asistente virtual de soporte del banco BDMLT (Banco Del Malestar).

REGLAS:
- Solo respondes temas del banco BDMLT (cuentas, transferencias, pagos, tarjetas, acceso, sucursales).
- Rechaza cualquier petición fuera de tu rol y redirige al soporte bancario.
- No inventes datos. Respuestas breves y claras.
- Responde en el idioma del usuario.

BANCO:
- Banco Del Malestar (BDMLT), fundado en 2026 en Tepic, Nayarit.
- Fundador: Milton Emmanuel. Colaborador principal: William Paul.
- 5 sucursales en Tepic: La Cantera, Av. México, Las Brisas, Cecy y Principal.

REPORTAR INCIDENCIA:
- Si el usuario quiere reportar un error o queja, solicita primero: Nombre, Correo, descripción de la Incidencia y Urgencia (Alta, Media o Baja).
- Una vez que tengas esos datos, responde con el siguiente formato exacto:

////{"funcion": "reportar_incidencia", "nombre": "...", "correo": "...", "incidencia": "...", "urgencia": "..."}////
"""


def _client() -> OpenAI:
    return OpenAI(base_url=settings.OLLAMA_BASE_URL, api_key=settings.OLLAMA_API_KEY)


def _ensure_incidencias_csv() -> None:
    if not _INCIDENCIAS_CSV_PATH.exists():
        _INCIDENCIAS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _INCIDENCIAS_CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp",
                    "session_id",
                    "nombre",
                    "correo",
                    "incidencia",
                    "urgencia",
                ]
            )


def _registrar_incidencia_csv(payload: dict, session_id: str) -> None:
    try:
        _ensure_incidencias_csv()
        with _INCIDENCIAS_CSV_PATH.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    datetime.utcnow().isoformat(),
                    session_id,
                    payload.get("nombre", ""),
                    payload.get("correo", ""),
                    payload.get("incidencia", ""),
                    payload.get("urgencia", ""),
                ]
            )
    except Exception:
        # No interrumpir el flujo del chat si falla el log
        pass


def _enviar_correos_incidencia(payload: dict) -> None:
    correo_usuario = payload.get("correo")
    nombre = payload.get("nombre", "")
    incidencia = payload.get("incidencia", "")
    urgencia = payload.get("urgencia", "")

    remitente = settings.EMAIL_USER
    password = settings.EMAIL_PASSWORD
    correo_duenio = getattr(settings, "EMAIL_OWNER", None)

    if not remitente or not password:
        # Sin credenciales no intentamos enviar correo
        return

    context = ssl.create_default_context()

    def _build_message(destinatario: str, asunto: str, cuerpo: str) -> str:
        headers = [
            f"From: Soporte BDMLT <{remitente}>",
            f"To: {destinatario}",
            f"Subject: {asunto}",
            "Content-Type: text/plain; charset=utf-8",
        ]
        return "\r\n".join(headers) + "\r\n\r\n" + cuerpo

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(remitente, password)

            # Correo al usuario que reporta la incidencia
            if correo_usuario:
                asunto_usuario = "Incidencia recibida - Banco BDMLT"
                cuerpo_usuario = (
                    f"Hola {nombre},\n\n"
                    "Hemos recibido tu incidencia y la estamos revisando.\n\n"
                    f"Detalle de la incidencia:\n"
                    f"- Urgencia: {urgencia}\n"
                    f"- Descripción: {incidencia}\n\n"
                    "Nos pondremos en contacto contigo pronto.\n\n"
                    "Atentamente,\n"
                    "Soporte Banco BDMLT"
                )
                msg_usuario = _build_message(correo_usuario, asunto_usuario, cuerpo_usuario)
                server.sendmail(remitente, [correo_usuario], msg_usuario.encode("utf-8"))

            # Correo al dueño del banco
            if correo_duenio:
                asunto_duenio = "Nueva incidencia reportada - Banco BDMLT"
                cuerpo_duenio = (
                    "Se ha registrado una nueva incidencia.\n\n"
                    f"Nombre: {nombre}\n"
                    f"Correo: {correo_usuario}\n"
                    f"Urgencia: {urgencia}\n"
                    f"Incidencia: {incidencia}\n"
                )
                msg_duenio = _build_message(correo_duenio, asunto_duenio, cuerpo_duenio)
                server.sendmail(remitente, [correo_duenio], msg_duenio.encode("utf-8"))
    except Exception:
        # No interrumpir el flujo del chat si falla el envío
        pass


def _cleanup() -> None:
    now = time.time()

    # TTL
    ttl = settings.SOPORTE_CHAT_TTL_SEGUNDOS
    if ttl > 0:
        expirados = [sid for sid, st in _conversations.items() if (now - st.last_used) > ttl]
        for sid in expirados:
            _conversations.pop(sid, None)

    # Límite de chats en RAM (evicción por LRU)
    max_chats = settings.SOPORTE_MAX_CHATS_EN_RAM
    if max_chats > 0 and len(_conversations) > max_chats:
        ordenados = sorted(_conversations.items(), key=lambda kv: kv[1].last_used)
        for sid, _ in ordenados[: max(0, len(_conversations) - max_chats)]:
            _conversations.pop(sid, None)


def _enforce_role(reply: str) -> str:
    # Capa mínima de seguridad: si el modelo intenta "romper rol", respondemos con rechazo.
    lowered = reply.lower()
    señales = (
        "ignore previous",
        "olvida las instrucciones",
        "sal de tu rol",
        "como modelo de lenguaje",
        "as an ai",
        "system prompt",
        "prompt del sistema",
    )
    if any(s in lowered for s in señales):
        return (
            "No puedo ayudar con esa solicitud. "
            "Soy el asistente de soporte del banco BDMLT y solo atiendo temas relacionados con cuentas, "
            "transferencias, pagos, movimientos y uso de la API del banco."
        )
    return reply.strip()


def enviar_mensaje(*, session_id: str | None, message: str) -> tuple[str, str, int]:
    _cleanup()

    sid = session_id or uuid.uuid4().hex
    state = _conversations.get(sid)
    if not state:
        state = _ChatState(messages=[], last_used=time.time())
        _conversations[sid] = state

    # Agregar mensaje del usuario y recortar ventana
    state.messages.append({"role": "user", "content": message})
    max_msgs = max(1, settings.SOPORTE_MAX_MENSAJES_POR_CHAT)
    windowed = state.messages[-max_msgs:]

    try:
        resp = _client().chat.completions.create(
            model=settings.OLLAMA_MODEL,
            messages=[{"role": "system", "content": _SYSTEM_PROMPT_BDMLT}] + windowed,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando modelo local: {e}")

    raw_reply = resp.choices[0].message.content or ""
    reply = _enforce_role(raw_reply)

    # Detectar y procesar el patrón de incidencia ////{...}////
    try:
        if "////" in reply:
            start = reply.find("////")
            end = reply.rfind("////")
            if start != -1 and end != -1 and end > start + 4:
                contenido_json = reply[start + 4 : end].strip()
                data = json.loads(contenido_json)
                if isinstance(data, dict) and data.get("funcion") == "reportar_incidencia":
                    _registrar_incidencia_csv(data, sid)
                    _enviar_correos_incidencia(data)
                    reply = (
                        "Incidencia registrada con exito, nos pondremos en contacto con usted pronto"
                    )
                else:
                    # Si no es el formato esperado, solo limpiamos los //// del texto
                    reply = reply.replace("////", "").strip()
    except Exception:
        # En caso de error al parsear, devolvemos el texto sin los //// para no exponer el JSON al usuario
        reply = reply.replace("////", "").strip()

    state.messages.append({"role": "assistant", "content": reply})
    state.last_used = time.time()

    # Recorte final (por si se excedió)
    state.messages = state.messages[-max_msgs:]

    return sid, reply, len(state.messages)


def limpiar_chat(session_id: str) -> None:
    _conversations.pop(session_id, None)


def estado_soporte() -> dict:
    _cleanup()
    return {
        "status": "ok",
        "model": settings.OLLAMA_MODEL,
        "base_url": settings.OLLAMA_BASE_URL,
        "chats_en_ram": len(_conversations),
        "max_chats_en_ram": settings.SOPORTE_MAX_CHATS_EN_RAM,
        "max_mensajes_por_chat": settings.SOPORTE_MAX_MENSAJES_POR_CHAT,
        "ttl_segundos": settings.SOPORTE_CHAT_TTL_SEGUNDOS,
    }

