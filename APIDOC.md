# Banco Simulado — Documentación de Endpoints

Base URL: `http://localhost:3000`  
Documentación interactiva: `http://localhost:3000/docs`

---

## Autenticación

Todos los endpoints protegidos requieren un header de autorización con el token JWT obtenido al registrarse o iniciar sesión:

```
Authorization: Bearer <token>
```

---

## `/auth` — Autenticación

### `POST /auth/registro`
Registra un nuevo usuario en el sistema. Crea automáticamente una cuenta de débito (con $1,000 de saldo inicial) y una cuenta de crédito (con límite de $5,000) para el usuario, pero deja la cuenta **desactivada** hasta que el usuario verifique su correo electrónico.

Al registrarse se envía un correo de verificación con un enlace que contiene un token JWT válido por **60 minutos**. Al entrar al enlace, la cuenta se activa automáticamente.

**Body (JSON):**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | ✅ | Nombre completo del usuario |
| `email` | string | ✅ | Correo electrónico (debe ser único) |
| `password` | string | ✅ | Contraseña (mínimo 6 caracteres) |
| `telefono` | string | ❌ | Teléfono de contacto del usuario |
| `calle_numero` | string | ❌ | Calle y número del domicilio |
| `colonia` | string | ❌ | Colonia del domicilio |
| `ciudad` | string | ❌ | Ciudad del domicilio |
| `codigo_postal` | string | ❌ | Código postal del domicilio |

**Ejemplo de solicitud:**
```json
{
  "nombre": "Milton Martínez",
  "email": "milton@correo.com",
  "password": "mipassword123",
  "telefono": "5551234567",
  "calle_numero": "Av. Siempre Viva 742",
  "colonia": "Centro",
  "ciudad": "CDMX",
  "codigo_postal": "01000"
}
```

**Respuesta exitosa `201`:**
```json
{
  "mensaje": "Usuario registrado correctamente. Revisa tu correo para verificar tu cuenta."
}
```

**Errores posibles:**
- `400` — El correo ya está registrado

---

### `POST /auth/login`
Inicia sesión con credenciales existentes y devuelve un token de acceso.

**Body (JSON):**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `email` | string | ✅ | Correo electrónico registrado |
| `password` | string | ✅ | Contraseña del usuario |

**Ejemplo de solicitud:**
```json
{
  "email": "milton@correo.com",
  "password": "mipassword123"
}
```

**Respuesta exitosa `200`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errores posibles:**
- `401` — Credenciales incorrectas
- `403` — La cuenta está desactivada

---

### `GET /auth/me`
Devuelve la información del usuario actualmente autenticado.

**Headers requeridos:** `Authorization: Bearer <token>`

**Sin body.**

**Respuesta exitosa `200`:**
```json
{
  "id": 1,
  "nombre": "Milton Martínez",
  "email": "milton@correo.com",
  "telefono": "5551234567",
  "calle_numero": "Av. Siempre Viva 742",
  "colonia": "Centro",
  "ciudad": "CDMX",
  "codigo_postal": "01000",
  "activo": true,
  "foto_perfil": "media/perfiles/2f9c1b0e0e9c4c3aa0f4f2f6a9b7c1d2.jpg",
  "creado_en": "2025-03-07T10:30:00"
}
```

**Errores posibles:**
- `401` — Token inválido o expirado
- `404` — Usuario no encontrado
- `403` — La cuenta está desactivada

---

### `POST /auth/desactivar`
Desactiva la cuenta de un usuario.  
La cuenta **default** (`default@banco.com`) **no** se puede desactivar.  
Una vez desactivada, la cuenta no puede iniciar sesión, no puede realizar operaciones ni recibir transferencias.

> Nota: la cuenta no se elimina físicamente de la base de datos, solo se marca como inactiva para evitar inconsistencias con los movimientos históricos.

**Body (JSON):**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `email` | string | ✅ | Correo electrónico de la cuenta a desactivar |
| `password` | string | ✅ | Contraseña actual del usuario |
| `confirmar_password` | string | ✅ | Debe coincidir con `password` |

**Ejemplo de solicitud:**
```json
{
  "email": "milton@correo.com",
  "password": "mipassword123",
  "confirmar_password": "mipassword123"
}
```

