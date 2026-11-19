# Manual de Pruebas y Validación de APIs REST - SubastAgro (README_TEST_5)
**Dirigido a:** Prof. LUIS GUILLERMO MORELO  
**Base de Datos:** `subastagro_db` (PostgreSQL 18)  
**URL Base Local:** `http://localhost:8000/api/v1`

## 1. Preparación del Entorno y Seeding
1. Crear la base de datos en PostgreSQL 18: `CREATE DATABASE subastagro_db;`
2. Ejecutar sembrado inicial: `python seed.py`
3. Iniciar servidor: `uvicorn app.main:app --reload`

### Usuarios de Prueba Sembrados
- **Administrador**: `admin@subastagro.co` / `AdminPassword2026*`
- **Ganadero**: `ganadero@subastagro.co` / `GanaderoPassword2026*`
- **Comprador**: `comprador@subastagro.co` / `CompradorPassword2026*`

## 2. Pruebas por Dominio con cURL

### Dominio 1: Auth (`/api/v1/auth`)
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "ganadero@subastagro.co", "password": "GanaderoPassword2026*"}'
```
- **Verificar sesión (`GET /auth/me`)**:
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```
- **Renovar token (`POST /auth/refresh`)** y **Cerrar sesión (`POST /auth/logout`)**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<REFRESH_TOKEN>"}'

curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Dominio 2: Usuarios (`/api/v1/users`)
- `POST /api/v1/users` (Registro público de `GANADERO` o `COMPRADOR`)
- `GET /api/v1/users` (Listado administrativo - requiere rol `ADMINISTRADOR`)
- `GET /api/v1/users/{id}` (Perfil propio o Admin)
- `PATCH /api/v1/users/{id}/status` (`{"estado": false}` - solo `ADMINISTRADOR`)

### Dominio 3: Razas y Lotes de Ganado (`/api/v1/cattle-lots`)
```bash
# Listar razas (Público)
curl -X GET "http://localhost:8000/api/v1/cattle-lots/breeds"

# Registrar lote (Solo GANADERO)
curl -X POST "http://localhost:8000/api/v1/cattle-lots" \
  -H "Authorization: Bearer <TOKEN_GANADERO>" \
  -H "Content-Type: application/json" \
  -d '{
    "raza_id": "<UUID_RAZA_BRAHMAN>",
    "codigo_lote": "LOT-2026-BRH-001",
    "cantidad_cabezas": 25,
    "peso_promedio_kg": 460.5,
    "vacunacion_al_dia": true,
    "ubicacion_hacienda": "Hacienda La Esperanza, Montería - Córdoba"
  }'

# Consultar lotes propios (Ownership)
curl -X GET "http://localhost:8000/api/v1/cattle-lots/my-lots" \
  -H "Authorization: Bearer <TOKEN_GANADERO>"
```

### Dominio 4: Eventos de Subasta (`/api/v1/auctions`)
```bash
# Programar subasta (GANADERO propietario o ADMINISTRADOR)
curl -X POST "http://localhost:8000/api/v1/auctions" \
  -H "Authorization: Bearer <TOKEN_GANADERO>" \
  -H "Content-Type: application/json" \
  -d '{
    "lote_id": "<UUID_LOTE>",
    "precio_base_kilo": 8500.00,
    "incremento_minimo_puja": 100.00,
    "fecha_inicio": "2026-11-18T12:00:00Z",
    "fecha_cierre": "2026-11-25T18:00:00Z",
    "estado_subasta": "ACTIVA"
  }'

# Listar subastas activas
curl -X GET "http://localhost:8000/api/v1/auctions/active"
```

### Dominio 5: Pujas y Ofertas (`/api/v1/bids`)
```bash
# Emitir puja (Solo COMPRADOR)
curl -X POST "http://localhost:8000/api/v1/bids" \
  -H "Authorization: Bearer <TOKEN_COMPRADOR>" \
  -H "Content-Type: application/json" \
  -d '{"subasta_id": "<UUID_SUBASTA>", "monto_ofertado_kilo": 8700.00}'

# Historial de pujas de la subasta
curl -X GET "http://localhost:8000/api/v1/bids/auction/<UUID_SUBASTA>" \
  -H "Authorization: Bearer <TOKEN_COMPRADOR>"

# Mis pujas (Ownership)
curl -X GET "http://localhost:8000/api/v1/bids/my-bids" \
  -H "Authorization: Bearer <TOKEN_COMPRADOR>"
```

### Dominio 6: Actas de Adjudicación (`/api/v1/adjudications`)
```bash
# Cerrar subasta y generar acta al mejor postor (Solo ADMINISTRADOR)
curl -X POST "http://localhost:8000/api/v1/adjudications/close-auction/<UUID_SUBASTA>" \
  -H "Authorization: Bearer <TOKEN_ADMIN>"

# Consultar mis actas ganadas (Solo COMPRADOR)
curl -X GET "http://localhost:8000/api/v1/adjudications/my-adjudications" \
  -H "Authorization: Bearer <TOKEN_COMPRADOR>"
```

## 3. Matriz de Validación de Errores y Seguridad
- **400 Bad Request**: Puja menor a `oferta_actual + incremento_minimo`.
- **401 Unauthorized**: Token ausente, expirado o invalidado tras `/auth/logout`.
- **403 Forbidden**: Un `COMPRADOR` intentando crear un lote (`POST /cattle-lots`) o un `GANADERO B` intentando editar/eliminar el lote del `GANADERO A`.
- **404 Not Found**: UUID inexistente.
- **422 Unprocessable Entity**: Datos inválidos según esquemas Pydantic v2.

## 4. Checklist de Validación Final
- [x] Base de datos `subastagro_db` inicializada en PostgreSQL 18.
- [x] Autenticación JWT + Cookies HttpOnly + Refresh Token Rotation.
- [x] RBAC y Ownership validados en todos los dominios.
- [x] Sin exposición de `password_hash` en respuestas JSON.
