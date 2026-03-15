# Banco Simulado — Backend API

API REST construida con **FastAPI** y **Supabase** (PostgreSQL) para el proyecto escolar de banco simulado.

---

## Estructura del proyecto

```
banco-api/
├── main.py                  # Punto de entrada, configuración de la app
├── requirements.txt
├── .env.example             # Copia como .env y edita
├── app/
│   ├── core/
│   │   ├── config.py        # Variables de entorno y configuración
│   │   ├── database.py      # Conexión Supabase y sesión
│   │   ├── security.py      # Hash de contraseñas y JWT
│   │   └── storage.py       # Subida de fotos a Supabase Storage
    ├── models/
    │   └── models.py        # Tablas de la base de datos (SQLAlchemy)
    ├── schemas/
    │   └── schemas.py       # Validación de datos de entrada/salida (Pydantic)
    ├── services/
    │   ├── auth_service.py  # Lógica de negocio: registro, login, token
    │   └── cuenta_service.py# Lógica de negocio: transferencias, pagos
    └── routers/
        ├── auth.py          # Endpoints: /auth/...
        ├── cuentas.py       # Endpoints: /cuentas/...
        └── operaciones.py   # Endpoints: /operaciones/...
```

---

## Instalación y ejecución

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Edita .env con tu URL y clave de Supabase

# 4. Ejecutar
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

La API estará en `http://localhost:8000`  
Documentación interactiva: `http://localhost:8000/docs`

---

## Configuración de Supabase

### Variables de entorno requeridas en `.env`:
```bash
# Base de datos PostgreSQL
DATABASE_URL=postgresql+psycopg2://postgres:TU_PASSWORD@db.PROJECT_ID.supabase.co:5432/postgres

# Storage para fotos de perfil
SUPABASE_URL=https://PROJECT_ID.supabase.co
SUPABASE_KEY=anon_key_o_service_role_key
SUPABASE_BUCKET_FOTOS=fotos_perfil

# Email (opcional, para verificación/recuperación)
EMAIL_USER=tu_email@dominio.com
EMAIL_PASSWORD=tu_app_password
EMAIL_OWNER=tu_email@dominio.com
```

### Configuración en Supabase Dashboard:
1. **Storage**: Crea el bucket `fotos_perfil`
2. **Policies**: Añade políticas RLS para el bucket:
```sql
-- Permitir subir archivos
CREATE POLICY "Upload fotos de perfil" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'fotos_perfil');

-- Permitir ver archivos
CREATE POLICY "Download fotos de perfil" ON storage.objects
FOR SELECT USING (bucket_id = 'fotos_perfil');

-- Permitir actualizar (upsert)
CREATE POLICY "Update fotos de perfil" ON storage.objects
FOR UPDATE USING (bucket_id = 'fotos_perfil');
```

---

## Endpoints disponibles

### Autenticación
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/auth/registro` | Registrar nuevo usuario (incluye teléfono y dirección opcionales) |
| POST | `/auth/login` | Iniciar sesión |
| GET | `/auth/me` | Perfil del usuario autenticado |
| PATCH | `/auth/me` | Actualizar perfil (nombre, contraseña, foto, teléfono y dirección) |
| POST | `/auth/desactivar` | Desactivar la cuenta del usuario (requiere correo y confirmación de contraseña, la cuenta `default@banco.com` no se puede desactivar) |

### Cuentas
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/cuentas/` | Ver cuentas débito y crédito |
| GET | `/cuentas/mi-qr` | Datos para QR de transferencia |
| GET | `/cuentas/movimientos` | Historial de movimientos |
| GET | `/cuentas/limite-gasto` | Ver límite de gasto mensual y gasto del mes |
| PUT | `/cuentas/limite-gasto` | Configurar límite de gasto mensual |

### Operaciones
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/operaciones/transferencia` | Transferir a otro usuario |
| POST | `/operaciones/pago-servicio` | Pagar CFE, Infinitum, Telcel, Agua, Gas (con débito o crédito) |
| POST | `/operaciones/pago-credito` | Pagar deuda de tarjeta de crédito |
| GET | `/operaciones/servicios-disponibles` | Lista de servicios disponibles |

---

## Conectar desde Android

En el emulador de Android usa:
```
http://10.0.2.2:8000
```

En un dispositivo físico usa la IP local de tu PC:
```
http://192.168.X.X:8000
```

---

## Fotos de perfil (Supabase Storage)

- Las fotos se guardan en **Supabase Storage** en el bucket `fotos_perfil`
- Se devuelven URLs públicas completas de Supabase: `https://PROJECT_ID.supabase.co/storage/v1/object/public/fotos_perfil/<archivo>.jpg`
- El frontend debe usar estas URLs directamente (no anteponer la base URL de la API)
- Formatos soportados: `.jpg`, `.png`, `.webp` (máximo 5MB)
- Las URLs son públicas y accesibles directamente desde cualquier cliente

---

## Servicios disponibles para pago

- `CFE` — Comisión Federal de Electricidad
- `Infinitum` — Internet Telmex
- `Telcel` — Telefonía móvil
- `Agua` — Servicio de agua
- `Gas` — Servicio de gas

Para agregar más servicios, solo añade valores al enum `Servicio` en `app/models/models.py`.