**Respuesta exitosa `200`:**
```json
{
  "mensaje": "La cuenta se ha desactivado correctamente"
}
```

**Errores posibles:**
- `400` — La cuenta ya está desactivada o se intenta desactivar la cuenta default
- `401` — Contraseña incorrecta
- `404` — Usuario no encontrado


---

### `PATCH /auth/me`
Actualiza los datos del usuario autenticado. Permite:
- Cambiar `nombre`
- Cambiar datos de contacto y domicilio (`telefono`, `calle_numero`, `colonia`, `ciudad`, `codigo_postal`)
- Cambiar contraseña (requiere `password_actual` y `password_nueva`)
- Subir `foto` de perfil (se guarda en `media/perfiles/` y se expone en `/media/...`)

**Headers requeridos:** `Authorization: Bearer <token>`

**Content-Type:** `multipart/form-data`

**Campos (form-data):**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | ❌ | Nuevo nombre del usuario |
| `telefono` | string | ❌ | Nuevo teléfono del usuario |
| `calle_numero` | string | ❌ | Nueva calle y número del domicilio |
| `colonia` | string | ❌ | Nueva colonia del domicilio |
| `ciudad` | string | ❌ | Nueva ciudad del domicilio |
| `codigo_postal` | string | ❌ | Nuevo código postal del domicilio |
| `password_actual` | string | ❌ | Contraseña actual (requerida si envías `password_nueva`) |
| `password_nueva` | string | ❌ | Nueva contraseña (mínimo 6 caracteres) |
| `foto` | file | ❌ | Imagen (`.jpg`, `.png`, `.webp`). Máximo 5MB |

**Respuesta exitosa `200`:** devuelve el usuario actualizado (mismo formato que `GET /auth/me`).

**Errores posibles:**
- `400` — Datos inválidos (por ejemplo: falta `password_actual`, formato de imagen no soportado, foto vacía, >5MB, contraseña nueva muy corta)
- `401` — Token inválido o expirado, o contraseña actual incorrecta
- `404` — Usuario no encontrado

### `POST /auth/forgot-password`
Inicia el flujo de recuperación de contraseña.  
Siempre responde de forma genérica para no revelar si el correo existe.

**Body (JSON):**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `email` | string (Email) | ✅ | Correo electrónico del usuario |

**Comportamiento:**
- Si el correo existe y la cuenta está activa, se envía un correo con un enlace para restablecer la contraseña.
- El enlace contiene un token JWT válido por `PASSWORD_RESET_EXPIRE_MINUTES` (5 minutos por defecto).
- Si el correo no existe o la cuenta no está activa, no se hace nada pero la respuesta es la misma.

**Respuesta exitosa `200`:**
```json
{
  "mensaje": "Si el correo existe en el sistema, enviaremos un enlace de recuperación."
}
```

---

### `GET /auth/reset-password-form`
Devuelve el HTML con el formulario para establecer una nueva contraseña.  
El token JWT llega como querystring: `?token=...`

- **Sin autenticación requerida.**
- **Sin body.**

El formulario envía internamente una solicitud `POST /auth/reset-password` con:
- `token`
- `password`
- `confirmar_password`

---

### `POST /auth/reset-password`
Actualiza la contraseña del usuario usando el token de recuperación.

**Body (JSON):**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `token` | string | ✅ | Token JWT enviado al correo (válido por 5 minutos) |
| `password` | string | ✅ | Nueva contraseña (mínimo 6 caracteres) |
| `confirmar_password` | string | ✅ | Debe coincidir con `password` |

**Respuesta exitosa `200`:**
```json
{
  "mensaje": "Contraseña actualizada correctamente"
}
```

**Errores posibles:**
- `400` — La confirmación de contraseña no coincide
- `400` — La contraseña nueva debe tener al menos 6 caracteres
- `400` — Enlace de recuperación inválido o expirado
- `404` — Usuario no encontrado

---

### `GET /auth/verificar-email-form`
Devuelve el HTML que verifica automáticamente el correo del usuario usando el token.  
El token JWT llega como querystring: `?token=...`

- **Sin autenticación requerida.**
- **Sin body.**

Al cargar la página, se hace una llamada interna a `POST /auth/verificar-email` para activar la cuenta y mostrar un mensaje de éxito o error.

---

