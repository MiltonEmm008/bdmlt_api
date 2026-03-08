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
Registra un nuevo usuario en el sistema. Crea automáticamente una cuenta de débito (con $1,000 de saldo inicial) y una cuenta de crédito (con límite de $5,000) para el usuario.

**Body (JSON):**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | ✅ | Nombre completo del usuario |
| `email` | string | ✅ | Correo electrónico (debe ser único) |
| `password` | string | ✅ | Contraseña (mínimo 6 caracteres) |

**Ejemplo de solicitud:**
```json
{
  "nombre": "Milton Martínez",
  "email": "milton@correo.com",
  "password": "mipassword123"
}
```

**Respuesta exitosa `201`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
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
  "creado_en": "2025-03-07T10:30:00"
}
```

**Errores posibles:**
- `401` — Token inválido o expirado
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
    "deuda": 0.0,
    "limite_credito": 0.0,
    "creada_en": "2025-03-07T10:30:00"
  },
  {
    "id": 2,
    "numero": "500098765432109876",
    "tipo": "credito",
    "saldo": 0.0,
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

## `/operaciones` — Operaciones bancarias

### `POST /operaciones/transferencia`
Transfiere dinero desde la cuenta de débito del usuario autenticado hacia la cuenta de débito de otro usuario.

**Headers requeridos:** `Authorization: Bearer <token>`

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
- `401` — Token inválido o expirado
- `404` — No tienes cuenta de débito
- `404` — Cuenta destino no encontrada

---

### `POST /operaciones/pago-servicio`
Paga un servicio doméstico o de telecomunicaciones.  
Por defecto se usa el saldo de la cuenta de **débito**, pero opcionalmente puedes **cargarlo a la tarjeta de crédito** (aumentando la deuda hasta el límite disponible).

**Headers requeridos:** `Authorization: Bearer <token>`

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

## Resumen de endpoints

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| POST | `/auth/registro` | ❌ | Registrar nuevo usuario |
| POST | `/auth/login` | ❌ | Iniciar sesión |
| GET | `/auth/me` | ✅ | Perfil del usuario autenticado |
| GET | `/cuentas/` | ✅ | Ver cuentas débito y crédito |
| GET | `/cuentas/mi-qr` | ✅ | Datos para QR de transferencia |
| GET | `/cuentas/movimientos` | ✅ | Historial de movimientos |
| POST | `/operaciones/transferencia` | ✅ | Transferir dinero a otro usuario |
| POST | `/operaciones/pago-servicio` | ✅ | Pagar CFE, Infinitum, Telcel, Agua o Gas |
| POST | `/operaciones/pago-credito` | ✅ | Pagar deuda de tarjeta de crédito |
| GET | `/operaciones/servicios-disponibles` | ❌ | Listar servicios disponibles |