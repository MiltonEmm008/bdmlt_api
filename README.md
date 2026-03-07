# Banco Simulado — Backend API

API REST construida con **FastAPI** y **SQLite** para el proyecto escolar de banco simulado.

---

## Estructura del proyecto

```
banco-api/
├── main.py                  # Punto de entrada, configuración de la app
├── requirements.txt
├── .env.example             # Copia como .env y edita
├── banco.db                 # Se genera automático al ejecutar
└── app/
    ├── core/
    │   ├── config.py        # Variables de entorno y configuración
    │   ├── database.py      # Conexión SQLite y sesión
    │   └── security.py      # Hash de contraseñas y JWT
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
# Edita .env si quieres cambiar la clave secreta

# 4. Ejecutar
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

La API estará en `http://localhost:8000`  
Documentación interactiva: `http://localhost:8000/docs`

---

## Endpoints disponibles

### Autenticación
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/auth/registro` | Registrar nuevo usuario |
| POST | `/auth/login` | Iniciar sesión |
| GET | `/auth/me` | Perfil del usuario autenticado |

### Cuentas
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/cuentas/` | Ver cuentas débito y crédito |
| GET | `/cuentas/movimientos` | Historial de movimientos |

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

## Servicios disponibles para pago

- `CFE` — Comisión Federal de Electricidad
- `Infinitum` — Internet Telmex
- `Telcel` — Telefonía móvil
- `Agua` — Servicio de agua
- `Gas` — Servicio de gas

Para agregar más servicios, solo añade valores al enum `Servicio` en `app/models/models.py`.