### `POST /auth/verificar-email`
Verifica el correo del usuario a partir de un token JWT enviado por correo y activa la cuenta.

**Body (JSON):**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `token` | string | ✅ | Token JWT de verificación enviado al correo (válido por 60 minutos) |

**Respuesta exitosa `200`:**
```json
{
  "mensaje": "Cuenta verificada correctamente. Ya puedes iniciar sesión."
}
```

**Errores posibles:**
- `400` — Enlace de verificación inválido o expirado
- `404` — Usuario no encontrado

---

## `/cuentas` — Cuentas bancarias

### `GET /cuentas/`
Devuelve las cuentas bancarias del usuario autenticado (débito y crédito).

**Headers requeridos:** `Authorization: Bearer <token>`

**Sin body.**

**Respuesta exitosa `200`:**
```json
[
  {
    "id": 1,
    "numero": "400012345678901234",
    "tipo": "debito",
    "saldo": 1000.0,
    "limite_gasto_mensual": 0.0,
    "deuda": 0.0,
    "limite_credito": 0.0,
    "creada_en": "2025-03-07T10:30:00"
  },
  {
    "id": 2,
    "numero": "500098765432109876",
    "tipo": "credito",
    "saldo": 0.0,
    "limite_gasto_mensual": 0.0,
    "deuda": 0.0,
    "limite_credito": 5000.0,
    "creada_en": "2025-03-07T10:30:00"
  }
]
```

> Para la cuenta de **débito**, el campo relevante es `saldo`.  
> Para la cuenta de **crédito**, los campos relevantes son `deuda` y `limite_credito`.

**Errores posibles:**
- `401` — Token inválido o expirado

---

### `GET /cuentas/mi-qr`
Devuelve el número de cuenta de débito, el nombre del usuario autenticado y la fecha/hora en que se generaron los datos. Se usa para que la app Android genere el código QR para recibir transferencias (el backend solo provee los datos, la app genera el QR visualmente).

**Headers requeridos:** `Authorization: Bearer <token>`

**Sin body.**

**Respuesta exitosa `200`:**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `numero_cuenta` | string | Número de la cuenta de débito |
| `nombre` | string | Nombre del usuario |
| `fecha` | string | Fecha y hora en que se enviaron los datos: día/mes/año y hora en formato 24h (minutos, segundos). Ejemplo: `07/03/2025 14:30:45` |

```json
{
  "numero_cuenta": "400012345678901234",
  "nombre": "Milton Martínez",
  "fecha": "07/03/2025 14:30:45"
}
```

**Errores posibles:**
- `401` — Token inválido o expirado
- `404` — No tienes cuenta de débito

---

### `GET /cuentas/movimientos`
Devuelve el historial de movimientos del usuario autenticado. Permite ordenar por fecha, filtrar por tipo de movimiento y limitar la cantidad de resultados.

**Headers requeridos:** `Authorization: Bearer <token>`

**Query params (opcionales):**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `limite` | integer | `20` | Número de movimientos a retornar (mínimo 1, máximo 100) |
| `orden_fecha` | string | `desc` | Orden por fecha: `asc` (más antiguos primero) o `desc` (más recientes primero) |
| `tipo` | string (enum) | — | Filtrar por tipo de movimiento. Valores: `transferencia`, `pago_servicio`, `pago_credito`, `deposito`. Si se omite, se devuelven todos los tipos. |

**Ejemplos:**
```
GET /cuentas/movimientos?limite=50
GET /cuentas/movimientos?orden_fecha=asc
GET /cuentas/movimientos?tipo=transferencia
GET /cuentas/movimientos?limite=30&orden_fecha=desc&tipo=pago_servicio
```

**Respuesta exitosa `200`:**
```json
[
  {
    "id": 1,
    "tipo": "transferencia",
    "monto": 200.0,
    "descripcion": "Pago de renta",
    "estado": "completada",
    "servicio": null,
    "referencia_servicio": null,
    "cuenta_origen_id": 1,
    "cuenta_destino_id": 4,
    "creada_en": "2025-03-07T11:00:00"
  },
  {
    "id": 2,
    "tipo": "pago_servicio",
    "monto": 350.0,
    "descripcion": "Pago CFE - Ref: 12345678",
    "estado": "completada",
    "servicio": "CFE",
    "referencia_servicio": "12345678",
    "cuenta_origen_id": 1,
    "cuenta_destino_id": null,
    "creada_en": "2025-03-07T11:30:00"
  }
]
```

