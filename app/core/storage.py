# app/core/storage.py
"""Subida de fotos de perfil a Supabase Storage (bucket fotos_perfil)."""

from __future__ import annotations

import io

from app.core.config import settings

_supabase_client = None


def _get_supabase_client():
    """Cliente de Supabase lazy; solo se crea si hay URL y key."""
    global _supabase_client
    if _supabase_client is None and settings.usa_supabase_storage:
        from supabase import create_client
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase_client


def subir_foto_perfil(contenido: bytes, nombre_archivo: str, content_type: str = "image/jpeg") -> str:
    """
    Sube una foto al bucket de Supabase y devuelve la URL pública.
    Requiere que el bucket esté configurado como público o que uses políticas RLS adecuadas.
    """
    client = _get_supabase_client()
    if not client:
        raise RuntimeError("Supabase no configurado para almacenamiento")

    bucket = settings.SUPABASE_BUCKET_FOTOS
    path = nombre_archivo

    client.storage.from_(bucket).upload(
        path=path,
        file=contenido,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    return client.storage.from_(bucket).get_public_url(path)