**Valores posibles del campo `tipo`:**
| Valor | Descripción |
|-------|-------------|
| `transferencia` | Transferencia a otro usuario |
| `pago_servicio` | Pago de servicio (CFE, Telcel, etc.) |
| `pago_credito` | Pago de deuda de tarjeta de crédito |
| `deposito` | Depósito recibido |

**Valores posibles del campo `estado`:**
| Valor | Descripción |
|-------|-------------|
| `completada` | Operación realizada con éxito |
| `pendiente` | En proceso |
| `fallida` | La operación no pudo completarse |

**Errores posibles:**
- `401` — Token inválido o expirado

---

### `GET /cuentas/limite-gasto`
Devuelve el límite de gasto mensual y el gasto del mes actual **por cuenta** (débito y crédito).

**Headers requeridos:** `Authorization: Bearer <token>`

**Sin body.**

**Respuesta exitosa `200`:**
```json
[
  {
    "tipo": "debito",
    "limite_gasto_mensual": 2000.0,
    "gasto_mes_actual": 750.0
  },
  {
    "tipo": "credito",
    "limite_gasto_mensual": 1500.0,
    "gasto_mes_actual": 450.0
  }
]
```

**Errores posibles:**
- `401` — Token inválido o expirado
- `404` — No tienes cuentas

---

### `PUT /cuentas/limite-gasto`
Configura el límite de gasto mensual. Si `limite` es `0`, el límite queda desactivado.  
Si no envías `tipo`, el límite se aplica a **débito y crédito**.

**Headers requeridos:** `Authorization: Bearer <token>`

**Body (JSON):**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `limite` | float | ✅ | Límite mensual (0 desactiva, no puede ser negativo) |
| `tipo` | string (enum) | ❌ | `debito` o `credito`. Si se omite, aplica a ambas |

**Ejemplos:**
```json
{ "limite": 2000.0 }
```
```json
{ "limite": 1500.0, "tipo": "credito" }
```

**Respuesta exitosa `200`:** devuelve el mismo formato que `GET /cuentas/limite-gasto`.

**Errores posibles:**
- `400` — Límite inválido
- `401` — Token inválido o expirado
- `404` — No tienes cuentas

## `/operaciones` — Operaciones bancarias

### `POST /operaciones/transferencia`
Transfiere dinero desde la cuenta de débito del usuario autenticado hacia la cuenta de débito de otro usuario.

**Headers requeridos:** `Authorization: Bearer <token>`

**Headers opcionales en respuesta:**
- `X-Gasto-Advertencia`: se envía cuando el movimiento hace que alcances el 90% de tu límite de gasto mensual.

**Body (JSON):**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `numero_cuenta_destino` | string | ✅ | Número de cuenta del destinatario |
| `monto` | float | ✅ | Cantidad a transferir (debe ser mayor a 0) |
| `descripcion` | string | ❌ | Concepto o nota de la transferencia (default: vacío) |

**Ejemplo de solicitud:**
```json
{
  "numero_cuenta_destino": "400087654321098765",
  "monto": 500.0,
  "descripcion": "Pago de renta"
}
```

**Respuesta exitosa `201`:**
```json
{
  "id": 5,
  "tipo": "transferencia",
  "monto": 500.0,
  "descripcion": "Pago de renta",
  "estado": "completada",
  "servicio": null,
  "referencia_servicio": null,
  "cuenta_origen_id": 1,
  "cuenta_destino_id": 4,
  "creada_en": "2025-03-07T12:00:00"
}
```

**Errores posibles:**
- `400` — Saldo insuficiente
- `400` — No puedes transferirte a ti mismo
- `400` — Monto debe ser mayor a 0
- `403` — Límite de gasto mensual alcanzado
- `403` — No puedes transferir a un usuario desactivado
- `401` — Token inválido o expirado
- `404` — No tienes cuenta de débito
- `404` — Cuenta destino no encontrada

---

### `POST /operaciones/pago-servicio`
Paga un servicio doméstico o de telecomunicaciones.  
Por defecto se usa el saldo de la cuenta de **débito**, pero opcionalmente puedes **cargarlo a la tarjeta de crédito** (aumentando la deuda hasta el límite disponible).

**Headers requeridos:** `Authorization: Bearer <token>`

**Headers opcionales en respuesta:**
- `X-Gasto-Advertencia`: se envía cuando el movimiento hace que alcances el 90% de tu límite de gasto mensual.

**Body (JSON):**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `servicio` | string (enum) | ✅ | Nombre del servicio a pagar (ver valores válidos abajo) |
| `referencia` | string | ✅ | Número de contrato, número de teléfono u otro identificador del recibo |
| `monto` | float | ✅ | Cantidad a pagar (debe ser mayor a 0) |
| `usar_credito` | boolean | ❌ | Si es `true`, el pago se carga a la tarjeta de crédito; si es `false` o se omite, se usa la cuenta de débito |

**Valores válidos para `servicio`:**
| Valor | Descripción |
|-------|-------------|
| `CFE` | Comisión Federal de Electricidad |
| `Infinitum` | Internet Telmex |
| `Telcel` | Telefonía móvil Telcel |
| `Agua` | Servicio de agua |
| `Gas` | Servicio de gas |

**Ejemplo de solicitud:**
```json
{
  "servicio": "CFE",
  "referencia": "123456789012",
  "monto": 450.0,
  "usar_credito": false
}
```

**Ejemplo de solicitud usando tarjeta de crédito:**
```json
{
  "servicio": "CFE",
  "referencia": "123456789012",
  "monto": 450.0,
  "usar_credito": true
}
```

**Respuesta exitosa `201`:**
```json
{
  "id": 6,
  "tipo": "pago_servicio",
  "monto": 450.0,
  "descripcion": "Pago CFE - Ref: 123456789012",
  "estado": "completada",
  "servicio": "CFE",
  "referencia_servicio": "123456789012",
  "cuenta_origen_id": 1,
  "cuenta_destino_id": null,
  "creada_en": "2025-03-07T12:30:00"
}
```

**Errores posibles:**
- `400` — Saldo insuficiente (cuando se usa cuenta de débito)
- `400` — Límite de crédito insuficiente (cuando se usa tarjeta de crédito)
- `400` — Monto debe ser mayor a 0
- `403` — Límite de gasto mensual alcanzado
- `401` — Token inválido o expirado
- `404` — No tienes cuenta de débito
- `404` — No tienes cuenta de crédito (cuando se usa tarjeta de crédito)
- `422` — Servicio no válido (valor fuera del enum)

---

### `POST /operaciones/pago-credito`
Paga la deuda de la tarjeta de crédito usando el saldo disponible en la cuenta de débito. Si el monto enviado es mayor a la deuda actual, solo se cobra lo que se debe.

**Headers requeridos:** `Authorization: Bearer <token>`

**Body (JSON):**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `monto` | float | ✅ | Cantidad a abonar a la deuda (debe ser mayor a 0) |

**Ejemplo de solicitud:**
```json
{
  "monto": 1000.0
}
```

**Respuesta exitosa `201`:**
```json
{
  "id": 7,
  "tipo": "pago_credito",
  "monto": 1000.0,
  "descripcion": "Pago de tarjeta de crédito",
  "estado": "completada",
  "servicio": null,
  "referencia_servicio": null,
  "cuenta_origen_id": 1,
  "cuenta_destino_id": 2,
  "creada_en": "2025-03-07T13:00:00"
}
```

**Errores posibles:**
- `400` — Saldo insuficiente en cuenta de débito
- `400` — No tienes deuda en tu tarjeta de crédito
- `400` — Monto debe ser mayor a 0
- `401` — Token inválido o expirado
- `404` — Cuentas no encontradas

---

### `GET /operaciones/servicios-disponibles`
Lista todos los servicios disponibles para pago. Útil para poblar un selector en la app móvil.

**Sin autenticación requerida.**

**Sin body.**

**Respuesta exitosa `200`:**
```json
[
  { "servicio": "CFE" },
  { "servicio": "Infinitum" },
  { "servicio": "Telcel" },
  { "servicio": "Agua" },
  { "servicio": "Gas" }
]
```

---

## `/soporte` — Chat de soporte (BDMLT)

Chat de soporte usando tu modelo local de Ollama (vía OpenAI SDK).  
**Sin autenticación requerida.** La memoria vive en RAM y se limpia/recorta automáticamente.

### `GET /soporte/health`
Devuelve estado del módulo de soporte y configuración activa (modelo, base_url, límites).

**Sin body.**

**Respuesta exitosa `200`:**
```json
{
  "status": "ok",
  "model": "qwen2.5:3b",
  "base_url": "http://localhost:11434/v1",
  "chats_en_ram": 2,
  "max_chats_en_ram": 200,
  "max_mensajes_por_chat": 20,
  "ttl_segundos": 1800
}
```

---

### `POST /soporte/chat`
Envía un mensaje al asistente de soporte BDMLT.  
Si no envías `session_id`, se crea una conversación nueva y se regresa el `session_id` para continuar el hilo.

**Body (JSON):**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `session_id` | string | ❌ | Identificador de conversación (si se omite, se crea uno nuevo) |
| `message` | string | ✅ | Mensaje del usuario |

**Ejemplo de solicitud (nueva conversación):**
```json
{
  "message": "Hola, ¿cómo veo mis movimientos?"
}
```

**Ejemplo de solicitud (continuar conversación):**
```json
{
  "session_id": "c2c6d78e1c5b4a5b8d3d7f0d9df2b1a8",
  "message": "¿Y puedo filtrar por transferencias?"
}
```

**Respuesta exitosa `200`:**
```json
{
  "session_id": "c2c6d78e1c5b4a5b8d3d7f0d9df2b1a8",
  "reply": "Para ver tus movimientos usa GET /cuentas/movimientos. Puedes filtrar con ?tipo=transferencia y ajustar limite/orden.",
  "memory_messages": 6
}
```

**Errores posibles:**
- `422` — Body inválido (por ejemplo `message` vacío)
- `500` — Error consultando el modelo local

---

### `DELETE /soporte/chat/{session_id}`
Borra el historial en RAM de una sesión.

**Sin body.**

**Respuesta exitosa `200`:**
```json
{ "mensaje": "Chat 'c2c6d78e1c5b4a5b8d3d7f0d9df2b1a8' limpiado" }
```

## Resumen de endpoints

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| POST | `/auth/registro` | ❌ | Registrar nuevo usuario (envía correo de verificación) |
| POST | `/auth/login` | ❌ | Iniciar sesión |
| GET | `/auth/me` | ✅ | Perfil del usuario autenticado |
| PATCH | `/auth/me` | ✅ | Actualizar perfil (nombre, contraseña, foto) |
| POST | `/auth/forgot-password` | ❌ | Iniciar flujo de recuperación de contraseña (envía correo) |
| GET | `/auth/reset-password-form` | ❌ | HTML para restablecer contraseña con token |
| POST | `/auth/reset-password` | ❌ | Actualizar contraseña usando token de recuperación |
| GET | `/auth/verificar-email-form` | ❌ | HTML que verifica automáticamente el correo con token |
| POST | `/auth/verificar-email` | ❌ | Verificar correo y activar cuenta |
| POST | `/auth/desactivar` | ❌ | Desactivar cuenta de usuario (no aplica a la cuenta default) |
| GET | `/cuentas/` | ✅ | Ver cuentas débito y crédito |
| GET | `/cuentas/mi-qr` | ✅ | Datos para QR de transferencia |
| GET | `/cuentas/movimientos` | ✅ | Historial de movimientos |
| GET | `/cuentas/limite-gasto` | ✅ | Ver límite de gasto mensual y gasto del mes |
| PUT | `/cuentas/limite-gasto` | ✅ | Configurar límite de gasto mensual |
| POST | `/operaciones/transferencia` | ✅ | Transferir dinero a otro usuario |
| POST | `/operaciones/pago-servicio` | ✅ | Pagar CFE, Infinitum, Telcel, Agua o Gas |
| POST | `/operaciones/pago-credito` | ✅ | Pagar deuda de tarjeta de crédito |
| GET | `/operaciones/servicios-disponibles` | ❌ | Listar servicios disponibles |
| GET | `/soporte/health` | ❌ | Salud/config del chat de soporte |
| POST | `/soporte/chat` | ❌ | Enviar mensaje al soporte BDMLT (con memoria) |
| DELETE | `/soporte/chat/{session_id}` | ❌ | Limpiar memoria de una sesión de soporte |